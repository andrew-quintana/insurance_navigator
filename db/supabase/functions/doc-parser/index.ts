import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface ParseRequest {
  documentId: string;
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization'
}

// Queue configuration
const QUEUE_CONFIG = {
  maxConcurrentRequests: 2,
  requestIntervalMs: 5000, // 5 seconds between requests
  maxQueueSize: 100
}

// Queue for tracking active requests
let activeRequests = 0
const requestQueue: Array<{
  resolve: (value: any) => void,
  reject: (error: any) => void,
  operation: () => Promise<any>
}> = []

async function queueRequest<T>(operation: () => Promise<T>): Promise<T> {
  if (activeRequests >= QUEUE_CONFIG.maxConcurrentRequests) {
    // If queue is full, reject immediately
    if (requestQueue.length >= QUEUE_CONFIG.maxQueueSize) {
      throw new Error('Request queue is full')
    }
    
    // Add to queue
    return new Promise((resolve, reject) => {
      requestQueue.push({ resolve, reject, operation })
    })
  }
  
  // Execute request
  activeRequests++
  try {
    const result = await operation()
    return result
  } finally {
    activeRequests--
    processQueue()
  }
}

async function processQueue() {
  // If queue is empty or we're at max concurrent requests, do nothing
  if (requestQueue.length === 0 || activeRequests >= QUEUE_CONFIG.maxConcurrentRequests) {
    return
  }
  
  // Process next request
  const { resolve, reject, operation } = requestQueue.shift()!
  activeRequests++
  
  try {
    const result = await operation()
    resolve(result)
  } catch (error) {
    reject(error)
  } finally {
    activeRequests--
    // Add delay before processing next request
    setTimeout(processQueue, QUEUE_CONFIG.requestIntervalMs)
  }
}

// Update the LlamaParse upload to use the queue
async function uploadToLlamaParse(formData: FormData, llamaCloudKey: string): Promise<Response> {
  return queueRequest(async () => {
    return retryWithBackoff(
      () => fetch('https://api.cloud.llamaindex.ai/api/parsing/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${llamaCloudKey}`,
        },
        body: formData
      })
    )
  })
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }
  
  try {
    console.log('🔍 Doc-parser started - method:', req.method)
    
    // Handle GET requests for health checks
    if (req.method === 'GET') {
      return new Response(JSON.stringify({
        status: 'healthy',
        service: 'doc-parser',
        timestamp: new Date().toISOString()
      }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }
    
    // Only handle POST requests for document processing
    if (req.method !== 'POST') {
      return new Response(JSON.stringify({
        error: 'Method not allowed',
        allowed_methods: ['POST', 'GET', 'OPTIONS']
      }), {
        status: 405,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    // ✅ REFACTORED: Simplified authentication - expects payload with document info
    let requestData: any
    try {
      requestData = await req.json()
    } catch (jsonError) {
      console.error('❌ JSON parsing error:', jsonError)
      return new Response(JSON.stringify({ 
        error: 'Invalid JSON payload',
        details: 'Request body must be valid JSON'
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }
    
    const { documentId, path, filename, contentType, fileSize } = requestData
    
    if (!documentId || !path) {
      return new Response(JSON.stringify({ 
        error: 'Document ID and storage path are required' 
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log('📄 Processing document:', { documentId, path, filename, contentType })

    // Get document record from database with improved error handling
    console.log('🔍 Querying for document ID:', documentId)
    const { data: documents, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)

    console.log('📋 Query result:', { documentsFound: documents?.length || 0, error: docError })

    if (docError) {
      console.error('❌ Database query error:', docError)
      return new Response(JSON.stringify({ 
        error: 'Document not found in database',
        details: docError.message || 'Database query failed'
      }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    if (!documents || documents.length === 0) {
      console.error('❌ No document found with ID:', documentId)
      return new Response(JSON.stringify({ 
        error: 'Document not found in database',
        details: 'No document record exists with the provided ID'
      }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    if (documents.length > 1) {
      console.error('❌ Multiple documents found with ID:', documentId, 'Count:', documents.length)
      return new Response(JSON.stringify({ 
        error: 'Document not found in database',
        details: 'Multiple documents found with the same ID'
      }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    const document = documents[0]
    console.log('✅ Document found:', { id: document.id, filename: document.original_filename, status: document.status })

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
      .from('raw_documents')
      .download(path)

    if (downloadError || !fileData) {
      console.error('❌ Failed to download file:', downloadError)
      await supabase
      .from('documents')
        .update({
          status: 'failed',
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
          throw new Error('LlamaParse API key not configured')
        }

        // Prepare file for LlamaCloud upload
            const formData = new FormData()
        formData.append('file', fileData, filename)
            
        const uploadResponse = await uploadToLlamaParse(formData, llamaCloudKey)

            if (!uploadResponse.ok) {
          if (uploadResponse.status === 429) {
            throw new Error('LlamaCloud rate limit exceeded after retries')
          }
          throw new Error(`LlamaCloud upload failed: ${uploadResponse.status}`)
            }

            const uploadResult = await uploadResponse.json()
            const jobId = uploadResult.id

        console.log('📤 File uploaded to LlamaCloud, job ID:', jobId)

        // Poll for completion with timeout
            let attempts = 0
        const maxAttempts = 60 // Wait up to 5 minutes
            
        while (attempts < maxAttempts) {
          const statusResponse = await retryWithBackoff(
            () => fetch(`https://api.cloud.llamaindex.ai/api/parsing/job/${jobId}`, {
                headers: {
              'Authorization': `Bearer ${llamaCloudKey}`,
                }
              })
          )

          if (!statusResponse.ok) {
            throw new Error(`Status check failed: ${statusResponse.status}`)
          }

          const statusResult = await statusResponse.json()
          console.log(`🔄 LlamaCloud status (attempt ${attempts + 1}):`, statusResult.status)
                
          if (statusResult.status === 'SUCCESS') {
            // Get the result
            const resultResponse = await retryWithBackoff(
              () => fetch(`https://api.cloud.llamaindex.ai/api/parsing/job/${jobId}/result/markdown`, {
              headers: {
                'Authorization': `Bearer ${llamaCloudKey}`,
              }
            })
            )

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
      body: { 
        documentId: documentId,
        extractedText: extractedText,
        documentType: 'user',
        userId: document.user_id
      }
    })

      if (vectorError) {
      console.error('❌ Vector processor invocation failed:', vectorError)
              await supabase
          .from('documents')
          .update({
            status: 'failed',
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
      progress_percentage: 0,
      updated_at: new Date().toISOString()
    })
    .eq('id', documentId)
}

async function retryWithBackoff(
  operation: () => Promise<Response>, 
  maxRetries = 5,  // Increased from 3 to 5
  initialDelay = 2000  // Increased from 1000 to 2000
): Promise<Response> {
  let retries = 0
  let delay = initialDelay

  while (retries < maxRetries) {
    try {
      const response = await operation()
      
      // If not rate limited, return immediately
      if (response.status !== 429) {
        return response
      }
      
      // Get retry-after header if available
      const retryAfter = response.headers.get('retry-after')
      const waitTime = retryAfter ? parseInt(retryAfter) * 1000 : delay
      
      retries++
      console.log(`🔄 Rate limited (attempt ${retries}/${maxRetries}), waiting ${waitTime}ms`)
      
      if (retries === maxRetries) {
        console.error('❌ Max retries reached, giving up')
        return response
      }
      
      // Exponential backoff with jitter
      await new Promise(resolve => setTimeout(resolve, waitTime))
      delay = Math.min(delay * 2, 32000) // Cap at 32 seconds
      delay += Math.random() * 1000 // Add jitter
      
    } catch (error) {
      retries++
      if (retries === maxRetries) {
        throw error
      }
      
      console.log(`⚠️ Operation failed (attempt ${retries}/${maxRetries}), retrying in ${delay}ms`)
      await new Promise(resolve => setTimeout(resolve, delay))
      delay = Math.min(delay * 2, 32000)
      delay += Math.random() * 1000
    }
  }

  throw new Error(`Operation failed after ${maxRetries} retries`)
} 