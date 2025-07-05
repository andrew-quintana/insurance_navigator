/// <reference lib="deno.ns" />
import { assertEquals, assertExists } from "std/assert/mod.ts";
import { handleUpload } from "upload-handler/processor.ts";
import { loadTestConfig, createMockClient, setupTestUser, createTestJWT } from "tests/_shared/test_helpers.ts";

const testConfig = await loadTestConfig();

Deno.test("upload-handler", async (t) => {
  const testUser = await setupTestUser(null);
  const testJWT = await createTestJWT(testUser.id);

  await t.step("should process upload successfully", async () => {
    const client = createMockClient({
      ...testConfig,
      serviceRoleKey: testConfig.serviceRoleKey
    });
    
    const result = await handleUpload(
      testUser.id,
      "test-123",
      {
        content: "Test content",
        metadata: {
          extractionMethod: "test",
          contentType: "application/pdf",
          size: 1024,
          filename: "test.pdf"
        }
      },
      client
    );

    assertExists(result);
    assertEquals(result.success, true);
    assertEquals(result.document_id, "test-123");
    assertEquals(result.status, "completed");
  });

  await t.step("should handle missing file gracefully", async () => {
    const client = createMockClient({
      ...testConfig,
      serviceRoleKey: testConfig.serviceRoleKey
    });

    // Override storage mock to simulate missing file
    const mockClient = {
      ...client,
      storage: {
        from: () => ({
          download: async () => ({ data: null, error: "File not found", exists: false }),
          upload: async () => ({ data: null, error: "File not found" }),
          remove: async () => ({ data: null, error: null })
        })
      }
    };
    
    const result = await handleUpload(
      testUser.id,
      "missing-123",
      {
        content: "Test content",
        metadata: {
          extractionMethod: "test",
          contentType: "application/pdf",
          size: 1024,
          filename: "missing.pdf"
        }
      },
      mockClient
    );

    assertExists(result);
    assertEquals(result.success, false);
    assertEquals(result.status, "error");
    assertEquals(result.statusCode, 404);
  });
}); 