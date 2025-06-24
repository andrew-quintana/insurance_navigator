/// <reference lib="deno.ns" />
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

interface ProcessRequest {
  documentId: string
  chunkIndices: number[]
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
}

async function generateEmbedding(text: string): Promise<number[]> {
  const response = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${Deno.env.get('OPENAI_API_KEY')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      input: text,
      model: 'text-embedding-3-small'
    })
  })

  if (!response.ok) {
    throw new Error(`OpenAI API error: ${response.status}`)
  }

  const result = await response.json()
  return result.data[0].embedding
}

serve(async (req) => {
    if (req.method === 'OPTIONS') {
      return new Response('ok', { headers: corsHeaders })
    }
    
  try {
    console.log('🚀 Starting vector processor...')
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    )

    // Log request details
    const requestText = await req.text()
    console.log('📥 Received request:', requestText)

    const { documentId, chunkIndices }: ProcessRequest = JSON.parse(requestText)
    console.log('📄 Parsed request:', { documentId, chunkIndices })
    
    if (!documentId || !chunkIndices) {
      throw new Error('Missing required fields')
    }

    // Get processing status
    const { data: processingStatus, error: statusError } = await supabaseClient
      .from('document_processing_status')
      .select('*')
      .eq('document_id', documentId)
      .single()

    if (statusError) throw statusError
    if (!processingStatus) throw new Error('Processing status not found')

    // Process each chunk
    console.log(`🔄 Processing chunks: ${chunkIndices.join(', ')}`)
    for (const chunkIndex of chunkIndices) {
      try {
        // Download chunk from storage
        const chunkPath = `${processingStatus.storage_path}/chunk_${chunkIndex}.txt`
        const { data: chunkData, error: downloadError } = await supabaseClient
          .storage
      .from('documents')
          .download(chunkPath)

        if (downloadError) throw downloadError
        
        // Convert blob to text
        const chunkText = await chunkData.text()
    
        // Generate embedding
        console.log(`📊 Generating embedding for chunk ${chunkIndex}`)
        const embedding = await generateEmbedding(chunkText)
      
        // Store vector
        await supabaseClient.from('document_vectors').insert({
         document_id: documentId,
          chunk_index: chunkIndex,
          embedding,
          content: chunkText
        })

        // Update processing status
        const updatedChunks = [...processingStatus.processed_chunks, chunkIndex]
        await supabaseClient
          .from('document_processing_status')
        .update({
            processed_chunks: updatedChunks,
            status: updatedChunks.length >= processingStatus.total_chunks ? 'completed' : 'processing'
          })
          .eq('document_id', documentId)

        // Update document progress
        await supabaseClient
          .from('documents')
          .update({
            processed_chunks: updatedChunks.length,
            status: updatedChunks.length >= processingStatus.total_chunks ? 'completed' : 'processing'
          })
          .eq('id', documentId)

        console.log(`✅ Processed chunk ${chunkIndex}`)

      } catch (error) {
        console.error(`❌ Error processing chunk ${chunkIndex}:`, error)
        // Mark error in status but continue with other chunks
        await supabaseClient
          .from('document_processing_status')
          .update({ 
            error: `Error processing chunk ${chunkIndex}: ${error.message}`
          })
          .eq('document_id', documentId)
      }
    }

    // Queue next batch if needed
    const processedCount = processingStatus.processed_chunks.length + chunkIndices.length
    if (processedCount < processingStatus.total_chunks) {
      console.log('🔄 Queueing next batch...')
      const nextBatchSize = 5
      const processedIndices = new Set([...processingStatus.processed_chunks, ...chunkIndices])
      const nextStartIndex = Math.max(...chunkIndices) + 1
      const nextIndices = Array.from(
        { length: nextBatchSize }, 
        (_, i) => nextStartIndex + i
      ).filter(i => i < processingStatus.total_chunks && !processedIndices.has(i))

      if (nextIndices.length > 0) {
        await supabaseClient.functions.invoke('vector-processor', {
          body: JSON.stringify({ documentId, chunkIndices: nextIndices })
        })
      }
    } else {
      console.log('🎉 All chunks processed!')
      // Clean up chunks from storage
      const { error: deleteError } = await supabaseClient
        .storage
        .from('documents')
        .remove([`${processingStatus.storage_path}`])

      if (deleteError) {
        console.warn('⚠️ Failed to clean up chunks:', deleteError)
      }
    }
    
    return new Response(
      JSON.stringify({ 
        success: true,
        processedChunks: chunkIndices.length,
        message: 'Chunks processed successfully'
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

// Check if OpenAI API is available and has quota
async function checkOpenAIAvailability(): Promise<boolean> {
  try {
    const response = await fetch('https://api.openai.com/v1/embeddings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${Deno.env.get('OPENAI_API_KEY')}`
      },
      body: JSON.stringify({ 
        input: "test", 
        model: "text-embedding-3-small", 
        dimensions: 1536 
      })
    })
    
    if (response.status === 429) {
      console.log('⚠️ OpenAI quota exceeded')
      return false
    }
    
    if (response.status === 401) {
      console.log('⚠️ OpenAI authentication failed')
      return false
    }
    
    // Even if other errors, we'll try the normal flow
    return response.ok || response.status < 500
  } catch (error) {
    console.log('⚠️ OpenAI availability check failed:', error.message)
    return false
  }
}

// Enhanced error reporting
async function updateDocumentError(supabase: any, documentId: string, errorMessage: string, classifiedError?: ProcessingError) {
  const errorDetails = classifiedError ? {
    error_type: classifiedError.type,
    retryable: classifiedError.retryable,
    details: classifiedError.details,
    timestamp: new Date().toISOString()
  } : null

  await supabase
    .from('documents')
    .update({ 
      status: 'failed',
      error_message: errorMessage,
      error_details: errorDetails,
      processing_completed_at: new Date().toISOString()
    })
    .eq('id', documentId)
}

async function processChunk(request: ChunkProcessingRequest, supabase: SupabaseClient) {
  const { content, documentId, chunkIndex, isPartial, userId, documentType } = request
  
  try {
    // Generate embeddings for the chunk
    const embedding = await generateEmbedding(content, `chunk ${chunkIndex}`)
    
    // Store the chunk vector with metadata
    const { error: insertError } = await supabase.from('document_vectors')
      .insert({
        user_id: userId,
        document_id: documentId,
        chunk_index: chunkIndex,
        content_embedding: embedding,
        encrypted_chunk_text: content,
        is_partial: isPartial,
        document_source_type: documentType === 'regulatory' ? 'regulatory_document' : 'user_document'
      })

    if (insertError) {
      throw new Error(`Database insertion failed: ${insertError.message}`)
    }
    
    return { success: true, chunkIndex }
    
  } catch (error) {
    console.error(`❌ Failed to process chunk ${chunkIndex}:`, error)
    throw error
  }
} 