/**
 * Document Parser Edge Function
 * 
 * This function handles document parsing using LlamaParse:
 * 1. Downloads document from storage
 * 2. Parses document content
 * 3. Stores parsed content
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// Configuration
const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? ''
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
const LLAMAPARSE_API_KEY = Deno.env.get('LLAMAPARSE_API_KEY') ?? ''
const LLAMAPARSE_BASE_URL = Deno.env.get('LLAMAPARSE_BASE_URL') ?? 'https://api.cloud.llamaindex.ai'

// Initialize Supabase client
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

interface ParseRequest {
  documentId: string
  storagePath: string
}

async function downloadDocument(storagePath: string): Promise<Uint8Array> {
  const { data, error } = await supabase.storage
    .from('documents')
    .download(storagePath)

  if (error) throw error
  return new Uint8Array(await data.arrayBuffer())
}

async function parseDocument(documentData: Uint8Array): Promise<any> {
  const formData = new FormData()
  formData.append('file', new Blob([documentData], { type: 'application/pdf' }))

  const response = await fetch(`${LLAMAPARSE_BASE_URL}/parse`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${LLAMAPARSE_API_KEY}`
    },
    body: formData
  })

  if (!response.ok) {
    throw new Error(`LlamaParse API error: ${await response.text()}`)
  }

  return response.json()
}

async function storeParseResult(documentId: string, parseResult: any) {
  const { error } = await supabase
    .from('document_content')
    .insert({
      document_id: documentId,
      content: parseResult,
      parsed_at: new Date().toISOString()
    })

  if (error) throw error
}

async function handleParseRequest(req: Request) {
  try {
    const { documentId, storagePath } = await req.json() as ParseRequest

    // Download document
    const documentData = await downloadDocument(storagePath)

    // Parse document
    const parseResult = await parseDocument(documentData)

    // Store parse result
    await storeParseResult(documentId, parseResult)

    return new Response(JSON.stringify({ 
      status: 'success',
      documentId,
      message: 'Document parsed successfully'
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

  return handleParseRequest(req)
}) 