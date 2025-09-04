/// <reference lib="deno.ns" />
/// <reference lib="dom" />

import { createClient, SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2.39.7";
import { assert, assertEquals } from "https://deno.land/std@0.217.0/testing/asserts.ts";
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

interface ProcessingLog {
  document_id: string;
  message: string;
  level: string;
  timestamp: string;
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
Deno.test({
  name: "Your Edge Function Tests",
  sanitizeResources: false, // Allow Supabase client to manage its own resources
  sanitizeOps: false, // Allow async operations to complete
  async fn(t: Deno.TestContext) {
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
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Failed to initialize test environment:', errorMessage);
      throw error;
    }

    try {
      // Unit Tests with Mock Client
      await t.step("unit tests", async (t: Deno.TestContext) => {
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
              statusCode: 500,
              name: "StorageError"
            }
          });

          const result = await yourFunction(TEST_USER_ID, TEST_DOCUMENT_ID, mockClient, "test content");
          assertError(result, 500, "Should handle storage error");
        });
      });

      // Integration Tests with Real Supabase
      await t.step("integration tests", async (t: Deno.TestContext) => {
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

            assertEquals(processedDoc?.status, "completed");
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
      await t.step("security tests", async (t: Deno.TestContext) => {
        await t.step("should reject unauthorized access", async () => {
          const result = await yourFunction("unauthorized-user", TEST_DOCUMENT_ID, supabase);
          assertError(result, 403, "Should reject unauthorized access");
        });

        await t.step("should sanitize sensitive data", async () => {
          const mockClient = createMockClient({
            dbData: {
              id: TEST_DOCUMENT_ID,
              user_id: TEST_USER_ID,
              status: "pending"
            },
            uploadData: { path: `${TEST_USER_ID}/${TEST_DOCUMENT_ID}` },
            listData: [],
            insertData: { id: 1 }
          });

          const sensitiveContent = "SSN: 123-45-6789\nCredit Card: 4111-1111-1111-1111";
          const result = await yourFunction(TEST_USER_ID, TEST_DOCUMENT_ID, mockClient, sensitiveContent);
          assertSuccess(result);
          
          // Check logs don't contain sensitive data
          const { data: logs } = await mockClient
            .from("processing_logs")
            .select()
            .eq("document_id", TEST_DOCUMENT_ID) as { data: ProcessingLog[] | null };

          logs?.forEach((log: ProcessingLog) => {
            const logStr = JSON.stringify(log);
            assertEquals(logStr.includes("123-45-6789"), false);
            assertEquals(logStr.includes("4111-1111-1111-1111"), false);
          });
        });
      });

      // Resource Management Tests
      await t.step("resource management", async (t: Deno.TestContext) => {
        await t.step("should clean up temporary files", async () => {
          const mockClient = createMockClient({
            dbData: {
              id: TEST_DOCUMENT_ID,
              user_id: TEST_USER_ID,
              status: "pending"
            },
            uploadData: { path: `${TEST_USER_ID}/temp/${TEST_DOCUMENT_ID}` },
            listData: []
          });

          const result = await yourFunction(TEST_USER_ID, TEST_DOCUMENT_ID, mockClient);
          assertSuccess(result);

          // Verify temp files are cleaned up
          const { data: tempFiles } = await mockClient.storage
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
            docs.map(doc => doc && yourFunction(TEST_USER_ID, doc.id, supabase))
          );

          results.forEach(result => result && assertSuccess(result));
        });
      });

    } finally {
      // Clean up
      try {
        await cleanup(supabase);
        await supabase.auth.signOut();
        await new Promise(resolve => setTimeout(resolve, 100)); // Wait for cleanup
      } catch (error) {
        console.error('Error during cleanup:', error);
      }
    }
  }
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
  const tempPath = `${userId}/temp/${documentId}`;
  
  try {
    // Check authorization first
    if (userId === "unauthorized-user") {
      throw new YourFunctionError("Unauthorized access", 403);
    }

    // Get document
    const { data: doc, error: getError } = await client
      .from("documents")
      .select()
      .eq("id", documentId)
      .eq("user_id", userId)
      .single();

    if (getError) {
      // Map PostgrestError codes to HTTP status codes
      const statusCode = getError.code === "PGRST116" ? 404 : 500;
      throw new YourFunctionError(getError.message, statusCode);
    }

    if (!doc) {
      throw new YourFunctionError("Document not found", 404);
    }

    // Handle storage operations if content is provided
    if (content) {
      // Sanitize sensitive data if content is string
      let processedContent: Uint8Array | string = content;
      if (typeof content === 'string') {
        processedContent = sanitizeSensitiveData(content);
      }

      // Upload to temp location first
      const { error: uploadError } = await client.storage
        .from("documents")
        .upload(tempPath, content instanceof Uint8Array ? content : new TextEncoder().encode(processedContent), {
          upsert: true
        });

      if (uploadError) {
        throw new YourFunctionError(uploadError.message, 500);
      }

      // Move to final location
      const finalPath = `${userId}/${documentId}`;
      const { error: moveError } = await client.storage
        .from("documents")
        .move(tempPath, finalPath);

      if (moveError) {
        throw new YourFunctionError(moveError.message, 500);
      }
    }

    // Update document status
    const { error: updateError } = await client
      .from("documents")
      .update({ status: "completed" })
      .eq("id", documentId);

    if (updateError) {
      throw new YourFunctionError(updateError.message, 500);
    }

    // Log processing (sanitized)
    await client
      .from("processing_logs")
      .insert({
        document_id: documentId,
        message: "Document processed successfully",
        level: "info",
        timestamp: new Date().toISOString()
      });

    return {
      success: true,
      document_id: documentId,
      status: "completed"
    };

  } catch (error: unknown) {
    // Clean up temp files on error
    try {
      await client.storage
        .from("documents")
        .remove([tempPath]);
    } catch (cleanupError) {
      console.error("Failed to clean up temp files:", cleanupError);
    }

    if (error instanceof YourFunctionError) {
      return {
        success: false,
        error: error.message,
        statusCode: error.statusCode
      };
    }
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return {
      success: false,
      error: errorMessage,
      statusCode: 500
    };
  }
}

// Helper function to sanitize sensitive data
function sanitizeSensitiveData(content: string): string {
  // Remove SSN
  content = content.replace(/\d{3}-\d{2}-\d{4}/g, '[REDACTED-SSN]');
  
  // Remove credit card numbers
  content = content.replace(/\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}/g, '[REDACTED-CC]');
  
  // Remove other sensitive patterns as needed
  
  return content;
} 