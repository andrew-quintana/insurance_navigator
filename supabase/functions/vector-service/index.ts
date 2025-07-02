/**
 * Vector Service Edge Function
 * 
 * This function handles document vectorization:
 * 1. Retrieves document chunks
 * 2. Creates embeddings using OpenAI
 * 3. Stores vectors in the database
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { OpenAIEmbeddings } from '../_shared/embeddings.ts'

// Configuration
const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? ''
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
const OPENAI_API_KEY = Deno.env.get('OPENAI_API_KEY') ?? ''

// Initialize clients
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
const embeddings = new OpenAIEmbeddings(OPENAI_API_KEY)

interface VectorRequest {
  documentId: string
}

interface DocumentChunk {
  id: string
  document_id: string
  content: string
  page_number?: number
  chunk_number: number
}

async function getDocumentChunks(documentId: string): Promise<DocumentChunk[]> {
  const { data, error } = await supabase
    .from('document_chunks')
    .select('*')
    .eq('document_id', documentId)
    .order('chunk_number', { ascending: true })

  if (error) throw error
  return data
}

async function createEmbeddings(chunks: DocumentChunk[]): Promise<number[][]> {
  const texts = chunks.map(chunk => chunk.content)
  return await embeddings.embedDocuments(texts)
}

async function storeVectors(chunks: DocumentChunk[], vectors: number[][]) {
  const vectorData = chunks.map((chunk, index) => ({
    document_id: chunk.document_id,
    chunk_id: chunk.id,
    vector: vectors[index],
    created_at: new Date().toISOString()
  }))

  const { error } = await supabase
    .from('document_vectors')
    .insert(vectorData)

  if (error) throw error
}

async function handleVectorRequest(req: Request) {
  try {
    const { documentId } = await req.json() as VectorRequest

    // Get document chunks
    const chunks = await getDocumentChunks(documentId)

    if (chunks.length === 0) {
      throw new Error('No chunks found for document')
    }

    // Create embeddings
    const vectors = await createEmbeddings(chunks)

    // Store vectors
    await storeVectors(chunks, vectors)

    return new Response(JSON.stringify({
      status: 'success',
      documentId,
      vectorCount: vectors.length,
      message: 'Document vectors created successfully'
    }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { 'Content-Type': 'application/json' },
      status: 500
    })
  }
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
      }
    })
  }

  return handleVectorRequest(req)
}) 