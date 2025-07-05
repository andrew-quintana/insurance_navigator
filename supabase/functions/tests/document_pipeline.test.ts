import { assertEquals, assertExists } from "https://deno.land/std@0.217.0/testing/asserts.ts";
import { createClient } from "@supabase/supabase-js";
import { processDocument } from "../doc-processor/processor.ts";
import { edgeConfig } from "../_shared/environment.ts";

Deno.test("Document Processing Pipeline", async (t) => {
  const config = await edgeConfig;
  const client = createClient(config.supabaseUrl, config.supabaseKey);
  const testUserId = config.testUserId;

  await t.step("processes documents correctly", async () => {
    // Create test document
    const { data: doc } = await client
      .from("documents")
      .insert({
        user_id: testUserId,
        filename: "test.pdf",
        content_type: "application/pdf",
        status: "uploaded",
        storage_path: `${testUserId}/test.pdf`
      })
      .select()
      .single();

    assertExists(doc, "Document should be created");

    // Process the document
    const result = await processDocument(
      testUserId,
      doc.id,
      {
        content: "Test document content",
        metadata: {
          extractionMethod: "test"
        }
      }
    );
    
    assertEquals(result.success, true, "Processing should succeed");
    assertEquals(result.document_id, doc.id, "Document ID should match");
    assertEquals(result.status, "processed", "Document should be processed");
    assertEquals(typeof result.metadata?.extractionMethod, "string", "Should have extraction method");

    // Verify document status
    const { data: updatedDoc } = await client
      .from("documents")
      .select()
      .eq("id", doc.id)
      .single();

    assertExists(updatedDoc, "Document should still exist");
    assertEquals(updatedDoc.status, "processed", "Document status should be updated");

    // Cleanup
    await client.from("documents").delete().eq("id", doc.id);
  });

  await t.step("handles errors gracefully", async () => {
    const nonExistentId = "99999999-9999-4999-a999-999999999999";
    const result = await processDocument(
      testUserId,
      nonExistentId,
      {
        content: "Test document content",
        metadata: {
          extractionMethod: "test"
        }
      }
    );

    assertEquals(result.success, false, "Should fail for non-existent document");
    assertExists(result.error, "Should have error message");
  });
}); 