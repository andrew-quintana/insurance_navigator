// @ts-ignore: Deno types
import { assertEquals } from "https://deno.land/std@0.217.0/testing/asserts.ts";
// @ts-ignore: Supabase types
import { createClient, SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2.39.7";
// @ts-ignore: Deno types
import { load } from "https://deno.land/std@0.217.0/dotenv/mod.ts";
// @ts-ignore: Deno types
import { join } from "https://deno.land/std@0.217.0/path/mod.ts";
// @ts-ignore: Local types
import { ProcessingLog } from "../doc-processor/types.ts";
// @ts-ignore: Local helpers
import { getProjectRoot, initializeTestClient } from "./test_helpers.ts";
import { ProcessingMetadata, ProcessingResponse } from "../doc-processor/types.ts";
import { ProcessingResult } from "../doc-processor/types.ts";

interface TestDocument {
  id: string;
  user_id: string;
  filename: string;
  content_type: string;
  status: string;
  storage_path: string;
  error_message?: string;
  document_chunks?: { count: number }[];
}

// Load environment variables from project root .env.test
const projectRoot = getProjectRoot();
await load({ export: true, envPath: join(projectRoot, '.env.test') });

// Set required environment variables for testing
const requiredEnvVars: Record<string, string> = {
  'SUPABASE_URL': Deno.env.get('SUPABASE_URL') || 'http://127.0.0.1:54321',
  'SUPABASE_SERVICE_ROLE_KEY': Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || '',
  'OPENAI_API_KEY': Deno.env.get('OPENAI_API_KEY') || 'dummy-key'
};

// Validate required environment variables
for (const [key, value] of Object.entries(requiredEnvVars)) {
  if (!value) {
    throw new Error(`Required environment variable ${key} is not set. Please check your .env.test file.`);
  }
  if (!Deno.env.get(key)) {
    Deno.env.set(key, value);
  }
}

// Define types for external API responses
interface LlamaParseResponse {
  text: string;
  metadata: {
    title: string;
    pages: number;
  };
}

interface OpenAIEmbeddingResponse {
  data: Array<{
    embedding: number[];
    index: number;
  }>;
}

// Mock external API clients
const mockLlamaParseClient = {
  parseDocument: async () => ({
    text: 'Test document content',
    metadata: { title: 'Test Document' }
  })
};

const mockOpenAIClient = {
  embeddings: {
    create: () => {
      return Promise.resolve({
        data: [{
          embedding: new Array(1536).fill(0.1),
          index: 0
        }]
      });
    }
  }
};

// Mock clients and setup
const mockStorageClient = {
  download: () => Promise.resolve(new Blob(['test content'])),
  upload: () => Promise.resolve({ error: null })
};

const mockVectorClient = {
  upsert: () => Promise.resolve({ error: null })
};

const mockParserClient = {
  parseDocument: () => Promise.resolve({
    content: 'test content',
    metadata: { pageCount: 1 }
  })
};

// Helper function to generate UUID v4
function uuidv4(): string {
  return crypto.randomUUID();
}

// Helper function to get service role client with proper configuration
function getServiceRoleClient(): SupabaseClient {
  const supabaseUrl = Deno.env.get('SUPABASE_URL');
  const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  
  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Missing required environment variables: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY');
  }

  return createClient(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false
    }
  });
}

// Helper function to setup test environment
async function setupTestEnv() {
  const client = getServiceRoleClient();
  
  // Create test user directly in the database
  const timestamp = Date.now();
  const testUserId = uuidv4();
  
  const { data: userRecord, error: userError } = await client
    .from('users')
    .insert({
      id: testUserId,
      email: `test${timestamp}@example.com`,
      name: `Test User ${timestamp}`
    })
    .select()
    .single();
  
  if (userError) throw userError;
  
  return { client, userId: userRecord.id };
}

// Helper function to read test PDF file
async function readTestPDF(): Promise<Uint8Array> {
  const projectRoot = getProjectRoot();
  const pdfPath = join(projectRoot, "tests", "test.pdf");
  
  try {
    const fileInfo = await Deno.stat(pdfPath);
    if (!fileInfo.isFile) {
      throw new Error(`Test PDF not found at ${pdfPath}`);
    }
    return await Deno.readFile(pdfPath);
  } catch (error: unknown) {
    console.error("Failed to read test PDF file:");
    console.error("- Error:", error instanceof Error ? error.message : String(error));
    console.error("- Project root:", projectRoot);
    console.error("- Attempted PDF path:", pdfPath);
    console.error("Please ensure test.pdf exists in the tests directory");
    throw error;
  }
}

// Helper function to verify document exists in storage
async function verifyDocumentStorage(client: SupabaseClient, storagePath: string): Promise<boolean> {
  try {
    const { data, error } = await client
      .storage
      .from('documents')
      .download(storagePath);
    
    if (error) {
      console.error('Failed to verify document in storage:', error);
      return false;
    }
    
    return data !== null;
  } catch (error) {
    console.error('Error checking document storage:', error);
    return false;
  }
}

// Helper function to create test document
async function createTestDocument(client: SupabaseClient, userId: string): Promise<TestDocument> {
  const pdfData = await readTestPDF();
  const filename = "test.pdf";
  const storagePath = `${userId}/${filename}`;

  // Upload file to storage
  const { error: uploadError } = await client.storage
    .from("documents")
    .upload(storagePath, pdfData, {
      contentType: "application/pdf",
      upsert: true
    });

  if (uploadError) {
    console.error("Failed to upload test document:", uploadError);
    throw uploadError;
  }

  // Create document record
  const { data: doc, error: insertError } = await client
    .from("documents")
    .insert({
      user_id: userId,
      filename,
      content_type: "application/pdf",
      status: "processing",
      storage_path: storagePath
    })
    .select()
    .single();

  if (insertError) {
    console.error("Failed to create document record:", insertError);
    throw insertError;
  }

  return doc as TestDocument;
}

// Helper function to cleanup test data
async function cleanupTestData(client: SupabaseClient, userId: string) {
  const prefix = 'test';
  
  // Delete test documents
  const { error: docError } = await client
    .from('documents')
    .delete()
    .match({ user_id: userId })
    .like('filename', `${prefix}_%`);
  
  if (docError) console.error('Error cleaning up test documents:', docError);
  
  // Delete test user
  const { error: userError } = await client
    .from('users')
    .delete()
    .eq('id', userId);
  
  if (userError) console.error('Error cleaning up test user:', userError);
}

// Helper function to get processing logs
async function getProcessingLogs(client: SupabaseClient, document_id: string): Promise<ProcessingLog[]> {
  const { data: logs, error } = await client
    .from('processing_logs')
    .select('*')
    .eq('document_id', document_id)
    .order('created_at', { ascending: true });

  if (error) {
    console.error('Failed to get processing logs:', error);
    throw error;
  }

  return logs || [];
}

// Helper function to display processing logs
function displayProcessingLogs(logs: ProcessingLog[]) {
  console.log('\nProcessing Logs:');
  console.log('----------------');
  for (const log of logs) {
    console.log(`[${new Date(log.created_at).toISOString()}] ${log.stage} - ${log.status}`);
    if (log.metadata) {
      console.log('  Metadata:', JSON.stringify(log.metadata, null, 2));
    }
    if (log.error_message) {
      console.log('  Error:', log.error_message);
    }
    console.log('----------------');
  }
}

// Helper function to wait for document status
async function waitForDocumentStatus(
  client: SupabaseClient,
  docId: string,
  expectedStatus: string,
  maxAttempts = 30
): Promise<TestDocument> {
  let attempts = 0;
  const delay = 2000; // 2 seconds between attempts

  while (attempts < maxAttempts) {
    attempts++;
    
    // Get current document status
    const { data: doc, error: docError } = await client
      .from('documents')
      .select('*, document_chunks(count)')
      .eq('id', docId)
      .single();

    if (docError) {
      console.error(`Failed to get document status (attempt ${attempts}):`, docError);
      throw docError;
    }

    // Get processing logs
    const logs = await getProcessingLogs(client, docId);
    
    // Display detailed status
    console.log(`\nAttempt ${attempts}/${maxAttempts}`);
    console.log('Current Status:', doc.status);
    console.log('Expected Status:', expectedStatus);
    console.log('Document Chunks:', doc.document_chunks?.[0]?.count ?? 0);
    console.log('Storage Path:', doc.storage_path);
    if (doc.error_message) {
      console.log('Error Message:', doc.error_message);
    }

    // Display processing logs
    console.log('\nProcessing Logs:');
    console.log('----------------');
    for (const log of logs) {
      console.log(`[${new Date(log.created_at).toISOString()}] ${log.stage} - ${log.status}`);
      console.log('  Metadata:', JSON.stringify(log.metadata, null, 2));
      if (log.error_message) {
        console.log('  Error:', log.error_message);
      }
      console.log('----------------');
    }

    // Check if document has reached expected status
    if (doc.status === expectedStatus) {
      return doc;
    }

    // Check for error status
    if (doc.status === 'error') {
      console.error('Document processing failed:', doc.error_message);
      throw new Error(`Document processing failed: ${doc.error_message}`);
    }

    // Wait before next attempt
    await new Promise(resolve => setTimeout(resolve, delay));
  }

  throw new Error(`Document status did not update to ${expectedStatus} after ${maxAttempts} attempts`);
}

// Helper function to verify document chunks
async function verifyDocumentChunks(client: SupabaseClient, docId: string): Promise<boolean> {
  const { data: chunks, error: chunksError } = await client
    .from('document_chunks')
    .select('*')
    .eq('document_id', docId)
    .order('chunk_index');

  if (chunksError) throw chunksError;
  
  // Verify we have chunks
  if (!chunks || chunks.length === 0) {
    throw new Error('No chunks found for document');
  }

  // Verify chunk properties
  chunks.forEach((chunk, index) => {
    assertEquals(chunk.id, index, 'Chunk indices should be sequential');
    assertEquals(chunk.content, 'Test content', 'Chunk content should be "Test content"');
  });

  return true;
}

// Helper function to verify document vectors
async function verifyDocumentVectors(client: SupabaseClient, documentId: string): Promise<void> {
  const { data: chunks } = await client
    .from('document_chunks')
    .select('id')
    .eq('document_id', documentId);

  if (!chunks || chunks.length === 0) {
    throw new Error('No chunks found for vector verification');
  }

  const chunkIds = chunks.map(c => c.id);
  const { data: vectors, error } = await client
    .from('document_vectors')
    .select('*')
    .in('chunk_id', chunkIds);

  if (error) {
    throw new Error(`Failed to verify vectors: ${error.message}`);
  }

  if (!vectors) {
    throw new Error('No vectors found');
  }

  assertEquals(vectors.length > 0, true, 'Should have at least one vector embedding');
}

// Test Supabase client setup and connection
Deno.test('Test Supabase Client Setup', async () => {
  const client = getServiceRoleClient();
  
  const { data, error } = await client
    .from('documents')
    .select('*')
    .limit(1);
  
  assertEquals(error, null, 'Should not have any errors');
  assertEquals(data.length > 0, true, 'Should be able to query documents table');
});

// Test document upload and initial processing
Deno.test('Test Document Upload Flow', async () => {
  const { client, userId } = await setupTestEnv();
  if (!userId) throw new Error('Failed to create test user');
  
  try {
    // Upload test document
    const testDoc = await createTestDocument(client, userId);
    assertEquals(testDoc.id, userId, 'Document ID should match user ID');
    assertEquals(testDoc.status, 'processing', 'Initial status should be processing');
  } finally {
    await cleanupTestData(client, userId);
  }
});

// Test document parsing with LlamaParse
Deno.test('Test Document Parsing Stage', async () => {
  const { userId } = await setupTestEnv();
  if (!userId) throw new Error('Failed to create test user');
  
  // Use service role client for all operations
  const serviceClient = getServiceRoleClient();
  
  try {
    console.log('Creating test document...');
    const testDoc = await createTestDocument(serviceClient, userId);
    console.log('Test document created:', testDoc.id);

    // Wait for document to be processed
    console.log('Waiting for document processing...');
    const processedDoc = await waitForDocumentStatus(serviceClient, testDoc.id, 'completed');
    
    // Verify document was processed successfully
    console.log('Verifying document processing...');
    assertEquals(processedDoc.status, 'completed', 'Document should be marked as completed');
    assertEquals(processedDoc.storage_path, userId + '/test.pdf', 'Document storage path should match');
    
    // Display processing logs for debugging
    const logs = await getProcessingLogs(serviceClient, testDoc.id);
    displayProcessingLogs(logs);
    
    // Verify document chunks were created
    console.log('Verifying document chunks...');
    const hasChunks = await verifyDocumentChunks(serviceClient, testDoc.id);
    assertEquals(hasChunks, true, 'Document should have chunks');
    
    // Verify vectors were created
    console.log('Verifying document vectors...');
    await verifyDocumentVectors(serviceClient, testDoc.id);
    
    console.log('Test completed successfully');
  } catch (error: unknown) {
    console.error('Test failed with error:', error);
    // Display detailed error information
    if (error instanceof Error) {
      const supabaseError = error as { error?: { details?: string; message?: string; code?: string } };
      if (supabaseError.error?.details) {
        console.error('Error details:', supabaseError.error.details);
      }
      if (supabaseError.error?.message) {
        console.error('Error message:', supabaseError.error.message);
      }
      if (supabaseError.error?.code) {
        console.error('Error code:', supabaseError.error.code);
      }
    }
    throw error;
  } finally {
    // Clean up test data
    console.log('Cleaning up test data...');
    await cleanupTestData(serviceClient, userId);
  }
});

// Test error handling
Deno.test('Test Error Handling', async () => {
  const { client, userId } = await setupTestEnv();
  if (!userId) throw new Error('Failed to create test user');
  
  try {
    // Test invalid file type
    const testDoc = await createTestDocument(client, userId);
    
    try {
      await client
        .from('documents')
        .update({ content_type: 'invalid/type' })
        .eq('id', testDoc.id);
      
      throw new Error('Should have rejected invalid content type');
    } catch (error) {
      assertEquals(error instanceof Error, true, 'Should throw error for invalid content type');
    }
    
    // Test error status update
    const { error: updateError } = await client
      .from('documents')
      .update({
        status: 'error',
        error_message: 'Test error message'
      })
      .eq('id', testDoc.id);
    
    assertEquals(updateError, null, 'Should update error status without error');
  } finally {
    await cleanupTestData(client, userId);
  }
});

// Test storage cleanup
Deno.test('Test Storage Cleanup', async () => {
  const { client: userClient, userId } = await setupTestEnv();
  if (!userId) throw new Error('Failed to create test user');
  
  // Get service role client for operations that need elevated permissions
  const serviceClient = getServiceRoleClient();
  
  try {
    // Create test document
    const testDoc = await createTestDocument(userClient, userId);
    
    // Create test chunk using service role client
    const { data: chunkData, error: chunkError } = await serviceClient
      .from('document_chunks')
      .insert({
        document_id: testDoc.id,
        chunk_index: 0,
        content: 'Test content'
      })
      .select()
      .single();
    
    assertEquals(chunkError, null, 'Should create chunk without error');
    
    // Create test vector using service role client
    const { error: vectorError } = await serviceClient
      .from('document_vectors')
      .insert({
        chunk_id: chunkData.id,
        vector_data: new Array(1536).fill(0.1)
      });
    
    assertEquals(vectorError, null, 'Should create vector without error');
    
    // Delete document using service role client (should cascade to chunks and vectors)
    const { error: deleteError } = await serviceClient
      .from('documents')
      .delete()
      .eq('id', testDoc.id);
    
    assertEquals(deleteError, null, 'Should delete document without error');
    
    // Verify document is deleted
    const { data: checkDoc, error: checkError } = await serviceClient
      .from('documents')
      .select()
      .eq('id', testDoc.id)
      .maybeSingle();
    
    assertEquals(checkDoc, null, 'Document should be deleted');
    assertEquals(checkError, null, 'Should not have error checking deleted document');
    
    // Verify chunks are deleted
    const { data: checkChunks, error: checkChunksError } = await serviceClient
      .from('document_chunks')
      .select()
      .eq('document_id', testDoc.id);
    
    assertEquals(checkChunks?.length, 0, 'Chunks should be deleted');
    assertEquals(checkChunksError, null, 'Should not have error checking deleted chunks');
  } finally {
    await cleanupTestData(serviceClient, userId);
  }
});

// Test complete document processing pipeline
Deno.test('Test Complete Document Processing Pipeline', async () => {
  const client = getServiceRoleClient();
  const userId = uuidv4(); // Generate a valid UUID for the user

  let testDoc: TestDocument | null = null;

  try {
    console.log('Starting complete pipeline test...');

    // Create test user
    console.log('Creating test user...');
    const { error: userError } = await client
      .from('users')
      .insert({
        id: userId,
        email: `test-${userId}@example.com`,
        name: 'Test User',
        created_at: new Date().toISOString()
      });

    if (userError) {
      throw new Error(`Failed to create test user: ${userError.message}`);
    }

    // 1. Create test document
    console.log('Creating test document...');
    const { data: doc, error: createError } = await client
      .from('documents')
      .insert({
        user_id: userId,
        filename: 'test.pdf',
        content_type: 'application/pdf',
        storage_path: `${userId}/test.pdf`,
        status: 'processing'
      })
      .select()
      .single();

    if (createError || !doc) {
      throw new Error(`Failed to create test document: ${createError?.message}`);
    }

    testDoc = doc as TestDocument;
    assertEquals(testDoc.id, userId, 'Document ID should match user ID');
    
    // 2. Upload real PDF file
    console.log('Uploading test PDF...');
    const testPdfContent = await readTestPDF();
    const { error: uploadError } = await client
      .storage
      .from('documents')
      .upload(testDoc.storage_path, testPdfContent, {
        contentType: 'application/pdf',
        duplex: 'simplex',
        upsert: true
      });
    
    if (uploadError) {
      console.error('Upload error:', uploadError);
      throw uploadError;
    }

    // 3. Call the Edge Function directly
    console.log('Calling document processor...');
    const response = await fetch('http://127.0.0.1:54321/functions/v1/doc-processor', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.p2fuVDatv5iaDizrYVeg2Gx_U1utFdpwLHwkiZfsRxs`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        document_id: testDoc.id,
        storage_path: testDoc.storage_path,
        content_type: testDoc.content_type
      })
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to call document processor: ${error}`);
    }

    // 4. Wait for document to be processed
    console.log('Waiting for document processing...');
    const processedDoc = await waitForDocumentStatus(client, testDoc.id, 'completed', 30);
    assertEquals(processedDoc.status, 'completed', 'Document should be processed');

    // 5. Verify chunks were created
    console.log('Verifying document chunks...');
    await verifyDocumentChunks(client, testDoc.id);

    // 6. Verify vectors were created
    console.log('Verifying document vectors...');
    await verifyDocumentVectors(client, testDoc.id);

    // 7. Display final processing logs
    const finalLogs = await getProcessingLogs(client, testDoc.id);
    console.log('\nFinal Processing Logs:');
    displayProcessingLogs(finalLogs);

    console.log('Pipeline test completed successfully');
  } catch (error) {
    console.error('Pipeline test failed:', error);
    throw error;
  } finally {
    // Cleanup test data
    if (testDoc?.id) {
      await client
        .from('documents')
        .delete()
        .eq('id', testDoc.id);
    }
    // Clean up test user
    await client
      .from('users')
      .delete()
      .eq('id', userId);
  }
});

// Test error handling in pipeline
Deno.test('Test Pipeline Error Handling', async () => {
  const { client, userId } = await setupTestEnv();
  if (!userId) throw new Error('Failed to create test user');

  try {
    console.log('Starting error handling test...');

    // 1. Create document with invalid content
    const testDoc = await createTestDocument(client, userId);
    
    // 2. Upload invalid content (corrupted PDF bytes)
    const invalidContent = new Uint8Array([0x25, 0x50, 0x44]); // Incomplete PDF header
    const { error: uploadError } = await client
      .storage
      .from('documents')
      .upload(testDoc.storage_path, invalidContent, {
        contentType: 'application/pdf',
        duplex: 'simplex',
        upsert: true
      });
    
    if (uploadError) {
      console.log('Expected upload error:', uploadError);
    } else {
      // 3. Document should move to error state
      const errorDoc = await waitForDocumentStatus(client, testDoc.id, 'error', 10);
      assertEquals(errorDoc.status, 'error', 'Document should be in error state');
      assertEquals(errorDoc.error_message, 'Invalid PDF content', 'Error message should be set');
    }

  } finally {
    await cleanupTestData(client, userId);
  }
});

// Helper function to query and display processing results
export async function displayProcessingResults(client: SupabaseClient, docId: string) {
  console.log('\nDocument Processing Results:');
  
  // Get document status
  const { data: doc } = await client
    .from('documents')
    .select('*')
    .eq('id', docId)
    .single();
  
  console.log('\nDocument Status:', doc?.status);
  if (doc?.error_message) {
    console.log('Error Message:', doc.error_message);
  }

  // Get chunks info
  const { data: chunks } = await client
    .from('document_chunks')
    .select('*')
    .eq('document_id', docId)
    .order('chunk_index');
  
  console.log('\nChunks Created:', chunks?.length || 0);
  if (chunks?.length) {
    console.log('Sample Chunk:', {
      id: chunks[0].id,
      index: chunks[0].chunk_index,
      contentPreview: chunks[0].content.substring(0, 100) + '...'
    });
  }

  // Get vectors info
  const { data: vectors } = await client
    .from('document_vectors')
    .select('*')
    .eq('chunk_id', chunks?.[0]?.id);
  
  console.log('\nVectors Created:', vectors?.length || 0);
  if (vectors?.length) {
    console.log('Vector Dimensions:', vectors[0].vector_data.length);
  }
}

// Test document processing
Deno.test("Document processing", async (t) => {
  const client = await initializeTestClient();
  const userId = "test-user-" + crypto.randomUUID();
  let testDoc: TestDocument;

  try {
    console.log('\nStarting document processing test');
    console.log('--------------------------------');
    
    // Create test document
    console.log('\nCreating test document...');
    testDoc = await createTestDocument(client, userId);
    console.log('Test document created:', testDoc);

    // Wait for processing to complete
    console.log('\nWaiting for document processing...');
    const processedDoc = await waitForDocumentStatus(client, testDoc.id, 'completed');
    console.log('\nDocument processing completed:', processedDoc);

    // Verify processing results
    console.log('\nVerifying processing results...');
    assertEquals(processedDoc.status, 'completed', 'Document should be marked as completed');
    
    // Get final processing logs
    const finalLogs = await getProcessingLogs(client, testDoc.id);
    console.log('\nFinal Processing Logs:');
    console.log('----------------');
    for (const log of finalLogs) {
      console.log(`[${new Date(log.created_at).toISOString()}] ${log.stage} - ${log.status}`);
      console.log('  Metadata:', JSON.stringify(log.metadata, null, 2));
      if (log.error_message) {
        console.log('  Error:', log.error_message);
      }
      console.log('----------------');
    }

  } catch (error) {
    console.error('\nTest failed:', error);
    throw error;
  } finally {
    // Cleanup
    console.log('\nCleaning up test data...');
    if (testDoc?.id) {
      await client.from('documents').delete().eq('id', testDoc.id);
      console.log('Test document deleted');
    }
    console.log('Test cleanup completed');
  }
}); 