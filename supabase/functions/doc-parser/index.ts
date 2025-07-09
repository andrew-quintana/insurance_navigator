import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { corsHeaders } from "../_shared/cors.ts";

const LLAMAPARSE_API_KEY = Deno.env.get("LLAMAPARSE_API_KEY");

serve(async (req: Request) => {
    const supabase = createClient(
        Deno.env.get("SUPABASE_URL") || Deno.env.get("URL")!,
        Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || Deno.env.get("SERVICE_ROLE_KEY")!
    );

    if (req.method !== "POST") {
        return new Response("Method Not Allowed", { status: 405 });
    }

    const { docId } = await req.json();

    if (!docId) {
        return new Response("Missing docId", { status: 400 });
    }

    const { data: doc, error } = await supabase
        .schema("documents")
        .from("documents")
        .select("source_path, name")
        .eq("id", docId)
        .single();

    if (error || !doc) {
        console.error("Error fetching document:", error);
        return new Response("Document not found", { status: 404 });
    }

    const { data: fileBlob, error: fileError } = await supabase.storage
        .from("files")
        .download(doc.source_path);

    if (fileError || !fileBlob) {
        console.error("Failed to download file:", fileError);
        return new Response("File download failed", { status: 500 });
    }

    // Send to LlamaParse
    const llamaRes = await fetch("https://api.llamaparse.com/upload", {
    method: "POST",
    headers: {
        "Authorization": `Bearer ${LLAMAPARSE_API_KEY}`,
    },
    body: fileBlob
    });

    const llamaData = await llamaRes.json();

    console.log("LlamaParse response:", llamaData);
    const parsedContent = JSON.stringify(llamaData, null, 2);  // Pretty-print for readability
    const parsedFileName = `user/${doc.owner}/parsed/${Date.now()}-${doc.name.replace(/\.[^/.]+$/, ".json")}`;

    // Upload the parsed file to the files bucket
    const { error: uploadParsedError } = await supabase.storage
        .from("files")
        .upload(parsedFileName, parsedContent, {
        contentType: "application/json"
    });

    if (uploadParsedError) {
        console.error("Failed to upload parsed file:", uploadParsedError);
        return new Response("Failed to save parsed file", { status: 500 });
    }

    // Update the document status to parsed
    const { data: updateDoc, error: updateDocError } = await supabase
        .schema("documents")
        .from("documents")
        .update({
        processing_status: "parsed"
        })
        .eq("id", docId);

    if (updateDocError) {
        console.error("Failed to update document status:", updateDocError);
        return new Response("Failed to update document status", { status: 500 });
    }

  return new Response(JSON.stringify({
    success: true,
    docId,
    llamaData
  }), {
    headers: corsHeaders
  });
});