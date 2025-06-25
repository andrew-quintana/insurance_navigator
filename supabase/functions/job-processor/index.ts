import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "@supabase/supabase-js"
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
  job_type: 'parse' | 'embed' | 'complete';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  payload: any;
  created_at: string;
}

interface JobResult {
  success: boolean;
  data?: any;
  error?: string;
  nextJob?: Partial<ProcessingJob>;
  metrics?: any;
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

serve(async (req) => {
  metrics.startTime = Date.now()
  metrics.jobStartTime = 0
  
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
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
    
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Get next pending job with retries
    console.log('📥 Fetching pending jobs...')
    const { data: jobs, error: jobError } = await withRetry(async () => {
      return await supabaseClient
        .from('processing_jobs')
        .select('*')
        .eq('status', 'pending')
        .order('priority', { ascending: false })
        .order('created_at', { ascending: true })
        .limit(1)
    })

    if (jobError) {
      console.error('❌ Failed to fetch jobs:', jobError)
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

    const job = jobs[0] as ProcessingJob
    metrics.jobStartTime = Date.now()
    
    console.log(`📝 Processing job ${job.id} of type ${job.job_type} for document ${job.document_id}`)
    console.log('📦 Job payload:', job.payload)
    logMetrics('job-start', job.job_type)

    if (!checkMemory()) {
      throw new Error('Memory limit exceeded before job processing')
    }

    // Update job status to processing with retries
    console.log('🔄 Updating job status to processing...')
    await withRetry(async () => {
      await supabaseClient
        .from('processing_jobs')
        .update({ 
          status: 'processing', 
          started_at: new Date().toISOString(),
          metadata: {
            memoryAtStart: Deno.memoryUsage(),
            retryCount: 0
          }
        })
        .eq('id', job.id)
    })

    // Process job based on type with retries
    let result: JobResult
    switch (job.job_type) {
      case 'parse':
        console.log('🔍 Executing parse job...')
        result = await executeParseJob(supabaseClient, job)
        break
      case 'embed':
        console.log('🧮 Executing embed job...')
        result = await executeEmbedJob(supabaseClient, job)
        break
      case 'complete':
        console.log('✅ Executing complete job...')
        result = await executeCompleteJob(supabaseClient, job)
        break
      default:
        throw new Error(`Unknown job type: ${job.job_type}`)
    }

    if (!checkMemory()) {
      throw new Error('Memory limit exceeded after job processing')
    }

    logMetrics('job-complete', job.job_type)

    // Update job status with retries
    if (result.success) {
      console.log(`✅ Job ${job.id} completed successfully`)
      console.log('📦 Result data:', result.data)
      
      await withRetry(async () => {
        await supabaseClient
          .from('processing_jobs')
          .update({
            status: 'completed',
            completed_at: new Date().toISOString(),
            result: result.data,
            metadata: {
              ...result.metrics,
              processingTime: Date.now() - metrics.jobStartTime,
              totalTime: Date.now() - metrics.startTime,
              memoryAtEnd: Deno.memoryUsage()
            }
          })
          .eq('id', job.id)
      })

      // Create next job if specified
      if (result.nextJob) {
        console.log('🔄 Creating next job:', result.nextJob)
        await withRetry(async () => {
          await supabaseClient
            .from('processing_jobs')
            .insert({
              document_id: job.document_id,
              ...result.nextJob,
              status: 'pending',
              created_at: new Date().toISOString(),
              metadata: {
                previousJobId: job.id,
                previousJobType: job.job_type,
                previousJobTime: Date.now() - metrics.jobStartTime,
                retryCount: 0
              }
            })
        })
      }
    } else {
      console.error(`❌ Job ${job.id} failed:`, result.error)
      logMetrics('job-failed', job.job_type)
      await withRetry(async () => {
        await supabaseClient
          .from('processing_jobs')
          .update({
            status: 'failed',
            error: result.error,
            completed_at: new Date().toISOString(),
            metadata: {
              processingTime: Date.now() - metrics.jobStartTime,
              totalTime: Date.now() - metrics.startTime,
              memoryAtFailure: Deno.memoryUsage()
            }
          })
          .eq('id', job.id)
      })
    }

    return new Response(
      JSON.stringify({
        ...result,
        metrics: {
          processingTime: Date.now() - metrics.startTime,
          jobTime: Date.now() - metrics.jobStartTime,
          memoryUsage: Deno.memoryUsage()
        }
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('❌ Fatal error:', error)
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

async function executeParseJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  const jobMetrics = {
    startTime: Date.now(),
    parseStartTime: 0,
    parseEndTime: 0
  }
  
  try {
    console.log(`🔍 Starting parse job for document ${job.document_id}`)
    console.log('📦 Parse job payload:', job.payload)
    
    // Call doc-parser function
    console.log('📞 Calling doc-parser function...')
    jobMetrics.parseStartTime = Date.now()
    
    const { data: parseResult, error: parseError } = await supabase.functions.invoke('doc-parser', {
      body: JSON.stringify({
        documentId: job.document_id,
        storagePath: job.payload.storage_path
      })
    })

    jobMetrics.parseEndTime = Date.now()

    if (parseError) {
      console.error('❌ Doc-parser error:', parseError)
      throw new Error(`Parsing failed: ${parseError.message}`)
    }

    console.log('✅ Doc-parser completed successfully')
    console.log('📦 Parse result:', parseResult)

    return {
      success: true,
      data: parseResult,
      nextJob: {
        job_type: 'embed',
        payload: {
          extractedText: parseResult.extractedText,
          documentId: job.document_id,
          storagePath: job.payload.storage_path
        }
      },
      metrics: {
        totalTime: Date.now() - jobMetrics.startTime,
        parseTime: jobMetrics.parseEndTime - jobMetrics.parseStartTime,
        memory: Deno.memoryUsage()
      }
    }

  } catch (error) {
    console.error(`❌ Parse job failed:`, error)
    return { 
      success: false, 
      error: error.message,
      metrics: {
        totalTime: Date.now() - jobMetrics.startTime,
        parseTime: jobMetrics.parseEndTime - jobMetrics.parseStartTime,
        memory: Deno.memoryUsage()
      }
    }
  }
}

async function executeEmbedJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  const jobMetrics = {
    startTime: Date.now(),
    vectorStartTime: 0,
    vectorEndTime: 0
  }
  
  try {
    console.log(`🧮 Starting embed job for document ${job.document_id}`)
    console.log('📦 Embed job payload:', job.payload)
    
    // Call vector-processor function
    console.log('📞 Calling vector-processor function...')
    jobMetrics.vectorStartTime = Date.now()
    
    const { data: vectorResult, error: vectorError } = await supabase.functions.invoke('vector-processor', {
      body: JSON.stringify({
        documentId: job.document_id,
        extractedText: job.payload.extractedText,
        storagePath: job.payload.storagePath
      })
    })

    jobMetrics.vectorEndTime = Date.now()

    if (vectorError) {
      console.error('❌ Vector-processor error:', vectorError)
      throw new Error(`Vector processing failed: ${vectorError.message}`)
    }

    console.log('✅ Vector-processor completed successfully')
    console.log('📦 Vector result:', vectorResult)

    return {
      success: true,
      data: vectorResult,
      nextJob: {
        job_type: 'complete',
        payload: {
          vectorCount: vectorResult.vectorCount,
          documentId: job.document_id
        }
      },
      metrics: {
        totalTime: Date.now() - jobMetrics.startTime,
        vectorTime: jobMetrics.vectorEndTime - jobMetrics.vectorStartTime,
        memory: Deno.memoryUsage()
      }
    }

  } catch (error) {
    console.error(`❌ Embed job failed:`, error)
    return { 
      success: false, 
      error: error.message,
      metrics: {
        totalTime: Date.now() - jobMetrics.startTime,
        vectorTime: jobMetrics.vectorEndTime - jobMetrics.vectorStartTime,
        memory: Deno.memoryUsage()
      }
    }
  }
}

async function executeCompleteJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  const jobMetrics = {
    startTime: Date.now()
  }
  
  try {
    console.log(`✅ Starting complete job for document ${job.document_id}`)
    console.log('📦 Complete job payload:', job.payload)
    
    // Update document status
    const { error: updateError } = await supabase
      .from('documents')
      .update({
        status: 'completed',
        updated_at: new Date().toISOString(),
        metadata: {
          ...job.payload,
          completed_at: new Date().toISOString(),
          processingTime: Date.now() - jobMetrics.startTime,
          memory: Deno.memoryUsage()
        }
      })
      .eq('id', job.document_id)

    if (updateError) {
      throw new Error(`Failed to update document: ${updateError.message}`)
    }

    return {
      success: true,
      data: { documentId: job.document_id },
      metrics: {
        totalTime: Date.now() - jobMetrics.startTime,
        memory: Deno.memoryUsage()
      }
    }

  } catch (error) {
    console.error(`❌ Complete job failed:`, error)
    return { 
      success: false, 
      error: error.message,
      metrics: {
        totalTime: Date.now() - jobMetrics.startTime,
        memory: Deno.memoryUsage()
      }
    }
  }
} 