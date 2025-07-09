    import { serve } from "http/server";
import { createClient } from '@supabase/supabase-js';
import { corsHeaders } from "../_shared/cors.ts";
import { Anthropic } from '@anthropic-ai/sdk';
import { chunkDocument } from './chunk.ts';
import { getPipelineFilename } from "../_shared/date_utils.ts";

const ANTHROPIC_API_KEY = Deno.env.get("ANTHROPIC_API_KEY");

serve(async (req: Request) => {
    console.log("🚀 Starting chunker function");
    console.log("📝 Configuration check:");
    console.log("- ANTHROPIC_API_KEY present:", !!ANTHROPIC_API_KEY);
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
            .select('source_path, name, owner, uploaded_at, parsed_path')
            .eq('id', docId)
            .single();

        if (dbError || !docDetails) {
            throw new Error(`Failed to get document details: ${dbError?.message || 'Document not found'}`);
        }
        console.log("✅ Document details retrieved:", { path: docDetails.source_path, name: docDetails.name });

        if (!docDetails.parsed_path) {
            throw new Error('Document has not been parsed yet - parsed_path is missing');
        }

        // Download parsed document using the stored path
        console.log("📥 Downloading parsed file from:", docDetails.parsed_path);
        const { data: parsedFile, error: fileError } = await supabase.storage
            .from("files")
            .download(docDetails.parsed_path);

        if (fileError || !parsedFile) {
            console.error("❌ Failed to download parsed file:", fileError);
            return new Response("Parsed file not found", { status: 404 });
        }
        console.log("✅ Parsed file downloaded successfully");

        // Parse the JSON content
        const parsedContent = await parsedFile.text();
        const documentData = JSON.parse(parsedContent);

        // Initialize Anthropic client
        console.log("🤖 Initializing Anthropic client");
        const anthropic = new Anthropic({
            apiKey: ANTHROPIC_API_KEY
        });

        // Process document chunks
        console.log("🔄 Processing document chunks");
        const chunks = await chunkDocument(documentData, anthropic);
        
        // Prepare chunks for database insertion
        console.log("💾 Preparing chunks for database");
        const chunksToInsert = chunks.map((chunk, index) => {
            // Convert path array to hierarchical levels
            const path = chunk.path || [];
            return {
                id: crypto.randomUUID(),
                doc_id: docId,
                chunk_index: chunk.chunk_index,
                section_title: chunk.title,
                section_path: path,
                content: chunk.text,
                embedding: null, // Will be populated later
                page_start: chunk.pages?.[0] || null,
                page_end: chunk.pages?.[1] || null,
                chunked_at: new Date().toISOString()
            };
        });

        // Insert chunks into database
        console.log("📝 Inserting chunks into database");
        const { error: insertError } = await supabase
            .schema("documents")
            .from("document_chunks")
            .insert(chunksToInsert);

        if (insertError) {
            console.error("❌ Failed to insert chunks:", insertError);
            throw new Error(`Failed to insert chunks: ${insertError.message}`);
        }
        console.log("✅ Chunks inserted successfully");

        // Update document status
        console.log("📝 Updating document status");
        const { error: updateError } = await supabase
            .schema("documents")
            .from("documents")
            .update({
                processing_status: "chunked",
            })
            .eq("id", docId);

        if (updateError) {
            console.error("❌ Error updating document status:", updateError);
            throw new Error(`Failed to update document status: ${updateError.message}`);
        }

        console.log("✅ Document status updated to 'chunked'");


        // Handoff to embedder (no await = fire-and-forget)
        fetch(`${Deno.env.get('SUPABASE_URL') || Deno.env.get('URL')}/functions/v1/embedder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || Deno.env.get('SERVICE_ROLE_KEY')}`
            },
            body: JSON.stringify({ docId: docId })
        }).then(res => {
            console.log("🛰️ embedder triggered, status:", res.status);
        }).catch(err => {
            console.error("⚠️ Error triggering embedder:", err);
        });

        return new Response(JSON.stringify({
            success: true,
            docId,
            chunkCount: chunksToInsert.length
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
