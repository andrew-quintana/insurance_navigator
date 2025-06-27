/// <reference lib="deno.ns" />
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

interface ChunkRequest {
  documentId: string
  text: string
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
}

function chunkText(text: string, chunkSize: number = 1500, overlap: number = 100): string[] {
  if (text.length <= chunkSize) return [text]
  
  const chunks: string[] = []
  let start = 0
  
  while (start < text.length) {
    let end = start + chunkSize
    
    // Find next sentence boundary
    if (end < text.length) {
      const nextPeriod = text.indexOf('.', end)
      end = nextPeriod > -1 && nextPeriod - end < 100 ? nextPeriod + 1 : end
    }
    
    chunks.push(text.slice(Math.max(0, start - overlap), end))
    start = end
  }
  
  return chunks
}

serve(async (req) => {
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

  // Add health check endpoint
  if (req.method === 'GET') {
    return new Response(
      JSON.stringify({ 
        status: 'healthy',
        service: 'chunking-service',
        timestamp: new Date().toISOString()
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    )

    const { documentId, text }: ChunkRequest = await req.json()
    
    if (!documentId || !text) {
      throw new Error('Missing required fields')
    }

    // Generate chunks
    console.log('📝 Chunking text...', { textLength: text.length })
    const chunks = chunkText(text)
    
    // Create storage folder path
    const storagePath = `raw_documents/${documentId}/chunks`
    
    // Store chunks in storage bucket
    console.log('💾 Storing chunks in bucket...')
    const chunkUploads = chunks.map(async (content, index) => {
      const chunkPath = `${storagePath}/chunk_${index}.txt`
      const { error: uploadError } = await supabaseClient
        .storage
        .from('documents')
        .upload(chunkPath, new Blob([content], { type: 'text/plain' }), {
          cacheControl: '3600',
          upsert: true
        })
      
      if (uploadError) throw uploadError
      return index
    })

    // Upload all chunks
    await Promise.all(chunkUploads)
    console.log('✅ All chunks stored successfully')

    // Store processing status in database
    console.log('📊 Creating processing status record...')
    const { error: statusError } = await supabaseClient
      .from('document_processing_status')
      .insert({
        document_id: documentId,
        total_chunks: chunks.length,
        processed_chunks: [],
        status: 'chunked',
        chunk_size: 1500,
        overlap: 100,
        storage_path: storagePath
      })

    if (statusError) throw statusError

    // Update document status
    await supabaseClient
      .from('documents')
      .update({ 
        status: 'processing',
        total_chunks: chunks.length,
        processed_chunks: 0
      })
      .eq('id', documentId)

    // Queue first batch for processing
    console.log('🚀 Queueing first batch for processing...')
    const batchSize = 5
    const firstBatch = Array.from({ length: Math.min(batchSize, chunks.length) }, (_, i) => i)
    
    await supabaseClient.functions.invoke('vector-processor', {
      body: JSON.stringify({ documentId, chunkIndices: firstBatch })
    })

    return new Response(
      JSON.stringify({ 
        success: true, 
        totalChunks: chunks.length,
        message: 'Document chunked and processing started',
        storagePath
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    )

  } catch (error) {
    console.error('❌ Error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400
      }
    )
  }
}) 