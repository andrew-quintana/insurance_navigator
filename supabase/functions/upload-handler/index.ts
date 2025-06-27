/// <reference lib="deno.unstable" />
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

interface UploadRequest {
  file: {
    name: string;
    type: string;
    size: number;
    data: string; // base64 encoded file data
  };
  metadata?: {
    documentType?: string;
    tags?: string[];
    [key: string]: unknown;
  };
}

const ALLOWED_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain'
];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// UUID validation regex
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

// Initialize Supabase client
const supabaseAdmin = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
)

// Validate authentication token and get user ID
async function getUserId(token: string): Promise<string> {
  try {
    // First try to get user ID from token payload
    const payload = JSON.parse(atob(token.split('.')[1]));
    console.log('Token payload:', payload);

    // Check for user_id in payload
    if (payload.user_id && UUID_REGEX.test(payload.user_id)) {
      console.log('Using user_id from token payload:', payload.user_id);
      return payload.user_id;
    }

    // If no valid user_id in payload, verify with Supabase Auth
    const supabaseUrl = Deno.env.get('SUPABASE_URL')
    const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY')
    if (!supabaseUrl || !supabaseAnonKey) {
      throw new Error('Missing environment variables')
    }

    const supabaseClient = createClient(supabaseUrl, supabaseAnonKey)
    const { data: { user }, error } = await supabaseClient.auth.getUser(token)
    
    if (error || !user) {
      console.error('Auth verification failed:', error);
      throw new Error('Invalid token')
    }

    if (!user.id || !UUID_REGEX.test(user.id)) {
      console.error('Invalid user ID format:', user.id);
      throw new Error('Invalid user ID format')
    }

    console.log('Using user ID from auth verification:', user.id);
    return user.id;
  } catch (error) {
    console.error('Auth error:', error)
    throw new Error('Authentication failed')
  }
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Get auth token
    const token = req.headers.get('Authorization')?.split(' ')[1]
    if (!token) {
      throw new Error('No authorization header')
    }

    // Get user ID with validation
    const userId = await getUserId(token);
    console.log('Validated user ID:', userId);

    // Parse request body as FormData
    const formData = await req.formData();
    const file = formData.get('file');
    const metadataStr = formData.get('metadata');

    // Parse metadata
    let metadata = {};
    if (metadataStr) {
      try {
        metadata = JSON.parse(metadataStr as string);
      } catch (error) {
        console.error('Metadata parsing error:', error);
        // Continue without metadata if parsing fails
      }
    }

    if (!file || !(file instanceof File)) {
      return new Response(
        JSON.stringify({ error: 'Missing or invalid file' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Validate file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      return new Response(
        JSON.stringify({ error: 'Unsupported file type' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      return new Response(
        JSON.stringify({ error: 'File too large' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Generate document ID and storage path
    const documentId = crypto.randomUUID()
    const timestamp = new Date().toISOString()
    const storagePath = `${userId}/raw/${timestamp}_${file.name}`

    // Upload file
    const { error: uploadError } = await supabaseAdmin
      .storage
      .from('docs')
      .upload(storagePath, file, {
        contentType: file.type,
        upsert: false
      })

    if (uploadError) {
      throw new Error(`Failed to upload file: ${uploadError.message}`)
    }

    // Create document record
    const { data: document, error: documentError } = await supabaseAdmin
      .from('documents')
      .insert({
        id: documentId,
        user_id: userId,
        original_filename: file.name,
        content_type: file.type,
        file_size: file.size,
        storage_path: storagePath,
        status: 'pending',
        metadata: {
          ...metadata,
          upload_timestamp: timestamp
        }
      })
      .select()
      .single()

    if (documentError) {
      throw new Error(`Failed to create document record: ${documentError.message}`)
    }

    // Create processing job
    const { data: job, error: jobError } = await supabaseAdmin
      .from('processing_jobs')
      .insert({
        document_id: documentId,
        job_type: 'doc_parse',
        status: 'pending',
        priority: 0,
        payload: {
          document_id: documentId,
          storage_path: storagePath,
          content_type: file.type,
          document_type: metadata.documentType
        }
      })
      .select()
      .single()

    if (jobError) {
      throw new Error(`Failed to create processing job: ${jobError.message}`)
    }

    return new Response(
      JSON.stringify({
        success: true,
        documentId,
        jobId: job.id,
        storagePath
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({
        error: error.message
      }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
});