import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.21.0'
import { corsHeaders } from '../_shared/cors.ts'

console.log('📄 Doc parser starting...')

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  // Health check
  if (req.method === 'GET') {
    return new Response(
      JSON.stringify({ 
        service: 'doc-parser',
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  try {
    console.log('📄 Processing request...')

    // Parse request body
    const { documentId, storagePath } = await req.json()
    console.log(`📄 Processing document ${documentId} from ${storagePath}`)

    // Initialize Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Download file from storage
    console.log(`📥 Downloading file from storage: ${storagePath}`)
    const { data: fileData, error: downloadError } = await supabaseClient.storage
      .from('raw_documents')
      .download(storagePath)
    
    if (downloadError) {
      console.error('❌ File download error:', downloadError)
      throw new Error(`Failed to download file: ${downloadError.message}`)
    }

    if (!fileData) {
      throw new Error('No file data received from storage')
    }

    console.log(`📄 File downloaded, size: ${fileData.size} bytes`)

    // Convert blob to array buffer for FormData
    const arrayBuffer = await fileData.arrayBuffer()

    // Call LlamaParse API
    console.log('🦙 Calling LlamaParse API...')
    const formData = new FormData()
    formData.append('file', new Blob([arrayBuffer], { type: 'application/pdf' }), 'document.pdf')

    const parseResponse = await fetch('https://api.cloud.llamaindex.ai/api/parsing/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('LLAMACLOUD_API_KEY')}`
      },
      body: formData
    })

    if (!parseResponse.ok) {
      const errorText = await parseResponse.text()
      throw new Error(`LlamaParse API error: ${parseResponse.status} - ${errorText}`)
    }

    const parseResult = await parseResponse.json()
    console.log(`📋 LlamaParse job created: ${parseResult.id}`)

    // Poll for results
    let attempts = 0
    const maxAttempts = 30 // 30 attempts with 2-second intervals = 1 minute max
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 2000)) // Wait 2 seconds
      attempts++
      
      const statusResponse = await fetch(`https://api.cloud.llamaindex.ai/api/parsing/job/${parseResult.id}`, {
        headers: {
          'Authorization': `Bearer ${Deno.env.get('LLAMACLOUD_API_KEY')}`
        }
      })

      if (!statusResponse.ok) {
        console.error(`Status check failed: ${statusResponse.status}`)
        continue
      }

      const statusResult = await statusResponse.json()
      console.log(`🔄 Parse status: ${statusResult.status} (attempt ${attempts}/${maxAttempts})`)

      if (statusResult.status === 'SUCCESS') {
        const resultResponse = await fetch(`https://api.cloud.llamaindex.ai/api/parsing/job/${parseResult.id}/result/markdown`, {
          headers: {
            'Authorization': `Bearer ${Deno.env.get('LLAMACLOUD_API_KEY')}`
          }
        })

        if (resultResponse.ok) {
          const extractedText = await resultResponse.text()
          console.log(`✅ Text extraction completed, length: ${extractedText.length} characters`)
          
          return new Response(
            JSON.stringify({ 
              success: true,
              extractedText,
              metadata: {
                documentId,
                storagePath,
                textLength: extractedText.length,
                extractionMethod: 'llamaparse',
                jobId: parseResult.id
              }
            }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          )
        } else {
          throw new Error(`Failed to get parse results: ${resultResponse.status}`)
        }
      } else if (statusResult.status === 'ERROR') {
        throw new Error(`LlamaParse job failed: ${statusResult.error || 'Unknown error'}`)
      }
      
      // Continue polling for PENDING status
    }

    throw new Error('LlamaParse job timed out after 1 minute')

  } catch (error) {
    console.error('❌ Document parsing failed:', error)
    return new Response(
      JSON.stringify({ 
        success: false,
        error: error.message,
        details: error.stack
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}) 