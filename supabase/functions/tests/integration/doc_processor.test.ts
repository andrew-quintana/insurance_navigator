import { assertEquals, assertExists, assertStringIncludes } from "https://deno.land/std@0.217.0/assert/mod.ts";
import { createClient } from "@supabase/supabase-js";
import { processDocument } from "../../doc-processor/processor.ts";
import { edgeConfig } from "../../_shared/environment.ts";
import { removeFiles } from "../../doc-processor/storage.ts";
import { config } from "https://deno.land/x/dotenv/mod.ts";
import { describe, it, afterEach } from "https://deno.land/std@0.217.0/testing/bdd.ts";

// Load environment variables
const env = config();

const TEST_USER_ID = "a0e777f9-d442-4b17-9f1e-bf5b3954c26a"; // Valid UUID

// Helper function to clean up test data
async function cleanupTestData(supabase: any, documentId: string) {
  const paths = [
    `${documentId}/raw/missing.pdf`,
    `${documentId}/processed/missing.pdf`
  ];

  const result = await removeFiles(supabase, paths);
  if (result.error) {
    console.warn('Cleanup warning:', result.error);
  }
}

// Integration Test: Handle missing raw file with real storage
Deno.test("should handle missing raw file (integration)", async () => {
  const supabase = createClient(
    edgeConfig.supabaseUrl,
    edgeConfig.supabaseKey as string,
    {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
        detectSessionInUrl: false
      }
    }
  );

  const missingDocId = '33333333-3333-4333-a333-333333333333';
  
  try {
    // Create document record pointing to a non-existent file
    const { data: document, error: insertError } = await supabase
      .from('documents')
      .insert({
        id: missingDocId,
        user_id: TEST_USER_ID,
        filename: 'missing.pdf',
        content_type: 'application/pdf',
        status: 'processing',
        storage_path: `${TEST_USER_ID}/raw/missing.pdf`
      })
      .select()
      .single();

    if (insertError) {
      throw insertError;
    }

    // Process the document - should fail because file doesn't exist
    const result = await processDocument(TEST_USER_ID, missingDocId, {
      content: 'test content',
      metadata: { extractionMethod: 'test' }
    });

    // Verify processor returned error result
    assertEquals(result.success, false);
    assertEquals(result.status, 'error');
    assertExists(result.error);
    assertStringIncludes(result.error, 'not found', 'Error should indicate file not found');

    // Verify document status was updated in database
    const { data: updatedDoc, error: getError } = await supabase
      .from('documents')
      .select()
      .eq('id', missingDocId)
      .single();

    if (getError) {
      throw getError;
    }

    assertEquals(updatedDoc.status, 'error');
    assertExists(updatedDoc.error_message);
    assertStringIncludes(updatedDoc.error_message, 'not found', 'Database error should indicate file not found');

  } finally {
    // Clean up test data
    await cleanupTestData(supabase, missingDocId);
  }
});

describe("should handle missing raw file", () => {
  it("(integration)", async () => {
    const supabase = createClient(edgeConfig.supabaseUrl, edgeConfig.supabaseKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
        detectSessionInUrl: false
      }
    });

    const documentId = "a0e777f9-d442-4b17-9f1e-bf5b3954c26a";
    const result = await removeFiles(supabase, [
      `${documentId}/raw/missing.pdf`,
      `${documentId}/processed/missing.pdf`
    ]);

    if (result.error) {
      console.warn('Cleanup warning:', result.error);
    }
  });

  it("should return error when raw file is missing", async () => {
    console.log('Starting missing raw file test');
    
    const testPath = 'test/missing-file.pdf';
    console.log('Test path:', testPath);

    let response;
    try {
      response = await fetch(
        `${edgeConfig.supabaseUrl}/functions/v1/doc-processor`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${edgeConfig.supabaseKey}`,
          },
          body: JSON.stringify({
            document_id: 'missing-doc-123',
          }),
        }
      );

      const responseText = await response.text();
      console.log('Response text:', responseText);

      let responseData;
      try {
        responseData = JSON.parse(responseText);
      } catch (e) {
        responseData = { error: responseText };
      }
      console.log('Response data:', responseData);

      // Check for 404 status since document not found
      if (response.status !== 404) {
        throw new Error(`Expected status 404, got ${response.status}`);
      }

      // Check that the error message contains 'not found' or 'missing' somewhere in the chain
      const errorMessage = responseData.error || responseData.message || JSON.stringify(responseData);
      if (!errorMessage.toLowerCase().includes('not found') && !errorMessage.toLowerCase().includes('missing')) {
        throw new Error(`Expected error to contain 'not found' or 'missing', got: ${errorMessage}`);
      }

    } catch (error) {
      console.log('Test error:', error);
      throw error;
    } finally {
      // Cleanup
      if (response) {
        const supabase = createClient(edgeConfig.supabaseUrl, edgeConfig.supabaseKey, {
          auth: {
            autoRefreshToken: false,
            persistSession: false,
            detectSessionInUrl: false
          }
        });
        await cleanupTestData(supabase, 'missing-doc-123');
      }
    }
  });
}); 