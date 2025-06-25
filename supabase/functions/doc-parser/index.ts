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
async function streamFileDownload(supabaseClient: any, storagePath: string): Promise<Uint8Array> {
  console.log(`📥 Streaming file download: ${storagePath}`)
  
  const { data: fileData, error: downloadError } = await supabaseClient.storage
    .from('raw_documents')
    .download(storagePath)

  if (downloadError) {
    throw new Error(`Failed to download file: ${downloadError.message}`)
  }

  if (!fileData) {
    throw new Error('No file data received from storage')
  }

  if (fileData.size > CONFIG.MAX_FILE_SIZE) {
    throw new Error(`File too large: ${fileData.size} bytes (max ${CONFIG.MAX_FILE_SIZE} bytes)`)
  }

  // Stream file data in chunks
  const chunks: Uint8Array[] = []
  const reader = fileData.stream().getReader()
  
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      chunks.push(value)
      
      // Check memory usage after each chunk
      if (!checkMemoryUsage()) {
        reader.releaseLock()
        throw new Error('Memory limit exceeded during file streaming')
      }
    }
  } finally {
    reader.releaseLock()
  }

  // Combine chunks efficiently
  const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0)
  const result = new Uint8Array(totalLength)
  let offset = 0
  for (const chunk of chunks) {
    result.set(chunk, offset)
    offset += chunk.length
  }

  return result
}

serve(async (req) => {
  metrics.startTime = Date.now()
  
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
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

      // Initialize Supabase client
      const supabaseClient = createClient(
        Deno.env.get('SUPABASE_URL') ?? '',
        Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
      )

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
    const { documentId, storagePath } = await req.json()
    console.log(`📄 Processing document ${documentId} from ${storagePath}`)

    // Initialize Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Stream file download
    const fileData = await streamFileDownload(supabaseClient, storagePath)
    metrics.fileSize = fileData.length
    console.log(`📄 File downloaded, size: ${fileData.length} bytes`)
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
    const webhookParams = new URLSearchParams({
      documentId,
      storagePath: encodeURIComponent(storagePath)
    })
    const fullWebhookUrl = `${webhookUrl}?${webhookParams.toString()}`

    // Call LlamaParse API with webhook
    console.log('🦙 Calling LlamaParse API with webhook...')
    const formData = new FormData()
    formData.append('file', new Blob([fileData], { type: 'application/pdf' }), 'document.pdf')
    formData.append('webhook_url', fullWebhookUrl)
    
    const parseResponse = await fetch('https://api.cloud.llamaindex.ai/api/v1/parsing/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('LLAMACLOUD_API_KEY')}`
      },
      body: formData
    })

    // Clean up file data
    fileData = null

    if (!parseResponse.ok) {
      const errorText = await parseResponse.text()
      throw new Error(`LlamaParse API error: ${parseResponse.status} - ${errorText}`)
    }

    const parseResult = await parseResponse.json()
    console.log(`📋 LlamaParse job created: ${parseResult.id}`)
    logMetrics('llamaparse-upload')

    // Update document status to processing
    const { error: updateError } = await supabaseClient
      .from('documents')
      .update({
        status: 'processing',
        metadata: {
          llamaparse_job_id: parseResult.id,
          startedAt: new Date().toISOString(),
          fileSize: metrics.fileSize,
          processingTime: Date.now() - metrics.startTime,
          memoryMetrics: Deno.memoryUsage()
        }
      })
      .eq('id', documentId)

    if (updateError) {
      throw new Error(`Failed to update document status: ${updateError.message}`)
    }

    logMetrics('request-complete')

    return new Response(
      JSON.stringify({ 
        success: true,
        jobId: parseResult.id,
        message: 'Document processing started. Results will be sent via webhook.',
        metrics: {
          processingTime: Date.now() - metrics.startTime,
          fileSize: metrics.fileSize,
          memoryUsage: Deno.memoryUsage()
        }
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('❌ Document parsing failed:', error)
    logMetrics('request-error')
    return new Response(
      JSON.stringify({ 
        success: false,
        error: error.message,
        details: error.stack,
        metrics: {
          processingTime: Date.now() - metrics.startTime,
          fileSize: metrics.fileSize,
          memoryUsage: Deno.memoryUsage()
        }
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}) 