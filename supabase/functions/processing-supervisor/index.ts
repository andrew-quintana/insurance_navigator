/**
 * Processing Supervisor Edge Function
 * 
 * This function coordinates the document processing pipeline:
 * 1. Monitors document status
 * 2. Triggers document parsing
 * 3. Manages chunking and vectorization
 * 4. Updates processing status
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { edgeConfig } from "../_shared/environment";

// Initialize Supabase client
const supabase = createClient(edgeConfig.supabaseUrl, edgeConfig.supabaseKey)

// Processing states
const ProcessingState = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  PARSED: 'parsed',
  CHUNKED: 'chunked',
  VECTORIZED: 'vectorized',
  COMPLETED: 'completed',
  ERROR: 'error'
}

interface Document {
  id: string
  user_id: string
  filename: string
  content_type: string
  status: string
  storage_path: string
  error_message?: string
}

async function handleProcessingRequest(req: Request) {
  try {
    // Get documents that need processing
    const { data: documents, error } = await supabase
      .from('documents')
      .select('*')
      .eq('status', ProcessingState.PENDING)
      .limit(10)

    if (error) throw error
    if (!documents || documents.length === 0) {
      return new Response(JSON.stringify({ message: 'No documents to process' }), {
        headers: { 'Content-Type': 'application/json' },
        status: 200
      })
    }

    // Process each document
    const results = await Promise.all(
      documents.map(async (doc: Document) => {
        try {
          // Update status to processing
          await supabase
            .from('documents')
            .update({ status: ProcessingState.PROCESSING })
            .eq('id', doc.id)

          // Call document parser
          const parserResponse = await fetch(
            `${edgeConfig.supabaseUrl}/functions/v1/doc-parser`,
            {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${edgeConfig.supabaseKey}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                documentId: doc.id,
                storagePath: doc.storage_path
              })
            }
          )

          if (!parserResponse.ok) {
            throw new Error(`Document parsing failed: ${await parserResponse.text()}`)
          }

          // Update status to parsed
          await supabase
            .from('documents')
            .update({ status: ProcessingState.PARSED })
            .eq('id', doc.id)

          // Call chunking service
          const chunkResponse = await fetch(
            `${edgeConfig.supabaseUrl}/functions/v1/chunking-service`,
            {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${edgeConfig.supabaseKey}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                documentId: doc.id
              })
            }
          )

          if (!chunkResponse.ok) {
            throw new Error(`Document chunking failed: ${await chunkResponse.text()}`)
          }

          // Update status to chunked
          await supabase
            .from('documents')
            .update({ status: ProcessingState.CHUNKED })
            .eq('id', doc.id)

          // Call vectorization service
          const vectorResponse = await fetch(
            `${edgeConfig.supabaseUrl}/functions/v1/vector-service`,
            {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${edgeConfig.supabaseKey}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                documentId: doc.id
              })
            }
          )

          if (!vectorResponse.ok) {
            throw new Error(`Document vectorization failed: ${await vectorResponse.text()}`)
          }

          // Update status to completed
          await supabase
            .from('documents')
            .update({ status: ProcessingState.COMPLETED })
            .eq('id', doc.id)

          return {
            documentId: doc.id,
            status: 'success'
          }
        } catch (error) {
          // Update document status to error
          await supabase
            .from('documents')
            .update({
              status: ProcessingState.ERROR,
              error_message: error.message
            })
            .eq('id', doc.id)

          return {
            documentId: doc.id,
            status: 'error',
            error: error.message
          }
        }
      })
    )

    return new Response(JSON.stringify({ results }), {
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

  return handleProcessingRequest(req)
}) 