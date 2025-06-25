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
    const { documentId, storagePath } = body
    
    if (!documentId || !storagePath) {
      throw new Error(`Missing required fields: ${!documentId ? 'documentId' : ''} ${!storagePath ? 'storagePath' : ''}`)
    }
    
    console.log(`📄 Processing document ${documentId} from ${storagePath}`)

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
    const webhookUrl = `https://${projectRef}.supabase.co/functions/v1/doc-parser/webhook`
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
    const llamaParseUrl = 'https://api.llamacloud.ai/v1/parse-document'
    const llamaParseResponse = await fetch(llamaParseUrl, {
      method: 'POST',
        headers: {
        'Authorization': `Bearer ${llamaParseApiKey}`,
          'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        file: fileData,
        webhook_url: fullWebhookUrl,
        options: {
          output_format: 'markdown',
          include_images: true
        }
      })
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