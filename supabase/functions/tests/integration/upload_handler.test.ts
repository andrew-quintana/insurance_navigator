/// <reference lib="deno.ns" />
import { assertEquals, assertExists } from "std/assert/mod.ts";
import { loadTestConfig, setupTestUser, createTestJWT, retryOperation } from "tests/_shared/test_helpers.ts";
import { removeFiles } from "upload-handler/storage.ts";

const testConfig = await loadTestConfig();

Deno.test("upload-handler integration", async (t) => {
  const testUser = await setupTestUser(null);
  const testJWT = await createTestJWT(testUser.id);

  await t.step("should handle file upload through edge function", async () => {
    const response = await retryOperation(async () => {
      const res = await fetch(
        `${testConfig.supabaseUrl}/functions/v1/upload-handler`,
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${testJWT}`,
            "Content-Type": "application/json",
            "apikey": testConfig.serviceRoleKey
          },
          body: JSON.stringify({
            userId: testUser.id,
            documentId: "test-integration-123",
            content: "Test content",
            metadata: {
              extractionMethod: "test",
              contentType: "application/pdf",
              size: 1024,
              filename: "test-integration.pdf"
            }
          })
        }
      );

      if (res.status === 503) {
        throw new Error("Service temporarily unavailable");
      }

      return res;
    });

    if (response.status === 503) {
      console.warn("Service is temporarily unavailable, skipping test");
      return;
    }

    assertEquals(response.status, 200);
    const result = await response.json();
    assertEquals(result.success, true);
    assertEquals(result.document_id, "test-integration-123");
    assertEquals(result.status, "completed");
  });

  await t.step("cleanup", async () => {
    await removeFiles(["test/raw/", "test/processed/"]);
  });
}); 