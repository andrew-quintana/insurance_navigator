// @deno-types="https://deno.land/x/types/deno.d.ts"

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.21.0'
import { corsHeaders } from '../_shared/cors.ts'
import { OpenAIEmbeddings } from '../_shared/embeddings.ts'

// Performance monitoring
const metrics = {
  startTime: 0,
  jobStartTime: 0,
  memoryUsage: 0
}

function logMetrics(stage: string, jobType?: string) {
  const memory = Deno.memoryUsage()
  const heapUsed = Math.round(memory.heapUsed / 1024 / 1024)
  const rss = Math.round(memory.rss / 1024 / 1024)
  console.log(`
📊 Performance Metrics - ${stage}${jobType ? ` (${jobType})` : ''}:
- Processing Time: ${Date.now() - metrics.startTime}ms
- Job Time: ${metrics.jobStartTime ? Date.now() - metrics.jobStartTime : 0}ms
- Heap Used: ${heapUsed}MB
- RSS: ${rss}MB
`)
}

interface ProcessingJob {
  id: string;
  document_id: string;
  job_type: 'parse' | 'chunk' | 'embed' | 'complete' | 'notify';
  payload: any;
  retry_count: number;
  priority: number;
}

interface JobResult {
  success: boolean;
  error?: string;
  data?: any;
}

// Add retry configuration
const RETRY_CONFIG = {
  MAX_RETRIES: 3,
  INITIAL_DELAY: 1000,
  BACKOFF_FACTOR: 2,
  MAX_DELAY: 10000
}

// Add memory management
const MEMORY_CONFIG = {
  LIMIT: 100 * 1024 * 1024, // 100MB
  WARNING_THRESHOLD: 80 * 1024 * 1024 // 80MB
}

// Add retry helper
async function withRetry<T>(
  operation: () => Promise<T>,
  retryCount = 0
): Promise<T> {
  try {
    return await operation()
  } catch (error) {
    if (retryCount >= RETRY_CONFIG.MAX_RETRIES) {
      throw error
    }

    const delay = Math.min(
      RETRY_CONFIG.INITIAL_DELAY * Math.pow(RETRY_CONFIG.BACKOFF_FACTOR, retryCount),
      RETRY_CONFIG.MAX_DELAY
    )

    console.log(`⚠️ Operation failed, retrying in ${delay}ms (attempt ${retryCount + 1}/${RETRY_CONFIG.MAX_RETRIES})`)
    await new Promise(resolve => setTimeout(resolve, delay))
    return withRetry(operation, retryCount + 1)
  }
}

// Add memory check
function checkMemory(): boolean {
  const memory = Deno.memoryUsage()
  const used = memory.heapUsed + memory.external
  
  if (used > MEMORY_CONFIG.LIMIT) {
    console.error(`❌ Memory limit exceeded: ${Math.round(used / 1024 / 1024)}MB used`)
    return false
  }
  
  if (used > MEMORY_CONFIG.WARNING_THRESHOLD) {
    console.warn(`⚠️ High memory usage: ${Math.round(used / 1024 / 1024)}MB used`)
  }

  return true
}

console.log('🔄 Job processor starting...')

// Initialize Supabase client
const supabase = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
)

// Job execution functions
async function executeParseJob(job: ProcessingJob): Promise<JobResult> {
  const { document_id, raw_storage_path, raw_storage_bucket, final_storage_path, final_storage_bucket, content_type } = job.payload

  if (!document_id || !raw_storage_path || !raw_storage_bucket || !final_storage_path || !final_storage_bucket || !content_type) {
    throw new Error('Missing required parameters in payload')
  }

  console.log('🔄 Executing parse job:', {
    jobId: job.id,
    documentId: document_id,
    rawPath: raw_storage_path,
    timestamp: new Date().toISOString()
  })

  // Call doc-parser with required parameters
  const { data: parserResult, error: parserError } = await supabase.functions.invoke('doc-parser', {
    body: {
      jobId: job.id,
      payload: {
        document_id,
        raw_storage_path,
        raw_storage_bucket,
        final_storage_path,
        final_storage_bucket,
        content_type
      }
    },
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
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

  if (!parserResult) {
    throw new Error('Doc-parser returned no result')
  }

  console.log('✅ Doc-parser completed successfully:', {
    jobId: job.id,
    documentId: document_id,
    timestamp: new Date().toISOString()
  })

  return {
    success: true,
    data: parserResult
  }
}

async function executeChunkJob(job: ProcessingJob): Promise<JobResult> {
  console.log(`📄 Executing chunk job for document ${job.document_id}`)
  
  try {
    const content = job.payload.content
    if (!content) {
      throw new Error('No content provided for chunking')
    }

    // Simple chunking strategy - split by paragraphs
    const chunks = content
      .split('\n\n')
      .filter(chunk => chunk.trim().length > 0)
      .map(chunk => chunk.trim())

    // Create embedding job for chunks
    await createNextJob(job.document_id, 'embed', {
      document_id: job.document_id,
      chunks,
      metadata: job.payload.metadata
    })

    return { success: true, data: { chunks: chunks.length } }
  } catch (error) {
    console.error(`❌ Chunk job failed:`, error)
    return { success: false, error: error.message }
  }
}

async function executeEmbedJob(job: ProcessingJob): Promise<JobResult> {
  console.log(`📄 Executing embed job for document ${job.document_id}`)
  
  try {
    const chunks = job.payload.chunks
    if (!chunks || !Array.isArray(chunks)) {
      throw new Error('Invalid chunks data')
    }

    // Store chunks in document_chunks table
    const { error: insertError } = await supabase
      .from('document_chunks')
      .insert(chunks.map(chunk => ({
        document_id: job.document_id,
        content: chunk,
        metadata: job.payload.metadata
      })))

    if (insertError) {
      throw insertError
    }

    return { success: true, data: { chunks: chunks.length } }
  } catch (error) {
    console.error(`❌ Embed job failed:`, error)
    return { success: false, error: error.message }
  }
}

async function executeCompleteJob(job: ProcessingJob): Promise<JobResult> {
  console.log(`📄 Executing complete job for document ${job.document_id}`)
  
  try {
    // Update document status
    const { error: updateError } = await supabase
      .from('documents')
      .update({
        status: 'completed',
        metadata: {
          ...job.payload.metadata,
          completed_at: new Date().toISOString()
        }
      })
      .eq('id', job.document_id)

    if (updateError) {
      throw updateError
    }

    // Create notification job
    await createNextJob(job.document_id, 'notify', {
      document_id: job.document_id,
      status: 'completed',
      metadata: job.payload.metadata
    })

    return { success: true }
  } catch (error) {
    console.error(`❌ Complete job failed:`, error)
    return { success: false, error: error.message }
  }
}

async function executeNotifyJob(job: ProcessingJob): Promise<JobResult> {
  console.log(`📄 Executing notify job for document ${job.document_id}`)
  
  try {
    // Get document owner
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('user_id')
      .eq('id', job.document_id)
      .single()

    if (docError || !document) {
      throw new Error('Failed to get document owner')
    }

    // Insert notification
    const { error: notifyError } = await supabase
      .from('notifications')
      .insert({
        user_id: document.user_id,
        type: 'document_processed',
        payload: {
          document_id: job.document_id,
          status: job.payload.status,
          metadata: job.payload.metadata
        }
      })

    if (notifyError) {
      throw notifyError
    }

    return { success: true }
  } catch (error) {
    console.error(`❌ Notify job failed:`, error)
    return { success: false, error: error.message }
  }
}

async function createNextJob(
  documentId: string,
  jobType: ProcessingJob['job_type'],
  payload: any
): Promise<void> {
  const { error } = await supabase
    .from('processing_jobs')
    .insert({
      document_id: documentId,
      job_type: jobType,
      status: 'pending',
      payload,
      priority: 1,
      retry_count: 0
    })

  if (error) {
    throw new Error(`Failed to create ${jobType} job: ${error.message}`)
  }
}

async function processJob(job: ProcessingJob): Promise<JobResult> {
  try {
    // Update job status to running
    const { error: updateError } = await supabase
      .from('processing_jobs')
      .update({ 
        status: 'running',
        started_at: new Date().toISOString()
      })
      .eq('id', job.id)

    if (updateError) {
      throw new Error(`Failed to update job status: ${updateError.message}`)
    }

    // Process based on job type
    let result: JobResult
    switch (job.job_type) {
      case 'parse':
        result = await executeParseJob(job)
        break
      case 'chunk':
        result = await executeChunkJob(job)
        break
      case 'embed':
        result = await executeEmbedJob(job)
        break
      case 'complete':
        result = await executeCompleteJob(job)
        break
      case 'notify':
        result = await executeNotifyJob(job)
        break
      default:
        throw new Error(`Unsupported job type: ${job.job_type}`)
    }

    // Update job with result
    const { error: completeError } = await supabase
      .from('processing_jobs')
      .update({
        status: result.success ? 'completed' : 'failed',
        result: result.data || null,
        error_message: result.error || null,
        completed_at: new Date().toISOString()
      })
      .eq('id', job.id)

    if (completeError) {
      throw new Error(`Failed to update job completion: ${completeError.message}`)
    }

    return result
  } catch (error) {
    console.error('❌ Job processing failed:', error)
    
    // Update job status to failed
    await supabase
      .from('processing_jobs')
      .update({
        status: 'failed',
        error_message: error.message,
        completed_at: new Date().toISOString()
      })
      .eq('id', job.id)

    return {
      success: false,
      error: error.message
    }
  }
}

// Add result type
interface JobProcessingResult {
  jobId: string;
  result?: JobResult;
  error?: string;
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    metrics.startTime = Date.now()
    console.log('🔄 Processing request...')
    logMetrics('request-start')

    // Parse request
    let requestData
    try {
      const text = await req.text()
      console.log('📄 Raw request body:', text)
      
      try {
        requestData = text ? JSON.parse(text) : {}
      } catch (parseError) {
        console.error('❌ Failed to parse request body:', parseError)
        return new Response(JSON.stringify({ 
          error: 'Invalid JSON in request body',
          details: parseError instanceof Error ? parseError.message : 'Failed to parse JSON',
          receivedBody: text
        }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }
    } catch (readError) {
      console.error('❌ Failed to read request body:', readError)
      return new Response(JSON.stringify({ 
        error: 'Failed to read request body',
        details: readError instanceof Error ? readError.message : 'Unknown error reading request body'
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log('📄 Parsed request data:', requestData)

    // Validate required fields
    if (!requestData.jobId) {
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
    const { data: job, error: jobError } = await supabase
      .from('processing_jobs')
      .select('*')
      .eq('id', requestData.jobId)
      .single()

    if (jobError || !job) {
      console.error('❌ Failed to fetch job:', jobError)
      return new Response(JSON.stringify({ 
        error: 'Failed to fetch job',
        details: jobError?.message || 'Job not found'
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
    
    const result = await processJob(job)

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