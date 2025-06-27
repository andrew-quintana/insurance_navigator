/// <reference lib="deno.unstable" />
/// <reference lib="dom" />

// @deno-types="https://deno.land/x/types/deno.d.ts"
// @deno-types="npm:@types/node"

// deno-lint-ignore-file no-explicit-any
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

declare global {
  interface Deno {
    env: {
      get(key: string): string | undefined;
    };
  }
}

// Types
interface ProcessingJob {
  id: string
  document_id: string
  job_type: string
  status: string
  payload: {
    document_id: string
    storage_path: string
    content_type: string
    document_type?: string
    created_at?: string
  }
}

interface JobResult {
  success: boolean
  data?: any
  error?: string
}

// Initialize Supabase client
const supabaseClient = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
)

// Retry configuration
const MAX_RETRIES = 3;
const INITIAL_BACKOFF_MS = 1000;

interface ProcessRequest {
  jobId: string;
  documentId: string;
}

interface JobRecord {
  id: string;
  status: JobStatus;
  document_id: string;
  created_at: string;
  updated_at: string;
  error_message?: string;
  error_details?: unknown;
  metadata: Record<string, unknown>;
}

type JobStatus = 
  | 'STARTED'
  | 'PARSE_FAILED'
  | 'VECTORIZE_FAILED'
  | 'COMPLETED';

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  retries = MAX_RETRIES,
  backoff = INITIAL_BACKOFF_MS
): Promise<T> {
  try {
    return await operation();
  } catch (error) {
    if (retries === 0) {
      throw error;
    }
    console.log(`Operation failed, retrying in ${backoff}ms... (${retries} retries left)`);
    await sleep(backoff);
    return retryWithBackoff(operation, retries - 1, backoff * 2);
  }
}

async function getJob(
  supabase: any,
  jobId: string
): Promise<JobRecord | null> {
  const { data, error } = await supabase
    .from('jobs')
    .select('*')
    .eq('id', jobId)
    .single();

  if (error) {
    console.error(`Failed to get job: ${error.message}`);
    return null;
  }

  return data;
}

async function updateJobStatus(
  supabase: any,
  jobId: string,
  status: JobStatus,
  errorMessage?: string,
  errorDetails?: unknown
): Promise<void> {
  const { error } = await supabase
    .from('jobs')
    .update({
      status,
      error_message: errorMessage,
      error_details: errorDetails,
      updated_at: new Date().toISOString()
    })
    .eq('id', jobId);

  if (error) {
    console.error(`Failed to update job status: ${error.message}`);
  }
}

async function startProcessing(
  supabase: any,
  jobId: string,
  documentId: string
): Promise<void> {
  try {
    // Call doc-parser function with retry
    await retryWithBackoff(async () => {
      const parserResponse = await fetch(`${supabaseUrl}/functions/v1/doc-parser`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${supabaseServiceRoleKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ documentId })
      });

      if (!parserResponse.ok) {
        throw new Error(`Parser failed: ${await parserResponse.text()}`);
      }
      return parserResponse;
    });

    // Call vector-processor function with retry
    await retryWithBackoff(async () => {
      const vectorResponse = await fetch(`${supabaseUrl}/functions/v1/vector-processor`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${supabaseServiceRoleKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ documentId })
      });

      if (!vectorResponse.ok) {
        throw new Error(`Vectorization failed: ${await vectorResponse.text()}`);
      }
      return vectorResponse;
    });

    await updateJobStatus(supabase, jobId, 'COMPLETED');
  } catch (error) {
    let status: JobStatus = 'PARSE_FAILED';
    if (error.message.includes('Vectorization failed')) {
      status = 'VECTORIZE_FAILED';
    }
    await updateJobStatus(supabase, jobId, status, error.message, error);
    throw error;
  }
}

async function executeParseJob(job: ProcessingJob): Promise<JobResult> {
  const { document_id, storage_path, content_type, document_type } = job.payload

  if (!document_id || !storage_path || !content_type) {
    throw new Error('Missing required parameters in payload')
  }

  console.log('🔄 Executing parse job:', {
    jobId: job.id,
    documentId: document_id,
    storagePath: storage_path,
    timestamp: new Date().toISOString()
  })

  // Extract user_id from storage_path
  const userId = storage_path.split('/')[0]
  if (!userId) {
    throw new Error('Invalid storage path: missing user_id')
  }

  // Call doc-parser with required parameters
  const { data: parserResult, error: parserError } = await supabaseClient.functions.invoke('doc-parser', {
    body: JSON.stringify({
      jobId: job.id,
      payload: {
        document_id,
        raw_storage_path: storage_path,
        raw_storage_bucket: 'docs',
        final_storage_path: `${userId}/processed/${storage_path.split('/').pop()}`,
        final_storage_bucket: 'docs',
        content_type,
        document_type
      }
    })
  })

  if (parserError) {
    console.error('❌ Doc-parser error:', {
      error: parserError,
      jobId: job.id,
      documentId: document_id,
      timestamp: new Date().toISOString()
    })

    // Check if it's a non-2xx response with error details
    if (parserError.message && typeof parserError.message === 'string') {
      try {
        const errorDetails = JSON.parse(parserError.message)
        if (errorDetails.error) {
          throw new Error(`Doc-parser failed: ${errorDetails.error}`)
        }
      } catch (e) {
        // If we can't parse the error, just use the original message
      }
    }
    throw new Error(`Doc-parser failed: ${parserError.message}`)
  }

  console.log('✅ Doc-parser completed successfully:', {
    jobId: job.id,
    documentId: document_id,
    timestamp: new Date().toISOString()
  })

  // Call vector-processor after successful parsing
  console.log('🔄 Starting vectorization:', {
    jobId: job.id,
    documentId: document_id,
    timestamp: new Date().toISOString()
  })

  const processedPath = `${userId}/processed/${storage_path.split('/').pop()}`

  // Get the processed document content
  const { data: processedDoc, error: downloadError } = await supabaseClient
    .storage
    .from('docs')
    .download(`${userId}/processed/${storage_path.split('/').pop()}`)

  if (downloadError) {
    console.error('❌ Failed to download processed document:', {
      error: downloadError,
      jobId: job.id,
      documentId: document_id,
      timestamp: new Date().toISOString()
    })
    throw new Error(`Failed to download processed document: ${downloadError.message}`)
  }

  // Convert blob to text
  const extractedText = await processedDoc.text()

  const { data: vectorResult, error: vectorError } = await supabaseClient.functions.invoke('vector-processor', {
    body: JSON.stringify({
      documentId: document_id,
      extractedText,
      metadata: {
        content_type,
        document_type,
        storage_path: processedPath,
        processing_time: new Date().toISOString()
      }
    })
  })

  if (vectorError) {
    console.error('❌ Vector-processor error:', {
      error: vectorError,
      jobId: job.id,
      documentId: document_id,
      timestamp: new Date().toISOString()
    })

    throw new Error(`Vector-processor failed: ${vectorError.message}`)
  }

  console.log('✅ Vector-processor completed successfully:', {
    jobId: job.id,
    documentId: document_id,
    timestamp: new Date().toISOString()
  })

  return { success: true, data: { parserResult, vectorResult } }
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    console.log('🔄 Processing request...')

    // Parse request body
    let requestData: { jobId: string; documentId?: string } | null = null
    const contentType = req.headers.get('content-type')
    
    if (contentType?.includes('application/json')) {
      try {
        const text = await req.text()
        console.log('📄 Raw request body:', text)
        
        if (text) {
          requestData = JSON.parse(text)
          console.log('📄 Parsed request data:', requestData)
        }
      } catch (parseError) {
        console.error('❌ Failed to parse JSON body:', parseError)
        return new Response(JSON.stringify({ 
          error: 'Invalid JSON in request body',
          details: parseError instanceof Error ? parseError.message : 'Failed to parse JSON'
        }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }
    }

    // Validate jobId
    if (!requestData?.jobId) {
      console.error('❌ Missing jobId in request:', requestData)
      return new Response(JSON.stringify({ 
        error: 'Missing required parameter: jobId',
        details: 'The jobId parameter is required for job processing',
        receivedData: requestData
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    // Get job details
    console.log('🔍 Fetching job details:', { jobId: requestData.jobId })
    const { data: job, error: jobError } = await supabaseClient
      .from('processing_jobs')
      .select('*')
      .eq('id', requestData.jobId)
      .single()

    if (jobError || !job) {
      console.error('❌ Failed to fetch job:', jobError)
      return new Response(JSON.stringify({ 
        error: 'Failed to fetch job',
        details: jobError?.message || 'Job not found',
        jobId: requestData.jobId
      }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    // Process job
    console.log('🔄 Processing job:', { 
      jobId: job.id, 
      documentId: job.document_id,
      jobType: job.job_type
    })
    
    const result = await executeParseJob(job)

    console.log('✅ Job processing complete:', {
      jobId: job.id,
      success: result.success,
      error: result.error
    })

    return new Response(JSON.stringify({ 
      success: true,
      jobId: job.id,
      result
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('❌ Job processing failed:', error)
    
    return new Response(JSON.stringify({ 
      error: 'Job processing failed',
      details: error instanceof Error ? error.message : 'Unknown error'
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
}) 