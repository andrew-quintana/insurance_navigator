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
  BUCKET: 'docs',
  RAW_PREFIX: 'raw',
  PROCESSED_PREFIX: 'processed',
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_MIME_TYPES: [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
  ],
  LLAMA_PARSE_API_URL: 'https://api.cloud.llamaindex.ai/api/v1/parsing/upload',
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 1000,
  MEMORY_LIMIT: 100 * 1024 * 1024 // 100MB
}

// Log configuration on startup
console.log('📝 Doc parser configuration:', {
  bucket: CONFIG.BUCKET,
  rawPrefix: CONFIG.RAW_PREFIX,
  processedPrefix: CONFIG.PROCESSED_PREFIX,
  maxFileSize: CONFIG.MAX_FILE_SIZE,
  allowedMimeTypes: CONFIG.ALLOWED_MIME_TYPES
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
    configBucket: CONFIG.BUCKET,
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

// Upload file to LlamaParse
async function uploadToLlamaParse(formData: FormData, llamaCloudKey: string): Promise<Response> {
  const headers = {
    'accept': 'application/json',
    'Authorization': `Bearer ${llamaCloudKey}`
  }

  try {
    const response = await fetch(CONFIG.LLAMA_PARSE_API_URL, {
      method: 'POST',
      headers,
      body: formData
    })

    if (!response.ok) {
      throw new Error(`LlamaParse API error: ${response.status} - ${await response.text()}`)
    }

    return response
  } catch (error) {
    console.error('❌ LlamaParse API error:', error)
    throw error
  }
}

serve(async (req) => {
  metrics.startTime = Date.now()

  try {
    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
      return new Response('ok', { headers: corsHeaders })
    }

    // Get environment variables
    const supabaseUrl = Deno.env.get('SUPABASE_URL')
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
    const llamaCloudKey = Deno.env.get('LLAMA_CLOUD_API_KEY')

    if (!supabaseUrl || !supabaseKey || !llamaCloudKey) {
      throw new Error('Missing required environment variables')
    }

    // Initialize Supabase client
    const supabase = createClient(supabaseUrl, supabaseKey)

    // Parse request body
    const { documentId, storagePath, filename, contentType = 'application/pdf' } = await req.json()

    if (!documentId || !storagePath || !filename) {
      throw new Error('Missing required parameters: documentId, storagePath, filename')
    }

    // Download file from storage
    const fileData = await downloadFileWithRetries(supabase, CONFIG.BUCKET, storagePath)
    if (!fileData) {
      throw new Error('Failed to download file')
    }

    metrics.fileSize = fileData.size

    // Create FormData for LlamaParse
    const formData = new FormData()
    formData.append('file', fileData, filename)

    // Upload to LlamaParse
    const llamaResponse = await uploadToLlamaParse(formData, llamaCloudKey)
    const extractedData = await llamaResponse.json()

    // Update document with extracted text
    const { error: updateError } = await supabase
      .from('documents')
      .update({
        extracted_text: extractedData.text,
        metadata: {
          ...extractedData.metadata,
          extraction_method: 'llama_parse',
          content_type: contentType,
          file_size: metrics.fileSize
        }
      })
      .eq('id', documentId)

    if (updateError) {
      throw new Error(`Failed to update document: ${updateError.message}`)
    }

    // Log final metrics
    logMetrics('Complete')

    return new Response(
      JSON.stringify({
        success: true,
        documentId,
        metrics: {
          fileSize: metrics.fileSize,
          processingTime: Date.now() - metrics.startTime
        }
      }),
      {
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      }
    )

  } catch (error) {
    console.error('❌ Error:', error)
    return new Response(
      JSON.stringify({
        error: error.message
      }),
      {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      }
    )
  }
}); 