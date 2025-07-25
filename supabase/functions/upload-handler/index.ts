import { serve } from "https://deno.land/std@0.208.0/http/server.ts"; 
import { corsHeaders } from "../_shared/cors.ts";
import { handleUpload } from "./upload.ts";
import { createClient, SupabaseClient } from 'https://esm.sh/@supabase/supabase-js@2';

console.log("Starting upload handler...");

function createSupabaseClient(): SupabaseClient {
  console.log('Creating Supabase client...');
  
  const supabaseUrl = Deno.env.get('SUPABASE_URL') || Deno.env.get('URL');
  const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || Deno.env.get('SERVICE_ROLE_KEY');

  console.log("Environment variables:", {
    hasSupabaseUrl: !!supabaseUrl,
    hasServiceRoleKey: !!serviceRoleKey,
    supabaseUrl,
    // Don't log the full key for security
    serviceRoleKeyPresent: !!serviceRoleKey
  });

  if (!supabaseUrl || !serviceRoleKey) {
    console.error('Missing required environment variables');
    throw new Error('Missing required environment variables');
  }

  return createClient(supabaseUrl, serviceRoleKey);
}

function createResponse(data: any, status = 200) {
  return new Response(
    JSON.stringify(data),
    {
      status,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    }
  );
}

serve(async (req: Request) => {
  console.log('Received request:', {
    method: req.method,
    url: req.url,
    headers: Object.fromEntries(Array.from(req.headers.entries()))
  });

  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    return createResponse({ success: true });
  }

  if (req.method !== "POST") {
    console.warn('Invalid method:', req.method);
    return createResponse(
      { success: false, error: "Method Not Allowed" },
      405
    );
  }

  try {
    // Create Supabase client
    const supabase = createSupabaseClient();

    const authHeader = req.headers.get('Authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return createResponse({ success: false, error: 'No authorization header' }, 401);
    }
    const token = authHeader.replace('Bearer ', '');
    const { data: { user }, error } = await supabase.auth.getUser(token);
    if (error || !user) {
      return createResponse({ success: false, error: 'Invalid token or user not found' }, 401);
    }

    // Handle file upload - pass TEST_USER_ID for now since we're not using JWT
    console.log('Processing upload with test user ID:', user.id);

    // --- MVP: Regulatory Document Support ---
    // 1. Detect admin role from user_metadata
    const isAdmin = user.user_metadata && (user.user_metadata.role === 'admin' || (Array.isArray(user.user_metadata.roles) && user.user_metadata.roles.includes('admin')));

    // 2. Parse form data to get documentType (if present)
    let documentType = 'user_document';
    let formData: FormData | undefined;

    if (req.headers.get('content-type') && req.headers.get('content-type').includes('multipart/form-data')) {
      formData = await req.formData();
      const docTypeField = formData.get('documentType');
      if (docTypeField && typeof docTypeField === 'string') {
        if (docTypeField === 'regulatory_document') {
          if (!isAdmin) {
            return createResponse({ 
              success: false, 
              error: 'Only admin users can upload regulatory documents' 
            }, 403);
          }
          documentType = 'regulatory_document';
        } else if (docTypeField === 'user_document') {
          documentType = 'user_document';
        }
      }
    }

    const result = await handleUpload(req, user.id, supabase, documentType, formData);
    console.log('Upload completed successfully:', result);
    fetch(`${Deno.env.get('SUPABASE_URL') || Deno.env.get('URL')}/functions/v1/doc-parser`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || Deno.env.get('SERVICE_ROLE_KEY')}`
      },
      body: JSON.stringify({ docId: result.document.id })
    }).then(res => {
      console.log("\ud83d\udef0\ufe0f doc-parser triggered, status:", res.status);
    }).catch(err => {
      console.error("\u26a0\ufe0f Error triggering doc-parser:", err);
    });
    return createResponse({ success: true, result });

  } catch (err: unknown) {
    const errorDetails = err instanceof Error ? {
      message: err.message,
      name: err.name,
      stack: err.stack
    } : 'Unknown error';
    
    console.error('Error processing request:', errorDetails);

    if (err instanceof Error) {
      switch (err.message) {
        case 'Missing required environment variables':
          return createResponse({ 
            success: false, 
            error: 'Server configuration error',
            details: errorDetails
          }, 500);
        
        case 'Invalid form data':
        case 'File missing':
          return createResponse({ 
            success: false, 
            error: err.message,
            details: errorDetails
          }, 400);
        
        case 'Upload to storage failed':
          return createResponse({ 
            success: false, 
            error: 'Upload to storage failed',
            details: errorDetails
          }, 500);
      }
    }

    return createResponse({ 
      success: false, 
      error: 'Internal server error',
      details: errorDetails
    }, 500);
  }

  
});