/**
 * Chunking Service Edge Function
 * 
 * This function handles document chunking:
 * 1. Retrieves parsed document content
 * 2. Chunks content into smaller segments
 * 3. Stores chunks for vectorization
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { edgeConfig } from "../_shared/environment";

// Initialize Supabase client
const supabase = createClient(edgeConfig.supabaseUrl, edgeConfig.supabaseKey)

interface ChunkRequest {
  documentId: string
}

interface Chunk {
  content: string
  metadata: {
    documentId: string
    pageNumber?: number
    chunkNumber: number
  }
}

async function getDocumentContent(documentId: string): Promise<any> {
  const { data, error } = await supabase
    .from('document_content')
    .select('content')
    .eq('document_id', documentId)
    .single()

  if (error) throw error
  return data.content
}

function chunkContent(content: any): Chunk[] {
  const chunks: Chunk[] = []
  let chunkNumber = 0

  // Process each page or section
  if (Array.isArray(content)) {
    content.forEach((section, pageNumber) => {
      // Split content into chunks of roughly 1000 characters
      const text = section.text || section.content || ''
      const words = text.split(/\s+/)
      let currentChunk = ''

      words.forEach((word: string) => {
        if ((currentChunk + ' ' + word).length > 1000) {
          // Store current chunk
          chunks.push({
            content: currentChunk.trim(),
            metadata: {
              documentId: content.documentId,
              pageNumber: pageNumber + 1,
              chunkNumber: ++chunkNumber
            }
          })
          currentChunk = word
        } else {
          currentChunk += (currentChunk ? ' ' : '') + word
        }
      })

      // Store the last chunk if not empty
      if (currentChunk.trim()) {
        chunks.push({
          content: currentChunk.trim(),
          metadata: {
            documentId: content.documentId,
            pageNumber: pageNumber + 1,
            chunkNumber: ++chunkNumber
          }
        })
      }
    })
  } else if (typeof content === 'string') {
    // Handle plain text content
    const words = content.split(/\s+/)
    let currentChunk = ''

    words.forEach((word: string) => {
      if ((currentChunk + ' ' + word).length > 1000) {
        chunks.push({
          content: currentChunk.trim(),
          metadata: {
            documentId: content.documentId,
            chunkNumber: ++chunkNumber
          }
        })
        currentChunk = word
      } else {
        currentChunk += (currentChunk ? ' ' : '') + word
      }
    })

    if (currentChunk.trim()) {
      chunks.push({
        content: currentChunk.trim(),
        metadata: {
          documentId: content.documentId,
          chunkNumber: ++chunkNumber
        }
      })
    }
  }

  return chunks
}

async function storeChunks(chunks: Chunk[]) {
  const { error } = await supabase
    .from('document_chunks')
    .insert(chunks.map(chunk => ({
      document_id: chunk.metadata.documentId,
      content: chunk.content,
      page_number: chunk.metadata.pageNumber,
      chunk_number: chunk.metadata.chunkNumber,
      created_at: new Date().toISOString()
    })))

  if (error) throw error
}

async function handleChunkRequest(req: Request) {
  try {
    const { documentId } = await req.json() as ChunkRequest

    // Get document content
    const content = await getDocumentContent(documentId)

    // Create chunks
    const chunks = chunkContent(content)

    // Store chunks
    await storeChunks(chunks)

    return new Response(JSON.stringify({
      status: 'success',
      documentId,
      chunkCount: chunks.length,
      message: 'Document chunked successfully'
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

  return handleChunkRequest(req)
}) 