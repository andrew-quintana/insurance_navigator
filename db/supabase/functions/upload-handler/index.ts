import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface UploadRequest {
  filename: string;
  contentType: string;
  fileSize: number;
  chunkIndex?: number;
  totalChunks?: number;
  documentId?: string;
}

interface DocumentRecord {
  id: string;
  user_id: string;
  original_filename: string;
  file_size: number;
  content_type: string;
  file_hash: string;
  storage_path?: string;
  status: string;
  progress_percentage: number;
  total_chunks?: number;
  processed_chunks: number;
  failed_chunks: number;
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    console.log('🚀 Upload handler started - method:', req.method)
    console.log('📋 Headers received:', JSON.stringify(Object.fromEntries(req.headers.entries())))
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    // Get authenticated user - now expects service role key + X-User-ID
    const authHeader = req.headers.get('Authorization')
    console.log('🔍 Auth header present:', !!authHeader)
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      console.log('❌ Missing or invalid authorization header format')
      return new Response(JSON.stringify({ error: 'Missing authorization header' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }
    
    const token = authHeader.replace('Bearer ', '')
    const serviceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    console.log('🔍 Auth Debug - Token length:', token.length)
    console.log('🔍 Auth Debug - Service key length:', serviceKey.length)
    console.log('🔍 Auth Debug - Tokens match:', token === serviceKey)
    
    // Verify service role key
    if (token !== serviceKey) {
      console.log('❌ Auth Debug - Invalid service role key')
      return new Response(JSON.stringify({ 
        error: 'Unauthorized',
        debug: 'Invalid service role key'
      }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }
    
    // Get user ID from header
    const userId = req.headers.get('X-User-ID')
    console.log('🔍 Auth Debug - X-User-ID header:', userId)
    
    if (!userId) {
      console.log('❌ Auth Debug - Missing X-User-ID header')
      return new Response(JSON.stringify({ 
        error: 'Unauthorized',
        debug: 'Missing X-User-ID header'
      }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log('✅ Authentication successful for userId:', userId)

    if (req.method === 'POST') {
      return await handleUpload(req, supabase, userId)
    } else if (req.method === 'GET') {
      return await handleUploadStatus(req, supabase, userId)
    } else if (req.method === 'PUT') {
      return await handleChunkUpload(req, supabase, userId)
    } else if (req.method === 'PATCH') {
      return await handleUploadComplete(req, supabase, userId)
    }

    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Upload handler error:', error)
    return new Response(JSON.stringify({ 
      error: 'Internal server error',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})

async function handleUpload(req: Request, supabase: any, userId: string) {
  const uploadData: UploadRequest = await req.json()
  
  // Validate file size (50MB limit)
  if (uploadData.fileSize > 52428800) {
    return new Response(JSON.stringify({ 
      error: 'File too large',
      maxSize: '50MB'
    }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  // Validate file type
  const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
  if (!allowedTypes.includes(uploadData.contentType)) {
    return new Response(JSON.stringify({ 
      error: 'File type not supported',
      allowedTypes: ['PDF', 'DOCX', 'TXT']
    }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  // Generate file hash for deduplication
  const fileHash = await generateFileHash(uploadData.filename, uploadData.fileSize, userId)
  
  // Check for existing file with same hash
  const { data: existingDoc, error: checkError } = await supabase
    .from('documents')
    .select('id, status, original_filename')
    .eq('file_hash', fileHash)
    .eq('user_id', userId)
    .single()

  if (existingDoc && existingDoc.status === 'completed') {
    return new Response(JSON.stringify({ 
      error: 'File already uploaded',
      documentId: existingDoc.id,
      filename: existingDoc.original_filename
    }), {
      status: 409,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  // Calculate chunks for large files (>5MB)
  const chunkSize = 5242880 // 5MB chunks
  const totalChunks = uploadData.fileSize > chunkSize ? Math.ceil(uploadData.fileSize / chunkSize) : 1
  
  // Create document record
  const documentRecord = {
    user_id: userId,
    original_filename: uploadData.filename,
    file_size: uploadData.fileSize,
    content_type: uploadData.contentType,
    file_hash: fileHash,
    status: 'pending',
    progress_percentage: 0,
    total_chunks: totalChunks,
    processed_chunks: 0,
    failed_chunks: 0,
    storage_path: `${userId}/${fileHash}/${uploadData.filename}`,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }

  const { data: document, error: insertError } = await supabase
    .from('documents')
    .insert(documentRecord)
    .select()
    .single()

  if (insertError) {
    console.error('Error creating document record:', insertError)
    return new Response(JSON.stringify({ 
      error: 'Failed to create document record',
      details: insertError.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  // Generate presigned URL for upload
  const { data: uploadUrl, error: urlError } = await supabase.storage
    .from('documents')
    .createSignedUploadUrl(document.storage_path)

  if (urlError) {
    console.error('Error generating upload URL:', urlError)
    return new Response(JSON.stringify({ 
      error: 'Failed to generate upload URL',
      details: urlError.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  // Update document status to uploading
  await supabase
    .from('documents')
    .update({ 
      status: 'uploading',
      processing_started_at: new Date().toISOString()
    })
    .eq('id', document.id)

  // Send initial progress update
  await sendProgressUpdate(supabase, userId, {
    documentId: document.id,
    status: 'uploading',
    progress: 5,
    metadata: { 
      step: 'upload_initialized',
      filename: uploadData.filename,
      fileSize: uploadData.fileSize
    }
  })

  return new Response(JSON.stringify({
    documentId: document.id,
    uploadUrl: uploadUrl.signedURL,
    path: document.storage_path,
    totalChunks: totalChunks,
    chunkSize: chunkSize,
    expiresIn: 3600,
    message: 'Upload initialized successfully'
  }), {
    status: 200,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  })
}

async function handleUploadStatus(req: Request, supabase: any, userId: string) {
  const url = new URL(req.url)
  const documentId = url.searchParams.get('documentId')
  
  if (!documentId) {
    return new Response(JSON.stringify({ error: 'Document ID required' }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  const { data: document, error } = await supabase
    .from('documents')
    .select('*')
    .eq('id', documentId)
    .eq('user_id', userId)
    .single()

  if (error || !document) {
    return new Response(JSON.stringify({ error: 'Document not found' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  return new Response(JSON.stringify({
    documentId: document.id,
    status: document.status,
    progress: document.progress_percentage,
    processedChunks: document.processed_chunks,
    totalChunks: document.total_chunks,
    failedChunks: document.failed_chunks,
    errorMessage: document.error_message,
    filename: document.original_filename,
    fileSize: document.file_size
  }), {
    status: 200,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  })
}

async function handleChunkUpload(req: Request, supabase: any, userId: string) {
  const url = new URL(req.url)
  const documentId = url.searchParams.get('documentId')
  const chunkIndex = parseInt(url.searchParams.get('chunkIndex') || '0')
  
  if (!documentId) {
    return new Response(JSON.stringify({ error: 'Document ID required' }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  // Get document record
  const { data: document, error: docError } = await supabase
    .from('documents')
    .select('*')
    .eq('id', documentId)
    .eq('user_id', userId)
    .single()

  if (docError || !document) {
    return new Response(JSON.stringify({ error: 'Document not found' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  // Update chunk progress
  const processedChunks = document.processed_chunks + 1
  const progressPercentage = Math.round((processedChunks / document.total_chunks) * 100)
  
  const updateData: any = {
    processed_chunks: processedChunks,
    progress_percentage: progressPercentage,
    updated_at: new Date().toISOString()
  }

  // Check if upload is complete
  if (processedChunks >= document.total_chunks) {
    updateData.status = 'processing'
    updateData.processing_completed_at = new Date().toISOString()
  }

  await supabase
    .from('documents')
    .update(updateData)
    .eq('id', documentId)

  return new Response(JSON.stringify({
    documentId: documentId,
    chunkIndex: chunkIndex,
    processedChunks: processedChunks,
    totalChunks: document.total_chunks,
    progress: progressPercentage,
    status: updateData.status || document.status,
    isComplete: processedChunks >= document.total_chunks
  }), {
    status: 200,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  })
}

async function generateFileHash(filename: string, fileSize: number, userId: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(`${filename}-${fileSize}-${userId}-${Date.now()}`)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

async function handleUploadComplete(req: Request, supabase: any, userId: string) {
  const { documentId, path } = await req.json()
  
  if (!documentId || !path) {
    return new Response(JSON.stringify({ 
      error: 'Document ID and storage path required' 
    }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  try {
    // Get document details
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .eq('user_id', userId)
      .single()

    if (docError || !document) {
      return new Response(JSON.stringify({ error: 'Document not found' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    // Update document status to processing
    await supabase
      .from('documents')
      .update({ 
        status: 'processing',
        progress_percentage: 20,
        upload_completed_at: new Date().toISOString()
      })
      .eq('id', documentId)

    // Send progress update
    await sendProgressUpdate(supabase, userId, {
      documentId: documentId,
      status: 'processing',
      progress: 20,
      metadata: { 
        step: 'upload_complete',
        storage_path: path
      }
    })

    // Check if we should use LlamaParse for this document type
    const needsLlamaParse = shouldUseLlamaParse(document.content_type)
    
    if (needsLlamaParse) {
      console.log(`🦙 Starting LlamaParse processing: ${document.original_filename}`)
      
      try {
        // Update document status to parsing with LlamaParse
        await supabase
          .from('documents')
          .update({
            status: 'parsing',
            progress_percentage: 30,
            metadata: {
              ...document.metadata,
              processing_method: 'llamaparse',
              parsing_started_at: new Date().toISOString()
            }
          })
          .eq('id', documentId)

        // Send progress update
        await sendProgressUpdate(supabase, userId, {
          documentId: documentId,
          status: 'parsing',
          progress: 30,
          metadata: { 
            step: 'llamaparse_started',
            processing_method: 'llamaparse'
          }
        })

        // Actually trigger doc-parser edge function with LlamaParse
        console.log(`🔗 Invoking doc-parser with LlamaParse for document: ${documentId}`)
        const { data, error } = await supabase.functions.invoke('doc-parser', {
          body: { documentId: documentId }
        })

        if (error) {
          console.error(`❌ doc-parser (LlamaParse) invocation failed:`, error)
          throw new Error(`doc-parser LlamaParse failed: ${error.message}`)
        }

        console.log(`✅ doc-parser (LlamaParse) invoked successfully for document: ${documentId}`)

      } catch (llamaParseError) {
        console.error('❌ LlamaParse processing failed:', llamaParseError)
        
        // Fall back to direct processing
        console.log('📝 Falling back to direct text processing')
        await triggerDirectProcessing(supabase, documentId, userId)
      }
    } else {
      // Skip LlamaParse for simple text files
      console.log(`📝 Skipping LlamaParse for ${document.content_type}, processing directly`)
      await triggerDirectProcessing(supabase, documentId, userId)
    }

    return new Response(JSON.stringify({
      success: true,
      documentId: documentId,
      status: 'processing',
      message: needsLlamaParse ? 
        'Upload complete, processing with LlamaParse' : 
        'Upload complete, processing directly'
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Upload completion error:', error)
    return new Response(JSON.stringify({ 
      error: 'Failed to complete upload',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
}

function shouldUseLlamaParse(contentType: string): boolean {
  const llamaParseTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // DOCX
    'application/vnd.openxmlformats-officedocument.presentationml.presentation', // PPTX
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // XLSX
    'application/msword', // DOC
    'application/vnd.ms-powerpoint', // PPT
    'application/vnd.ms-excel' // XLS
  ]
  
  return llamaParseTypes.includes(contentType)
}

async function triggerDirectProcessing(supabase: any, documentId: string, userId: string) {
  // For simple text files or fallback processing
  console.log(`📄 Starting direct processing for document: ${documentId}`)
  
  try {
    // Update status to parsing
    await supabase
      .from('documents')
      .update({
        status: 'parsing',
        progress_percentage: 30,
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)

    // Send progress update
    await sendProgressUpdate(supabase, userId, {
      documentId: documentId,
      status: 'parsing',
      progress: 30,
      metadata: { 
        step: 'direct_processing_started',
        processing_method: 'native'
      }
    })

    // Actually trigger doc-parser edge function
    console.log(`🔗 Invoking doc-parser for document: ${documentId}`)
    const { data, error } = await supabase.functions.invoke('doc-parser', {
      body: { documentId: documentId }
    })

    if (error) {
      console.error(`❌ doc-parser invocation failed:`, error)
      throw new Error(`doc-parser failed: ${error.message}`)
    }

    console.log(`✅ doc-parser invoked successfully for document: ${documentId}`)

  } catch (error) {
    console.error(`❌ Direct processing failed for ${documentId}:`, error)
    
    await supabase
      .from('documents')
      .update({
        status: 'failed',
        error_message: `Direct processing failed: ${error.message}`,
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)
  }
}

// Helper functions

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