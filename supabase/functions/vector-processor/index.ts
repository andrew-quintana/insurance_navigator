import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface VectorRequest {
  documentId: string;
  extractedText: string;
  documentType?: 'user' | 'regulatory'; // New field to specify document type
}

// Enhanced error types for better handling
interface ProcessingError {
  type: 'quota_exceeded' | 'api_error' | 'network_error' | 'validation_error' | 'database_error';
  message: string;
  retryable: boolean;
  details?: any;
}

// Document type configuration
interface DocumentConfig {
  sourceTable: string;
  vectorTable: string;
  documentSourceType: string;
  idField: string;
  updateFields: Record<string, any>;
}

function getDocumentConfig(documentType: 'user' | 'regulatory'): DocumentConfig {
  if (documentType === 'regulatory') {
    return {
      sourceTable: 'regulatory_documents',
      vectorTable: 'document_vectors',
      documentSourceType: 'regulatory_document',
      idField: 'document_id',
      updateFields: {
        processing_status: 'vectorizing',
        progress_percentage: 70
      }
    };
  }
  
  // Default to user documents
  return {
    sourceTable: 'documents',
    vectorTable: 'document_vectors',
    documentSourceType: 'user_document',
    idField: 'id',
    updateFields: {
      status: 'vectorizing',
      progress_percentage: 70
    }
  };
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
  let documentType: 'user' | 'regulatory' = 'user'
  
  try {
    console.log('🚀 vector-processor started (agnostic mode)')
    
    const supabase = createClient(
        Deno.env.get('SUPABASE_URL') ?? '',
  (Deno.env.get('SERVICE_ROLE_KEY') || Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')) ?? ''
    )

    const requestBody = await req.json()
    console.log('📥 Request received:', { 
      hasDocumentId: !!requestBody.documentId,
      textLength: requestBody.extractedText?.length || 0,
      documentType: requestBody.documentType || 'user'
    })

    const { documentId: reqDocumentId, extractedText, documentType: reqDocumentType }: VectorRequest = requestBody
    documentId = reqDocumentId
    documentType = reqDocumentType || 'user'

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

    // Get document configuration based on type
    const config = getDocumentConfig(documentType)
    console.log('📋 Using configuration:', { documentType, config })

    // Get document info from appropriate table
    console.log(`📋 Fetching ${documentType} document details...`)
    const { data: document, error: docError } = await supabase
      .from(config.sourceTable)
      .select('*')
      .eq(config.idField, documentId)
      .single()

    if (docError || !document) {
      console.error(`❌ ${documentType} document not found:`, docError)
      return new Response(
        JSON.stringify({ error: `${documentType} document not found` }),
        { status: 404 }
      )
    }

    if (documentType === 'user') {
      console.log('✅ User document found:', {
        filename: document.original_filename,
        status: document.status,
        userId: document.user_id
      })
    } else {
      console.log('✅ Regulatory document found:', {
        title: document.title,
        jurisdiction: document.jurisdiction,
        documentType: document.document_type
      })
    }

    // Update status to vectorizing
    await supabase
      .from(config.sourceTable)
      .update(config.updateFields)
      .eq(config.idField, documentId)

    // Chunk the text
    const chunks = chunkText(extractedText)
    console.log(`📦 Text chunked into ${chunks.length} pieces`)

    // Get active encryption key (only for user documents)
    let encryptionKey = null
    if (documentType === 'user') {
      console.log('🔐 Fetching encryption key...')
      const { data: key, error: keyError } = await supabase
        .from('encryption_keys')
        .select('id')
        .eq('key_status', 'active')
        .order('created_at', { ascending: false })
        .limit(1)
        .single()

      if (keyError) {
        console.error('❌ Encryption key error:', keyError)
        await updateDocumentError(supabase, documentId, documentType, config, 'Failed to get encryption key', {
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
      
      encryptionKey = key
      console.log('✅ Encryption key found')
    }

    // Check OpenAI API availability first
    console.log('🔍 Checking OpenAI API availability...')
    const openaiAvailable = await checkOpenAIAvailability()
    
    if (!openaiAvailable) {
      console.log('⚠️ OpenAI API not available - implementing graceful degradation')
      
      // Graceful degradation: Store text chunks with zero embeddings
      const zeroEmbedding = JSON.stringify(new Array(1536).fill(0))
       
      const textOnlyVectors = chunks.map((chunk, index) => {
        if (documentType === 'regulatory') {
          return {
            user_id: null,
            document_id: null,
            regulatory_document_id: documentId,
            chunk_index: index,
            content_embedding: zeroEmbedding,
            encrypted_chunk_text: chunk,
            encrypted_chunk_metadata: JSON.stringify({
              title: document.title,
              jurisdiction: document.jurisdiction,
              document_type: document.document_type,
              chunk_length: chunk.length,
              total_chunks: chunks.length,
              processed_at: new Date().toISOString(),
              extraction_method: 'regulatory_bulk_processing',
              embedding_method: 'none_quota_exceeded',
              note: 'Processed without embeddings due to OpenAI quota limits - zero vector used as placeholder'
            }),
            document_source_type: 'regulatory_document',
            is_active: true,
            created_at: new Date().toISOString()
          }
        } else {
          return {
            user_id: document.user_id,
            document_id: documentId,
            document_record_id: documentId,
            chunk_index: index,
            content_embedding: zeroEmbedding,
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
            encryption_key_id: encryptionKey?.id
          }
        }
      })

      // Insert text-only vectors
      const { error: insertError } = await supabase
        .from(config.vectorTable)
        .insert(textOnlyVectors)

      if (insertError) {
        console.error('❌ Error storing text-only vectors:', insertError)
        await updateDocumentError(supabase, documentId, documentType, config, 'Failed to store document chunks', {
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
      const completedFields = documentType === 'regulatory' ? {
        processing_status: 'completed',
        status: 'completed',
        progress_percentage: 100,
        vectors_generated: true,
        vector_count: chunks.length,
        error_message: 'Processed without embeddings due to OpenAI quota limits. Text search available.'
      } : {
        status: 'completed',
        progress_percentage: 100,
        processing_completed_at: new Date().toISOString(),
        processed_chunks: chunks.length,
        total_chunks: chunks.length,
        error_message: 'Processed without embeddings due to OpenAI quota limits. Text search available.'
      }

      await supabase
        .from(config.sourceTable)
        .update(completedFields)
        .eq(config.idField, documentId)

      console.log(`✅ ${documentType} document processed without embeddings (graceful degradation)`)
      return new Response(JSON.stringify({
        success: true,
        chunksProcessed: chunks.length,
        totalChunks: chunks.length,
        documentId: documentId,
        documentType: documentType,
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
          
          if (documentType === 'regulatory') {
            return {
              user_id: null,
              document_id: null,
              regulatory_document_id: documentId,
              chunk_index: i + batchIndex,
              content_embedding: JSON.stringify(embeddingData.data[0].embedding),
              encrypted_chunk_text: chunk,
              encrypted_chunk_metadata: JSON.stringify({
                title: document.title,
                jurisdiction: document.jurisdiction,
                document_type: document.document_type,
                chunk_length: chunk.length,
                total_chunks: chunks.length,
                processed_at: new Date().toISOString(),
                extraction_method: 'regulatory_bulk_processing',
                embedding_method: 'openai'
              }),
              document_source_type: 'regulatory_document',
              is_active: true,
              created_at: new Date().toISOString()
            }
          } else {
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
              encryption_key_id: encryptionKey?.id
            }
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
          .from(config.vectorTable)
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
        const progressFields = documentType === 'regulatory' ? {
          progress_percentage: progress,
          vector_count: processedChunks
        } : {
          progress_percentage: progress,
          processed_chunks: processedChunks,
          total_chunks: chunks.length
        }

        await supabase
          .from(config.sourceTable)
          .update(progressFields)
          .eq(config.idField, documentId)

        console.log(`✅ Batch processed: ${processedChunks}/${chunks.length} chunks`)
      } catch (batchError) {
        console.error(`❌ Batch processing failed:`, batchError)
        const classifiedError = typeof batchError === 'object' && batchError.type ? batchError : classifyError(batchError)
        await updateDocumentError(supabase, documentId, documentType, config, `Vector processing failed: ${classifiedError.message}`, classifiedError)
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
    console.log(`🎉 Marking ${documentType} document as completed...`)
    const completedFields = documentType === 'regulatory' ? {
      processing_status: 'completed',
      status: 'completed',
      progress_percentage: 100,
      vectors_generated: true,
      vector_count: processedChunks
    } : {
      status: 'completed',
      progress_percentage: 100,
      processing_completed_at: new Date().toISOString()
    }

    const { error: completeError } = await supabase
      .from(config.sourceTable)
      .update(completedFields)
      .eq(config.idField, documentId)

    if (completeError) {
      console.error('⚠️ Error marking document as completed:', completeError)
    }

    console.log(`✅ vector-processor completed successfully for ${documentType} document`)
    return new Response(JSON.stringify({
      success: true,
      chunksProcessed: processedChunks,
      totalChunks: chunks.length,
      documentId: documentId,
      documentType: documentType,
      embeddingMethod: 'openai'
    }))
  } catch (error) {
    console.error('❌ vector-processor unexpected error:', error)
    
    if (documentId) {
      const config = getDocumentConfig(documentType)
      const classifiedError = classifyError(error)
      await updateDocumentError(supabase, documentId, documentType, config, `Unexpected error: ${classifiedError.message}`, classifiedError)
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
async function updateDocumentError(supabase: any, documentId: string, documentType: 'user' | 'regulatory', config: DocumentConfig, errorMessage: string, classifiedError?: ProcessingError) {
  const errorDetails = classifiedError ? {
    error_type: classifiedError.type,
    retryable: classifiedError.retryable,
    details: classifiedError.details,
    timestamp: new Date().toISOString()
  } : null

  const errorFields = documentType === 'regulatory' ? {
    processing_status: 'failed',
    status: 'failed',
    error_message: errorMessage,
    progress_percentage: 0
  } : {
    status: 'failed',
    error_message: errorMessage,
    error_details: errorDetails,
    progress_percentage: 0
  }

  await supabase
    .from(config.sourceTable)
    .update(errorFields)
    .eq(config.idField, documentId)
} 