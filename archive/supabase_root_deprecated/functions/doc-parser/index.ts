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
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  LLAMA_PARSE_API_URL: 'https://api.cloud.llamaindex.ai/api/v1/parsing/upload',
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 1000,
  MEMORY_LIMIT: 100 * 1024 * 1024 // 100MB
}

// Log configuration on startup
console.log('📝 Doc parser configuration:', {
  uploadBucket: CONFIG.UPLOAD_BUCKET,
  storageBucket: CONFIG.STORAGE_BUCKET,
  maxFileSize: CONFIG.MAX_FILE_SIZE,
  maxRetries: CONFIG.MAX_RETRIES
})

// Add memory check function
function checkMemoryUsage(): boolean {
  const memory = Deno.memoryUsage()
  const used = memory.heapUsed + memory.external
  
  if (used > CONFIG.MEMORY_LIMIT) {
    console.error(`❌ Memory limit exceeded: ${Math.round(used / 1024 / 1024)}MB used`)
    return false
  }
  
  if (used > CONFIG.MEMORY_LIMIT * 0.8) {
    console.warn(`⚠️ High memory usage: ${Math.round(used / 1024 / 1024)}MB used`)
  }

  return true
}

// Get file from storage with retries
async function downloadFileWithRetries(supabase: SupabaseClient, bucket: string, path: string): Promise<Blob | null> {
  let lastError: Error | null = null
  
  console.log('🔍 Starting file download:', {
    bucket,
    path,
    configBucket: CONFIG.UPLOAD_BUCKET,
    timestamp: new Date().toISOString()
  })
  
  // Verify bucket exists
  const { data: buckets, error: bucketError } = await supabase.storage.listBuckets()
  if (bucketError) {
    console.error('❌ Failed to list buckets:', bucketError)
  } else {
    console.log('📦 Available buckets:', buckets.map(b => b.name))
  }
  
  for (let attempt = 0; attempt < CONFIG.MAX_RETRIES; attempt++) {
    try {
      console.log(`📥 Download attempt ${attempt + 1}/${CONFIG.MAX_RETRIES}:`, {
        bucket,
        path,
        timestamp: new Date().toISOString()
      })

      const { data: fileData, error: fileError } = await supabase.storage
        .from(bucket)
        .download(path)

      if (fileError) {
        console.error(`❌ Download attempt ${attempt + 1} failed:`, {
          error: fileError,
          bucket,
          path,
          errorCode: fileError.code,
          errorMessage: fileError.message,
          timestamp: new Date().toISOString()
        })
        lastError = new Error(fileError.message)
        if (attempt < CONFIG.MAX_RETRIES - 1) {
          await new Promise(resolve => setTimeout(resolve, CONFIG.RETRY_DELAY_MS * Math.pow(2, attempt)))
          continue
        }
        throw fileError
      }

      if (!fileData) {
        console.error('❌ No data received from storage:', {
          bucket,
          path,
          timestamp: new Date().toISOString()
        })
        throw new Error('No data received from storage')
      }

      console.log('✅ File downloaded successfully:', {
        bucket,
        path,
        size: fileData.size,
        timestamp: new Date().toISOString()
      })

      return fileData
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error))
      console.error(`❌ Download attempt ${attempt + 1} caught error:`, {
        error: lastError.message,
        bucket,
        path,
        timestamp: new Date().toISOString()
      })
      if (attempt < CONFIG.MAX_RETRIES - 1) {
        await new Promise(resolve => setTimeout(resolve, CONFIG.RETRY_DELAY_MS * Math.pow(2, attempt)))
        continue
      }
    }
  }

  throw new Error(`Failed to download file after ${CONFIG.MAX_RETRIES} attempts: ${lastError?.message || 'Unknown error'}`)
}

// Add streaming file download
async function streamFileDownload(storagePath: string): Promise<Uint8Array | null> {
  const maxRetries = 3
  const retryDelays = [2000, 4000, 8000] // 2s, 4s, 8s delays

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      console.log(`📥 Attempt ${attempt + 1}/${maxRetries} to download file: ${storagePath}`)
      
      const { data, error } = await supabase
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

// Initialize Supabase client
const supabase = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
)

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Parse request
    const { jobId, payload } = await req.json()
    
    if (!jobId || !payload) {
      throw new Error('Missing required parameters: jobId and payload')
    }

    const {
      document_id,
      raw_storage_path,
      raw_storage_bucket,
      final_storage_path,
      final_storage_bucket,
      content_type
    } = payload

    if (!document_id || !raw_storage_path || !raw_storage_bucket || !final_storage_path || !final_storage_bucket || !content_type) {
      throw new Error('Invalid job payload: missing required fields')
    }

    // Start job
    await supabase
      .from('processing_jobs')
      .update({ 
        status: 'processing',
        started_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      .eq('id', jobId)

    // Update document status
    await supabase
      .from('documents')
      .update({ 
        status: 'processing',
        updated_at: new Date().toISOString()
      })
      .eq('id', document_id)

    // Get file from storage with retries
    console.log('📥 Downloading file from storage:', {
      bucket: raw_storage_bucket,
      path: raw_storage_path
    })
    
    const fileData = await downloadFileWithRetries(supabase, raw_storage_bucket, raw_storage_path)
    if (!fileData) {
      throw new Error('Failed to download file: No data received')
    }

    // Create FormData for LlamaParse API
    const formData = new FormData()
    formData.append('file', fileData, raw_storage_path)

    // Call LlamaParse API
    let parseResponse: Response | null = null
    let retryCount = 0
    let lastError: string | Error | null = null

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
    const { error: uploadError } = await supabase.storage
      .from(final_storage_bucket)
      .upload(final_storage_path, fileData, {
        contentType: content_type,
        upsert: true
      })

    if (uploadError) {
      throw new Error(`Failed to upload processed file: ${uploadError.message}`)
    }

    // Complete job
    await supabase
      .from('processing_jobs')
      .update({
        status: 'completed',
        completed_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        result: {
          parsedData,
          final_storage_path,
          final_storage_bucket
        }
      })
      .eq('id', jobId)
    
    // Update document status
    await supabase
      .from('documents')
      .update({ 
        status: 'completed',
        metadata: {
          ...payload,
          parsed_data: parsedData,
          processing_completed_at: new Date().toISOString()
        },
        updated_at: new Date().toISOString()
      })
      .eq('id', document_id)
    
    console.log('✅ Document processing complete:', {
      jobId,
      document_id,
      final_storage_path
    })

    return new Response(JSON.stringify({
      success: true,
      jobId,
      document_id,
      final_storage_path
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('❌ Document processing failed:', error)
    
    // Get jobId and documentId from the error context
    let errorJobId: string | undefined
    let errorDocumentId: string | undefined
    
    try {
      // Try to parse the error message for jobId
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      if (errorMessage.includes('jobId:')) {
        errorJobId = errorMessage.split('jobId:')[1].trim().split(' ')[0]
      }
      
      // Update job status if we have the jobId
      if (errorJobId) {
        await supabase
          .from('processing_jobs')
          .update({
            status: 'failed',
            error_message: error instanceof Error ? error.message : 'Unknown error occurred',
            updated_at: new Date().toISOString()
          })
          .eq('id', errorJobId)

        // Get document ID from job
        const { data: job } = await supabase
          .from('processing_jobs')
          .select('payload')
          .eq('id', errorJobId)
          .single()

        if (job?.payload?.document_id) {
          errorDocumentId = job.payload.document_id
          await supabase
            .from('documents')
            .update({ 
              status: 'failed',
              error_message: error instanceof Error ? error.message : 'Unknown error occurred',
              updated_at: new Date().toISOString()
            })
            .eq('id', errorDocumentId)
        }
      }
    } catch (updateError) {
      console.error('❌ Failed to update error status:', updateError)
    }
        
        return new Response(JSON.stringify({
          success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      jobId: errorJobId,
      document_id: errorDocumentId
        }), { 
          status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
}) 