/// <reference lib="deno.ns" />
import { assertEquals } from "std/assert/mod.ts";
import { handleUpload } from "upload-handler/processor.ts";
import { loadTestConfig, createMockClient, setupTestUser, createTestJWT } from "tests/_shared/test_helpers.ts";

const testConfig = await loadTestConfig();

Deno.test("upload-handler security", async (t) => {
  const testUser = await setupTestUser(null);
  const testJWT = await createTestJWT(testUser.id);

  await t.step("should require authentication", async () => {
    // Mock client with invalid auth
    const client = createMockClient({
      ...testConfig,
      serviceRoleKey: "invalid-key"
    });

    // Mock auth.getUser to return error
    const mockClient = {
      ...client,
      auth: {
        getUser: async () => ({ data: null, error: { message: "Invalid JWT", status: 401 } })
      }
    };
    
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
      mockClient
    );

    assertEquals(result.success, false);
    assertEquals(result.statusCode, 401);
    assertEquals(result.status, "error");
  });

  await t.step("should validate input", async () => {
    const client = createMockClient({
      ...testConfig,
      serviceRoleKey: testConfig.serviceRoleKey
    });
    
    const result = await handleUpload(
      testUser.id,
      "",
      {
        content: "Test content",
        metadata: {
          extractionMethod: "test",
          contentType: "application/pdf",
          size: 1024,
          filename: ""
        }
      },
      client
    );

    assertEquals(result.success, false);
    assertEquals(result.statusCode, 400);
    assertEquals(result.status, "error");
  });

  await t.step("should prevent path traversal", async () => {
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
          filename: "../../../etc/passwd"
        }
      },
      client
    );

    assertEquals(result.success, false);
    assertEquals(result.statusCode, 400);
    assertEquals(result.status, "error");
  });
}); 