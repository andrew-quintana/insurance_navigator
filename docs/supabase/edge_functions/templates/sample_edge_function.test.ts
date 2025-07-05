import { assertEquals, assertExists, assert } from "https://deno.land/std@0.217.0/testing/asserts.ts";
import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { 
  loadTestEnvironment,
  createMockClient,
  setupTestUser,
  cleanup,
  assertSuccess,
  assertError,
  waitForCondition,
  EnvironmentConfig
} from "./test_helpers.ts";

// Define test data types
interface TestDocument {
  id: string;
  user_id: string;
  filename: string;
  content_type: string;
  status: string;
  storage_path: string;
}

// Mock data
const TEST_USER_ID = "test-user-123";
const TEST_DOCUMENT_ID = "test-doc-123";

// Custom error class for your edge function
class YourFunctionError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: any
  ) {
    super(message);
    this.name = "YourFunctionError";
  }
}

// Main test suite
Deno.test("Your Edge Function Tests", async (t) => {
  let config: EnvironmentConfig;
  let supabase: SupabaseClient;

  // Set up test environment
  try {
    config = await loadTestEnvironment();
    supabase = createClient(config.supabaseUrl, config.supabaseKey);

    // Log debug information if enabled
    if (config.debug) {
      console.log('Test configuration:', {
        url: config.supabaseUrl,
        environment: config.nodeEnv,
        vectorProcessing: config.enableVectorProcessing,
        regulatoryProcessing: config.enableRegulatoryProcessing
      });
    }
  } catch (error) {
    console.error('Failed to initialize test environment:', error);
    throw error;
  }

  // Unit Tests with Mock Client
  await t.step("unit tests", async (t) => {
    await t.step("should handle success case", async () => {
      const mockClient = createMockClient({
        dbData: {
          id: TEST_DOCUMENT_ID,
          user_id: TEST_USER_ID,
          status: "processing"
        }
      });

      const result = await yourFunction(TEST_USER_ID, TEST_DOCUMENT_ID, mockClient);
      assertSuccess(result);
      assertEquals(result.document_id, TEST_DOCUMENT_ID);
    });

    await t.step("should handle not found error", async () => {
      const mockClient = createMockClient({
        dbError: {
          message: "Document not found",
          statusCode: 404
        }
      });

      const result = await yourFunction(TEST_USER_ID, "non-existent", mockClient);
      assertError(result, 404, "Should return not found error");
    });

    await t.step("should handle storage error", async () => {
      const mockClient = createMockClient({
        dbData: {
          id: TEST_DOCUMENT_ID,
          user_id: TEST_USER_ID,
          status: "processing"
        },
        storageError: {
          message: "Storage error",
          statusCode: 500
        }
      });

      const result = await yourFunction(TEST_USER_ID, TEST_DOCUMENT_ID, mockClient);
      assertError(result, 500, "Should handle storage error");
    });
  });

  // Integration Tests with Real Supabase
  await t.step("integration tests", async (t) => {
    // Skip integration tests if mock mode is enabled
    if (config.mockExternalServices) {
      console.log('Skipping integration tests in mock mode');
      return;
    }

    try {
      // Set up test data
      await setupTestUser(supabase);

      await t.step("should process document successfully", async () => {
        // Create test document
        const { data: doc, error: createError } = await supabase
          .from("documents")
          .insert({
            id: TEST_DOCUMENT_ID,
            user_id: TEST_USER_ID,
            filename: "test.pdf",
            content_type: "application/pdf",
            status: "pending",
            storage_path: `${TEST_USER_ID}/test.pdf`
          })
          .select()
          .single();

        if (createError) {
          throw createError;
        }

        // Upload test file
        const testContent = new TextEncoder().encode("Test content");
        const { error: uploadError } = await supabase.storage
          .from("documents")
          .upload(`${TEST_USER_ID}/test.pdf`, testContent, {
            contentType: "application/pdf",
            upsert: true
          });

        if (uploadError) {
          throw uploadError;
        }

        // Process document
        const result = await yourFunction(TEST_USER_ID, TEST_DOCUMENT_ID, supabase);
        assertSuccess(result);
        assertEquals(result.document_id, TEST_DOCUMENT_ID);

        // Verify document status
        const { data: processedDoc } = await supabase
          .from("documents")
          .select()
          .eq("id", TEST_DOCUMENT_ID)
          .single();

        assertEquals(processedDoc.status, "completed");
      });

      // Only run vector processing tests if enabled
      if (config.enableVectorProcessing) {
        await t.step("should handle large files with vector processing", async () => {
          const largeContent = new Uint8Array(5 * 1024 * 1024); // 5MB file
          const result = await yourFunction(TEST_USER_ID, TEST_DOCUMENT_ID, supabase, largeContent);
          assertSuccess(result);
        });
      }

      // Only run regulatory processing tests if enabled
      if (config.enableRegulatoryProcessing) {
        await t.step("should handle regulatory content", async () => {
          const regulatoryContent = "HIPAA compliance document";
          const result = await yourFunction(TEST_USER_ID, TEST_DOCUMENT_ID, supabase, regulatoryContent);
          assertSuccess(result);
        });
      }

      await t.step("should respect rate limits", async () => {
        const promises = Array(10).fill(null).map(() => 
          yourFunction(TEST_USER_ID, TEST_DOCUMENT_ID, supabase)
        );
        const results = await Promise.all(promises);
        const successCount = results.filter(r => r.success).length;
        assert(successCount <= 5, "Should respect rate limits");
      });

    } finally {
      // Clean up test data
      await cleanup(supabase);
    }
  });

  // Security Tests
  await t.step("security tests", async (t) => {
    await t.step("should reject unauthorized access", async () => {
      const result = await yourFunction("unauthorized-user", TEST_DOCUMENT_ID, supabase);
      assertError(result, 403, "Should reject unauthorized access");
    });

    await t.step("should sanitize sensitive data", async () => {
      const sensitiveContent = "SSN: 123-45-6789\nCredit Card: 4111-1111-1111-1111";
      const result = await yourFunction(TEST_USER_ID, TEST_DOCUMENT_ID, supabase, sensitiveContent);
      assertSuccess(result);
      
      // Check logs don't contain sensitive data
      const { data: logs } = await supabase
        .from("processing_logs")
        .select()
        .eq("document_id", TEST_DOCUMENT_ID);

      logs?.forEach(log => {
        const logStr = JSON.stringify(log);
        assertEquals(logStr.includes("123-45-6789"), false);
        assertEquals(logStr.includes("4111-1111-1111-1111"), false);
      });
    });
  });

  // Resource Management Tests
  await t.step("resource management", async (t) => {
    await t.step("should clean up temporary files", async () => {
      const result = await yourFunction(TEST_USER_ID, TEST_DOCUMENT_ID, supabase);
      assertSuccess(result);

      // Verify temp files are cleaned up
      const { data: tempFiles } = await supabase.storage
        .from("documents")
        .list(`${TEST_USER_ID}/temp`);

      assertEquals(tempFiles?.length, 0, "Should clean up temp files");
    });

    await t.step("should handle concurrent processing", async () => {
      const docs = await Promise.all(
        Array(3).fill(null).map(async () => {
          const { data } = await supabase
            .from("documents")
            .insert({
              user_id: TEST_USER_ID,
              filename: "concurrent.pdf",
              status: "pending"
            })
            .select()
            .single();
          return data;
        })
      );

      const results = await Promise.all(
        docs.map(doc => yourFunction(TEST_USER_ID, doc.id, supabase))
      );

      results.forEach(result => assertSuccess(result));
    });
  });
});

// Example edge function implementation
async function yourFunction(
  userId: string,
  documentId: string,
  client: SupabaseClient,
  content?: Uint8Array | string
): Promise<{
  success: boolean;
  document_id?: string;
  status?: string;
  error?: string;
  statusCode?: number;
}> {
  try {
    // Get document
    const { data: doc, error: getError } = await client
      .from("documents")
      .select()
      .eq("id", documentId)
      .eq("user_id", userId)
      .single();

    if (getError) {
      throw new YourFunctionError(
        getError.message,
        getError.code === "PGRST116" ? 404 : 500
      );
    }

    // Process document
    // ... your processing logic here ...

    return {
      success: true,
      document_id: documentId,
      status: "completed"
    };

  } catch (error) {
    if (error instanceof YourFunctionError) {
      return {
        success: false,
        error: error.message,
        statusCode: error.statusCode
      };
    }
    return {
      success: false,
      error: error.message || "Unknown error",
      statusCode: 500
    };
  }
} 