import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { corsHeaders } from "../_shared/cors.ts";

const LLAMAPARSE_API_KEY = Deno.env.get("LLAMAPARSE_API_KEY");

serve(async (req: Request) => {
    console.log("🚀 Starting doc-parser function");
    console.log("📝 Configuration check:");
    console.log("- LLAMAPARSE_API_KEY present:", !!LLAMAPARSE_API_KEY);
    console.log("- SUPABASE_URL present:", !!Deno.env.get("SUPABASE_URL"));
    console.log("- SERVICE_ROLE_KEY present:", !!Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"));

    try {
        console.log("🔄 Initializing Supabase client");
        const supabase = createClient(
            Deno.env.get("SUPABASE_URL") || Deno.env.get("URL")!,
            Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || Deno.env.get("SERVICE_ROLE_KEY")!
        );
        console.log("✅ Supabase client initialized");

        if (req.method !== "POST") {
            console.log("❌ Invalid method:", req.method);
            return new Response("Method Not Allowed", { status: 405 });
        }

        console.log("📥 Parsing request body");
        const { docId } = await req.json();
        console.log("📄 Processing document:", docId);

        if (!docId) {
            console.log("❌ Missing docId in request");
            return new Response("Missing docId", { status: 400 });
        }

        // Get document details from database
        console.log("🔍 Fetching document details from database");
        const { data: docDetails, error: dbError } = await supabase
            .schema('documents')
            .from('documents')
            .select('source_path, name, owner')
            .eq('id', docId)
            .single();

        if (dbError || !docDetails) {
            throw new Error(`Failed to get document details: ${dbError?.message || 'Document not found'}`);
        }
        console.log("✅ Document details retrieved:", { path: docDetails.source_path, name: docDetails.name });

        console.log("📥 Downloading file from storage");
        const { data: fileBlob, error: fileError } = await supabase.storage
            .from("files")
            .download(docDetails.source_path);

        if (fileError || !fileBlob) {
            console.error("❌ Failed to download file:", fileError);
            return new Response("File download failed", { status: 500 });
        }
        console.log("✅ File downloaded successfully");

        console.log("🔄 Sending file to LlamaParse");
        console.log("- File size:", fileBlob.size, "bytes");
        console.log("- Content type:", fileBlob.type);
        
        // First, create the FormData object
        const formData = new FormData();
        formData.append('file', fileBlob, docDetails.name);

        // Add parsing configuration (optional but recommended)
        const config = {
            result_type: "markdown",  // or "text" or "json"
            parsing_mode: "balanced" // "fast", "balanced", or "premium"
        };

        console.log('📤 Sending to LlamaParse API');
        const llamaRes = await fetch('https://api.cloud.llamaindex.ai/api/v1/parsing/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${LLAMAPARSE_API_KEY}`,
                'accept': 'application/json'
            },
            body: formData
        });

        if (!llamaRes.ok) {
            const errorText = await llamaRes.text();
            console.error('❌ LlamaParse API error:', errorText);
            throw new Error(`LlamaParse API error: ${errorText}`);
        }

        // Log the full response for debugging
        const responseData = await llamaRes.json();
        console.log('📄 Full LlamaParse response:', JSON.stringify(responseData, null, 2));

        // The job_id might be nested differently in the response
        const job_id = responseData.job_id || responseData.id || responseData.data?.job_id;
        
        if (!job_id) {
            console.error('⚠️ No job_id found in response. Response structure:', responseData);
            throw new Error('No job_id found in LlamaParse response');
        }

        console.log('✅ Upload successful, job_id:', job_id);

        // Poll for job completion
        let result;
        let pollCount = 0;
        const maxPolls = 60; // Maximum number of polls (60 seconds timeout)
        console.log('🔄 Starting polling for job completion');
        while (true) {
            pollCount++;
            console.log(`📡 Polling attempt ${pollCount}/${maxPolls}`);
            
            const statusRes = await fetch(`https://api.cloud.llamaindex.ai/api/v1/parsing/job/${job_id}`, {
                headers: {
                    'Authorization': `Bearer ${LLAMAPARSE_API_KEY}`,
                    'accept': 'application/json'
                }
            });
            
            const status = await statusRes.json();
            console.log(`ℹ️ Job status:`, status.status);
            
            if (status.status === 'SUCCESS') {
                console.log('✅ Parsing completed successfully, fetching results');
                // Get the results
                const resultRes = await fetch(`https://api.cloud.llamaindex.ai/api/v1/parsing/job/${job_id}/result/markdown`, {
                    headers: {
                        'Authorization': `Bearer ${LLAMAPARSE_API_KEY}`,
                        'accept': 'application/json'
                    }
                });
                result = await resultRes.json();
                console.log('📄 Results retrieved successfully');
                break;
            } else if (status.status === 'FAILED') {
                console.error('❌ Parsing job failed:', status.error);
                throw new Error(`Parsing failed: ${status.error}`);
            } else if (status.status === 'PROCESSING') {
                console.log('⏳ Document still processing...');
            } else {
                console.log('❓ Unknown status:', status.status);
            }
            
            if (pollCount >= maxPolls) {
                console.error('⚠️ Polling timeout reached');
                throw new Error('Polling timeout: Job took too long to complete');
            }
            
            // Wait before polling again
            console.log('⏱️ Waiting before next poll attempt...');
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        console.log('✅ Document parsing complete:', result);

        console.log("💾 Preparing to save parsed content");
        const parsedContent = JSON.stringify(responseData, null, 2);
        const parsedFileName = `user/${docDetails.owner}/parsed/${Date.now()}-${docDetails.name.replace(/\.[^/.]+$/, ".json")}`;
        console.log("- Target path:", parsedFileName);

        console.log("📤 Uploading parsed file");
        const { error: uploadParsedError } = await supabase.storage
            .from("files")
            .upload(parsedFileName, parsedContent, {
                contentType: "application/json"
            });

        if (uploadParsedError) {
            console.error("❌ Failed to upload parsed file:", uploadParsedError);
            return new Response("Failed to save parsed file", { status: 500 });
        }
        console.log("✅ Parsed file uploaded successfully");

        console.log("📝 Updating document status");
        const { data: updateDoc, error: updateDocError } = await supabase
            .schema("documents")
            .from("documents")
            .update({
                processing_status: "parsed"
            })
            .eq("id", docId);

        if (updateDocError) {
            console.error("❌ Failed to update document status:", updateDocError);
            return new Response("Failed to update document status", { status: 500 });
        }
        console.log("✅ Document status updated to 'parsed'");

        console.log("🎉 Processing completed successfully");
        return new Response(JSON.stringify({
            success: true,
            docId,
            responseData
        }), {
            headers: corsHeaders
        });

    } catch (error) {
        console.error("❌ Unhandled error:", error);
        return new Response(JSON.stringify({
            success: false,
            error: error.message || "Internal server error"
        }), {
            status: 500,
            headers: corsHeaders
        });
    }
});