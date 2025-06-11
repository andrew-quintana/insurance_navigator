import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface VectorRequest {
  documentId: string;
  extractedText: string;
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

Deno.serve(async (req) => {
  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const { documentId, extractedText }: VectorRequest = await req.json()

    // Get document and user info
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .single()

    if (docError || !document) {
      console.error('Error fetching document:', docError)
      return new Response(
        JSON.stringify({ error: 'Document not found' }),
        { status: 404 }
      )
    }

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
    console.log(`Processing ${chunks.length} chunks for document ${documentId}`)

    // Get active encryption key
    const { data: encryptionKey, error: keyError } = await supabase
      .from('encryption_keys')
      .select('id')
      .eq('key_status', 'active')
      .order('created_at', { ascending: false })
      .limit(1)
      .single()

    if (keyError) {
      console.error('Error fetching encryption key:', keyError)
      await updateDocumentError(supabase, documentId, 'Failed to get encryption key')
      return new Response(
        JSON.stringify({ error: 'Failed to get encryption key' }),
        { status: 400 }
      )
    }

    // Process chunks in batches to avoid overwhelming the embedding API
    const batchSize = 5
    let processedChunks = 0
    
    for (let i = 0; i < chunks.length; i += batchSize) {
      const batch = chunks.slice(i, i + batchSize)
      
      // Generate embeddings for batch
      const embeddingPromises = batch.map(async (chunk, batchIndex) => {
        try {
          let embeddingData
          let embeddingMethod = 'openai'

          // Try OpenAI first
          try {
            console.log(`🧠 Generating embedding for chunk ${i + batchIndex} using OpenAI...`)
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
              console.error(`Embedding generation failed for chunk ${i + batchIndex}: ${embeddingResponse.status} - ${errorText}`)
              
              // If quota exceeded (429), throw specific error to trigger fallback
              if (embeddingResponse.status === 429) {
                throw new Error(`QUOTA_EXCEEDED:${errorText}`)
              } else {
                throw new Error(`Embedding generation failed: ${embeddingResponse.status}`)
              }
            }

            embeddingData = await embeddingResponse.json()
            console.log(`✅ OpenAI embedding generated for chunk ${i + batchIndex}`)
          } catch (openaiError) {
            console.log(`⚠️ OpenAI embedding failed for chunk ${i + batchIndex}: ${openaiError.message}`)
            
            // If it's a quota issue, fall back to Supabase embeddings
            if (openaiError.message.includes('QUOTA_EXCEEDED')) {
              console.log(`🔄 Falling back to Supabase embeddings for chunk ${i + batchIndex}...`)
              
              try {
                // Use Supabase's built-in embedding function
                const { data: supabaseEmbedding, error: embeddingError } = await supabase.rpc('get_embedding', {
                  input_text: chunk
                })

                if (embeddingError || !supabaseEmbedding) {
                  console.error(`❌ Supabase embedding failed for chunk ${i + batchIndex}:`, embeddingError)
                  throw new Error(`Supabase embedding failed: ${embeddingError?.message || 'Unknown error'}`)
                }

                embeddingData = { data: [{ embedding: supabaseEmbedding }] }
                embeddingMethod = 'supabase'
                console.log(`✅ Supabase embedding generated for chunk ${i + batchIndex}`)
              } catch (supabaseError) {
                console.error(`❌ Both OpenAI and Supabase embeddings failed for chunk ${i + batchIndex}`)
                throw new Error(`All embedding methods failed: ${supabaseError.message}`)
              }
            } else {
              // For non-quota errors, re-throw
              throw openaiError
            }
          }
          
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
              embedding_method: embeddingMethod
            }),
            encryption_key_id: encryptionKey.id
          }
        } catch (error) {
          console.error(`Failed to process chunk ${i + batchIndex}:`, error)
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
          console.error('Error inserting vectors:', insertError)
          throw new Error(`Failed to store vectors: ${insertError.message}`)
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

        console.log(`Processed batch ${Math.ceil((i + batchSize) / batchSize)} of ${Math.ceil(chunks.length / batchSize)}`)
      } catch (batchError) {
        console.error(`Failed to process batch starting at ${i}:`, batchError)
        await updateDocumentError(supabase, documentId, `Vector processing failed: ${batchError.message}`)
        return new Response(
          JSON.stringify({ error: 'Vector processing failed' }),
          { status: 400 }
        )
      }
    }

    // Mark as completed
    const { error: completeError } = await supabase
      .from('documents')
      .update({
        status: 'completed',
        progress_percentage: 100,
        processing_completed_at: new Date().toISOString()
      })
      .eq('id', documentId)

    if (completeError) {
      console.error('Error marking document as completed:', completeError)
    }

    return new Response(JSON.stringify({
      success: true,
      chunksProcessed: processedChunks,
      totalChunks: chunks.length,
      documentId: documentId
    }))
  } catch (error) {
    console.error('vector-processor error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500 }
    )
  }
})

async function updateDocumentError(supabase: any, documentId: string, errorMessage: string) {
  await supabase
    .from('documents')
    .update({ 
      status: 'failed',
      error_message: errorMessage,
      processing_completed_at: new Date().toISOString()
    })
    .eq('id', documentId)
} 