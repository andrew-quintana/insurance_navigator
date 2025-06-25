import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.21.0'
import { corsHeaders } from '../_shared/cors.ts'

// Add Deno types
declare const Deno: {
  env: {
    get(key: string): string | undefined;
    toObject(): { [key: string]: string };
  };
  memoryUsage(): { heapUsed: number; rss: number; external: number };
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

// Initialize Supabase client
const supabaseClient = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
)

// Debug environment loading
console.log('🔑 Environment check:', {
  hasSupabaseUrl: !!Deno.env.get('SUPABASE_URL'),
  hasServiceKey: !!Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'),
  hasLlamaKey: !!Deno.env.get('LLAMA_CLOUD_API_KEY'),
  envKeys: Object.keys(Deno.env.toObject()).sort(),
})

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

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }
  
  try {
    console.log('🔍 Doc-parser started - method:', req.method)
    
    // Handle GET requests for health checks
    if (req.method === 'GET') {
      return new Response(JSON.stringify({
        status: 'healthy',
        service: 'doc-parser',
        timestamp: new Date().toISOString()
      }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }
    
    // Only handle POST requests for document processing
    if (req.method !== 'POST') {
      return new Response(JSON.stringify({
        error: 'Method not allowed',
        allowed_methods: ['POST', 'GET', 'OPTIONS']
      }), {
        status: 405,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    // Parse request body
    let requestData: any
    try {
      requestData = await req.json()
    } catch (jsonError) {
      console.error('❌ JSON parsing error:', jsonError)
      return new Response(JSON.stringify({ 
        error: 'Invalid JSON payload',
        details: 'Request body must be valid JSON'
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }
    
    const { jobId, documentId, storagePath } = requestData
    
    if (!jobId || !documentId || !storagePath) {
      return new Response(JSON.stringify({ 
        error: 'Missing required parameters: jobId, documentId, storagePath'
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log('📄 Processing document:', { jobId, documentId, storagePath })

    // Get document record from database
    const { data: documents, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .single()

    if (docError || !documents) {
      console.error('❌ Document not found:', docError || 'No document record')
      return new Response(JSON.stringify({ 
        error: 'Document not found',
        details: docError?.message || 'No document record exists'
      }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    // Download file from storage
    const { data: fileData, error: downloadError } = await supabase.storage
      .from('documents')
      .download(storagePath)

    if (downloadError || !fileData) {
      console.error('❌ File download failed:', downloadError || 'No file data')
      return new Response(JSON.stringify({ 
        error: 'File download failed',
        details: downloadError?.message || 'No file data'
      }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    // Update document status to processing
    await supabase
      .from('documents')
      .update({
        status: 'processing',
        progress_percentage: 30,
        processing_started_at: new Date().toISOString()
      })
      .eq('id', documentId)

    // Process with LlamaParse
    const llamaCloudKey = Deno.env.get('LLAMA_CLOUD_API_KEY')
    if (!llamaCloudKey) {
      throw new Error('LlamaParse API key not configured')
    }

    // Prepare file for LlamaCloud upload
    const formData = new FormData()
    formData.append('file', fileData, documents.original_filename)

    // Upload to LlamaParse
    const uploadResponse = await uploadToLlamaParse(formData, llamaCloudKey)
    if (!uploadResponse.ok) {
      throw new Error(`LlamaParse upload failed: ${uploadResponse.status}`)
    }

    const uploadResult = await uploadResponse.json()
    const extractedText = uploadResult.text || ''

    if (!extractedText || extractedText.length < 50) {
      throw new Error('LlamaParse returned insufficient content')
    }

    // Update document with extracted text
    await supabase
      .from('documents')
      .update({
        status: 'completed',
        progress_percentage: 100,
        processing_completed_at: new Date().toISOString(),
        structured_contents: {
          text: extractedText,
          metadata: uploadResult.metadata || {}
        }
      })
      .eq('id', documentId)

    return new Response(JSON.stringify({
      success: true,
      jobId,
      documentId,
      extractedText,
      metadata: uploadResult.metadata || {}
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('❌ Processing error:', error)
    return new Response(JSON.stringify({ 
      success: false,
      error: error.message
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
}) 