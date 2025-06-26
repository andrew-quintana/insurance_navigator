// @deno-types="npm:@types/node"
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
// @deno-types="npm:@supabase/supabase-js"
import { createClient, SupabaseClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

// Configuration
const CONFIG = {
  UPLOAD_BUCKET: 'raw_documents',
  STORAGE_BUCKET: 'documents',
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_MIME_TYPES: [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
  ]
}

// Log configuration on startup
console.log('📝 Upload handler configuration:', {
  uploadBucket: CONFIG.UPLOAD_BUCKET,
  storageBucket: CONFIG.STORAGE_BUCKET,
  maxFileSize: CONFIG.MAX_FILE_SIZE,
  allowedMimeTypes: CONFIG.ALLOWED_MIME_TYPES
})

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
  document_type: string;
  metadata: any;
  created_at: string;
  updated_at: string;
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client with service role key for full access
    const supabaseClient: SupabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Parse request
    const requestData = await req.json()
    
    // Handle both backend and frontend upload requests
    let userId: string
    let uploadData: {
      filename: string
      contentType: string
      fileSize: number
      fileHash?: string
    }

    // Backend request format
    if (requestData.userId && requestData.filename) {
      userId = requestData.userId
      uploadData = {
        filename: requestData.filename,
        contentType: requestData.contentType,
        fileSize: requestData.fileSize,
        fileHash: requestData.fileHash
      }
    }
    // Frontend request format
    else if (requestData.filename && requestData.contentType) {
      // Get user ID from auth token
      const authHeader = req.headers.get('authorization')
      if (!authHeader) {
        throw new Error('Missing authorization header')
    }
    
    const token = authHeader.replace('Bearer ', '')
      const { data: { user }, error: authError } = await supabaseClient.auth.getUser(token)
      
      if (authError || !user) {
        throw new Error('Authentication failed')
      }

      userId = user.id
      uploadData = {
        filename: requestData.filename,
        contentType: requestData.contentType,
        fileSize: requestData.fileSize,
        fileHash: requestData.fileHash
      }
    } else {
      throw new Error('Invalid request format')
    }

    // Generate file hash if not provided
    if (!uploadData.fileHash) {
      const encoder = new TextEncoder()
      const data = encoder.encode(`${uploadData.filename}-${uploadData.fileSize}-${userId}-${Date.now()}`)
      const hashBuffer = await crypto.subtle.digest('SHA-256', data)
      const hashArray = Array.from(new Uint8Array(hashBuffer))
      uploadData.fileHash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
    }

    // Validate file size
    if (uploadData.fileSize > CONFIG.MAX_FILE_SIZE) {
      return new Response(JSON.stringify({ 
        error: 'File too large',
        details: `Maximum file size is ${CONFIG.MAX_FILE_SIZE / 1024 / 1024}MB`
      }), {
        status: 413,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }
    
    // Validate content type
    if (!CONFIG.ALLOWED_MIME_TYPES.includes(uploadData.contentType)) {
      return new Response(JSON.stringify({ 
        error: 'Invalid file type',
        details: `Allowed file types: ${CONFIG.ALLOWED_MIME_TYPES.join(', ')}`
      }), {
        status: 415,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    // Generate storage paths
    const uploadPath = `${userId}/${uploadData.fileHash}/${uploadData.filename}`
    const finalPath = `${userId}/${uploadData.fileHash}/processed_${uploadData.filename}`

    console.log('📤 Creating upload URL:', {
      bucket: CONFIG.UPLOAD_BUCKET,
      path: uploadPath,
      contentType: uploadData.contentType
    })

    // Create signed upload URL
    console.log('🔍 Creating signed upload URL:', {
      bucket: CONFIG.UPLOAD_BUCKET,
      path: uploadPath,
      contentType: uploadData.contentType,
      timestamp: new Date().toISOString()
    })

    const { data: uploadUrl, error: urlError } = await supabaseClient.storage
      .from(CONFIG.UPLOAD_BUCKET)
      .createSignedUploadUrl(uploadPath)

    if (urlError) {
      console.error('❌ Failed to create upload URL:', {
        error: urlError,
        bucket: CONFIG.UPLOAD_BUCKET,
        path: uploadPath,
        errorCode: urlError.code,
        errorMessage: urlError.message,
        timestamp: new Date().toISOString()
      })
      throw new Error(`Failed to create upload URL: ${urlError.message}`)
    }

    // Create document record
    console.log('📄 Creating document record:', {
      userId,
      filename: uploadData.filename,
      fileSize: uploadData.fileSize,
      contentType: uploadData.contentType,
      uploadPath,
      finalPath,
      timestamp: new Date().toISOString()
    })

    const { data: document, error: docError } = await supabaseClient
    .from('documents')
      .insert({
    user_id: userId,
    original_filename: uploadData.filename,
    file_size: uploadData.fileSize,
    content_type: uploadData.contentType,
        file_hash: uploadData.fileHash,
        storage_path: finalPath,
    status: 'pending',
        metadata: {
          upload_started_at: new Date().toISOString(),
          raw_storage_path: uploadPath,
          raw_storage_bucket: CONFIG.UPLOAD_BUCKET,
          final_storage_bucket: CONFIG.STORAGE_BUCKET
        }
      })
    .select()
    .single()

    if (docError) {
      console.error('❌ Failed to create document record:', docError)
      throw new Error(`Failed to create document record: ${docError.message}`)
  }

  // Create initial processing job
    const { data: job, error: jobError } = await supabaseClient
    .from('processing_jobs')
    .insert({
      document_id: document.id,
      job_type: 'parse',
      payload: {
          document_id: document.id,
          raw_storage_path: uploadPath,
          raw_storage_bucket: CONFIG.UPLOAD_BUCKET,
          final_storage_path: finalPath,
          final_storage_bucket: CONFIG.STORAGE_BUCKET,
          content_type: uploadData.contentType
      },
      status: 'pending',
      priority: 1,
      retry_count: 0
    })
    .select()
    .single()

  if (jobError) {
      console.error('❌ Failed to create processing job:', jobError)
      
      // Update document status to failed
      await supabaseClient
      .from('documents')
        .update({
          status: 'failed',
          error_message: `Failed to create processing job: ${jobError.message}`,
          updated_at: new Date().toISOString()
        })
      .eq('id', document.id)

      throw new Error(`Failed to create processing job: ${jobError.message}`)
    }

    // Invoke job processor to start processing immediately
    console.log('🔄 Triggering job processor for immediate processing:', {
      jobId: job.id,
      documentId: document.id
    })
    
    const { data: processorData, error: processorError } = await supabaseClient.functions.invoke('job-processor', {
      method: 'POST',
      body: { 
        jobId: job.id
      },
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    })

    if (processorError) {
      console.warn('⚠️ Failed to trigger job processor:', {
        error: processorError,
        jobId: job.id,
        documentId: document.id,
        timestamp: new Date().toISOString()
      })

      // Update document status to reflect processing issue
      await supabaseClient
        .from('documents')
        .update({
          status: 'processing_queued',
          metadata: {
            ...document.metadata,
            processor_trigger_error: processorError.message,
            processor_trigger_time: new Date().toISOString()
          }
        })
        .eq('id', document.id)

      // Non-critical error - the cron job will pick it up
      console.log('ℹ️ Document queued for processing:', {
        documentId: document.id,
        jobId: job.id,
        status: 'processing_queued'
      })
    } else {
      console.log('✅ Job processor triggered successfully:', {
        documentId: document.id,
        jobId: job.id,
        processorResponse: processorData
      })

      // Update document status
      await supabaseClient
        .from('documents')
        .update({
          status: 'processing',
          metadata: {
            ...document.metadata,
            processor_trigger_time: new Date().toISOString()
          }
        })
        .eq('id', document.id)
    }

    console.log('✅ Upload handler setup complete:', {
      documentId: document.id,
      uploadPath,
      finalPath
    })

    return new Response(JSON.stringify({ 
      success: true,
      uploadUrl: uploadUrl.signedUrl,
      documentId: document.id,
      storagePath: uploadPath,
      status: processorError ? 'queued' : 'processing'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('❌ Unexpected error:', error)
    return new Response(JSON.stringify({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error occurred'
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})

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
  const chunkData = await req.json()
  const { documentId, chunkIndex, totalChunks } = chunkData

  // Get current document
  const { data: document, error: docError } = await supabase
    .from('documents')
    .select('*')
    .eq('id', documentId)
    .eq('user_id', userId)
    .single()

  if (docError || !document) {
    return new Response(JSON.stringify({ 
      error: 'Document not found',
      details: docError?.message || 'No document found'
    }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }

  // Update document metadata with chunk progress
  const currentMetadata = document.metadata || {}
  const processedChunks = new Set(currentMetadata.processed_chunks || [])
  processedChunks.add(chunkIndex)
  
  const updatedMetadata = {
    ...currentMetadata,
    processed_chunks: Array.from(processedChunks),
    total_chunks: totalChunks,
    last_chunk_processed: new Date().toISOString()
  }

  // Calculate progress percentage
  const progress = Math.floor((processedChunks.size / totalChunks) * 100)

  // Update document
  const { error: updateError } = await supabase
    .from('documents')
    .update({
      metadata: updatedMetadata,
      status: progress === 100 ? 'uploaded' : 'uploading',
      updated_at: new Date().toISOString()
    })
    .eq('id', documentId)
    .eq('user_id', userId)

  if (updateError) {
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
    progress,
    chunksProcessed: processedChunks.size,
    totalChunks
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

    return new Response(JSON.stringify({
      success: true,
      documentId: documentId,
      status: 'processing',
      message: 'Upload complete, processing started'
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
    // Get document details
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .single()

    if (docError || !document) {
      throw new Error(`Failed to get document details: ${docError?.message || 'Document not found'}`)
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
      body: { 
        documentId: documentId,
        storagePath: document.storage_path
      }
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