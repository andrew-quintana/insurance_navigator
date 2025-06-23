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
            console.log('🌐 Making request to LlamaCloud API...')
            console.log('🔍 LlamaCloud request details:', {
              url: 'https://api.cloud.llamaindex.ai/api/v1/parsing/upload',
              method: 'POST',
              hasAuth: !!llamaApiKey,
              keyPrefix: llamaApiKey?.substring(0, 10) + '...',
              fileSize: arrayBuffer.byteLength
            })

            // Step 1: Upload file to LlamaCloud
            const formData = new FormData()
            const blob = new Blob([arrayBuffer], { type: 'application/pdf' })
            formData.append('file', blob, document.original_filename)
            
            console.log('📤 Uploading file to LlamaCloud...')
            const uploadResponse = await fetch('https://api.cloud.llamaindex.ai/api/v1/parsing/upload', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${llamaApiKey}`,
                // Don't set Content-Type for FormData, let browser set it with boundary
              },
              body: formData
            })

            console.log('📡 LlamaCloud upload response:', {
              status: uploadResponse.status,
              statusText: uploadResponse.statusText,
              ok: uploadResponse.ok
            })

            if (!uploadResponse.ok) {
              const errorText = await uploadResponse.text()
              console.error(`❌ LlamaCloud upload error:`, {
                status: uploadResponse.status,
                statusText: uploadResponse.statusText,
                errorBody: errorText
              })
              throw new Error(`LlamaCloud upload error: ${uploadResponse.status} - ${errorText}`)
            }

            const uploadResult = await uploadResponse.json()
            const jobId = uploadResult.id
            console.log('✅ File uploaded to LlamaCloud, job ID:', jobId)

            // Step 2: Poll for job completion
            console.log('⏳ Polling for job completion...')
            let jobComplete = false
            let attempts = 0
            const maxAttempts = 30 // 5 minutes max wait
            
            while (!jobComplete && attempts < maxAttempts) {
              await new Promise(resolve => setTimeout(resolve, 10000)) // Wait 10 seconds
              attempts++
              
              const statusResponse = await fetch(`https://api.cloud.llamaindex.ai/api/v1/parsing/job/${jobId}`, {
                headers: {
                  'Authorization': `Bearer ${llamaApiKey}`,
                  'Accept': 'application/json'
                }
              })

              if (statusResponse.ok) {
                const status = await statusResponse.json()
                console.log(`🔄 Job status check ${attempts}:`, status.status)
                
                if (status.status === 'SUCCESS') {
                  jobComplete = true
                } else if (status.status === 'ERROR') {
                  throw new Error(`LlamaCloud job failed: ${status.error || 'Unknown error'}`)
                }
              } else {
                console.log(`⚠️ Status check failed, attempt ${attempts}/${maxAttempts}`)
              }
            }

            if (!jobComplete) {
              throw new Error('LlamaCloud job timeout - job did not complete within 5 minutes')
            }

            // Step 3: Get results
            console.log('📥 Fetching parsed results...')
            const resultResponse = await fetch(`https://api.cloud.llamaindex.ai/api/v1/parsing/job/${jobId}/result/markdown`, {
              headers: {
                'Authorization': `Bearer ${llamaApiKey}`,
                'Accept': 'application/json'
              }
            })

            if (!resultResponse.ok) {
              const errorText = await resultResponse.text()
              console.error(`❌ LlamaCloud result error:`, {
                status: resultResponse.status,
                errorBody: errorText
              })
              throw new Error(`LlamaCloud result error: ${resultResponse.status} - ${errorText}`)
            }

            const result = await resultResponse.json()
            extractedText = result.markdown || result.text || ''
            console.log('✅ LlamaCloud extraction completed:', {
              textLength: extractedText.length,
              hasText: !!extractedText
            })
          } catch (llamaError) {
            console.error('❌ LlamaParse error:', llamaError)
            // Fallback to basic text extraction
            const arrayBuffer = await fileData.arrayBuffer()
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

      if (!extractedText || extractedText.length < 10) {
        console.error('❌ No text extracted from document')
        await updateDocumentError(supabase, documentId, 'No text content found in document')
        return new Response(
          JSON.stringify({ error: 'No text content found' }),
          { status: 400 }
        )
      }

      // Update progress
      console.log('📝 Updating document status to vectorizing...')
      await supabase
        .from('documents')
        .update({
          status: 'vectorizing',
          progress_percentage: 60,
          metadata: {
            ...document.metadata,
            text_length: extractedText.length,
            extraction_completed_at: new Date().toISOString()
          }
        })
        .eq('id', documentId)

      // ✅ CRITICAL FIX: Trigger vector-processor automatically
      console.log('🚀 Triggering vector-processor for document:', documentId)
      try {
        const { data: vectorResult, error: vectorError } = await supabase.functions.invoke('vector-processor', {
          body: { 
            documentId: documentId,
            extractedText: extractedText
          }
        })

        if (vectorError) {
          console.error('❌ vector-processor invocation failed:', vectorError)
          throw new Error(`vector-processor failed: ${vectorError.message}`)
        }

        console.log('✅ vector-processor invoked successfully for document:', documentId)
        
        return new Response(
          JSON.stringify({ 
            success: true,
            message: 'Document parsed and vectorization started',
            documentId: documentId,
            textLength: extractedText.length,
            nextStage: 'vectorizing'
          }),
          { status: 200 }
        )

      } catch (vectorError) {
        console.error(`❌ Vector processing failed for ${documentId}:`, vectorError)
        
        await supabase
          .from('documents')
          .update({
            status: 'failed',
            error_message: `Vector processing failed: ${vectorError.message}`,
            updated_at: new Date().toISOString()
          })
          .eq('id', documentId)

        return new Response(
          JSON.stringify({ 
            error: 'Vector processing failed',
            details: vectorError.message
          }),
          { status: 500 }
        )
      }

    } catch (extractionError) {
      console.error('❌ Text extraction failed:', extractionError)
      await updateDocumentError(supabase, documentId, `Text extraction failed: ${extractionError.message}`)
      return new Response(
        JSON.stringify({ error: 'Text extraction failed' }),
        { status: 400 }
      )
    }
  } catch (error) {
    console.error('❌ doc-parser error:', error)
    await updateDocumentError(supabase, documentId, `Parsing failed: ${error.message}`)
    return new Response(
      JSON.stringify({ 
        error: 'Document parsing failed',
        details: error.message
      }),
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
      progress_percentage: 0,
      updated_at: new Date().toISOString()
    })
    .eq('id', documentId)
} 