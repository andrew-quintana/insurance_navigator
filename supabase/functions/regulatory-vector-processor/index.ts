import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface RegulatoryVectorRequest {
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

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
}

Deno.serve(async (req) => {
  let documentId: string | null = null
  
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

  // Add health check endpoint
  if (req.method === 'GET') {
    return new Response(
      JSON.stringify({ 
        status: 'healthy',
        service: 'regulatory-vector-processor',
        timestamp: new Date().toISOString()
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  try {
    console.log('🚀 regulatory-vector-processor started')
    
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      (Deno.env.get('SERVICE_ROLE_KEY') || Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')) ?? ''
    )

    const requestBody = await req.json()
    console.log('📥 Request received:', { 
      hasDocumentId: !!requestBody.documentId,
      textLength: requestBody.extractedText?.length || 0
    })

    const { documentId: reqDocumentId, extractedText }: RegulatoryVectorRequest = requestBody
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

    // Get regulatory document info
    console.log('📋 Fetching regulatory document details...')
    const { data: document, error: docError } = await supabase
      .from('regulatory_documents')
      .select('*')
      .eq('document_id', documentId)
      .single()

    if (docError || !document) {
      console.error('❌ Regulatory document not found:', docError)
      return new Response(
        JSON.stringify({ error: 'Regulatory document not found' }),
        { status: 404 }
      )
    }

    console.log('✅ Regulatory document found:', {
      title: document.title,
      jurisdiction: document.jurisdiction,
      documentType: document.document_type
    })

    // Chunk the text
    const chunks = chunkText(extractedText)
    console.log(`📦 Text chunked into ${chunks.length} pieces`)

    // Check OpenAI API availability first
    console.log('🔍 Checking OpenAI API availability...')
    const openaiAvailable = await checkOpenAIAvailability()
    
    if (!openaiAvailable) {
      console.log('⚠️ OpenAI API not available - implementing graceful degradation')
      
      // Graceful degradation: Store text chunks with zero embeddings
      const zeroEmbedding = JSON.stringify(new Array(1536).fill(0))
       
             const textOnlyVectors = chunks.map((chunk, index) => ({
         user_id: null,
         document_id: null,
         regulatory_document_id: documentId,
         chunk_index: index,
         content_embedding: zeroEmbedding, // Zero vector placeholder
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
       }))

      // Insert text-only vectors
      const { error: insertError } = await supabase
        .from('document_vectors')
        .insert(textOnlyVectors)

      if (insertError) {
        console.error('❌ Error storing text-only vectors:', insertError)
        return new Response(
          JSON.stringify({ error: 'Failed to store document chunks' }),
          { status: 400 }
        )
      }

      console.log('✅ Regulatory document processed without embeddings (graceful degradation)')
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
            throw new Error(`Embedding generation failed: ${embeddingResponse.status}`)
          }

          const embeddingData = await embeddingResponse.json()
          console.log(`✅ Embedding generated for chunk ${i + batchIndex}`)
          
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
        } catch (error) {
          console.error(`❌ Failed to process chunk ${i + batchIndex}:`, error)
          throw error
        }
      })

      try {
        const batchVectors = await Promise.all(embeddingPromises)

        // Insert batch to database
        const { error: insertError } = await supabase
          .from('document_vectors')
          .insert(batchVectors)

        if (insertError) {
          console.error('❌ Database insertion error:', insertError)
          throw new Error(`Failed to store vectors in database: ${insertError.message}`)
        }

        processedChunks += batch.length
        console.log(`✅ Batch processed: ${processedChunks}/${chunks.length} chunks`)
      } catch (batchError) {
        console.error(`❌ Batch processing failed:`, batchError)
        return new Response(
          JSON.stringify({ 
            error: 'Vector processing failed',
            details: batchError.message
          }),
          { status: 400 }
        )
      }
    }

    console.log('✅ regulatory-vector-processor completed successfully')
    return new Response(JSON.stringify({
      success: true,
      chunksProcessed: processedChunks,
      totalChunks: chunks.length,
      documentId: documentId,
      embeddingMethod: 'openai'
    }))
  } catch (error) {
    console.error('❌ regulatory-vector-processor unexpected error:', error)
    
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