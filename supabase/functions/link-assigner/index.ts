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
    url: req.url,
    headers: Object.fromEntries(req.headers.entries())
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

    console.log('📥 Reading request body...')
    
    // Get raw request body text first
    let requestBodyText
    try {
      requestBodyText = await req.text()
      console.log('📋 Raw request body length:', requestBodyText.length)
    } catch (err) {
      console.error('❌ Error reading request body:', err)
      return new Response(
        JSON.stringify({ error: 'Failed to read request body' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }
    
    if (!requestBodyText || requestBodyText.trim() === '') {
      console.error('❌ Empty request body received')
      return new Response(
        JSON.stringify({ error: 'Request body is empty' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }
    
    // Parse JSON
    let parsedBody
    try {
      parsedBody = JSON.parse(requestBodyText)
      console.log('✅ JSON parsed successfully:', parsedBody)
    } catch (parseError) {
      console.error('❌ JSON parsing failed:', parseError)
      return new Response(
        JSON.stringify({ 
          error: 'Invalid JSON format',
          details: parseError.message,
          receivedBody: requestBodyText
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }
    
    const { documentId, storagePath }: LinkRequest = parsedBody
    
    if (!documentId || !storagePath) {
      console.error('❌ Missing required fields:', { documentId, storagePath })
      return new Response(
        JSON.stringify({ 
          error: 'Missing documentId or storagePath',
          received: { documentId, storagePath }
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }
    
    console.log('✅ Request validated:', { documentId, storagePath })

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

    // Create parsing job in queue instead of direct invocation
    console.log('📋 Creating parse job in queue...')
    const { data: jobId, error: jobError } = await supabase
      .rpc('create_processing_job', {
        doc_id: documentId,
        job_type_param: 'parse',
        job_payload: { 
          documentId: documentId,
          storagePath: storagePath 
        },
        priority_param: 5, // High priority for user-initiated uploads
        schedule_delay_seconds: 2 // Small delay to ensure document is ready
      })

    if (jobError) {
      console.error('❌ Error creating parse job:', jobError)
      await supabase
        .from('documents')
        .update({ 
          status: 'failed',
          error_message: 'Failed to queue processing job'
        })
        .eq('id', documentId)
        
      return new Response(
        JSON.stringify({ error: 'Failed to queue processing job' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    console.log('✅ Parse job queued successfully:', jobId)
    return new Response(JSON.stringify({ 
      success: true,
      message: 'Document processing started'
    }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
    
  } catch (error) {
    console.error('❌ link-assigner unexpected error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        details: error.message 
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}) 