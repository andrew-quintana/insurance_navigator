import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface LinkRequest {
  documentId: string;
  storagePath: string;
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
}

Deno.serve(async (req) => {
  console.log('🚀 link-assigner invoked:', { 
    method: req.method, 
    url: req.url 
  })

  if (req.method === 'OPTIONS') {
    console.log('✅ CORS preflight handled')
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    console.log('🔧 Initializing Supabase client with service role...')
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false
        }
      }
    )

    console.log('📥 Parsing request body...')
    const { documentId, storagePath }: LinkRequest = await req.json()
    console.log('✅ Request parsed:', { documentId, storagePath })

    // Update document with storage path and set status to processing
    console.log('📝 Updating document status to processing...')
    const { error: updateError } = await supabase
      .from('documents')
      .update({
        storage_path: storagePath,
        status: 'processing',
        progress_percentage: 10,
        processing_started_at: new Date().toISOString()
      })
      .eq('id', documentId)

    if (updateError) {
      console.error('❌ Error updating document:', updateError)
      return new Response(
        JSON.stringify({ error: 'Failed to update document status' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    console.log('✅ Document status updated to processing')

    // Trigger parsing workflow
    console.log('🔗 Invoking doc-parser function...')
    const { error: invokeError } = await supabase.functions.invoke('doc-parser', {
      body: { documentId }
    })

    if (invokeError) {
      console.error('❌ Error invoking doc-parser:', invokeError)
      // Update document status to failed
      await supabase
        .from('documents')
        .update({ 
          status: 'failed',
          error_message: 'Failed to start processing pipeline'
        })
        .eq('id', documentId)
        
      return new Response(
        JSON.stringify({ error: 'Failed to start processing pipeline' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    console.log('✅ Processing pipeline started successfully')
    return new Response(JSON.stringify({ 
      success: true,
      message: 'Document processing started'
    }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
  } catch (error) {
    console.error('❌ link-assigner error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}) 