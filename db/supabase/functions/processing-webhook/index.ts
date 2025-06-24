import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-webhook-signature',
}

interface WebhookPayload {
  documentId?: string;
  jobId?: string;
  status: 'completed' | 'failed' | 'processing';
  result?: any;
  error?: string;
  metadata?: Record<string, any>;
  source: 'llamaparse' | 'internal' | 'storage' | 'embedding';
  
  // LlamaParse specific fields (from their webhook documentation)
  txt?: string;
  md?: string;
  json?: Array<{
    page: number;
    text: string;
    md: string;
    images?: Array<{
      name: string;
      height: number;
      width: number;
      x: number;
      y: number;
    }>;
  }>;
  images?: string[];
}

interface LlamaParseResult {
  txt?: string;
  md?: string;
  json?: Array<{
    page: number;
    text: string;
    md: string;
    images?: Array<{
      name: string;
      height: number;
      width: number;
      x: number;
      y: number;
    }>;
  }>;
  images?: string[];
}

interface ProcessingResult {
  extractedText?: string;
  chunks?: string[];
  embeddings?: number[][];
  metadata?: Record<string, any>;
  processingTime?: number;
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    if (req.method === 'POST') {
      return await handleWebhook(req, supabase)
    }

    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Processing webhook error:', error)
    return new Response(JSON.stringify({ 
      error: 'Internal server error',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})

async function handleWebhook(req: Request, supabase: any) {
  const webhookData: WebhookPayload = await req.json()
  
  console.log('Processing webhook:', JSON.stringify(webhookData, null, 2))

  // Detect LlamaParse webhook format
  const isLlamaParseWebhook = webhookData.txt || webhookData.md || webhookData.json || 
                             (!webhookData.source && (webhookData.txt !== undefined))

  if (isLlamaParseWebhook) {
    console.log('🦙 Detected LlamaParse webhook format')
    return await handleLlamaParseWebhook(req, supabase, webhookData)
  }

  // Legacy webhook verification for non-LlamaParse sources
  const signature = req.headers.get('x-webhook-signature')
  const expectedSignature = Deno.env.get('WEBHOOK_SECRET')
  
  if (expectedSignature && signature !== expectedSignature) {
    console.log('❌ Invalid webhook signature for non-LlamaParse webhook')
    return new Response(JSON.stringify({ error: 'Invalid webhook signature' }), {
      status: 401,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  // Find document by ID or job ID
  let document
  if (webhookData.documentId) {
    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .eq('id', webhookData.documentId)
      .single()
    
    if (error) {
      console.error('Document lookup error:', error)
      return new Response(JSON.stringify({ error: 'Document not found' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }
    document = data
  } else if (webhookData.jobId) {
    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .eq('llama_parse_job_id', webhookData.jobId)
      .single()
    
    if (error) {
      console.error('Document lookup by job ID error:', error)
      return new Response(JSON.stringify({ error: 'Document not found by job ID' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }
    document = data
  } else {
    return new Response(JSON.stringify({ error: 'Document ID or Job ID required' }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  // Process the webhook based on source
  switch (webhookData.source) {
    case 'storage':
      return await handleStorageWebhook(supabase, document, webhookData)
    case 'embedding':
      return await handleEmbeddingWebhook(supabase, document, webhookData)
    case 'internal':
      return await handleInternalWebhook(supabase, document, webhookData)
    default:
      return new Response(JSON.stringify({ error: 'Unknown webhook source' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
  }
}

async function handleLlamaParseWebhook(req: Request, supabase: any, webhookData: WebhookPayload) {
  console.log('🦙 Processing LlamaParse webhook...')
  
  try {
    // Find document by looking for recent uploads without LlamaParse job IDs
    // Since LlamaParse doesn't send document IDs, we need to match by other means
    const { data: recentDocuments, error: searchError } = await supabase
      .from('documents')
      .select('*')
      .is('llama_parse_job_id', null)
      .eq('status', 'processing')
      .order('created_at', { ascending: false })
      .limit(10)

    if (searchError || !recentDocuments || recentDocuments.length === 0) {
      console.error('No matching documents found for LlamaParse webhook')
      
      // Try to find by any processing document as fallback
      const { data: fallbackDocs } = await supabase
        .from('documents')
        .select('*')
        .eq('status', 'processing')
        .order('created_at', { ascending: false })
        .limit(1)
      
      if (!fallbackDocs || fallbackDocs.length === 0) {
        return new Response(JSON.stringify({ 
          error: 'No matching document found for LlamaParse webhook',
          message: 'This webhook may be for a completed or non-existent document'
        }), {
          status: 404,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }
      
      console.log('📄 Using fallback document matching for LlamaParse webhook')
    }

    // Use the most recent processing document
    const document = recentDocuments?.[0] || null
    
    if (!document) {
      return new Response(JSON.stringify({ error: 'No document found for processing' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log(`📋 Processing LlamaParse result for document: ${document.id}`)

    // Extract text content from LlamaParse response
    let extractedText = ''
    let extractedMarkdown = ''
    let pageCount = 0
    
    if (webhookData.txt) {
      extractedText = webhookData.txt
    }
    
    if (webhookData.md) {
      extractedMarkdown = webhookData.md
    }
    
    if (webhookData.json && Array.isArray(webhookData.json)) {
      pageCount = webhookData.json.length
      
      // If no txt provided, combine from JSON pages
      if (!extractedText) {
        extractedText = webhookData.json.map(page => page.text || '').join('\n\n')
      }
      
      // If no markdown provided, combine from JSON pages
      if (!extractedMarkdown) {
        extractedMarkdown = webhookData.json.map(page => page.md || '').join('\n\n')
      }
    }

    const hasValidContent = extractedText && extractedText.trim().length > 0

    // Update document with LlamaParse results
    const updateData: any = {
      status: hasValidContent ? 'chunking' : 'failed',
      progress_percentage: hasValidContent ? 60 : 0,
      updated_at: new Date().toISOString(),
      llama_parse_job_id: `llamaparse_${Date.now()}`, // Generate job ID for tracking
      extracted_text_length: extractedText.length
    }

    if (hasValidContent) {
      updateData.metadata = {
        ...document.metadata,
        llamaparse_result: {
          text_length: extractedText.length,
          markdown_length: extractedMarkdown.length,
          page_count: pageCount,
          has_images: webhookData.images && webhookData.images.length > 0,
          image_count: webhookData.images?.length || 0,
          processing_completed_at: new Date().toISOString()
        },
        parsing_completed_at: new Date().toISOString()
      }
    } else {
      updateData.status = 'failed'
      updateData.error_message = 'LlamaParse returned empty content'
      updateData.error_details = {
        source: 'llamaparse',
        webhook_data: webhookData,
        timestamp: new Date().toISOString()
      }
    }

    // Update document
    const { error: updateError } = await supabase
      .from('documents')
      .update(updateData)
      .eq('id', document.id)

    if (updateError) {
      console.error('Error updating document after LlamaParse webhook:', updateError)
      return new Response(JSON.stringify({ 
        error: 'Failed to update document',
        details: updateError.message 
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    // Trigger next processing step if successful
    if (hasValidContent) {
      console.log(`✅ LlamaParse processing successful, triggering chunking for ${extractedText.length} characters`)
      await triggerChunking(supabase, document.id, { 
        text: extractedText, 
        markdown: extractedMarkdown,
        metadata: updateData.metadata.llamaparse_result 
      })
    } else {
      console.error('❌ LlamaParse returned empty or invalid content')
    }

    // Send progress update
    await sendProgressUpdate(supabase, document.user_id, {
      documentId: document.id,
      status: updateData.status,
      progress: updateData.progress_percentage,
      metadata: { 
        source: 'llamaparse', 
        step: hasValidContent ? 'parsing_complete' : 'parsing_failed',
        content_length: extractedText.length
      }
    })

    return new Response(JSON.stringify({ 
      success: true,
      documentId: document.id,
      status: updateData.status,
      contentLength: extractedText.length,
      message: hasValidContent ? 'LlamaParse webhook processed successfully' : 'LlamaParse processing failed - no content extracted'
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('❌ LlamaParse webhook processing error:', error)
    return new Response(JSON.stringify({ 
      error: 'Failed to process LlamaParse webhook',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
}

async function handleStorageWebhook(supabase: any, document: any, webhookData: WebhookPayload) {
  const updateData: any = {
    updated_at: new Date().toISOString()
  }

  if (webhookData.status === 'completed') {
    updateData.status = 'processing'
    updateData.progress_percentage = 30
    
    // Check if we need LlamaParse or can process directly
    const featureFlag = await checkFeatureFlag(supabase, 'llama_parse_integration', document.user_id)
    
    if (featureFlag && needsLlamaParse(document.content_type)) {
      // Trigger LlamaParse
      await triggerLlamaParseJob(supabase, document.id)
    } else {
      // Skip to chunking
      updateData.status = 'chunking'
      updateData.progress_percentage = 50
      await triggerChunking(supabase, document.id, null)
    }
  } else if (webhookData.status === 'failed') {
    updateData.status = 'failed'
    updateData.error_message = webhookData.error || 'Storage processing failed'
  }

  // Update document
  const { error: updateError } = await supabase
    .from('documents')
    .update(updateData)
    .eq('id', document.id)

  if (updateError) {
    console.error('Error updating document after storage webhook:', updateError)
    return new Response(JSON.stringify({ 
      error: 'Failed to update document',
      details: updateError.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  return new Response(JSON.stringify({ 
    success: true,
    documentId: document.id,
    status: updateData.status,
    message: 'Storage webhook processed'
  }), {
    status: 200,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  })
}

async function handleEmbeddingWebhook(supabase: any, document: any, webhookData: WebhookPayload) {
  const updateData: any = {
    status: webhookData.status === 'completed' ? 'completed' : 'failed',
    progress_percentage: webhookData.status === 'completed' ? 100 : document.progress_percentage,
    updated_at: new Date().toISOString()
  }

  if (webhookData.status === 'completed') {
    updateData.processing_completed_at = new Date().toISOString()
  } else {
    updateData.error_message = webhookData.error || 'Embedding processing failed'
    updateData.error_details = {
      source: 'embedding',
      webhook_data: webhookData,
      timestamp: new Date().toISOString()
    }
  }

  // Update document
  const { error: updateError } = await supabase
    .from('documents')
    .update(updateData)
    .eq('id', document.id)

  if (updateError) {
    console.error('Error updating document after embedding webhook:', updateError)
    return new Response(JSON.stringify({ 
      error: 'Failed to update document',
      details: updateError.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  return new Response(JSON.stringify({ 
    success: true,
    documentId: document.id,
    status: updateData.status,
    message: 'Embedding webhook processed'
  }), {
    status: 200,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  })
}

async function handleInternalWebhook(supabase: any, document: any, webhookData: WebhookPayload) {
  // Handle internal processing updates
  const updateData: any = {
    updated_at: new Date().toISOString()
  }

  if (webhookData.status) {
    updateData.status = webhookData.status
  }

  if (webhookData.metadata?.progress) {
    updateData.progress_percentage = webhookData.metadata.progress
  }

  // Update document
  const { error: updateError } = await supabase
    .from('documents')
    .update(updateData)
    .eq('id', document.id)

  if (updateError) {
    console.error('Error updating document after internal webhook:', updateError)
    return new Response(JSON.stringify({ 
      error: 'Failed to update document',
      details: updateError.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  return new Response(JSON.stringify({ 
    success: true,
    documentId: document.id,
    message: 'Internal webhook processed'
  }), {
    status: 200,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  })
}

// Helper functions

async function triggerChunking(supabase: any, documentId: string, parseResult: any) {
  console.log('Triggering chunking for document:', documentId)
  
  try {
    // Get document content
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .single()

    if (docError) throw docError
    if (!document) throw new Error('Document not found')

    // Get the text content to process
    const text = parseResult?.text || document.content || document.extracted_text
    if (!text) throw new Error('No text content found to process')

    // Call chunking service
    console.log('Calling chunking service...')
    const response = await supabase.functions.invoke('chunking-service', {
      body: JSON.stringify({
        documentId,
        text
      })
    })

    if (!response.data?.success) {
      throw new Error(`Chunking service failed: ${response.error?.message || 'Unknown error'}`)
    }

    console.log('Chunking service response:', response.data)
    return response.data

  } catch (error) {
    console.error('Error in triggerChunking:', error)
    
    // Update document with error status
    await supabase
      .from('documents')
      .update({
        status: 'failed',
        error_message: `Chunking failed: ${error.message}`,
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)
    
    throw error
  }
}

async function triggerLlamaParseJob(supabase: any, documentId: string) {
  // This would trigger LlamaParse job
  console.log('Triggering LlamaParse job for document:', documentId)
  
  // Generate job ID and update document
  const jobId = `llama_${documentId}_${Date.now()}`
  await supabase
    .from('documents')
    .update({
      llama_parse_job_id: jobId,
      status: 'processing',
      progress_percentage: 40,
      updated_at: new Date().toISOString()
    })
    .eq('id', documentId)
}

function needsLlamaParse(contentType: string): boolean {
  return contentType === 'application/pdf' || 
         contentType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

async function checkFeatureFlag(supabase: any, flagName: string, userId: string): Promise<boolean> {
  const { data, error } = await supabase
    .rpc('evaluate_feature_flag', {
      flag_name_param: flagName,
      user_id_param: userId
    })

  if (error) {
    console.warn('Feature flag check failed:', error)
    return false
  }

  return data || false
}

async function sendProgressUpdate(supabase: any, userId: string, update: any) {
  try {
    await supabase
      .from('realtime_progress_updates')
      .insert({
        user_id: userId,
        document_id: update.documentId,
        payload: {
          type: 'progress_update',
          documentId: update.documentId,
          progress: update.progress || 0,
          status: update.status || 'processing',
          timestamp: new Date().toISOString(),
          details: update.metadata || {}
        },
        created_at: new Date().toISOString()
      })
  } catch (error) {
    console.warn('Failed to send progress update:', error)
  }
} 