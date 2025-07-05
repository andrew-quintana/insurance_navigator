// @ts-ignore: Deno types
import { assertEquals, assertExists } from "std/testing/asserts.ts";
// @ts-ignore: Supabase types
import { createClient, SupabaseClient } from "@supabase/supabase-js";
// @ts-ignore: Deno types
import { load } from "https://deno.land/std@0.217.0/dotenv/mod.ts";
// @ts-ignore: Deno types
import { join } from "https://deno.land/std@0.217.0/path/mod.ts";
// @ts-ignore: Local types
import { ProcessingLog } from "../doc-processor/types.ts";
// @ts-ignore: Local helpers
import { getProjectRoot, loadEnvironment, initializeTestClient, getEdgeFunctionLogs } from "./test_helpers.ts";
import { ProcessingMetadata, ProcessingResponse, ProcessingResult } from "../doc-processor/types.ts";
import { edgeConfig } from "../_shared/environment.ts";
import { createServiceRoleJWT } from "../_shared/jwt.ts";

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

// Load environment variables
async function loadTestEnvironment() {
  const env = Deno.env.get("ENV") || "test";
  const envFiles = [
    `.env.${env}.local`,
    `.env.${env}`,
    '.env.local',
    '.env'
  ];

  for (const file of envFiles) {
    try {
      await load({ export: true, envPath: file });
      console.log(`Loading environment from ${file}`);
    } catch (e) {
      // Ignore missing files
      if (!(e instanceof Deno.errors.NotFound)) {
        console.error(`Error loading ${file}:`, e);
      }
    }
  }
}

// Initialize before running tests
await loadTestEnvironment();

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
  const pdfPath = join(projectRoot, 'supabase', 'functions', 'tests', 'test.pdf');
  
  try {
    const fileInfo = await Deno.stat(pdfPath);
    if (!fileInfo.isFile) {
      throw new Error('Test PDF path exists but is not a file');
    }
    return await Deno.readFile(pdfPath);
  } catch (error) {
    console.error('Failed to read test PDF file:');
    console.error(`- ${error}`);
    console.error(`- Project root: ${projectRoot}`);
    console.error(`- Attempted PDF path: ${pdfPath}`);
    console.error('Please ensure test.pdf exists in the tests directory');
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

// Helper function to create a test user
async function createTestUser(client: SupabaseClient): Promise<string> {
  const userId = crypto.randomUUID();
  const { error } = await client
    .from('users')
    .insert({
      id: userId,
      email: `test-${userId}@example.com`,
      name: `Test User ${userId}`
    });

  if (error) {
    throw error;
  }

  return userId;
}

// Helper function to create a test document
async function createTestDocument(client: SupabaseClient, userId: string): Promise<TestDocument> {
  // Create a simple test PDF file
  const testContent = new Uint8Array([37, 80, 68, 70, 45, 49, 46, 55, 10]); // %PDF-1.7 header
  const filename = 'test-document.pdf';
  const storagePath = `test-documents/${crypto.randomUUID()}.pdf`;

  // Upload file to storage
  const { error: uploadError } = await client.storage
    .from('documents')
    .upload(storagePath, testContent, {
      contentType: 'application/pdf',
      upsert: true
    });

  if (uploadError) {
    console.error('Failed to upload test document:', uploadError);
    throw uploadError;
  }

  // Create document record
  const testDoc = {
    id: crypto.randomUUID(), // Document ID should be unique, not match user ID
    user_id: userId,
    filename: filename,
    content_type: 'application/pdf',
    status: 'processing',
    storage_path: storagePath
  };

  const { error: insertError } = await client
    .from('documents')
    .insert(testDoc);

  if (insertError) {
    // Clean up uploaded file if document creation fails
    await client.storage.from('documents').remove([storagePath]);
    throw insertError;
  }

  return testDoc;
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

// Helper function to verify processing logs
async function verifyProcessingLogs(client: SupabaseClient, document_id: string) {
  const logs = await getProcessingLogs(client, document_id);
  if (!logs || logs.length === 0) {
    throw new Error('No processing logs found');
  }
  
  // Verify we have logs for each stage
  const expectedStages = [
    'metadata_fetch',
    'status_update',
    'document_download',
    'chunk_creation',
    'chunk_storage',
    'vector_generation',
    'completion_update',
    'processing_complete'
  ];

  // Check that we have all expected stages
  const stages = logs.map(log => log.stage);
  for (const expectedStage of expectedStages) {
    assertEquals(
      stages.includes(expectedStage),
      true,
      `Missing log for stage: ${expectedStage}`
    );
  }

  // Verify each log has required metadata
  for (const log of logs) {
    // Basic log structure
    assertExists(log.id, 'Log should have an ID');
    assertExists(log.document_id, 'Log should have a document_id');
    assertExists(log.stage, 'Log should have a stage');
    assertExists(log.status, 'Log should have a status');
    assertExists(log.metadata, 'Log should have metadata');

    // Metadata fields
    const metadata = log.metadata;
    assertExists(metadata.timestamp, 'Metadata should have timestamp');
    assertExists(metadata.memory_usage, 'Metadata should have memory_usage');
    assertExists(metadata.duration_ms, 'Metadata should have duration_ms');
    assertExists(metadata.stage_number, 'Metadata should have stage_number');
    assertExists(metadata.total_stages_completed, 'Metadata should have total_stages_completed');

    // Stage-specific metadata
    switch (log.stage) {
      case 'metadata_fetch':
        assertExists(metadata.document_type, 'Metadata fetch should have document_type');
        assertExists(metadata.filename, 'Metadata fetch should have filename');
        break;
      case 'document_download':
        assertExists(metadata.size, 'Document download should have size');
        assertExists(metadata.content_type, 'Document download should have content_type');
        break;
      case 'chunk_creation':
        assertExists(metadata.chunk_count, 'Chunk creation should have chunk_count');
        assertExists(metadata.avg_chunk_size, 'Chunk creation should have avg_chunk_size');
        break;
      case 'chunk_storage':
        assertExists(metadata.chunks_stored, 'Chunk storage should have chunks_stored');
        break;
      case 'vector_generation':
        assertExists(metadata.vectors_generated, 'Vector generation should have vectors_generated');
        break;
      case 'processing_complete':
        assertExists(metadata.total_chunks, 'Processing complete should have total_chunks');
        assertExists(metadata.total_vectors, 'Processing complete should have total_vectors');
        assertExists(metadata.processing_time_ms, 'Processing complete should have processing_time_ms');
        assertExists(metadata.stage_timings, 'Processing complete should have stage_timings');
        break;
    }

    // Verify timing data
    if (metadata.duration_ms !== undefined) {
      assertEquals(
        typeof metadata.duration_ms,
        'number',
        'duration_ms should be a number'
      );
      assertEquals(
        metadata.duration_ms >= 0,
        true,
        'duration_ms should be non-negative'
      );
    }
  }

  // Verify processing completion
  const completionLog = logs.find(log => log.stage === 'processing_complete');
  assertExists(completionLog, 'Should have a processing_complete log');
  assertEquals(completionLog.status, 'success', 'Final status should be success');
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

// Helper function to verify document chunks
async function verifyDocumentChunks(client: SupabaseClient, document_id: string): Promise<boolean> {
  const { data: chunks, error } = await client
    .from('document_chunks')
    .select('*')
    .eq('document_id', document_id)
    .order('chunk_index', { ascending: true });

  if (error) {
    console.error('Failed to fetch chunks:', error);
    throw error;
  }

  if (!chunks || chunks.length === 0) {
    throw new Error('No chunks found for document');
  }

  // Verify each chunk has required fields
  chunks.forEach((chunk, index) => {
    assertExists(chunk.id, 'Chunk should have an ID');
    assertExists(chunk.document_id, 'Chunk should have a document_id');
    assertExists(chunk.content, 'Chunk should have content');
    assertExists(chunk.chunk_index, 'Chunk should have an index');
    assertEquals(chunk.chunk_index, index, 'Chunk indices should be sequential');
  });

  return true;
}

// Helper function to verify document vectors
async function verifyDocumentVectors(client: SupabaseClient, document_id: string): Promise<boolean> {
  // First get all chunks for the document
  const { data: chunks, error: chunksError } = await client
    .from('document_chunks')
    .select('id')
    .eq('document_id', document_id);

  if (chunksError) {
    console.error('Failed to fetch chunks:', chunksError);
    throw chunksError;
  }

  if (!chunks || chunks.length === 0) {
    throw new Error('No chunks found for document');
  }

  // Then verify vectors exist for each chunk
  for (const chunk of chunks) {
    const { data: vectors, error: vectorError } = await client
      .from('document_vectors')
      .select('*')
      .eq('chunk_id', chunk.id);

    if (vectorError) {
      console.error('Failed to fetch vectors:', vectorError);
      throw vectorError;
    }

    if (!vectors || vectors.length === 0) {
      throw new Error(`No vectors found for chunk ${chunk.id}`);
    }

    // Verify each vector has required fields and dimensions
    vectors.forEach(vector => {
      assertExists(vector.id, 'Vector should have an ID');
      assertExists(vector.chunk_id, 'Vector should have a chunk_id');
      assertExists(vector.vector_data, 'Vector should have vector_data');
      assertEquals(vector.vector_data.length, 1536, 'Vector should have 1536 dimensions (text-embedding-3-small)');
    });
  }

  return true;
}

// Helper function to wait for document status
async function waitForDocumentStatus(client: SupabaseClient, documentId: string, targetStatus: string, maxAttempts = 30): Promise<void> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const { data: document } = await client
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .single();

    if (document?.status === targetStatus) {
      return;
    }

    // Check edge function logs
    const logs = await getEdgeFunctionLogs(client, 'doc-processor');
    if (logs.length > 0) {
      console.log('Edge Function Logs:');
      logs.forEach(log => {
        console.log(`[${log.status}] ${log.function_name} - ${log.execution_time_ms}ms`);
        if (log.metadata) {
          console.log('Metadata:', log.metadata);
        }
        if (log.error_message) {
          console.log('Error:', log.error_message);
        }
      });
    }

    console.log(`Current processing stage: ${document?.status || 'unknown'}`);
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  throw new Error(`Timeout waiting for document status to become ${targetStatus}`);
}

// Helper function to display edge function logs
async function displayEdgeFunctionLogs(client: SupabaseClient, functionName: string) {
  const { data: logs, error } = await client
    .schema('monitoring')
    .from('edge_function_logs')
    .select('*')
    .eq('function_name', functionName)
    .order('created_at', { ascending: true });

  if (error) {
    console.error('Failed to fetch edge function logs:', error);
    return;
  }

  console.log('\nEdge Function Logs:');
  console.log('===================');
  for (const log of logs) {
    console.log(`[${new Date(log.created_at).toISOString()}] ${log.status.toUpperCase()}`);
    console.log(`Request ID: ${log.request_id}`);
    console.log(`Execution Time: ${log.execution_time_ms}ms`);
    console.log(`Memory Usage: ${log.memory_usage_mb.toFixed(2)}MB`);
    if (log.error_message) {
      console.log(`Error: ${log.error_message}`);
    }
    if (log.metadata) {
      console.log('Metadata:', JSON.stringify(log.metadata, null, 2));
    }
    console.log('-------------------');
  }
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
Deno.test("Document Upload Flow", async (t) => {
  const jwt = await createServiceRoleJWT();
  const client = createClient(
    edgeConfig.supabaseUrl,
    edgeConfig.supabaseKey,
    {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
        detectSessionInUrl: false
      },
      global: {
        headers: {
          Authorization: `Bearer ${jwt}`
        }
      }
    }
  );
  let userId: string | undefined;
  let testDoc: TestDocument | undefined;

  try {
    // Create test user
    userId = await createTestUser(client);

    // Create test document
    testDoc = await createTestDocument(client, userId);

    // Verify document was created with correct user_id
    assertEquals(testDoc.user_id, userId, 'Document should be associated with the correct user');
    assertEquals(testDoc.status, 'processing', 'Document should be in processing state');
    assertExists(testDoc.storage_path, 'Document should have a storage path');

  } catch (error) {
    console.error('Test failed:', error);
    throw error;
  } finally {
    // Cleanup
    if (testDoc?.id) {
      await client.from('documents').delete().eq('id', testDoc.id);
    }
    if (userId) {
      await client.from('users').delete().eq('id', userId);
    }
  }
});

// Test document parsing with LlamaParse
Deno.test("Test Document Parsing Stage", async () => {
  // Use service role client for all operations
  const client = getServiceRoleClient();
  
  try {
    console.log("Creating test document...");
    const testDoc = await createTestDocument(client, "test-user-" + Math.random().toString(36).substring(7));
    console.log("Test document created:", testDoc.id);

    // Create test PDF content
    const testContent = new Blob(["Test PDF content"], { type: "application/pdf" });
    
    // Upload to raw directory
    const rawPath = `buckets/raw/${testDoc.storage_path}`;
    await client.storage
      .from("documents")
      .upload(rawPath, testContent, {
        contentType: "application/pdf",
        upsert: true
      });
    console.log("Test file uploaded to:", rawPath);
    
    // Call doc-processor function
    const response = await fetch(`${Deno.env.get("SUPABASE_URL")}/functions/v1/doc-processor`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        documentId: testDoc.id
      })
    });

    assertEquals(response.status, 200, "Doc processor should return 200");
    const result: ProcessingResult = await response.json();
    assertEquals(result.success, true, "Processing should succeed");
    assertEquals(result.document_id, testDoc.id, "Document ID should match");
    assertEquals(result.status, "parsed", "Status should be parsed");
    assertExists(result.metadata, "Metadata should exist");
    
    // Verify document was processed
    const processedDoc = await waitForDocumentStatus(client, testDoc.id, "parsed");
    assertEquals(processedDoc.status, "parsed", "Document should be marked as parsed");
    
    // Verify storage paths
    const parsedPath = `buckets/parsed/${testDoc.storage_path}`;
    const { data: parsedContent } = await client.storage
      .from("documents")
      .download(parsedPath);
    assertExists(parsedContent, "Parsed content should exist");

    // Display processing logs
    const logs = await getProcessingLogs(client, testDoc.id);
    displayProcessingLogs(logs);

    console.log("Test completed successfully");

  } catch (error) {
    console.error("Test failed:", error);
    throw error;
  } finally {
    // Cleanup
    if (testDoc?.id) {
      await client.from("documents").delete().eq("id", testDoc.id);
      await client.storage.from("documents").remove([
        `buckets/raw/${testDoc.storage_path}`,
        `buckets/parsed/${testDoc.storage_path}`
      ]);
    }
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
  // Initialize test environment and client
  await loadEnvironment();
  const client = await initializeTestClient();
  const userId = crypto.randomUUID();
  let testDoc = null;

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

    // Create test document
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

    testDoc = doc;
    assertExists(testDoc.id, 'Document should have an ID');
    assertEquals(testDoc.user_id, userId, 'Document should be associated with the correct user');

    // Upload test PDF
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

    // Call the Edge Function
    console.log('Calling document processor...');
    const response = await fetch('http://127.0.0.1:54321/functions/v1/doc-processor', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        document_id: testDoc.id
      })
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to call document processor: ${error}`);
    }

    // Wait for document processing
    console.log('Waiting for document processing...');
    const processedDoc = await waitForDocumentStatus(client, testDoc.id, 'completed', 30);
    assertEquals(processedDoc.status, 'completed', 'Document should be processed');

    // Display edge function logs
    console.log('Fetching edge function logs...');
    await displayEdgeFunctionLogs(client, 'doc-processor');

    // Verify processing results
    console.log('Verifying processing results...');
    await verifyProcessingLogs(client, testDoc.id);
    await verifyDocumentChunks(client, testDoc.id);
    await verifyDocumentVectors(client, testDoc.id);

    console.log('Pipeline test completed successfully');
  } catch (error) {
    console.error('Pipeline test failed:', error);
    
    // Display edge function logs on failure for debugging
    if (testDoc?.id) {
      console.log('\nEdge Function Logs for Failed Test:');
      await displayEdgeFunctionLogs(client, 'doc-processor');
    }
    
    throw error;
  } finally {
    // Cleanup test data
    if (testDoc?.id) {
      await client
        .from('documents')
        .delete()
        .eq('id', testDoc.id);
    }
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
  let userId: string | undefined;
  let testDoc: TestDocument | undefined;

  try {
    console.log('\nStarting document processing test');
    console.log('--------------------------------');
    
    // Create test user
    console.log('\nCreating test user...');
    userId = await createTestUser(client);
    console.log('Test user created:', userId);
    
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
    
    // Verify processing logs
    console.log('\nVerifying processing logs...');
    await verifyProcessingLogs(client, testDoc.id);
    
    // Get final processing logs for display
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

    // Display timing summary
    const completionLog = finalLogs.find(log => log.stage === 'processing_complete');
    if (completionLog?.metadata.stage_timings) {
      console.log('\nProcessing Stage Timings:');
      console.log('------------------------');
      for (const [stage, duration] of Object.entries(completionLog.metadata.stage_timings)) {
        console.log(`${stage}: ${duration}ms`);
      }
      console.log('------------------------');
      console.log(`Total Processing Time: ${completionLog.metadata.processing_time_ms}ms`);
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
    if (userId) {
      await client.from('users').delete().eq('id', userId);
      console.log('Test user deleted');
    }
    console.log('Test cleanup completed');
  }
}); 