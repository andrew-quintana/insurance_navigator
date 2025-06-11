import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface ParseRequest {
  documentId: string;
}

Deno.serve(async (req) => {
  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const { documentId }: ParseRequest = await req.json()

    // Get document record
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .single()

    if (docError || !document) {
      console.error('Error fetching document:', docError)
      return new Response(
        JSON.stringify({ error: 'Document not found' }),
        { status: 404 }
      )
    }

    // Update status to parsing
    await supabase
      .from('documents')
      .update({
        status: 'parsing',
        progress_percentage: 20
      })
      .eq('id', documentId)

    // Download file from storage
    const { data: fileData, error: downloadError } = await supabase.storage
      .from('documents')
      .download(document.storage_path)

    if (downloadError) {
      console.error('Error downloading file:', downloadError)
      await updateDocumentError(supabase, documentId, 'Failed to download file from storage')
      return new Response(
        JSON.stringify({ error: 'Failed to download file' }),
        { status: 400 }
      )
    }

    let extractedText = ''
    
    try {
      if (document.content_type === 'application/pdf') {
        // Convert to base64 for LlamaParse
        const arrayBuffer = await fileData.arrayBuffer()
        const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)))

        // Update progress
        await supabase
          .from('documents')
          .update({ progress_percentage: 40 })
          .eq('id', documentId)

        const llamaResponse = await fetch('https://api.llamaparse.com/v1/parse', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${Deno.env.get('LLAMAPARSE_API_KEY')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            file: base64,
            parsing_instruction: 'Extract all text content while preserving structure. Focus on Medicare policy documents, insurance terms, coverage details, and any important policy information.'
          })
        })

        if (!llamaResponse.ok) {
          const errorText = await llamaResponse.text()
          console.error(`LlamaParse error: ${llamaResponse.status} - ${errorText}`)
          throw new Error(`LlamaParse API error: ${llamaResponse.status}`)
        }

        const result = await llamaResponse.json()
        extractedText = result.text || ''
      } else if (document.content_type === 'text/plain') {
        // Handle text files directly
        extractedText = await fileData.text()
      } else {
        // For other document types, try to extract as text
        extractedText = await fileData.text()
      }

      // Update document with extracted text metadata
      await supabase
        .from('documents')
        .update({
          extracted_text_length: extractedText.length,
          status: 'chunking',
          progress_percentage: 60
        })
        .eq('id', documentId)

      // Trigger vector processing
      const { error: vectorError } = await supabase.functions.invoke('vector-processor', {
        body: { documentId, extractedText }
      })

      if (vectorError) {
        console.error('Error invoking vector-processor:', vectorError)
        await updateDocumentError(supabase, documentId, 'Failed to start vector processing')
        return new Response(
          JSON.stringify({ error: 'Failed to start vector processing' }),
          { status: 400 }
        )
      }

      return new Response(JSON.stringify({ 
        success: true, 
        textLength: extractedText.length,
        documentId: documentId
      }))
    } catch (parseError) {
      console.error('Text extraction error:', parseError)
      await updateDocumentError(supabase, documentId, `Text extraction failed: ${parseError.message}`)
      return new Response(
        JSON.stringify({ error: 'Text extraction failed' }),
        { status: 400 }
      )
    }
  } catch (error) {
    console.error('doc-parser error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500 }
    )
  }
})

async function updateDocumentError(supabase: any, documentId: string, errorMessage: string) {
  await supabase
    .from('documents')
    .update({ 
      status: 'failed',
      error_message: errorMessage,
      processing_completed_at: new Date().toISOString()
    })
    .eq('id', documentId)
} 