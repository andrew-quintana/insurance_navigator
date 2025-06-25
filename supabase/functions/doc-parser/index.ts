// @deno-types="npm:@types/node"
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
// @deno-types="npm:@supabase/supabase-js"
import { createClient, SupabaseClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

// Add Deno types
declare const Deno: {
  env: {
    get(key: string): string | undefined;
    toObject(): { [key: string]: string };
  };
  memoryUsage(): { heapUsed: number; rss: number; external: number };
  serve: (handler: (req: Request) => Promise<Response>) => void;
};

// Performance monitoring
const metrics = {
  startTime: 0,
  fileSize: 0,
  processingTime: 0,
  memoryUsage: 0
}

function logMetrics(stage: string) {
  const memory = Deno.memoryUsage()
  const heapUsed = Math.round(memory.heapUsed / 1024 / 1024)
  const rss = Math.round(memory.rss / 1024 / 1024)
  console.log(`
📊 Performance Metrics - ${stage}:
- Processing Time: ${Date.now() - metrics.startTime}ms
- Heap Used: ${heapUsed}MB
- RSS: ${rss}MB
- File Size: ${metrics.fileSize} bytes
`)
}

console.log('📄 Doc parser starting...')

// Configuration
const CONFIG = {
  UPLOAD_BUCKET: 'raw_documents',
  STORAGE_BUCKET: 'documents',
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
  LLAMA_PARSE_API_URL: 'https://api.cloud.llamaindex.ai/api/v1/parsing/upload',
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 1000
}

// Add memory check function
function checkMemoryUsage(): boolean {
  const memory = Deno.memoryUsage()
  const usedMemory = memory.heapUsed + memory.external
  if (usedMemory > CONFIG.MEMORY_LIMIT) {
    console.warn(`⚠️ High memory usage: ${Math.round(usedMemory / 1024 / 1024)}MB`)
    return false
  }
  return true
}

// Add streaming file download
async function streamFileDownload(storagePath: string): Promise<Uint8Array | null> {
  const maxRetries = 3
  const retryDelays = [2000, 4000, 8000] // 2s, 4s, 8s delays

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      console.log(`📥 Attempt ${attempt + 1}/${maxRetries} to download file: ${storagePath}`)
      
      const { data, error } = await supabaseClient
        .storage
        .from('documents')
        .download(storagePath)

      if (error) {
        throw error
      }

      if (!data) {
        throw new Error('No data received from storage')
      }

      return new Uint8Array(await data.arrayBuffer())
    } catch (err) {
      console.error(`❌ Download attempt ${attempt + 1} failed:`, err)
      
      if (attempt < maxRetries - 1) {
        console.log(`⏳ Waiting ${retryDelays[attempt]}ms before retry...`)
        await new Promise(resolve => setTimeout(resolve, retryDelays[attempt]))
        } else {
        console.error('❌ All download attempts failed:', err)
        throw err
      }
    }
  }

  return null
}

// Add retry mechanism for LlamaParse uploads
async function uploadToLlamaParse(formData: FormData, llamaCloudKey: string): Promise<Response> {
  const maxRetries = 3
  const retryDelays = [2000, 4000, 8000] // 2s, 4s, 8s

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      console.log(`📤 LlamaParse upload attempt ${attempt + 1}/${maxRetries}`)
      
      const response = await fetch('https://api.cloud.llamaindex.ai/api/parsing/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${llamaCloudKey}`,
          'Accept': 'application/json'
        },
        body: formData
      })

      // If not rate limited, return immediately
      if (response.status !== 429) {
        return response
      }

      // Get retry-after header if available
      const retryAfter = response.headers.get('retry-after')
      const waitTime = retryAfter ? parseInt(retryAfter) * 1000 : retryDelays[attempt]

      console.log(`🔄 Rate limited (attempt ${attempt + 1}/${maxRetries}), waiting ${waitTime}ms`)

      if (attempt < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, waitTime))
      } else {
        return response
      }
    } catch (error) {
      console.error(`❌ LlamaParse upload attempt ${attempt + 1} failed:`, error)

      if (attempt < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, retryDelays[attempt]))
      } else {
        throw error
      }
    }
  }

  throw new Error('Upload failed after all retries')
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client with service role key for full access
    const supabaseClient: SupabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Parse request
    const { jobId } = await req.json()
    
    if (!jobId) {
      throw new Error('Missing required parameter: jobId')
    }

    // Get job details
    const { data: job, error: jobError } = await supabaseClient
      .from('processing_jobs')
      .select('*')
      .eq('id', jobId)
      .single()

    if (jobError || !job) {
      throw new Error(`Failed to fetch job details: ${jobError?.message || 'Job not found'}`)
    }

    const {
      rawStoragePath,
      rawStorageBucket,
      finalStoragePath,
      finalStorageBucket,
      contentType,
      documentId
    } = job.payload

    if (!rawStoragePath || !rawStorageBucket || !finalStoragePath || !finalStorageBucket || !contentType || !documentId) {
      throw new Error('Invalid job payload: missing required fields')
    }

    // Start job
    await supabaseClient
      .from('processing_jobs')
      .update({
        status: 'processing',
        started_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      .eq('id', jobId)

    // Update document status
    await supabaseClient
      .from('documents')
      .update({
        status: 'processing',
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)

    // Get file from storage
    const { data: fileData, error: fileError } = await supabaseClient.storage
      .from(rawStorageBucket)
      .download(rawStoragePath)

    if (fileError || !fileData) {
      throw new Error(`Failed to download file: ${fileError?.message || 'File not found'}`)
    }

    // Create FormData for LlamaParse API
    const formData = new FormData()
    formData.append('file', fileData, rawStoragePath)

    // Call LlamaParse API
    let parseResponse = null
    let retryCount = 0
    let lastError = null

    while (retryCount < CONFIG.MAX_RETRIES) {
      try {
        parseResponse = await fetch(CONFIG.LLAMA_PARSE_API_URL, {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Authorization': `Bearer ${Deno.env.get('LLAMA_CLOUD_API_KEY')}`
          },
          body: formData
        })

        if (parseResponse.ok) {
          break
        }

        lastError = await parseResponse.text()
        throw new Error(`LlamaParse API error: ${lastError}`)
      } catch (error) {
        lastError = error
        retryCount++
        if (retryCount < CONFIG.MAX_RETRIES) {
          await new Promise(resolve => setTimeout(resolve, CONFIG.RETRY_DELAY_MS * retryCount))
          continue
        }
        throw error
      }
    }

    if (!parseResponse?.ok) {
      throw new Error(`Failed to parse document after ${CONFIG.MAX_RETRIES} retries: ${lastError}`)
    }

    const parsedData = await parseResponse.json()

    // Upload processed file to final storage
    const { error: uploadError } = await supabaseClient.storage
      .from(finalStorageBucket)
      .upload(finalStoragePath, fileData, {
        contentType,
        upsert: true
      })

    if (uploadError) {
      throw new Error(`Failed to upload processed file: ${uploadError.message}`)
    }

    // Complete job
    await supabaseClient
      .from('processing_jobs')
      .update({
        status: 'completed',
        completed_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        result: {
          parsedData,
          finalStoragePath,
          finalStorageBucket
        }
      })
      .eq('id', jobId)

    // Update document status
    await supabaseClient
      .from('documents')
      .update({
        status: 'completed',
        metadata: {
          ...job.metadata,
          parsed_data: parsedData,
          processing_completed_at: new Date().toISOString()
        },
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)

    console.log('✅ Document processing complete:', {
      jobId,
      documentId,
      finalStoragePath
    })

    return new Response(JSON.stringify({
      success: true,
      jobId,
      documentId,
      finalStoragePath
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('❌ Document processing failed:', error)

    // Update job status
    if (req.body) {
      const { jobId } = await req.json()
      if (jobId) {
        await supabaseClient
          .from('processing_jobs')
          .update({
            status: 'failed',
            error_message: error instanceof Error ? error.message : 'Unknown error occurred',
            updated_at: new Date().toISOString()
          })
          .eq('id', jobId)

        // Get document ID from job
        const { data: job } = await supabaseClient
          .from('processing_jobs')
          .select('payload')
          .eq('id', jobId)
          .single()

        if (job?.payload?.documentId) {
          await supabaseClient
            .from('documents')
            .update({
              status: 'failed',
              error_message: error instanceof Error ? error.message : 'Unknown error occurred',
              updated_at: new Date().toISOString()
            })
            .eq('id', job.payload.documentId)
        }
      }
    }

    return new Response(JSON.stringify({
      error: 'Document processing failed',
      details: error instanceof Error ? error.message : 'Unknown error occurred'
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
}) 