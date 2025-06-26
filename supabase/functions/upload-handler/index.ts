// @deno-types="https://esm.sh/@supabase/supabase-js@2.7.1/dist/module/index.d.ts"
import { serve } from "https://deno.land/std@0.177.0/http/server.ts"
import { createClient } from "@supabase/supabase-js"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

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
    // Log request details for debugging
    console.log('Request headers:', Object.fromEntries(req.headers.entries()));
    
    // Get auth token
    const token = req.headers.get('Authorization')?.split(' ')[1]
    if (!token) {
      throw new Error('No authorization header')
    }

    // Get user ID with validation
    const userId = await getUserId(token);
    console.log('Validated user ID:', userId);

    // Initialize Supabase admin client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')
    const supabaseServiceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
    if (!supabaseUrl || !supabaseServiceRoleKey) {
      throw new Error('Missing environment variables')
    }

    const supabaseAdmin = createClient(supabaseUrl, supabaseServiceRoleKey)

    // Parse request body as FormData with error handling
    let formData: FormData;
    try {
      formData = await req.formData();
      console.log('FormData parsed successfully');
    } catch (error) {
      console.error('FormData parsing error:', error);
      return new Response(
        JSON.stringify({ error: 'Invalid form data format' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Get file and metadata from FormData with logging
    const file = formData.get('file');
    const metadataStr = formData.get('metadata');
    console.log('Received file:', file ? 'yes' : 'no');
    console.log('Received metadata:', metadataStr ? 'yes' : 'no');

    // Parse metadata
    let metadata = {};
    if (metadataStr) {
      try {
        metadata = JSON.parse(metadataStr as string);
        console.log('Parsed metadata:', metadata);
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
    const storagePath = `docs/${userId}/${timestamp}_${file.name}`

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
          upload_completed_at: new Date().toISOString()
        }
      })
      .select()
      .single()

    if (documentError) {
      // Try to clean up the uploaded file if document creation fails
      await supabaseAdmin.storage.from('docs').remove([storagePath])
      throw new Error(`Failed to create document: ${documentError.message}`)
    }

    // The database trigger will automatically create a job record
    // and the job processor will pick it up

    return new Response(
      JSON.stringify({
        success: true,
        documentId: document.id,
        storagePath,
        status: 'pending'
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})