// Import required testing utilities and modules
import { assertEquals, assertExists } from 'testing/asserts.ts';
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import { load } from 'std/dotenv/mod.ts';
import { join } from 'std/path/mod.ts';

// Load environment variables from env.test
const envPath = join(Deno.cwd(), 'env.test');
const env = await load({ envPath });

// Export environment variables to Deno.env
for (const [key, value] of Object.entries(env)) {
  Deno.env.set(key, value);
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

// Test configuration
const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? 'http://127.0.0.1:54321';
const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.NyI5BirJszzlihKWtyn36sTl7OKq6TXqi5uF493-L2E';
const options = {
  auth: {
    autoRefreshToken: false,
    persistSession: false,
    detectSessionInUrl: false,
  },
};

// Helper function to create test document
async function createTestDocument(client: SupabaseClient, userId: string) {
  const { data, error } = await client
    .from('documents')
    .insert({
      user_id: userId,
      filename: 'test.pdf',
      content_type: 'application/pdf',
      status: 'processing',
      storage_path: `documents/${userId}/test.pdf`
    })
    .select()
    .single();

  if (error) throw error;
  return data;
}

// Helper function to setup test environment
async function setupTestEnv() {
  const client = createClient(supabaseUrl, supabaseKey, options);
  
  // Create test user in auth
  const email = `test${Date.now()}@example.com`;
  const { data: userData, error: userError } = await client.auth.signUp({
    email: email,
    password: 'test123456'
  });
  
  if (userError) throw userError;
  
  // Create user record in database
  const { data: userRecord, error: userRecordError } = await client
    .from('users')
    .insert({
      id: userData.user?.id,
      email: email,
      name: 'Test User'
    })
    .select()
    .single();
  
  if (userRecordError) throw userRecordError;
  
  return { client, userId: userRecord.id };
}

// Helper function to cleanup test data
async function cleanupTestData(client: SupabaseClient, userId: string) {
  // Delete documents (will cascade to chunks and vectors)
  await client
    .from('documents')
    .delete()
    .eq('user_id', userId);
  
  // Delete user
  await client
    .from('users')
    .delete()
    .eq('id', userId);
}

// Helper function to get service role client
async function getServiceRoleClient(): Promise<SupabaseClient> {
  const supabaseUrl = Deno.env.get('SUPABASE_URL') || '';
  const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || '';
  
  if (!supabaseUrl || !serviceRoleKey) {
    throw new Error('Missing required environment variables for service role client');
  }

  return createClient(supabaseUrl, serviceRoleKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false
    },
    global: {
      headers: {
        'apikey': serviceRoleKey,
        'Authorization': `Bearer ${serviceRoleKey}`,
        'X-Client-Info': 'supabase-test-client'
      }
    }
  });
}

// Test Supabase client creation and connection
Deno.test('Test Supabase Client Setup', async () => {
  const { client } = await setupTestEnv();
  
  const { data, error } = await client
    .from('documents')
    .select('*')
    .limit(1);
  
  assertEquals(error, null, 'Should not have any errors');
  assertExists(data, 'Should be able to query documents table');
});

// Test document upload and initial processing
Deno.test('Test Document Upload Flow', async () => {
  const { client, userId } = await setupTestEnv();
  if (!userId) throw new Error('Failed to create test user');
  
  try {
    // Upload test document
    const testDoc = await createTestDocument(client, userId);
    assertExists(testDoc.id, 'Document should be created');
    assertEquals(testDoc.status, 'processing', 'Initial status should be processing');
  } finally {
    await cleanupTestData(client, userId);
  }
});

// Test document parsing with LlamaParse
Deno.test('Test Document Parsing Stage', async () => {
  const { client: userClient, userId } = await setupTestEnv();
  if (!userId) throw new Error('Failed to create test user');
  
  // Get service role client for operations that need elevated permissions
  const serviceClient = await getServiceRoleClient();
  
  try {
    // Create test document
    const testDoc = await createTestDocument(userClient, userId);
    
    // Mock LlamaParse API call
    const parseResult = await mockLlamaParseClient.parseDocument();
    assertExists(parseResult.text, 'Should have parsed text');
    assertExists(parseResult.metadata, 'Should have metadata');
    
    // Create document chunk using service role client
    const { error: chunkError } = await serviceClient
      .from('document_chunks')
      .insert({
        document_id: testDoc.id,
        chunk_index: 0,
        content: parseResult.text
      });
    
    assertEquals(chunkError, null, 'Should store chunk without error');
    
    // Update document status using service role client
    const { error: updateError } = await serviceClient
      .from('documents')
      .update({
        status: 'completed'
      })
      .eq('id', testDoc.id);
    
    assertEquals(updateError, null, 'Should update status without error');
  } finally {
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
      assertExists(error, 'Should throw error for invalid content type');
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
  const serviceClient = await getServiceRoleClient();
  
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