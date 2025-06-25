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
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Get next pending job
    const { data: jobs, error: jobError } = await supabaseClient
      .from('processing_jobs')
      .select('*')
      .eq('status', 'pending')
      .order('priority', { ascending: false })
      .order('created_at', { ascending: true })
      .limit(1)

    if (jobError) {
      throw new Error(`Failed to fetch jobs: ${jobError.message}`)
    }

    if (!jobs || jobs.length === 0) {
      return new Response(
        JSON.stringify({ message: 'No pending jobs' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const job = jobs[0] as ProcessingJob
    console.log(`📝 Processing job ${job.id} of type ${job.job_type}`)

    // Update job status to processing
    await supabaseClient
      .from('processing_jobs')
      .update({ status: 'processing', started_at: new Date().toISOString() })
      .eq('id', job.id)

    // Process job based on type
    let result: JobResult
    switch (job.job_type) {
      case 'parse':
        result = await executeParseJob(supabaseClient, job)
        break
      case 'embed':
        result = await executeEmbedJob(supabaseClient, job)
        break
      case 'complete':
        result = await executeCompleteJob(supabaseClient, job)
        break
      default:
        throw new Error(`Unknown job type: ${job.job_type}`)
    }

    // Update job status
    if (result.success) {
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
    console.error('Error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

async function executeParseJob(supabase: any, job: ProcessingJob): Promise<JobResult> {
  try {
    // Call doc-parser function
    const { data: parseResult, error: parseError } = await supabase.functions.invoke('doc-parser', {
      body: {
        documentId: job.document_id,
        storagePath: job.payload.storage_path
      }
    })

    if (parseError) throw new Error(`Parsing failed: ${parseError.message}`)

    return {
      success: true,
      data: parseResult,
      nextJob: {
        type: 'embed',
        payload: {
          extractedText: parseResult.extractedText
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
    // Initialize OpenAI embeddings
    const embeddings = new OpenAIEmbeddings(Deno.env.get('OPENAI_API_KEY') ?? '')

    // Get document record
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', job.document_id)
      .single()

    if (docError || !document) {
      throw new Error(`Document not found: ${docError?.message || 'Unknown error'}`)
    }

    // Create text chunks
    const chunkSize = 1000
    const chunkOverlap = 200
    const chunks: string[] = []

    let start = 0
    const text = job.payload.extractedText
    while (start < text.length) {
      const end = start + chunkSize
      const chunk = text.slice(start, end)
      chunks.push(chunk)
      start = end - chunkOverlap
      if (start >= text.length) break
    }

    console.log(`Created ${chunks.length} chunks for document ${job.document_id}`)

    // Generate embeddings for all chunks
    const embeddingsList = await embeddings.embedBatch(chunks)

    // Store vectors
    for (let i = 0; i < chunks.length; i++) {
      const { error: insertError } = await supabase
        .from('document_vectors')
        .insert({
          document_id: job.document_id,
          chunk_index: i,
          content_embedding: embeddingsList[i],
          chunk_text: chunks[i],
          chunk_metadata: {
            total_chunks: chunks.length,
            chunk_length: chunks[i].length,
            processed_at: new Date().toISOString(),
            extraction_method: document.content_type === 'application/pdf' ? 'llamaparse' : 'direct',
            embedding_method: 'openai'
          }
        })

      if (insertError) {
        console.error(`Failed to store vector ${i}:`, insertError)
      }
    }

    return {
      success: true,
      data: { vectorCount: chunks.length },
      nextJob: {
        type: 'complete',
        payload: {
          vectorCount: chunks.length
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
        updated_at: new Date().toISOString(),
        metadata: {
          ...job.payload,
          completed_at: new Date().toISOString()
        }
      })
      .eq('id', job.document_id)

    if (updateError) throw new Error(`Status update failed: ${updateError.message}`)

    return {
      success: true,
      data: { message: 'Document processing completed' }
    }

  } catch (error) {
    console.error(`❌ Complete job failed:`, error)
    return { success: false, error: error.message }
  }
} 