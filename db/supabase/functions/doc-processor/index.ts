import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

interface UploadRequest {
  filename: string;
  contentType: string;
  fileSize: number;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    )

    // Get authenticated user from JWT token
    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      return new Response(
        JSON.stringify({ error: 'Authorization header required' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const token = authHeader.replace('Bearer ', '')
    const { data: { user }, error: authError } = await supabase.auth.getUser(token)
    
    if (authError || !user) {
      return new Response(
        JSON.stringify({ error: 'Invalid or expired token' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const { filename, contentType, fileSize }: UploadRequest = await req.json()

    // Validate file size (50MB limit)
    if (fileSize > 52428800) {
      return new Response(
        JSON.stringify({ 
          error: 'File too large',
          maxSize: '50MB'
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Validate file type
    const allowedTypes = [
      'application/pdf', 
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain'
    ]
    if (!allowedTypes.includes(contentType)) {
      return new Response(
        JSON.stringify({ 
          error: 'File type not supported',
          allowedTypes: ['PDF', 'DOCX', 'DOC', 'TXT']
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Generate file hash for deduplication
    const fileHash = await generateFileHash(filename, fileSize, user.id)
    
    // Check for existing file with same hash
    const { data: existingDoc } = await supabase
      .from('documents')
      .select('id, status, original_filename')
      .eq('file_hash', fileHash)
      .eq('user_id', user.id)
      .single()

    if (existingDoc && existingDoc.status === 'completed') {
      return new Response(
        JSON.stringify({ 
          error: 'File already uploaded',
          documentId: existingDoc.id,
          filename: existingDoc.original_filename
        }),
        { status: 409, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Create document record
    const storagePath = `${user.id}/${fileHash}/${filename}`
    const { data: document, error: docError } = await supabase
      .from('documents')
      .insert({
        user_id: user.id,
        original_filename: filename,
        content_type: contentType,
        file_size: fileSize,
        file_hash: fileHash,
        storage_path: storagePath,
        status: 'uploading',
        progress_percentage: 0,
        processed_chunks: 0,
        failed_chunks: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      .select()
      .single()

    if (docError) {
      console.error('Error creating document record:', docError)
      return new Response(
        JSON.stringify({ error: 'Failed to create document record' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Generate signed upload URL
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('documents')
      .createSignedUploadUrl(storagePath)

    if (uploadError) {
      console.error('Error generating upload URL:', uploadError)
      return new Response(
        JSON.stringify({ error: 'Failed to generate upload URL' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    return new Response(
      JSON.stringify({
        documentId: document.id,
        uploadUrl: uploadData.signedUrl,
        uploadPath: uploadData.path,
        storagePath: storagePath
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('doc-processor error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

async function generateFileHash(filename: string, fileSize: number, userId: string): Promise<string> {
  const data = `${filename}-${fileSize}-${userId}-${Date.now()}`
  const encoder = new TextEncoder()
  const dataBytes = encoder.encode(data)
  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBytes)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
} 