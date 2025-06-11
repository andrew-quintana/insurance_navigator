import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface LinkRequest {
  documentId: string;
  storagePath: string;
}

Deno.serve(async (req) => {
  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const { documentId, storagePath }: LinkRequest = await req.json()

    // Update document with storage path and set status to processing
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
      console.error('Error updating document:', updateError)
      return new Response(
        JSON.stringify({ error: 'Failed to update document status' }),
        { status: 400 }
      )
    }

    // Trigger parsing workflow
    const { error: invokeError } = await supabase.functions.invoke('doc-parser', {
      body: { documentId }
    })

    if (invokeError) {
      console.error('Error invoking doc-parser:', invokeError)
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
        { status: 400 }
      )
    }

    return new Response(JSON.stringify({ 
      success: true,
      message: 'Document processing started'
    }))
  } catch (error) {
    console.error('link-assigner error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500 }
    )
  }
}) 