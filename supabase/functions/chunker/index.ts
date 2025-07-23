import { serve } from "http/server";
import { createClient } from '@supabase/supabase-js';
import { corsHeaders } from "../_shared/cors.ts";
import { updateDocumentStatus } from "../_shared/status.ts";
import { DocumentChunker } from "./document_chunker.ts";
import { ChunkerResponse, ChunkerResponseSchema } from "./types.ts";

declare global {
  interface Window {
    Deno: {
      env: {
        get(key: string): string | undefined;
      };
    };
  }
}

const Deno = window.Deno;

serve(async (req: Request) => {
  console.log("🚀 Starting chunker function");
  let docId: string | undefined;
  let supabase: ReturnType<typeof createClient>;

  try {
    // Initialize Supabase client
    console.log("🔄 Initializing Supabase client");
    supabase = createClient(
      Deno.env.get("SUPABASE_URL") || Deno.env.get("URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || Deno.env.get("SERVICE_ROLE_KEY")!
    );
    console.log("✅ Supabase client initialized");

    // Validate request method
    if (req.method !== "POST") {
      return new Response(
        JSON.stringify(ChunkerResponseSchema.parse({
          success: false,
          message: "Method not allowed",
          chunks: 0,
          error: "Only POST requests are supported"
        })), 
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
        JSON.stringify(ChunkerResponseSchema.parse({
          success: false,
          message: "Missing docId",
          chunks: 0,
          error: "Document ID is required"
        })),
        { status: 400, headers: corsHeaders }
      );
    }

    // Set initial chunking status
    await updateDocumentStatus(supabase, docId, "chunking");

    // Get document details from database
    console.log("🔍 Fetching document details from database");
    const { data: docDetails, error: dbError } = await supabase
      .schema('documents')
      .from('documents')
      .select('source_path, parsed_path, name, owner')
      .eq('id', docId)
      .single();

    if (dbError || !docDetails) {
      const error = dbError?.message || 'Document not found';
      await updateDocumentStatus(supabase, docId, "chunking-failed", dbError, "Database error or document not found");
      throw new Error(`Failed to get document details: ${error}`);
    }

    if (!docDetails.parsed_path) {
      await updateDocumentStatus(supabase, docId, "chunking-failed", "Missing parsed_path", "Document not parsed yet");
      throw new Error('Document has not been parsed yet - parsed_path is missing');
    }

    // Download parsed content
    console.log("📥 Downloading parsed content from storage");
    const { data: parsedContent, error: downloadError } = await supabase.storage
      .from("files")
      .download(docDetails.parsed_path);

    if (downloadError || !parsedContent) {
      await updateDocumentStatus(supabase, docId, "chunking-failed", downloadError, "Failed to download parsed content");
      throw new Error(`Failed to download parsed content: ${downloadError?.message || 'Unknown error'}`);
    }

    // Parse the JSON content
    const parsedData = JSON.parse(await parsedContent.text());
    console.log("✅ Parsed content downloaded and decoded");

    // Initialize document chunker (no API key needed for markdown parsing)
    const chunker = new DocumentChunker();

    // Generate chunks
    console.log("🔄 Generating chunks from parsed content");
    const { chunks, metadata } = await chunker.chunkDocument(parsedData.markdown);
    console.log(`✅ Generated ${chunks.length} chunks`);

    // Insert chunks into database
    console.log("💾 Inserting chunks into database");
    const { error: insertError } = await supabase
      .schema('documents')
      .from('document_chunks')
      .insert(chunks.map((chunk, idx) => ({
        doc_id: docId,
        chunk_index: idx,
        section_path: chunk.path,
        section_title: chunk.title,
        content: chunk.text,
        chunked_at: new Date().toISOString()
      })));

    if (insertError) {
      await updateDocumentStatus(supabase, docId, "chunking-failed", insertError, "Failed to insert chunks");
      throw new Error(`Failed to insert chunks: ${insertError.message}`);
    }

    console.log("✅ Chunks inserted successfully");

    // Update document status to chunked
    await updateDocumentStatus(supabase, docId, "chunked");

    // Handoff to embedder (no await = fire-and-forget)
    fetch(`${Deno.env.get('SUPABASE_URL') || Deno.env.get('URL')}/functions/v1/embedder`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || Deno.env.get('SERVICE_ROLE_KEY')}`
      },
      body: JSON.stringify({ docId })
    }).then(res => {
      console.log("🛰️ embedder triggered, status:", res.status);
    }).catch(err => {
      console.error("⚠️ Error triggering embedder:", err);
    });

    // Return success response
    return new Response(
      JSON.stringify(ChunkerResponseSchema.parse({
        success: true,
        message: "Document chunked successfully",
        chunks: chunks.length,
        metadata
      })), 
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );

  } catch (error) {
    console.error("❌ Unhandled error:", error);
    
    // Update status to chunking-failed if we have docId and haven't already set a failed status
    if (docId && supabase) {
      await updateDocumentStatus(supabase, docId, "chunking-failed", error, "Unhandled error");
    }
    
    return new Response(
      JSON.stringify(ChunkerResponseSchema.parse({
        success: false,
        message: "Internal server error",
        chunks: 0,
        error: error instanceof Error ? error.message : "Unknown error"
      })),
      { status: 500, headers: corsHeaders }
    );
  }
});
