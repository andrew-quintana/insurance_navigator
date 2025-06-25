import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.21.0'
import { corsHeaders } from '../_shared/cors.ts'

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

// Initialize Supabase client
const supabaseClient = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
)

// Add file size limits and streaming configuration
const CONFIG = {
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
  CHUNK_SIZE: 1024 * 1024, // 1MB chunks for streaming
  MEMORY_LIMIT: 512 * 1024 * 1024 // 512MB soft limit
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

// Custom fetch implementation for file uploads
async function uploadFile(url: string, formData: FormData, authToken: string): Promise<Response> {
  const boundary = '----FormBoundary' + Math.random().toString(36).slice(2);
  const chunks: Uint8Array[] = [];
  
  for (const [key, value] of formData.entries()) {
    // Add boundary
    chunks.push(new TextEncoder().encode(`--${boundary}\r\n`));
    
    if (value instanceof Blob) {
      // Handle file data
      chunks.push(new TextEncoder().encode(
        `Content-Disposition: form-data; name="${key}"; filename="${value.name || 'file'}"\r\n` +
        `Content-Type: ${value.type || 'application/octet-stream'}\r\n\r\n`
      ));
      chunks.push(new Uint8Array(await value.arrayBuffer()));
      chunks.push(new TextEncoder().encode('\r\n'));
    } else {
      // Handle text fields
      chunks.push(new TextEncoder().encode(
        `Content-Disposition: form-data; name="${key}"\r\n\r\n${value}\r\n`
      ));
    }
  }
  
  // Add final boundary
  chunks.push(new TextEncoder().encode(`--${boundary}--\r\n`));
  
  // Combine all chunks
  const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
  const body = new Uint8Array(totalLength);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.length;
  }
  
  // Make request with proper binary body
  return await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': authToken,
      'Content-Type': `multipart/form-data; boundary=${boundary}`
    },
    body
  });
}

serve(async (req) => {
  metrics.startTime = Date.now()
  
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { 
      headers: {
        ...corsHeaders,
        'Allow': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
      }
    })
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

  // Handle webhook callback from LlamaParse
  if (req.method === 'POST' && req.url.endsWith('/webhook')) {
    try {
      console.log('📥 Received webhook from LlamaParse')
      logMetrics('webhook-start')
      
      const webhookData = await req.json()
      
      // Extract document ID from the URL query params
      const url = new URL(req.url)
      const documentId = url.searchParams.get('documentId')
      const storagePath = url.searchParams.get('storagePath')
      
      if (!documentId || !storagePath) {
        throw new Error('Missing documentId or storagePath in webhook URL')
      }

      console.log(`📄 Processing webhook for document ${documentId}`)
      console.log('📦 Webhook data size:', JSON.stringify(webhookData).length, 'bytes')
      
      // Check memory before processing webhook
      if (!checkMemoryUsage()) {
        throw new Error('Memory limit exceeded before processing webhook')
      }
      
      // Update document status and content
      const { error: updateError } = await supabaseClient
        .from('documents')
        .update({
          status: 'completed',
          content: webhookData.md,
          metadata: {
            extractionMethod: 'llamaparse_webhook',
            textLength: webhookData.md.length,
            images: webhookData.images || [],
            completedAt: new Date().toISOString(),
            processingTime: Date.now() - metrics.startTime,
            memoryMetrics: Deno.memoryUsage()
          }
        })
        .eq('id', documentId)

      if (updateError) {
        throw new Error(`Failed to update document: ${updateError.message}`)
      }

      logMetrics('webhook-complete')

      // Clean up webhook data
      webhookData.md = null
      webhookData.images = null

      // Return success response
      return new Response(
        JSON.stringify({ 
          success: true,
          message: 'Document updated successfully',
          metrics: {
            processingTime: Date.now() - metrics.startTime,
            memoryUsage: Deno.memoryUsage()
        }
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    } catch (error) {
      console.error('❌ Webhook processing failed:', error)
      logMetrics('webhook-error')
      return new Response(
        JSON.stringify({ success: false, error: error.message }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }
  }

  // Health check
  if (req.method === 'GET') {
    return new Response(
      JSON.stringify({ 
        service: 'doc-parser',
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        memory: Deno.memoryUsage(),
        config: {
          maxFileSize: CONFIG.MAX_FILE_SIZE,
          chunkSize: CONFIG.CHUNK_SIZE,
          memoryLimit: CONFIG.MEMORY_LIMIT
        }
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  try {
    // Verify JWT for document upload requests
    const authHeader = req.headers.get('Authorization')
    if (!authHeader?.startsWith('Bearer ')) {
      throw new Error('Missing or invalid authorization header')
    }

    console.log('📄 Processing request...')
    logMetrics('request-start')

    // Parse request body
    const body = await req.json()
    const { documentId, storagePath, filename, contentType = 'application/pdf' } = body
    
    if (!documentId || !storagePath) {
      console.error('❌ Missing required fields:', { documentId, storagePath })
      throw new Error(`Missing required fields: ${!documentId ? 'documentId' : ''} ${!storagePath ? 'storagePath' : ''}`)
    }
    
    console.log('📄 Processing document:', { documentId, path: storagePath, filename, contentType })

    // Remove bucket name if present
    const bucketName = 'documents'  // Changed from 'raw_documents' to match actual bucket
    const finalPath = storagePath.startsWith(`${bucketName}/`) 
      ? storagePath.slice(bucketName.length + 1) // +1 for the slash
      : storagePath

    console.log(`📁 Downloading file from path: ${finalPath}`)

    // Download file with retries
    let fileData = await streamFileDownload(finalPath)  // Changed to let
    if (!fileData) {
      throw new Error('Failed to download file')
    }
    metrics.fileSize = fileData.length
    console.log(`📄 File downloaded, size: ${metrics.fileSize} bytes`)
    logMetrics('file-download')

    // Check memory before processing
    if (!checkMemoryUsage()) {
      throw new Error('Memory limit exceeded after file download')
    }

    // Get the Edge Function URL for webhook callback
    const projectRef = 'jhrespvvhbnloxrieycf'
    const webhookUrl = `https://${projectRef}.functions.supabase.co/doc-parser/webhook`
    console.log('🔗 Generated webhook URL:', webhookUrl)
    console.log('🔑 Checking webhook URL requirements:')
    console.log('  - HTTPS protocol:', webhookUrl.startsWith('https://'))
    console.log('  - Domain name (not IP):', !webhookUrl.match(/^https?:\/\/\d+\.\d+\.\d+\.\d+/))
    console.log('  - URL length:', webhookUrl.length, '(must be < 200)')
    
    // Add document metadata as query params to webhook URL
    const webhookParams = new URLSearchParams()
    webhookParams.append('documentId', documentId)
    // Don't encode the storage path twice - URLSearchParams will handle encoding
    webhookParams.append('storagePath', finalPath)
    const fullWebhookUrl = `${webhookUrl}?${webhookParams.toString()}`

    // Call LlamaParse API with webhook
    const llamaParseApiKey = Deno.env.get('LLAMA_CLOUD_API_KEY')
    if (!llamaParseApiKey) {
      throw new Error('Missing LlamaParse API key')
    }

    // Send to LlamaParse for processing
    const llamaParseUrl = 'https://api.cloud.llamaindex.ai/api/v1/parsing/upload'
    const formData = new FormData()
    
    // Keep it simple - just append the file with correct content type
    formData.append('file', new Blob([fileData], { type: contentType }))
    
    // Add webhook if needed
    if (!/[^\x20-\x7E]/.test(fullWebhookUrl)) {
      formData.append('webhook_url', fullWebhookUrl)
    }
    
    // Use minimal headers matching the official example
    const llamaParseResponse = await fetch(llamaParseUrl, {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'Authorization': `Bearer ${llamaParseApiKey}`
      },
      body: formData
    })
      
    if (!llamaParseResponse.ok) {
      const errorText = await llamaParseResponse.text()
      throw new Error(`LlamaParse API error: ${llamaParseResponse.status} - ${errorText}`)
      }
      
    // Clean up file data
    fileData = null

    // Return success response
    return new Response(
      JSON.stringify({
        success: true,
        message: 'Document sent for processing',
        documentId,
        storagePath: finalPath,
        metrics: {
          processingTime: Date.now() - metrics.startTime,
          memoryUsage: Deno.memoryUsage(),
          fileSize: metrics.fileSize
        }
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('❌ Document parsing failed:', error)
    logMetrics('request-error')
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}) 