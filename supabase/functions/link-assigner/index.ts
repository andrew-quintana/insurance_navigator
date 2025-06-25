import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient, SupabaseClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

interface LinkRequest {
  documentId: string
  documentType: 'user_uploaded' | 'regulatory'
  metadata?: {
    jurisdiction?: string
    programs?: string[]
    tags?: string[]
    [key: string]: any
  }
}

interface LinkResult {
  success: boolean
  documentId: string
  linkedDocuments: Array<{
    id: string
    title: string
    similarity: number
    documentType: string
  }>
  error?: string
}

serve(async (req: Request) => {
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
        service: 'link-assigner',
        timestamp: new Date().toISOString()
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  try {
    const supabaseClient: SupabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const { documentId, documentType, metadata = {} } = await req.json() as LinkRequest

    if (!documentId) {
      throw new Error('Missing required parameter: documentId')
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

    // Get document vectors
    const { data: vectors, error: vectorError } = await supabaseClient
      .from('document_vectors')
      .select('content_embedding')
      .eq('document_id', documentId)
      .eq('is_active', true)

    if (vectorError || !vectors || vectors.length === 0) {
      throw new Error('No vectors found for document')
    }

    // Calculate average embedding for the document
    const avgEmbedding = vectors.reduce((acc, vec) => {
      const embedding = vec.content_embedding
      return acc.map((val: number, i: number) => val + embedding[i] / vectors.length)
    }, new Array(1536).fill(0))

    // Find similar documents using vector similarity
    const { data: similarDocs, error: similarError } = await supabaseClient.rpc(
      'match_documents',
      {
        query_embedding: avgEmbedding,
        match_threshold: 0.7,
        match_count: 5,
        min_content_length: 100
      }
    )

    if (similarError) {
      throw new Error(`Failed to find similar documents: ${similarError.message}`)
    }

    // Filter out the query document itself
    const linkedDocuments = similarDocs
      .filter((doc: any) => doc.id !== documentId)
      .map((doc: any) => ({
        id: doc.id,
        title: doc.original_filename,
        similarity: doc.similarity,
        documentType: doc.document_type
      }))

    // Update document with linked documents
    await supabaseClient
      .from('documents')
      .update({
        metadata: {
          ...document.metadata,
          linked_documents: linkedDocuments.map(doc => doc.id),
          linking_timestamp: new Date().toISOString()
        },
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)

    return new Response(
      JSON.stringify({
        success: true,
        documentId,
        linkedDocuments
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Document linking failed:', error)

    // Update document metadata with error
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