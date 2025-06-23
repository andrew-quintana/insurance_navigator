import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface ParseRequest {
  documentId: string;
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization'
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    console.log('🔍 Doc-parser started - method:', req.method)
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    // ✅ REFACTORED: Simplified authentication - expects payload with document info
    const { documentId, path, filename, contentType, fileSize } = await req.json()
    
    if (!documentId || !path) {
      return new Response(JSON.stringify({ 
        error: 'Document ID and storage path are required' 
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log('📄 Processing document:', { documentId, path, filename, contentType })

    // Get document record from database 
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .single()

    if (docError || !document) {
      console.error('❌ Document not found:', docError)
      return new Response(JSON.stringify({ 
        error: 'Document not found' 
      }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    // Update status to parsing
    await supabase
      .from('documents')
      .update({
        status: 'parsing',
        progress_percentage: 30,
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)

    console.log('📁 Downloading file from storage:', path)
    
    // Download file from Supabase Storage
    const { data: fileData, error: downloadError } = await supabase.storage
      .from('documents')
      .download(path)

    if (downloadError || !fileData) {
      console.error('❌ Failed to download file:', downloadError)
      await supabase
        .from('documents')
        .update({
          status: 'failed',
          error_message: `Failed to download file: ${downloadError?.message || 'Unknown error'}`,
          updated_at: new Date().toISOString()
        })
        .eq('id', documentId)
      
      return new Response(JSON.stringify({ 
        error: 'Failed to download file from storage',
        details: downloadError?.message 
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    let extractedText = ''
    
    // Check if we should use LlamaParse for PDFs
    if (contentType === 'application/pdf') {
      console.log('🦙 Using LlamaParse for PDF processing...')
      
      // Update status to indicate LlamaParse processing
      await supabase
        .from('documents')
        .update({
          status: 'parsing',
          progress_percentage: 40,
          metadata: {
            processing_method: 'llamaparse',
            parsing_started_at: new Date().toISOString()
          }
        })
        .eq('id', documentId)

      try {
        const llamaCloudKey = Deno.env.get('LLAMA_CLOUD_API_KEY')
        
        if (!llamaCloudKey) {
          throw new Error('LlamaCloud API key not configured')
        }

        // Prepare file for LlamaCloud upload
        const formData = new FormData()
        formData.append('file', fileData, filename)

        const uploadResponse = await fetch('https://api.cloud.llamaindex.ai/api/parsing/upload', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${llamaCloudKey}`,
          },
          body: formData
        })

        if (!uploadResponse.ok) {
          throw new Error(`LlamaCloud upload failed: ${uploadResponse.status}`)
        }

        const uploadResult = await uploadResponse.json()
        const jobId = uploadResult.id

        console.log('📤 File uploaded to LlamaCloud, job ID:', jobId)

        // Poll for completion with timeout
        let attempts = 0
        const maxAttempts = 60 // Wait up to 5 minutes
        
        while (attempts < maxAttempts) {
          const statusResponse = await fetch(`https://api.cloud.llamaindex.ai/api/parsing/job/${jobId}`, {
            headers: {
              'Authorization': `Bearer ${llamaCloudKey}`,
            }
          })

          if (!statusResponse.ok) {
            throw new Error(`Status check failed: ${statusResponse.status}`)
          }

          const statusResult = await statusResponse.json()
          console.log(`🔄 LlamaCloud status (attempt ${attempts + 1}):`, statusResult.status)

          if (statusResult.status === 'SUCCESS') {
            // Get the result
            const resultResponse = await fetch(`https://api.cloud.llamaindex.ai/api/parsing/job/${jobId}/result/markdown`, {
              headers: {
                'Authorization': `Bearer ${llamaCloudKey}`,
              }
            })

            if (!resultResponse.ok) {
              throw new Error(`Result fetch failed: ${resultResponse.status}`)
            }

            const result = await resultResponse.json()
            extractedText = result.markdown || result.text || ''
            console.log('✅ LlamaCloud extraction completed:', {
              textLength: extractedText.length,
              hasText: !!extractedText
            })
            break
          } else if (statusResult.status === 'ERROR') {
            throw new Error(`LlamaCloud processing failed: ${statusResult.error || 'Unknown error'}`)
          }

          attempts++
          await new Promise(resolve => setTimeout(resolve, 5000)) // Wait 5 seconds
        }

        if (attempts >= maxAttempts) {
          throw new Error('LlamaCloud processing timeout')
        }

      } catch (llamaError) {
        console.error('❌ LlamaParse error:', llamaError)
        // Fallback to basic text extraction
        const arrayBuffer = await fileData.arrayBuffer()
        const text = new TextDecoder().decode(arrayBuffer)
        extractedText = text.replace(/[^\x20-\x7E\n\r\t]/g, ' ').trim()
        console.log('✅ Fallback extraction completed, length:', extractedText.length)
      }
    } else {
      // Direct text processing for non-PDF files
      console.log('📝 Using direct text processing...')
      const arrayBuffer = await fileData.arrayBuffer()
      extractedText = new TextDecoder().decode(arrayBuffer)
      console.log('✅ Direct text extraction completed, length:', extractedText.length)
    }

    if (!extractedText || extractedText.length === 0) {
      console.error('❌ No text extracted from document')
      await supabase
        .from('documents')
        .update({
          status: 'failed',
          error_message: 'No text could be extracted from the document',
          updated_at: new Date().toISOString()
        })
        .eq('id', documentId)
      
      return new Response(JSON.stringify({ 
        error: 'No text extracted',
        message: 'Document processing completed but no text was extracted'
      }), {
        status: 422,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    // Update document with extracted text
    await supabase
      .from('documents')
      .update({
        status: 'vectorizing',
        progress_percentage: 60,
        extracted_text: extractedText,
        text_extracted_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)

    console.log('✅ Text extraction completed, triggering vector processing...')

    // ✅ AUTOMATIC PIPELINE: Trigger vector processor
    console.log('🚀 Triggering vector-processor for document:', documentId)
    const { data: vectorResult, error: vectorError } = await supabase.functions.invoke('vector-processor', {
      body: { documentId: documentId }
    })

    if (vectorError) {
      console.error('❌ Vector processor invocation failed:', vectorError)
      await supabase
        .from('documents')
        .update({
          status: 'failed',
          error_message: `Vector processing failed: ${vectorError.message}`,
          updated_at: new Date().toISOString()
        })
        .eq('id', documentId)
      
      return new Response(JSON.stringify({ 
        error: 'Vector processing failed',
        details: vectorError.message,
        textLength: extractedText.length
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log('✅ Vector processor triggered successfully')

    return new Response(JSON.stringify({
      success: true,
      documentId: documentId,
      textLength: extractedText.length,
      status: 'vectorizing',
      message: 'Document parsing completed, vectorization in progress'
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('❌ Doc-parser error:', error)
    return new Response(JSON.stringify({ 
      error: 'Document parsing failed',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
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