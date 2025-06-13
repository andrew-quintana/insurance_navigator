import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
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
  data?: any;
  error?: string;
  nextJob?: {
    type: string;
    payload: any;
    delay?: number;
  };
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    if (req.method === 'POST') {
      return await processJobs(supabase)
    }

    if (req.method === 'GET') {
      return await getJobStats(supabase)
    }

    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Job processor error:', error)
    return new Response(JSON.stringify({ 
      error: 'Internal server error',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})

// Helper function to determine required data keys for job validation
function getRequiredDataKeys(jobType: string): string[] {
  switch (jobType) {
    case 'parse':
      return ['extractedText', 'metadata']
    case 'chunk':
      return ['chunks']
    case 'embed':
      return ['vectors', 'embeddings']
    case 'complete':
      return ['processingResult']
    case 'notify':
      return []
    default:
      return []
  }
}

async function processJobs(supabase: any): Promise<Response> {
  console.log('🔄 Starting job processing cycle...')
  
  try {
    // Get pending jobs
    const { data: jobs, error: jobsError } = await supabase
      .rpc('get_pending_jobs', { limit_param: 5 })

    if (jobsError) {
      console.error('❌ Error fetching pending jobs:', jobsError)
      return new Response(JSON.stringify({ 
        error: 'Failed to fetch jobs',
        details: jobsError.message 
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    if (!jobs || jobs.length === 0) {
      console.log('✅ No pending jobs found')
      return new Response(JSON.stringify({ 
        message: 'No pending jobs',
        processed: 0 
      }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log(`📋 Found ${jobs.length} pending jobs`)
    
    const results = []
    for (const job of jobs) {
      const result = await executeJob(supabase, job)
      results.push({ jobId: job.id, jobType: job.job_type, ...result })
    }

    const successCount = results.filter(r => r.success).length
    const failureCount = results.length - successCount

    console.log(`✅ Job processing complete: ${successCount} success, ${failureCount} failed`)

    return new Response(JSON.stringify({ 
      message: 'Job processing complete',
      processed: results.length,
      successful: successCount,
      failed: failureCount,
      results: results
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('❌ Job processing cycle failed:', error)
    return new Response(JSON.stringify({ 
      error: 'Job processing failed',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
}

async function executeJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  console.log(`🚀 Executing job ${job.id} (${job.job_type}) for document ${job.document_id}`)
  
  try {
    // Mark job as running
    const { error: startError } = await supabase
      .rpc('start_processing_job', { job_id_param: job.id })

    if (startError) {
      console.error(`❌ Failed to start job ${job.id}:`, startError)
      return { success: false, error: `Failed to start job: ${startError.message}` }
    }

    // Execute the appropriate function based on job type
    let result: JobResult
    switch (job.job_type) {
      case 'parse':
        result = await executeParseJob(supabase, job)
        break
      case 'chunk':
        result = await executeChunkJob(supabase, job)
        break
      case 'embed':
        result = await executeEmbedJob(supabase, job)
        break
      case 'complete':
        result = await executeCompleteJob(supabase, job)
        break
      case 'notify':
        result = await executeNotifyJob(supabase, job)
        break
      default:
        result = { success: false, error: `Unknown job type: ${job.job_type}` }
    }

    // Handle job completion or failure
    if (result.success) {
      // Mark job as completed
      const { error: completeError } = await supabase
        .rpc('complete_processing_job', { 
          job_id_param: job.id,
          job_result: result.data || null
        })

      if (completeError) {
        console.error(`❌ Failed to mark job ${job.id} as completed:`, completeError)
        return { success: false, error: `Failed to complete job: ${completeError.message}` }
      }

      // Schedule next job if specified - with validation
      if (result.nextJob) {
        try {
          // Use enhanced scheduling with validation
          const requiredKeys = getRequiredDataKeys(job.job_type)
          
          const { data: nextJobId, error: scheduleError } = await supabase
            .rpc('schedule_next_job_safely', {
              prev_job_id: job.id,
              doc_id: job.document_id,
              next_job_type: result.nextJob.type,
              next_payload: result.nextJob.payload || {},
              required_data_keys: requiredKeys
            })

          if (scheduleError) {
            console.error(`❌ Failed to schedule next job for ${job.id}:`, scheduleError)
            // Don't fail the current job, but log the issue
            console.warn(`⚠️ Job ${job.id} completed but next job scheduling failed`)
          } else {
            console.log(`📅 Scheduled next job: ${result.nextJob.type} (${nextJobId}) for document ${job.document_id}`)
          }
        } catch (scheduleError) {
          console.error(`❌ Exception scheduling next job for ${job.id}:`, scheduleError)
        }
      }

      console.log(`✅ Job ${job.id} completed successfully`)
    } else {
      // Mark job as failed (with retry logic)
      const retryResult = await supabase
        .rpc('fail_processing_job', {
          job_id_param: job.id,
          error_msg: result.error || 'Unknown error',
          error_details_param: { 
            job_type: job.job_type,
            retry_count: job.retry_count,
            timestamp: new Date().toISOString()
          }
        })

      console.log(`❌ Job ${job.id} failed: ${result.error} (${retryResult.data})`)
    }

    return result

  } catch (error) {
    console.error(`❌ Job execution error for ${job.id}:`, error)
    
    // Mark job as failed
    await supabase
      .rpc('fail_processing_job', {
        job_id_param: job.id,
        error_msg: error.message || 'Unexpected error',
        error_details_param: { 
          job_type: job.job_type,
          error_stack: error.stack,
          timestamp: new Date().toISOString()
        }
      })

    return { success: false, error: error.message || 'Unexpected error' }
  }
}

async function executeParseJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  console.log(`📄 Executing parse job for document ${job.document_id}`)
  
  try {
    // Call doc-parser function
    const { data, error } = await supabase.functions.invoke('doc-parser', {
      body: {
        documentId: job.document_id,
        storagePath: job.payload.storagePath
      }
    })

    if (error) {
      return { success: false, error: `Parse failed: ${error.message}` }
    }

    // Schedule next step: embedding
    return {
      success: true,
      data: data,
      nextJob: {
        type: 'embed',
        payload: {
          documentId: job.document_id,
          extractedText: data.extractedText || data.text
        }
      }
    }

  } catch (error) {
    return { success: false, error: `Parse job failed: ${error.message}` }
  }
}

async function executeChunkJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  console.log(`✂️ Executing chunk job for document ${job.document_id}`)
  
  // For now, chunking is handled within the embedding step
  // This is a placeholder for future separation of concerns
  return {
    success: true,
    data: { message: 'Chunking handled in embedding step' },
    nextJob: {
      type: 'embed',
      payload: job.payload
    }
  }
}

async function executeEmbedJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  console.log(`🧠 Executing embed job for document ${job.document_id}`)
  
  try {
    // Call vector-processor function
    const { data, error } = await supabase.functions.invoke('vector-processor', {
      body: {
        documentId: job.document_id,
        extractedText: job.payload.extractedText
      }
    })

    if (error) {
      return { success: false, error: `Embedding failed: ${error.message}` }
    }

    // Schedule completion job
    return {
      success: true,
      data: data,
      nextJob: {
        type: 'complete',
        payload: {
          documentId: job.document_id,
          processingResult: data
        }
      }
    }

  } catch (error) {
    return { success: false, error: `Embed job failed: ${error.message}` }
  }
}

async function executeCompleteJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  console.log(`🎉 Executing completion job for document ${job.document_id}`)
  
  try {
    // Send completion webhook
    const webhookUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/processing-webhook`
    
    const webhookResponse = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source: 'internal',
        documentId: job.document_id,
        status: 'completed',
        step: 'processing_complete',
        metadata: job.payload.processingResult
      })
    })

    if (!webhookResponse.ok) {
      console.warn('⚠️ Completion webhook failed (non-critical)')
    }

    // Optionally schedule notification
    return {
      success: true,
      data: { message: 'Document processing completed' },
      nextJob: {
        type: 'notify',
        payload: {
          documentId: job.document_id,
          notificationType: 'completion'
        },
        delay: 5 // 5 second delay
      }
    }

  } catch (error) {
    return { success: false, error: `Completion job failed: ${error.message}` }
  }
}

async function executeNotifyJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  console.log(`📧 Executing notify job for document ${job.document_id}`)
  
  try {
    // Get document and user info
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select(`
        *,
        users!inner(email, full_name)
      `)
      .eq('id', job.document_id)
      .single()

    if (docError || !document) {
      return { success: false, error: 'Document not found for notification' }
    }

    // Send real-time progress update
    await supabase
      .from('realtime_progress_updates')
      .insert({
        user_id: document.user_id,
        document_id: job.document_id,
        payload: {
          type: 'complete',
          documentId: job.document_id,
          progress: 100,
          status: 'completed',
          timestamp: new Date().toISOString(),
          details: {
            filename: document.original_filename,
            fileSize: document.file_size,
            processedChunks: document.processed_chunks,
            totalChunks: document.total_chunks
          }
        }
      })

    console.log(`📨 Notification sent for document ${job.document_id}`)

    return {
      success: true,
      data: { message: 'Notification sent successfully' }
    }

  } catch (error) {
    return { success: false, error: `Notify job failed: ${error.message}` }
  }
}

async function getJobStats(supabase: any): Promise<Response> {
  try {
    // Get job queue statistics
    const { data: stats, error: statsError } = await supabase
      .from('job_queue_stats')
      .select('*')

    const { data: failedJobs, error: failedError } = await supabase
      .from('failed_jobs')
      .select('*')
      .limit(10)

    const { data: stuckJobs, error: stuckError } = await supabase
      .from('stuck_jobs')
      .select('*')

    if (statsError || failedError || stuckError) {
      console.error('Error fetching job stats:', { statsError, failedError, stuckError })
    }

    return new Response(JSON.stringify({
      stats: stats || [],
      failedJobs: failedJobs || [],
      stuckJobs: stuckJobs || [],
      timestamp: new Date().toISOString()
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Error getting job stats:', error)
    return new Response(JSON.stringify({ 
      error: 'Failed to get job stats',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
} 