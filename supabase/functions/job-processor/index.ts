import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
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
  INITIAL_DELAY: 1000, // 1 second
  MAX_DELAY: 8000, // 8 seconds
  BACKOFF_FACTOR: 2
}

// Add memory management
const MEMORY_CONFIG = {
  LIMIT: 512 * 1024 * 1024, // 512MB
  WARNING_THRESHOLD: 384 * 1024 * 1024 // 384MB
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
const supabaseClient = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
)

// Job execution functions
async function executeParseJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  const { documentId, storagePath } = job.payload

  if (!documentId || !storagePath) {
    throw new Error('Missing required parameters: documentId, storagePath')
  }

  // Call doc-parser with required parameters
  const { data: parserResult, error: parserError } = await supabase.functions.invoke('doc-parser', {
    body: {
      jobId: job.id,
      documentId: documentId,
      storagePath: storagePath
    }
  })

  if (parserError) {
    throw new Error(`Doc-parser failed: ${parserError.message}`)
  }

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
      documentId: job.document_id,
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
    const { error: insertError } = await supabaseClient
      .from('document_chunks')
      .insert(chunks.map(chunk => ({
        document_id: job.document_id,
        content: chunk,
        metadata: job.payload.metadata
      })))

    if (insertError) {
      throw insertError
    }

    // Create completion job
    await createNextJob(job.document_id, 'complete', {
      documentId: job.document_id,
      totalChunks: chunks.length
    })

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
    const { error: updateError } = await supabaseClient
      .from('documents')
      .update({
        status: 'completed',
        processed_at: new Date().toISOString(),
        metadata: {
          ...job.payload.metadata,
          total_chunks: job.payload.totalChunks,
          completed_at: new Date().toISOString()
        }
      })
      .eq('id', job.document_id)

    if (updateError) {
      throw updateError
    }

    // Create notification job
    await createNextJob(job.document_id, 'notify', {
      documentId: job.document_id,
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
    const { data: document, error: docError } = await supabaseClient
      .from('documents')
      .select('user_id')
      .eq('id', job.document_id)
      .single()

    if (docError || !document) {
      throw new Error('Failed to get document owner')
    }

    // Insert notification
    const { error: notifyError } = await supabaseClient
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
  const { error } = await supabaseClient
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

async function processJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
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
        result = await executeParseJob(supabase, job)
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

serve(async (req) => {
  metrics.startTime = Date.now()
  metrics.jobStartTime = 0
  
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  // Handle unsupported methods
  if (!['GET', 'POST', 'OPTIONS'].includes(req.method)) {
    return new Response('Method not allowed', { 
      status: 405,
      headers: {
        ...corsHeaders,
        'Allow': 'GET, POST, OPTIONS',
        'Content-Type': 'text/plain'
      }
    })
  }

  // Health check
  if (req.method === 'GET') {
    return new Response(
      JSON.stringify({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        memory: Deno.memoryUsage(),
        config: {
          retries: RETRY_CONFIG,
          memory: MEMORY_CONFIG
        }
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  try {
    console.log('🔄 Processing request...')
    logMetrics('request-start')
    
    if (!checkMemory()) {
      throw new Error('Memory limit exceeded before processing')
    }
    
    // Get pending jobs
    const { data: jobs, error: jobError } = await supabaseClient
      .from('processing_jobs')
      .select('*')
      .eq('status', 'pending')
      .order('priority', { ascending: false })
      .order('created_at', { ascending: true })
      .limit(5)

    if (jobError) {
      throw new Error(`Failed to fetch jobs: ${jobError.message}`)
    }

    if (!jobs || jobs.length === 0) {
      console.log('ℹ️ No pending jobs found')
      logMetrics('no-jobs')
      return new Response(
        JSON.stringify({ 
          message: 'No pending jobs',
          metrics: {
            processingTime: Date.now() - metrics.startTime,
            memoryUsage: Deno.memoryUsage()
          }
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Process jobs sequentially
    const results = []
    for (const job of jobs) {
      const result = await processJob(supabaseClient, job)
      results.push({ jobId: job.id, result })
    }

    return new Response(
      JSON.stringify({ success: true, results }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('❌ Job processor error:', error)
    logMetrics('fatal-error')
    return new Response(
      JSON.stringify({ 
        error: error.message,
        metrics: {
          processingTime: Date.now() - metrics.startTime,
          jobTime: metrics.jobStartTime ? Date.now() - metrics.jobStartTime : 0,
          memoryUsage: Deno.memoryUsage()
        }
      }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}) 