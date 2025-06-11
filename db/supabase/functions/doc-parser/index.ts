import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface ParseRequest {
  documentId: string;
}

Deno.serve(async (req) => {
  console.log('🚀 doc-parser invoked')
  
  try {
    console.log('🔧 Initializing Supabase client...')
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    console.log('📥 Parsing request body...')
    const { documentId }: ParseRequest = await req.json()
    console.log('📋 Document ID:', documentId)

    // Get document record
    console.log('📄 Fetching document record...')
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .single()

    if (docError || !document) {
      console.error('❌ Error fetching document:', docError)
      return new Response(
        JSON.stringify({ error: 'Document not found' }),
        { status: 404 }
      )
    }

    console.log('✅ Document found:', document.original_filename)

    // Update status to parsing
    console.log('📝 Updating status to parsing...')
    await supabase
      .from('documents')
      .update({
        status: 'parsing',
        progress_percentage: 20
      })
      .eq('id', documentId)

    // Download file from storage
    console.log('⬇️ Downloading file from storage...')
    const { data: fileData, error: downloadError } = await supabase.storage
      .from('documents')
      .download(document.storage_path)

    if (downloadError) {
      console.error('❌ Error downloading file:', downloadError)
      await updateDocumentError(supabase, documentId, 'Failed to download file from storage')
      return new Response(
        JSON.stringify({ error: 'Failed to download file' }),
        { status: 400 }
      )
    }

    console.log('✅ File downloaded successfully')

    let extractedText = ''
    
    try {
      if (document.content_type === 'application/pdf') {
        // Check LlamaParse API key
        const llamaApiKey = Deno.env.get('LLAMAPARSE_API_KEY')
        console.log('🔑 LlamaParse API Key check:', {
          hasKey: !!llamaApiKey,
          keyLength: llamaApiKey?.length || 0
        })

        if (!llamaApiKey) {
          console.log('⚠️ LlamaParse API key missing, using fallback text extraction')
          // Fallback: Extract basic text from PDF bytes
          const arrayBuffer = await fileData.arrayBuffer()
          const text = new TextDecoder().decode(arrayBuffer)
          extractedText = text.replace(/[^\x20-\x7E\n\r\t]/g, ' ').trim()
          console.log('✅ Fallback extraction completed, length:', extractedText.length)
        } else {
          console.log('🦙 Using LlamaParse for PDF extraction...')
          // Convert to base64 for LlamaParse
          const arrayBuffer = await fileData.arrayBuffer()
          const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)))

          // Update progress
          await supabase
            .from('documents')
            .update({ progress_percentage: 40 })
            .eq('id', documentId)

          try {
            console.log('🌐 Making request to LlamaParse API...')
            const llamaResponse = await fetch('https://api.llamaparse.com/v1/parse', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${llamaApiKey}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                file: base64,
                parsing_instruction: 'Extract all text content while preserving structure. Focus on Medicare policy documents, insurance terms, coverage details, and any important policy information.'
              })
            })

            if (!llamaResponse.ok) {
              const errorText = await llamaResponse.text()
              console.error(`❌ LlamaParse error: ${llamaResponse.status} - ${errorText}`)
              throw new Error(`LlamaParse API error: ${llamaResponse.status}`)
            }

            const result = await llamaResponse.json()
            extractedText = result.text || ''
            console.log('✅ LlamaParse extraction completed, length:', extractedText.length)
          } catch (llamaError) {
            console.log(`⚠️ LlamaParse failed: ${llamaError.message}`)
            console.log('🔄 Falling back to basic text extraction...')
            
            // Graceful fallback to basic text extraction
            const text = new TextDecoder().decode(arrayBuffer)
            extractedText = text.replace(/[^\x20-\x7E\n\r\t]/g, ' ').trim()
            console.log('✅ Fallback extraction completed, length:', extractedText.length)
          }
        }
      } else if (document.content_type === 'text/plain') {
        // Handle text files directly
        console.log('📝 Extracting text from plain text file...')
        extractedText = await fileData.text()
      } else {
        // For other document types, try to extract as text
        console.log('📄 Extracting text from other document type...')
        extractedText = await fileData.text()
      }

      console.log('📊 Final extracted text length:', extractedText.length)

      // Update document with extracted text metadata
      console.log('💾 Updating document with extraction results...')
      await supabase
        .from('documents')
        .update({
          extracted_text_length: extractedText.length,
          status: 'chunking',
          progress_percentage: 60
        })
        .eq('id', documentId)

      // Trigger vector processing
      console.log('🔗 Invoking vector-processor...')
      const { error: vectorError } = await supabase.functions.invoke('vector-processor', {
        body: { documentId, extractedText }
      })

      if (vectorError) {
        console.error('❌ Error invoking vector-processor:', vectorError)
        await updateDocumentError(supabase, documentId, 'Failed to start vector processing')
        return new Response(
          JSON.stringify({ error: 'Failed to start vector processing' }),
          { status: 400 }
        )
      }

      console.log('✅ doc-parser completed successfully')
      return new Response(JSON.stringify({ 
        success: true, 
        textLength: extractedText.length,
        documentId: documentId,
        usedLlamaParse: !!Deno.env.get('LLAMAPARSE_API_KEY')
      }))
    } catch (parseError) {
      console.error('❌ Text extraction error:', parseError)
      await updateDocumentError(supabase, documentId, `Text extraction failed: ${parseError.message}`)
      return new Response(
        JSON.stringify({ error: 'Text extraction failed' }),
        { status: 400 }
      )
    }
  } catch (error) {
    console.error('❌ doc-parser error:', error)
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