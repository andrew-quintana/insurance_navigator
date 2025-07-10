import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { corsHeaders } from "../_shared/cors.ts";
import { updateDocumentStatus } from "../_shared/status.ts";

const LLAMAPARSE_API_KEY = Deno.env.get("LLAMAPARSE_API_KEY");

serve(async (req: Request) => {
    console.log("🚀 Starting doc-parser function");
    console.log("📝 Configuration check:");
    console.log("- LLAMAPARSE_API_KEY present:", !!LLAMAPARSE_API_KEY);
    console.log("- SUPABASE_URL present:", !!Deno.env.get("SUPABASE_URL"));
    console.log("- SERVICE_ROLE_KEY present:", !!Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"));

    let docId: string | undefined;
    let supabase: ReturnType<typeof createClient>;

    try {
        console.log("🔄 Initializing Supabase client");
        const supabaseUrl = Deno.env.get("SUPABASE_URL") || Deno.env.get("URL")!;
        supabase = createClient(
            supabaseUrl,
            Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || Deno.env.get("SERVICE_ROLE_KEY")!
        );
        console.log("✅ Supabase client initialized");

        if (req.method !== "POST") {
            console.log("❌ Invalid method:", req.method);
            return new Response("Method Not Allowed", { status: 405 });
        }

        console.log("📥 Parsing request body");
        const body = await req.json();
        docId = body.docId;
        console.log("📄 Processing document:", docId);

        if (!docId) {
            console.log("❌ Missing docId in request");
            return new Response("Missing docId", { status: 400 });
        }

        // Set initial parsing status
        await updateDocumentStatus(supabase, docId, "parsing");

        // Get document details from database
        console.log("🔍 Fetching document details from database");
        const { data: docDetails, error: dbError } = await supabase
            .schema('documents')
            .from('documents')
            .select('source_path, name, owner, uploaded_at')
            .eq('id', docId)
            .single();

        if (dbError || !docDetails) {
            await updateDocumentStatus(supabase, docId, "parsing-failed", dbError, "Database error or document not found");
            throw new Error(`Failed to get document details: ${dbError?.message || 'Document not found'}`);
        }
        console.log("✅ Document details retrieved:", { path: docDetails.source_path, name: docDetails.name });

        console.log("📥 Downloading file from storage");
        const { data: fileBlob, error: fileError } = await supabase.storage
            .from("files")
            .download(docDetails.source_path);

        if (fileError || !fileBlob) {
            await updateDocumentStatus(supabase, docId, "parsing-failed", fileError, "Failed to download file from storage");
            return new Response("File download failed", { status: 500 });
        }
        console.log("✅ File downloaded successfully");

        console.log("🔄 Sending file to LlamaParse");
        console.log("- File size:", fileBlob.size, "bytes");
        console.log("- Content type:", fileBlob.type);

        // Get base URL and determine webhook URL based on environment
        const environment = Deno.env.get('ENVIRONMENT') || 'development';
        let webhookUrl: string;

        switch (environment) {
            case 'development':
                const ngrokUrl = Deno.env.get('NGROK_URL');
                if (!ngrokUrl) {
                    throw new Error('NGROK_URL environment variable must be set in development');
                }
                webhookUrl = `${ngrokUrl}/functions/v1/processing-webhook?token=${Deno.env.get("LLAMAPARSE_WEBHOOK_SECRET")}`;
                break;
            
            case 'staging':
            case 'production':
                webhookUrl = `${supabaseUrl}/functions/v1/processing-webhook?token=${Deno.env.get("LLAMAPARSE_WEBHOOK_SECRET")}`;
                break;
            
            default:
                throw new Error(`Unknown environment: ${environment}`);
        }

        console.log(`🌍 Environment: ${environment}`);
        console.log(`🔗 Webhook URL: ${webhookUrl}`);

        // Create the FormData object
        const formData = new FormData();
        formData.append('file', fileBlob, docDetails.name);

        // Add required fields directly
        formData.append('result_type', 'markdown');
        formData.append('parsing_mode', 'balanced');
        formData.append('webhook_url', webhookUrl);

        console.log('📤 Sending to LlamaParse API with config:', {
            result_type: formData.get('result_type'),
            parsing_mode: formData.get('parsing_mode'),
            webhook_url: formData.get('webhook_url'),
            file_name: formData.get('file')?.name
        });
        
        try {
            const llamaRes = await fetch('https://api.cloud.llamaindex.ai/api/v1/parsing/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${LLAMAPARSE_API_KEY}`,
                    'accept': 'application/json'
                },
                body: formData
            });

            if (!llamaRes.ok) {
                throw new Error(`LlamaParse API error: ${llamaRes.status} ${await llamaRes.text()}`);
            }

            const responseData = await llamaRes.json();
            const job_id = responseData.job_id || responseData.id || responseData.data?.job_id;
            console.log('📋 LlamaParse job ID:', job_id);

            if (!job_id) {
                throw new Error('No job ID returned from LlamaParse API');
            }

            // Update document with LlamaParse job ID
            const { error: updateError } = await supabase
                .schema("documents")
                .from("documents")
                .update({ llama_parse_job_id: job_id })
                .eq("id", docId);

            if (updateError) {
                console.error('❌ Failed to update document with job ID:', updateError);
                throw new Error(`Failed to update document with job ID: ${updateError.message}`);
            }
            console.log('✅ Document updated with LlamaParse job ID');

            // Update document status to parsing - webhook will handle the rest
            await updateDocumentStatus(supabase, docId, 'parsing');
            
            return new Response(
                JSON.stringify({ success: true, job_id }),
                { 
                    status: 200,
                    headers: {
                        ...corsHeaders,
                        'Content-Type': 'application/json'
                    }
                }
            );

        } catch (error) {
            console.error('❌ Request error:', error);
            throw error;
        }

    } catch (error) {
        console.error("❌ Unhandled error:", error);
        
        // Update status to parsing-failed if we have docId and haven't already set a failed status
        if (docId && supabase) {
            await updateDocumentStatus(supabase, docId, "parsing-failed", error, "Unhandled error");
        }
        
        return new Response(JSON.stringify({
            success: false,
            error: error instanceof Error ? error.message : "Internal server error"
        }), {
            status: 500,
            headers: corsHeaders
        });
    }
});