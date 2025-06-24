/// <reference lib="deno.ns" />
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient, SupabaseClient } from '@supabase/supabase-js'
import { corsHeaders } from '../_shared/cors.ts'
import { OpenAIEmbeddings } from '../_shared/embeddings.ts'

interface VectorRequest {
  documentId: string
  extractedText: string
  documentType: 'user_uploaded' | 'regulatory'
  metadata?: {
    jurisdiction?: string
    programs?: string[]
    tags?: string[]
    extraction_method?: string
    content_length?: number
    [key: string]: any
  }
}

interface VectorResult {
  success: boolean
  documentId: string
  chunksProcessed: number
  error?: string
}

serve(async (req: Request) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient: SupabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const { documentId, extractedText, documentType, metadata = {} } = await req.json() as VectorRequest

    if (!documentId || !extractedText) {
      throw new Error('Missing required parameters: documentId and extractedText')
    }

    // Get document record
    const { data: document, error: docError } = await supabaseClient
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .single()

    if (docError || !document) {
      throw new Error(`Document not found: ${docError?.message || 'Unknown error'}`)
    }

    // Initialize OpenAI embeddings
    const embeddings = new OpenAIEmbeddings(Deno.env.get('OPENAI_API_KEY') ?? '')

    // Create text chunks
    const chunkSize = 1000
    const chunkOverlap = 200
    const chunks: string[] = []

    let start = 0
    while (start < extractedText.length) {
      const end = start + chunkSize
      const chunk = extractedText.slice(start, end)
      chunks.push(chunk)
      start = end - chunkOverlap
      if (start >= extractedText.length) break
    }

    console.log(`Created ${chunks.length} chunks for document ${documentId}`)

    // Generate embeddings for all chunks
    const embeddingsList: number[][] = []
    for (let i = 0; i < chunks.length; i++) {
      try {
        const embedding = await embeddings.embedText(chunks[i])
        embeddingsList.push(embedding)
        console.log(`Generated embedding for chunk ${i}: ${embedding.length} dimensions`)
      } catch (error) {
        console.error(`Failed to generate embedding for chunk ${i}:`, error)
        // Use zero vector as fallback
        embeddingsList.push(new Array(1536).fill(0))
      }
    }

    // Store vectors in document_vectors table
    const vectorIds: string[] = []

    for (let i = 0; i < chunks.length; i++) {
      try {
        const chunkMetadata = {
          ...metadata,
          chunk_index: i,
          total_chunks: chunks.length,
          chunk_length: chunks[i].length,
          processed_at: new Date().toISOString(),
          document_type: documentType
        }

        const { data: vector, error: vectorError } = await supabaseClient
          .from('document_vectors')
          .insert({
            document_id: documentId,
            chunk_index: i,
            content_embedding: embeddingsList[i],
            chunk_text: chunks[i],
            chunk_metadata: chunkMetadata,
            document_source_type: documentType,
            is_active: true
          })
          .select('id')
          .single()

        if (vectorError) {
          throw new Error(`Failed to store vector ${i}: ${vectorError.message}`)
        }

        vectorIds.push(vector.id)
        console.log(`Stored vector ${i} with ID ${vector.id}`)

      } catch (error) {
        console.error(`Failed to store vector ${i}:`, error)
        continue
      }
    }

    // Update document with vector processing metadata
    await supabaseClient
      .from('documents')
      .update({
        metadata: {
          ...document.metadata,
          vector_processing_complete: true,
          vector_count: vectorIds.length,
          vector_processing_timestamp: new Date().toISOString()
        },
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)

    return new Response(
      JSON.stringify({
        success: true,
        documentId,
        chunksProcessed: vectorIds.length
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Vector processing failed:', error)

    // Update document status to failed
    if (error.documentId) {
      try {
        const supabaseClient = createClient(
          Deno.env.get('SUPABASE_URL') ?? '',
          Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
        )

        await supabaseClient
          .from('documents')
          .update({
            metadata: {
              error_message: error.message,
              error_timestamp: new Date().toISOString()
            },
            updated_at: new Date().toISOString()
          })
          .eq('id', error.documentId)
      } catch (updateError) {
        console.error('Failed to update document metadata:', updateError)
      }
    }

    return new Response(
      JSON.stringify({
        success: false,
        error: error.message
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}) 