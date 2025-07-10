import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { createClient, SupabaseClient } from 'https://esm.sh/@supabase/supabase-js@2.39.0';
import { corsHeaders } from "../_shared/cors.ts";
import { updateDocumentStatus } from "../_shared/status.ts";

declare global {
  interface Window {
    Deno: {
      env: {
        get(key: string): string | undefined;
      };
    };
  }
}

interface DocumentChunk {
  id: string;
  content: string;
}

interface OpenAIEmbeddingResponse {
  data: [{
    embedding: number[];
  }];
}

const Deno = window.Deno;

serve(async (req: Request) => {
  console.log("🚀 Starting embedder function");
  let docId: string | undefined;
  
  // Initialize Supabase client
  console.log("🔄 Initializing Supabase client");
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL") || Deno.env.get("URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || Deno.env.get("SERVICE_ROLE_KEY")!
  );
  console.log("✅ Supabase client initialized");

  try {
    // Validate request method
    if (req.method !== "POST") {
      return new Response(
        JSON.stringify({
          success: false,
          message: "Method not allowed",
          error: "Only POST requests are supported"
        }), 
        { status: 405, headers: corsHeaders }
      );
    }

    // Parse request body
    console.log("📥 Parsing request body");
    const body = await req.json() as { docId: string };
    docId = body.docId;
    console.log("📄 Processing document:", docId);

    if (!docId) {
      return new Response(
        JSON.stringify({
          success: false,
          message: "Missing docId",
          error: "Document ID is required"
        }),
        { status: 400, headers: corsHeaders }
      );
    }

    // Set initial embedding status
    await updateDocumentStatus(supabase, docId, "embedding");

    // Get document chunks
    console.log("🔍 Fetching document chunks from database");
    const { data: chunks, error: chunksError } = await supabase
      .schema('documents')
      .from('document_chunks')
      .select('id, content')
      .eq('doc_id', docId)
      .is('embedding', null);

    console.log("🔍 Chunks:", chunks);

    if (chunksError) {
      await updateDocumentStatus(supabase, docId, "embedding-failed", chunksError, "Failed to fetch chunks");
      throw new Error(`Failed to get document chunks: ${chunksError.message}`);
    }

    if (!chunks || chunks.length === 0) {
      await updateDocumentStatus(supabase, docId, "embedding-failed", "No chunks found", "No chunks found to embed");
      throw new Error('No chunks found to embed');
    }

    console.log(`📊 Found ${chunks.length} chunks to embed`);

    // Process chunks in batches to avoid rate limits
    const batchSize = 20;
    let processedChunks = 0;

    for (let i = 0; i < chunks.length; i += batchSize) {
      const batch = chunks.slice(i, Math.min(i + batchSize, chunks.length));
      console.log(`\n🔄 Processing batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(chunks.length / batchSize)}`);

      // Generate embeddings for batch
      const embeddingPromises = batch.map(async (chunk: DocumentChunk) => {
        try {
          console.log(`🧠 Generating embedding for chunk ${chunk.id}...`);
          const response = await fetch('https://api.openai.com/v1/embeddings', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${Deno.env.get('OPENAI_API_KEY')}`
            },
            body: JSON.stringify({
              input: chunk.content,
              model: "text-embedding-3-small",
              dimensions: 1536
            })
          });

          if (!response.ok) {
            const errorText = await response.text();
            console.error(`❌ Embedding failed for chunk ${chunk.id}:`, {
              status: response.status,
              error: errorText
            });
            throw new Error(`Embedding generation failed: ${response.status}`);
          }

          const data = await response.json() as OpenAIEmbeddingResponse;
          console.log(`✅ Embedding generated for chunk ${chunk.id}`);

          // Update chunk with embedding
          const { error: updateError } = await supabase
            .schema('documents')
            .from('document_chunks')
            .update({ 
              embedding: data.data[0].embedding,
              embedded_at: new Date().toISOString()
            })
            .eq('id', chunk.id);

          if (updateError) {
            throw new Error(`Failed to update chunk ${chunk.id}: ${updateError.message}`);
          }

          processedChunks++;
          return true;
        } catch (error) {
          console.error(`❌ Error processing chunk ${chunk.id}:`, error);
          return false;
        }
      });

      // Wait for batch to complete
      const results = await Promise.all(embeddingPromises);
      const failedChunks = results.filter((r: boolean) => !r).length;
      
      if (failedChunks > 0) {
        console.warn(`⚠️ ${failedChunks} chunks failed in this batch`);
      }
    }

    // Check if all chunks were processed
    if (processedChunks === 0) {
      await updateDocumentStatus(supabase, docId, "embedding-failed", "All chunks failed", "Failed to generate embeddings for any chunks");
      throw new Error('Failed to process any chunks');
    }

    if (processedChunks < chunks.length) {
      console.warn(`⚠️ Only ${processedChunks}/${chunks.length} chunks were successfully processed`);
    }

    // Update document status to embedded
    await updateDocumentStatus(supabase, docId, "embedded");

    // Return success response
    return new Response(
      JSON.stringify({
        success: true,
        message: "Document embedded successfully",
        totalChunks: chunks.length,
        processedChunks
      }), 
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );

  } catch (error) {
    console.error("❌ Unhandled error:", error);
    
    // Update status to embedding-failed if we have docId
    if (docId) {
      await updateDocumentStatus(supabase, docId, "embedding-failed", error, "Unhandled error");
    }
    
    return new Response(
      JSON.stringify({
        success: false,
        message: "Internal server error",
        error: error instanceof Error ? error.message : "Unknown error"
      }),
      { status: 500, headers: corsHeaders }
    );
  }
}); 