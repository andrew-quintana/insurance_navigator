import { serve } from "https://deno.land/std@0.177.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

interface ProcessingJob {
  id: string;
  document_id: string;
  job_type: string;
  status: string;
  priority: number;
  retry_count: number;
  payload: any;
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

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
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
      await supabase
        .rpc('complete_processing_job', { 
          job_id_param: job.id,
          job_result: result.data || null
        })

      // Schedule next job if specified
      if (result.nextJob) {
        await supabase
          .rpc('create_processing_job', {
            doc_id: job.document_id,
            job_type_param: result.nextJob.type,
            job_payload: result.nextJob.payload || {},
            schedule_delay_seconds: result.nextJob.delay || 0
          })
        
        console.log(`📅 Scheduled next job: ${result.nextJob.type} for document ${job.document_id}`)
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

      if (retryResult.error) {
        console.error(`❌ Failed to mark job ${job.id} as failed:`, retryResult.error)
      }
    }

    return result

  } catch (error) {
    console.error(`❌ Job execution failed:`, error)
    return { success: false, error: error.message }
  }
}

async function executeParseJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  try {
    // Get document info
    const { data: doc, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', job.document_id)
      .single()

    if (docError) throw new Error(`Failed to get document: ${docError.message}`)
    if (!doc) throw new Error('Document not found')

    // Call doc-parser function
    const { data: parseResult, error: parseError } = await supabase.functions.invoke('doc-parser', {
      body: {
        document_id: job.document_id,
        filename: doc.original_filename,
        content_type: doc.content_type
      }
    })

    if (parseError) throw new Error(`Parse failed: ${parseError.message}`)

    return {
      success: true,
      data: parseResult,
      nextJob: {
        type: 'chunk',
        payload: {
          document_id: job.document_id,
          text: parseResult.text
        }
      }
    }

  } catch (error) {
    console.error(`❌ Parse job failed:`, error)
    return { success: false, error: error.message }
  }
}

async function executeChunkJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  try {
    // Call chunking service
    const { data: chunkResult, error: chunkError } = await supabase.functions.invoke('chunking-service', {
      body: {
        document_id: job.document_id,
        text: job.payload.text
      }
    })

    if (chunkError) throw new Error(`Chunking failed: ${chunkError.message}`)

    return {
      success: true,
      data: chunkResult,
      nextJob: {
        type: 'embed',
        payload: {
          document_id: job.document_id,
          chunks: chunkResult.chunks
        }
      }
    }

  } catch (error) {
    console.error(`❌ Chunk job failed:`, error)
    return { success: false, error: error.message }
  }
}

async function executeEmbedJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  try {
    // Call vector processor
    const { data: embedResult, error: embedError } = await supabase.functions.invoke('vector-processor', {
      body: {
        document_id: job.document_id,
        chunks: job.payload.chunks
      }
    })

    if (embedError) throw new Error(`Embedding failed: ${embedError.message}`)

    return {
      success: true,
      data: embedResult,
      nextJob: {
        type: 'complete',
        payload: {
          document_id: job.document_id,
          vector_count: embedResult.vector_count
        }
      }
    }

  } catch (error) {
    console.error(`❌ Embed job failed:`, error)
    return { success: false, error: error.message }
  }
}

async function executeCompleteJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  try {
    // Update document status
    const { error: updateError } = await supabase
      .from('documents')
      .update({
        status: 'completed',
        processing_stage: 'completed',
        processing_progress: 100,
        updated_at: new Date().toISOString()
      })
      .eq('id', job.document_id)

    if (updateError) throw new Error(`Failed to update document: ${updateError.message}`)

    return {
      success: true,
      data: { message: 'Document processing completed' },
      nextJob: {
        type: 'notify',
        payload: {
          document_id: job.document_id,
          status: 'completed'
        }
      }
    }

  } catch (error) {
    console.error(`❌ Complete job failed:`, error)
    return { success: false, error: error.message }
  }
}

async function executeNotifyJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  try {
    // Get document info
    const { data: doc, error: docError } = await supabase
      .from('documents')
      .select('user_id, original_filename')
      .eq('id', job.document_id)
      .single()

    if (docError) throw new Error(`Failed to get document: ${docError.message}`)
    if (!doc) throw new Error('Document not found')

    // Insert realtime notification
    const { error: notifyError } = await supabase
      .from('realtime_progress')
      .insert({
        user_id: doc.user_id,
        document_id: job.document_id,
        event_type: 'document_processed',
        status: job.payload.status,
        message: `Document "${doc.original_filename}" processing completed`,
        metadata: {
          document_id: job.document_id,
          filename: doc.original_filename,
          status: job.payload.status
        }
      })

    if (notifyError) throw new Error(`Failed to send notification: ${notifyError.message}`)

    return {
      success: true,
      data: { message: 'Notification sent' }
    }

  } catch (error) {
    console.error(`❌ Notify job failed:`, error)
    return { success: false, error: error.message }
  }
}

async function getJobStats(supabase: any): Promise<Response> {
  try {
    const { data: stats, error: statsError } = await supabase
      .rpc('get_job_stats')

    if (statsError) {
      return new Response(JSON.stringify({ 
        error: 'Failed to get job stats',
        details: statsError.message 
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    return new Response(JSON.stringify(stats), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    return new Response(JSON.stringify({ 
      error: 'Failed to get job stats',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
} 