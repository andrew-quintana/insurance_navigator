import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface VectorRequest {
  documentId: string;
  extractedText: string;
}

// Enhanced error types for better handling
interface ProcessingError {
  type: 'quota_exceeded' | 'api_error' | 'network_error' | 'validation_error' | 'database_error';
  message: string;
  retryable: boolean;
  details?: any;
}

// Chunking function
function chunkText(text: string, chunkSize: number = 1000, overlap: number = 200): string[] {
  if (text.length <= chunkSize) return [text]
  
  const chunks: string[] = []
  let start = 0
  
  while (start < text.length) {
    let end = start + chunkSize
    if (end >= text.length) {
      chunks.push(text.slice(start))
      break
    }
    
    // Find sentence boundary
    const sentenceEnd = text.lastIndexOf('.', end)
    if (sentenceEnd > start) {
      end = sentenceEnd + 1
    }
    
    chunks.push(text.slice(start, end).trim())
    start = end - overlap
  }
  
  return chunks.filter(chunk => chunk.length > 0)
}

// Enhanced error classification
function classifyError(error: any): ProcessingError {
  const errorMessage = error.message || error.toString()
  
  if (errorMessage.includes('quota') || errorMessage.includes('insufficient_quota') || error.status === 429) {
    return {
      type: 'quota_exceeded',
      message: 'OpenAI API quota exceeded. Please check your billing and usage limits.',
      retryable: false,
      details: error
    }
  }
  
  if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
    return {
      type: 'network_error', 
      message: 'Network connectivity issue with OpenAI API',
      retryable: true,
      details: error
    }
  }
  
  if (error.status >= 400 && error.status < 500) {
    return {
      type: 'api_error',
      message: `OpenAI API error: ${error.status}`,
      retryable: false,
      details: error
    }
  }
  
  return {
    type: 'validation_error',
    message: errorMessage,
    retryable: false,
    details: error
  }
}

Deno.serve(async (req) => {
  let documentId: string | null = null
  
  try {
    console.log('🚀 vector-processor started')
    
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const requestBody = await req.json()
    console.log('📥 Request received:', { 
      hasDocumentId: !!requestBody.documentId,
      textLength: requestBody.extractedText?.length || 0
    })

    const { documentId: reqDocumentId, extractedText }: VectorRequest = requestBody
    documentId = reqDocumentId

    // Validation
    if (!documentId || !extractedText) {
      console.error('❌ Missing required parameters:', { documentId: !!documentId, extractedText: !!extractedText })
      return new Response(
        JSON.stringify({ 
          error: 'Missing required parameters',
          details: 'Both documentId and extractedText are required'
        }),
        { status: 400 }
      )
    }

    // Get document and user info
    console.log('📋 Fetching document details...')
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .single()

    if (docError || !document) {
      console.error('❌ Document not found:', docError)
      return new Response(
        JSON.stringify({ error: 'Document not found' }),
        { status: 404 }
      )
    }

    console.log('✅ Document found:', {
      filename: document.original_filename,
      status: document.status,
      userId: document.user_id
    })

    // Update status to vectorizing
    await supabase
      .from('documents')
      .update({
        status: 'vectorizing',
        progress_percentage: 70
      })
      .eq('id', documentId)

    // Chunk the text
    const chunks = chunkText(extractedText)
    console.log(`📦 Text chunked into ${chunks.length} pieces`)

    // Get active encryption key
    console.log('🔐 Fetching encryption key...')
    const { data: encryptionKey, error: keyError } = await supabase
      .from('encryption_keys')
      .select('id')
      .eq('key_status', 'active')
      .order('created_at', { ascending: false })
      .limit(1)
      .single()

    if (keyError) {
      console.error('❌ Encryption key error:', keyError)
      await updateDocumentError(supabase, documentId, 'Failed to get encryption key', {
        type: 'database_error',
        message: 'Encryption key not found',
        retryable: false,
        details: keyError
      })
      return new Response(
        JSON.stringify({ error: 'Failed to get encryption key' }),
        { status: 400 }
      )
    }

    console.log('✅ Encryption key found')

    // Check OpenAI API availability first
    console.log('🔍 Checking OpenAI API availability...')
    const openaiAvailable = await checkOpenAIAvailability()
    
    if (!openaiAvailable) {
      console.log('⚠️ OpenAI API not available - implementing graceful degradation')
      
             // Graceful degradation: Store text chunks with zero embeddings
       // This allows the document to be marked as processed and searchable via text
       // Zero vector indicates no semantic search available, but text search works
       const zeroEmbedding = JSON.stringify(new Array(1536).fill(0))
       
       const textOnlyVectors = chunks.map((chunk, index) => ({
         user_id: document.user_id,
         document_id: documentId,
         document_record_id: documentId,
         chunk_index: index,
         content_embedding: zeroEmbedding, // Zero vector placeholder
         encrypted_chunk_text: chunk,
         encrypted_chunk_metadata: JSON.stringify({
           filename: document.original_filename,
           file_size: document.file_size,
           content_type: document.content_type,
           chunk_length: chunk.length,
           total_chunks: chunks.length,
           processed_at: new Date().toISOString(),
           extraction_method: document.content_type === 'application/pdf' ? 'llamaparse' : 'direct',
           embedding_method: 'none_quota_exceeded',
           note: 'Processed without embeddings due to OpenAI quota limits - zero vector used as placeholder'
         }),
         encryption_key_id: encryptionKey.id
       }))

      // Insert text-only vectors
      const { error: insertError } = await supabase
        .from('user_document_vectors')
        .insert(textOnlyVectors)

      if (insertError) {
        console.error('❌ Error storing text-only vectors:', insertError)
        await updateDocumentError(supabase, documentId, 'Failed to store document chunks', {
          type: 'database_error',
          message: 'Database insertion failed',
          retryable: true,
          details: insertError
        })
        return new Response(
          JSON.stringify({ error: 'Failed to store document chunks' }),
          { status: 400 }
        )
      }

      // Mark as completed with warning
      await supabase
        .from('documents')
        .update({
          status: 'completed',
          progress_percentage: 100,
          processing_completed_at: new Date().toISOString(),
          processed_chunks: chunks.length,
          total_chunks: chunks.length,
          error_message: 'Processed without embeddings due to OpenAI quota limits. Text search available.'
        })
        .eq('id', documentId)

      console.log('✅ Document processed without embeddings (graceful degradation)')
      return new Response(JSON.stringify({
        success: true,
        chunksProcessed: chunks.length,
        totalChunks: chunks.length,
        documentId: documentId,
        warning: 'Document processed without embeddings due to API quota limits. Text search is available.',
        embeddingMethod: 'none_quota_exceeded'
      }))
    }

    // Process chunks with embeddings (normal flow)
    console.log('🧠 Processing chunks with embeddings...')
    const batchSize = 5
    let processedChunks = 0
    
    for (let i = 0; i < chunks.length; i += batchSize) {
      const batch = chunks.slice(i, i + batchSize)
      console.log(`📦 Processing batch ${Math.ceil((i + batchSize) / batchSize)} of ${Math.ceil(chunks.length / batchSize)}`)
      
      // Generate embeddings for batch
      const embeddingPromises = batch.map(async (chunk, batchIndex) => {
        try {
          console.log(`🧠 Generating embedding for chunk ${i + batchIndex}...`)
          const embeddingResponse = await fetch('https://api.openai.com/v1/embeddings', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${Deno.env.get('OPENAI_API_KEY')}`
            },
            body: JSON.stringify({ input: chunk, model: "text-embedding-3-small", dimensions: 1536 })
          })

          if (!embeddingResponse.ok) {
            const errorText = await embeddingResponse.text()
            console.error(`❌ Embedding failed for chunk ${i + batchIndex}:`, {
              status: embeddingResponse.status,
              error: errorText
            })
            
            const error = { status: embeddingResponse.status, message: errorText }
            const classifiedError = classifyError(error)
            throw classifiedError
          }

          const embeddingData = await embeddingResponse.json()
          console.log(`✅ Embedding generated for chunk ${i + batchIndex}`)
          
          return {
            user_id: document.user_id,
            document_id: documentId,
            document_record_id: documentId,
            chunk_index: i + batchIndex,
            content_embedding: JSON.stringify(embeddingData.data[0].embedding),
            encrypted_chunk_text: chunk,
            encrypted_chunk_metadata: JSON.stringify({
              filename: document.original_filename,
              file_size: document.file_size,
              content_type: document.content_type,
              chunk_length: chunk.length,
              total_chunks: chunks.length,
              processed_at: new Date().toISOString(),
              extraction_method: document.content_type === 'application/pdf' ? 'llamaparse' : 'direct',
              embedding_method: 'openai'
            }),
            encryption_key_id: encryptionKey.id
          }
        } catch (error) {
          console.error(`❌ Failed to process chunk ${i + batchIndex}:`, error)
          throw error
        }
      })

      try {
        const batchVectors = await Promise.all(embeddingPromises)

        // Insert batch to database
        const { error: insertError } = await supabase
          .from('user_document_vectors')
          .insert(batchVectors)

        if (insertError) {
          console.error('❌ Database insertion error:', insertError)
          throw {
            type: 'database_error',
            message: 'Failed to store vectors in database',
            retryable: true,
            details: insertError
          }
        }

        processedChunks += batch.length

        // Update progress
        const progress = Math.min(70 + Math.round((processedChunks / chunks.length) * 25), 95)
        await supabase
          .from('documents')
          .update({
            progress_percentage: progress,
            processed_chunks: processedChunks,
            total_chunks: chunks.length
          })
          .eq('id', documentId)

        console.log(`✅ Batch processed: ${processedChunks}/${chunks.length} chunks`)
      } catch (batchError) {
        console.error(`❌ Batch processing failed:`, batchError)
        const classifiedError = typeof batchError === 'object' && batchError.type ? batchError : classifyError(batchError)
        await updateDocumentError(supabase, documentId, `Vector processing failed: ${classifiedError.message}`, classifiedError)
        return new Response(
          JSON.stringify({ 
            error: 'Vector processing failed',
            details: classifiedError.message,
            retryable: classifiedError.retryable
          }),
          { status: 400 }
        )
      }
    }

    // Mark as completed
    console.log('🎉 Marking document as completed...')
    const { error: completeError } = await supabase
      .from('documents')
      .update({
        status: 'completed',
        progress_percentage: 100,
        processing_completed_at: new Date().toISOString()
      })
      .eq('id', documentId)

    if (completeError) {
      console.error('⚠️ Error marking document as completed:', completeError)
    }

    console.log('✅ vector-processor completed successfully')
    return new Response(JSON.stringify({
      success: true,
      chunksProcessed: processedChunks,
      totalChunks: chunks.length,
      documentId: documentId,
      embeddingMethod: 'openai'
    }))
  } catch (error) {
    console.error('❌ vector-processor unexpected error:', error)
    
    if (documentId) {
      const classifiedError = classifyError(error)
      await updateDocumentError(supabase, documentId, `Unexpected error: ${classifiedError.message}`, classifiedError)
    }
    
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        details: error.message || 'Unknown error occurred'
      }),
      { status: 500 }
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