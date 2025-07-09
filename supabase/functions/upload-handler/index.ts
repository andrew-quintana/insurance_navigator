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
    headers: Object.fromEntries(req.headers.entries())
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
    const result = await handleUpload(req, user.id, supabase);
    console.log('Upload completed successfully:', result);
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