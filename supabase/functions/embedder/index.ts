import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { corsHeaders } from "../_shared/cors.ts";
import OpenAI from "https://esm.sh/openai@4.28.0";

const OPENAI_API_KEY = Deno.env.get("OPENAI_API_KEY");
const BATCH_SIZE = 100;

serve(async (req: Request) => {
    console.log("🚀 Starting embedder function");
    console.log("📝 Configuration check:");
    console.log("- OPENAI_API_KEY present:", !!OPENAI_API_KEY);
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

        // Initialize OpenAI client
        console.log("🤖 Initializing OpenAI client");
        const openai = new OpenAI({
            apiKey: OPENAI_API_KEY
        });

        // Get unembedded chunks from database
        console.log("🔍 Fetching unembedded chunks");
        const { data: chunks, error: chunksError } = await supabase
            .schema('documents')
            .from('document_chunks')
            .select('id, content, chunk_index, section_title, section_path, page_start, page_end')
            .eq('doc_id', docId)
            .is('embedding', null);

        if (chunksError) {
            console.error("❌ Failed to fetch chunks:", chunksError);
            throw new Error(`Failed to fetch chunks: ${chunksError.message}`);
        }

        if (!chunks || chunks.length === 0) {
            console.log("ℹ️ No unembedded chunks found");
            return new Response(JSON.stringify({
                success: true,
                message: "No chunks to embed"
            }), {
                headers: corsHeaders
            });
        }

        console.log(`📊 Found ${chunks.length} chunks to embed`);

        // Process chunks in batches
        const batchCount = Math.ceil(chunks.length / BATCH_SIZE);
        console.log(`🔄 Processing ${batchCount} batches of up to ${BATCH_SIZE} chunks each`);

        for (let i = 0; i < chunks.length; i += BATCH_SIZE) {
            const batch = chunks.slice(i, i + BATCH_SIZE);
            console.log(`📦 Processing batch ${Math.floor(i / BATCH_SIZE) + 1}/${batchCount}`);

            try {
                // Generate embeddings for batch
                const embeddingResponse = await openai.embeddings.create({
                    model: "text-embedding-3-small",
                    input: batch.map(chunk => chunk.content),
                    encoding_format: "float"
                });

                // Prepare updates with only the fields we want to change
                const updates = batch.map((chunk, index) => ({
                    id: chunk.id,
                    embedding: embeddingResponse.data[index].embedding,
                    embedded_at: new Date().toISOString()
                }));

                // Update database in batch - use update instead of upsert
                console.log("💾 Updating chunk embeddings in database");
                for (const update of updates) {
                    const { error: updateError } = await supabase
                        .schema('documents')
                        .from('document_chunks')
                        .update({
                            embedding: update.embedding,
                            embedded_at: update.embedded_at
                        })
                        .eq('id', update.id);

                    if (updateError) {
                        console.error("❌ Failed to update chunk:", updateError);
                        throw new Error(`Failed to update chunk: ${updateError.message}`);
                    }
                }

                console.log(`✅ Successfully processed batch ${Math.floor(i / BATCH_SIZE) + 1}`);
            } catch (error) {
                console.error(`❌ Error processing batch ${Math.floor(i / BATCH_SIZE) + 1}:`, error);
                throw error;
            }
        }

        // Verify all chunks are embedded
        console.log("🔍 Verifying embeddings");
        const { data: unembeddedCount, error: verifyError } = await supabase
            .schema('documents')
            .from('document_chunks')
            .select('id', { count: 'exact', head: true })
            .eq('doc_id', docId)
            .is('embedding', null);

        if (verifyError) {
            console.error("❌ Failed to verify embeddings:", verifyError);
            throw new Error(`Failed to verify embeddings: ${verifyError.message}`);
        }

        if (unembeddedCount === 0) {
            console.log("📝 Updating document status");
            const { error: updateError } = await supabase
                .schema("documents")
                .from("documents")
                .update({
                    processing_status: "embedded",
                })
                .eq("id", docId);

            if (updateError) {
                console.error("❌ Error updating document status:", updateError);
                throw new Error(`Failed to update document status: ${updateError.message}`);
            }
        }

        console.log("🎉 Processing completed successfully");
        return new Response(JSON.stringify({
            success: true,
            docId,
            chunksProcessed: chunks.length
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