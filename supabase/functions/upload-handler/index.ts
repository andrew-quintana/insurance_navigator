import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { corsHeaders } from "../_shared/cors.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.3";
import { handleUpload, ParsedContent, ProcessingResult, UploadHandlerError } from "./processor.ts";
import { edgeConfig } from "../_shared/environment.ts";

interface RequestBody {
  userId: string;
  documentId: string;
  content: string;
  metadata: {
    extractionMethod: string;
    contentType: string;
    size: number;
    filename: string;
  };
}

async function logExecution(
  supabaseClient: any,
  functionName: string,
  requestId: string,
  startTime: number,
  status: string,
  error?: string,
  metadata?: any
) {
  const executionTime = Date.now() - startTime;
  const memoryUsage = Deno.memoryUsage().heapUsed / 1024 / 1024; // Convert to MB

  try {
    await supabaseClient
      .from('function_executions')
      .insert({
        function_name: functionName,
        request_id: requestId,
        status,
        execution_time_ms: executionTime,
        memory_usage_mb: memoryUsage,
        error_message: error,
        metadata
      });
  } catch (logError) {
    console.error('Failed to log execution:', logError);
  }
}

serve(async (req) => {
  const startTime = Date.now();
  const requestId = crypto.randomUUID();

  try {
    // Handle preflight CORS
    if (req.method === 'OPTIONS') {
      return new Response('ok', { headers: corsHeaders });
    }

    // Parse request body
    let body: RequestBody;
    try {
      body = await req.json();
    } catch (error) {
      console.error('Failed to parse request body:', error);
      return new Response(
        JSON.stringify({ error: "Invalid request body" }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 400
        }
      );
    }

    // Validate request body
    if (!body.userId || !body.documentId || !body.metadata?.filename) {
      return new Response(
        JSON.stringify({ error: "userId, documentId, and metadata.filename are required" }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 400
        }
      );
    }

    // Initialize Supabase client
    let supabaseClient;
    try {
      supabaseClient = createClient(
        edgeConfig.supabaseUrl,
        edgeConfig.supabaseKey,
        {
          auth: {
            autoRefreshToken: false,
            persistSession: false,
            detectSessionInUrl: false
          }
        }
      );
    } catch (error) {
      console.error('Failed to initialize Supabase client:', error);
      return new Response(
        JSON.stringify({ error: "Service unavailable" }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 503
        }
      );
    }

    // Log processing start
    await logExecution(
      supabaseClient,
      'upload-handler',
      requestId,
      startTime,
      'started',
      undefined,
      { userId: body.userId, documentId: body.documentId }
    );

    console.log(`[${body.documentId}] Starting document processing in edge function`);

    // Process the document
    try {
      const result = await handleUpload(
        body.userId,
        body.documentId,
        {
          content: body.content,
          metadata: body.metadata
        },
        supabaseClient
      );

      // Log successful completion
      await logExecution(
        supabaseClient,
        'upload-handler',
        requestId,
        startTime,
        'completed',
        undefined,
        { userId: body.userId, documentId: body.documentId, result }
      );

      return new Response(
        JSON.stringify(result),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: result.success ? 200 : (result.statusCode || 500)
        }
      );
    } catch (error) {
      console.error('Error processing document:', error);
      const statusCode = error instanceof UploadHandlerError ? error.statusCode : 500;
      const errorMessage = error instanceof Error ? error.message : 'Internal server error';

      // Log error
      await logExecution(
        supabaseClient,
        'upload-handler',
        requestId,
        startTime,
        'error',
        errorMessage
      );

      return new Response(
        JSON.stringify({ error: errorMessage }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: statusCode
        }
      );
    }
  } catch (error) {
    console.error('Unhandled error:', error);
    return new Response(
      JSON.stringify({ error: "Internal server error" }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 500
      }
    );
  }
});