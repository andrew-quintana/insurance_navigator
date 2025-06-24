import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient, SupabaseClient } from '@supabase/supabase-js'
import { corsHeaders } from '../_shared/cors.ts'

interface TriggerRequest {
  documentId: string
  documentType: 'user_uploaded' | 'regulatory'
  action: 'parse' | 'vectorize' | 'link'
  metadata?: {
    jurisdiction?: string
    programs?: string[]
    tags?: string[]
    [key: string]: any
  }
}

interface TriggerResult {
  success: boolean
  documentId: string
  action: string
  status: string
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

    const { documentId, documentType, action, metadata = {} } = await req.json() as TriggerRequest

    if (!documentId || !action) {
      throw new Error('Missing required parameters: documentId and action')
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

    // Call appropriate processor based on action
    let processorUrl: string
    let processorPayload: any

    switch (action) {
      case 'parse':
        processorUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/doc-parser`
        processorPayload = {
          documentId,
          documentType,
          path: document.storage_path,
          contentType: document.mime_type,
          metadata
        }
        break

      case 'vectorize':
        processorUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/vector-processor`
        processorPayload = {
          documentId,
          documentType,
          extractedText: document.metadata?.extracted_text,
          metadata
        }
        break

      case 'link':
        processorUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/link-assigner`
        processorPayload = {
          documentId,
          documentType,
          metadata
        }
        break

      default:
        throw new Error(`Invalid action: ${action}`)
    }

    // Call processor
    const processorResponse = await fetch(processorUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`
      },
      body: JSON.stringify(processorPayload)
    })

    if (!processorResponse.ok) {
      const errorText = await processorResponse.text()
      throw new Error(`Processor failed: ${errorText}`)
    }

    const processorResult = await processorResponse.json()

    // Update document with processing result
    await supabaseClient
      .from('documents')
      .update({
        metadata: {
          ...document.metadata,
          [`${action}_complete`]: true,
          [`${action}_timestamp`]: new Date().toISOString(),
          [`${action}_result`]: processorResult
        },
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)

    return new Response(
      JSON.stringify({
        success: true,
        documentId,
        action,
        status: 'completed',
        result: processorResult
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Processing trigger failed:', error)

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