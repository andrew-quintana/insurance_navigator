import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { corsHeaders } from "../_shared/cors.ts";
import { getPipelineFilename } from "../_shared/date_utils.ts";
import { updateDocumentStatus } from "../_shared/status.ts";

// Initialize Supabase client
const supabase = createClient(
  Deno.env.get('SUPABASE_URL') || Deno.env.get('URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || Deno.env.get('SERVICE_ROLE_KEY')!
);

serve(async (req: Request) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    console.log('📥 Received webhook request');
    
    // Verify webhook token
    const token = new URL(req.url).searchParams.get("token");
    if (token !== Deno.env.get("LLAMAPARSE_WEBHOOK_SECRET")) {
      console.error('❌ Invalid webhook token');
      return new Response('Unauthorized', { 
        status: 401,
        headers: corsHeaders
      });
    }
    
    // Parse webhook payload
    const payload = await req.json();
    //console.log('📄 Webhook payload:', JSON.stringify(payload, null, 2));
    // Log just the keys from the webhook payload
    console.log('🔑 Webhook payload keys:', Object.keys(payload));

    // Validate payload
    if (!payload.jobId) {
      throw new Error('Missing jobId in webhook payload');
    }

    // Get document by job_id
    const { data: document, error: docError } = await supabase
      .schema("documents")
      .from("documents")
      .select("*")
      .eq("llama_parse_job_id", payload.jobId)
      .single();

    if (docError || !document) {
      console.error('❌ Document not found for jobId:', payload.jobId);
      throw new Error(`Document not found for jobId: ${payload.jobId}`);
    }

    // Handle webhook payload
    if (payload.md || payload.json) {
      console.log('✅ LlamaParse processing successful');

      // Save parsed content - we have it directly in the payload
      const parsedContent = JSON.stringify({
        markdown: payload.md,
        text: payload.txt,
        json: payload.json,
        xlsx: payload.xlsx,
        images: payload.images
      }, null, 2);

      const parsedFileName = `user/${document.owner}/parsed/${
        getPipelineFilename(document.uploaded_at, document.name.replace(/\.[^/.]+$/, ".json"))
      }`;

      console.log("📤 Uploading parsed file");
      const { error: uploadParsedError } = await supabase.storage
        .from("files")
        .upload(parsedFileName, parsedContent, {
          contentType: "application/json"
        });

      if (uploadParsedError) {
        await updateDocumentStatus(supabase, document.id, "parsing-failed", uploadParsedError, "Failed to save parsed file");
        throw new Error(`Failed to save parsed file: ${uploadParsedError.message}`);
      }
      console.log("✅ Parsed file uploaded successfully");

      // Update document status and parsed path
      await updateDocumentStatus(supabase, document.id, "parsed");
      
      // Update parsed_path separately
      const { error: updatePathError } = await supabase
        .schema("documents")
        .from("documents")
        .update({
          parsed_at: new Date().toISOString(),
          parsed_path: parsedFileName
        })
        .eq("id", document.id);

      if (updatePathError) {
        await updateDocumentStatus(supabase, document.id, "parsing-failed", updatePathError, "Failed to update parsed path");
        throw new Error(`Failed to update document status: ${updatePathError.message}`);
      }

      console.log("✅ Document status updated to 'parsed'");

      // Handoff to chunker (no await = fire-and-forget)
      fetch(`${Deno.env.get('SUPABASE_URL') || Deno.env.get('URL')}/functions/v1/chunker`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || Deno.env.get('SERVICE_ROLE_KEY')}`
        },
        body: JSON.stringify({ docId: document.id })
      }).then(res => {
        console.log("🛰️ chunker triggered, status:", res.status);
      }).catch(err => {
        console.error("⚠️ Error triggering chunker:", err);
      });

    } else {
      console.error('❌ LlamaParse processing failed: No results in payload');
      await updateDocumentStatus(supabase, document.id, "parsing-failed", "No results in payload", "LlamaParse processing failed");
    }

    return new Response(JSON.stringify({ success: true }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('❌ Webhook processing error:', error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    );
  }
});