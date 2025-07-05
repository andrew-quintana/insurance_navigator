import { assertEquals, assertExists } from "https://deno.land/std@0.217.0/testing/asserts.ts";
import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { SectionChunker } from "../chunking-service/section_chunker.ts";
import { ChunkingService } from "../chunking-service/service.ts";
import { edgeConfig } from "../_shared/environment.ts";
import { describe, it } from "std/testing/bdd.ts";
import type { DocumentChunk } from "../types/document.ts";

interface TestContext {
  step(name: string, fn: () => Promise<void>): Promise<void>;
}

Deno.test("Chunking Service", async (t: TestContext) => {
  let client: SupabaseClient;
  let chunker: SectionChunker;
  let chunkingService: ChunkingService;
  const testUserId = '00000000-0000-4000-a000-000000000000';

  // Setup
  const config = await edgeConfig;
  client = createClient(config.supabaseUrl, config.supabaseKey);
  chunker = new SectionChunker(config.openaiApiKey);
  chunkingService = new ChunkingService(client, chunker);

  await t.step("should create chunks with proper metadata", async () => {
    const testContent = `# Test Document
      ## Section 1
      This is section 1 content.
      ## Section 2
      This is section 2 content.
      ### Subsection 2.1
      This is subsection 2.1 content.`;

    const chunks = await chunker.createChunks(testContent);
    assertExists(chunks, "Chunks should be created");
    assertEquals(chunks.length > 0, true, "Should have at least one chunk");

    chunks.forEach(chunk => {
      assertExists(chunk.metadata.section_title, "Section title should exist");
      assertExists(chunk.metadata.section_level, "Section level should exist");
      assertExists(chunk.metadata.chunk_index, "Chunk index should exist");
      assertExists(chunk.metadata.total_chunks, "Total chunks should exist");

      assertEquals(typeof chunk.metadata.section_level === 'number', true, "Section level should be a number");
      assertEquals(chunk.metadata.section_level > 0, true, "Section level should be positive");
      assertEquals(chunk.metadata.section_level <= 3, true, "Section level should be <= 3");
    });
  });

  await t.step("should preserve all content in chunks", async () => {
    const testContent = "This is a test document with multiple paragraphs.\n\nIt should be preserved in chunks.";
    const chunks = await chunker.createChunks(testContent);

    const allContent = chunks.map(c => c.pageContent).join("");
    const normalizedContent = allContent.replace(/\s+/g, ' ').trim();
    const normalizedTestText = testContent.replace(/\s+/g, ' ').trim();

    assertEquals(normalizedContent.includes(normalizedTestText), true, "All content should be preserved");
  });

  await t.step("should identify sections correctly", async () => {
    const testContent = `# Main Section
      ## Subsection 1
      Content 1
      ## Subsection 2
      Content 2
      ### Sub-subsection 2.1
      Content 3`;

    const chunks = await chunker.createChunks(testContent);

    // Check main sections (level 1)
    const mainSections = chunks.filter(c =>
      c.metadata.section_level === 1
    );
    assertEquals(mainSections.length > 0, true, "Should have main sections");

    // Check subsections (level 2)
    const subSections = chunks.filter(c =>
      c.metadata.section_level === 2
    );
    assertEquals(subSections.length > 0, true, "Should have subsections");

    // Check sub-subsections (level 3)
    const subSubSections = chunks.filter(c =>
      c.metadata.section_level === 3
    );
    assertEquals(subSubSections.length > 0, true, "Should have sub-subsections");
  });

  await t.step("processes document correctly", async () => {
    // Create a test document first
    const { data: doc } = await client
      .from("documents")
      .insert({
        user_id: config.testUserId,
        name: "test.pdf",
        content_type: "application/pdf",
        status: "parsed"
      })
      .select()
      .single();

    if (!doc) {
      throw new Error("Failed to create test document");
    }

    // Upload test content
    const content = JSON.stringify({ text: "Test document content" });
    await client.storage
      .from("documents")
      .upload(`buckets/parsed/${config.testUserId}/test.pdf`, content);

    // Process the document
    const result = await chunkingService.processDocument(doc.id);
    
    assertEquals(result.success, true);
    assertEquals(result.status, "chunked");
    assertEquals(result.document_id, doc.id);
    assertEquals(typeof result.metadata?.chunk_count, "number");
    assertEquals(Array.isArray(result.metadata?.sections), true);

    // Cleanup
    await client.from("documents").delete().eq("id", doc.id);
    await client.storage
      .from("documents")
      .remove([`buckets/parsed/${config.testUserId}/test.pdf`]);
  });
}); 