import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "@supabase/supabase-js"
import { corsHeaders } from '../_shared/cors.ts'
import { OpenAIEmbeddings } from '../_shared/embeddings.ts'

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
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    console.log('🔄 Job processor started')
    
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Get next pending job
    console.log('📥 Fetching pending jobs...')
    const { data: jobs, error: jobError } = await supabaseClient
      .from('processing_jobs')
      .select('*')
      .eq('status', 'pending')
      .order('priority', { ascending: false })
      .order('created_at', { ascending: true })
      .limit(1)

    if (jobError) {
      console.error('❌ Failed to fetch jobs:', jobError)
      throw new Error(`Failed to fetch jobs: ${jobError.message}`)
    }

    if (!jobs || jobs.length === 0) {
      console.log('ℹ️ No pending jobs found')
      return new Response(
        JSON.stringify({ message: 'No pending jobs' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const job = jobs[0] as ProcessingJob
    console.log(`📝 Processing job ${job.id} of type ${job.job_type} for document ${job.document_id}`)
    console.log('📦 Job payload:', job.payload)

    // Update job status to processing
    console.log('🔄 Updating job status to processing...')
    await supabaseClient
      .from('processing_jobs')
      .update({ status: 'processing', started_at: new Date().toISOString() })
      .eq('id', job.id)

    // Process job based on type
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

    // Update job status
    if (result.success) {
      console.log(`✅ Job ${job.id} completed successfully`)
      console.log('📦 Result data:', result.data)
      
      await supabaseClient
        .from('processing_jobs')
        .update({
          status: 'completed',
          completed_at: new Date().toISOString(),
          result: result.data
        })
        .eq('id', job.id)

      // Create next job if specified
      if (result.nextJob) {
        console.log('🔄 Creating next job:', result.nextJob)
        await supabaseClient
          .from('processing_jobs')
          .insert({
            document_id: job.document_id,
            ...result.nextJob,
            status: 'pending',
            created_at: new Date().toISOString()
          })
      }
    } else {
      console.error(`❌ Job ${job.id} failed:`, result.error)
      await supabaseClient
        .from('processing_jobs')
        .update({
          status: 'failed',
          error: result.error,
          completed_at: new Date().toISOString()
        })
        .eq('id', job.id)
    }

    return new Response(
      JSON.stringify(result),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('❌ Fatal error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

async function executeParseJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  try {
    console.log(`🔍 Starting parse job for document ${job.document_id}`)
    console.log('📦 Parse job payload:', job.payload)
    
    // Call doc-parser function
    console.log('📞 Calling doc-parser function...')
    const { data: parseResult, error: parseError } = await supabase.functions.invoke('doc-parser', {
      body: JSON.stringify({
        documentId: job.document_id,
        storagePath: job.payload.storage_path
      })
    })

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
      }
    }

  } catch (error) {
    console.error(`❌ Parse job failed:`, error)
    return { success: false, error: error.message }
  }
}

async function executeEmbedJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  try {
    console.log(`🧮 Starting embed job for document ${job.document_id}`)
    console.log('📦 Embed job payload:', job.payload)
    
    // Call vector-processor function
    console.log('📞 Calling vector-processor function...')
    const { data: vectorResult, error: vectorError } = await supabase.functions.invoke('vector-processor', {
      body: JSON.stringify({
        documentId: job.document_id,
        extractedText: job.payload.extractedText,
        storagePath: job.payload.storagePath
      })
    })

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
      }
    }

  } catch (error) {
    console.error(`❌ Embed job failed:`, error)
    return { success: false, error: error.message }
  }
}

async function executeCompleteJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
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
          completed_at: new Date().toISOString()
        }
      })
      .eq('id', job.document_id)

    if (updateError) {
      console.error('❌ Status update error:', updateError)
      throw new Error(`Status update failed: ${updateError.message}`)
    }

    console.log('✅ Document status updated successfully')

    return {
      success: true,
      data: { message: 'Document processing completed' }
    }

  } catch (error) {
    console.error(`❌ Complete job failed:`, error)
    return { success: false, error: error.message }
  }
} 