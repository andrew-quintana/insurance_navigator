import { describe, it, beforeAll, beforeEach, afterEach, expect } from '@jest/globals';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { VectorService } from '../vector-service/service';
import { OpenAIEmbeddings } from '@langchain/openai';
import { processVectors } from '../vector-service/service';
import { edgeConfig } from '../../../shared/environment';

interface TestDocument {
  id: string;
  user_id: string;
  filename: string;
  content_type: string;
  status: string;
  storage_path: string;
}

interface TestChunk {
  id: string;
  document_id: string;
  content: string;
  metadata: {
    section_title: string;
    section_level: number;
    chunk_index: number;
    total_chunks: number;
  };
}

describe('Vector Service', () => {
  let vectorService: VectorService;
  let client: SupabaseClient;
  let testDocId: string;
  let testChunks: TestChunk[];
  const testUserId = '00000000-0000-4000-a000-000000000000';
  const testDocumentId = '11111111-1111-4111-a111-111111111111';

  beforeAll(() => {
    client = createClient(edgeConfig.supabaseUrl, edgeConfig.supabaseKey);
    
    const embeddings = new OpenAIEmbeddings({
      openAIApiKey: edgeConfig.openaiApiKey,
      modelName: 'text-embedding-3-small'
    });
    
    vectorService = new VectorService(client, embeddings);
  });

  beforeEach(async () => {
    // Create test document
    const { data: doc, error: docError } = await client
      .from('documents')
      .insert({
        user_id: testUserId,
        filename: 'test.pdf',
        content_type: 'application/pdf',
        status: 'chunked',
        storage_path: `${testUserId}/test.pdf`
      })
      .select()
      .single<TestDocument>();

    if (docError || !doc) throw docError || new Error('No document created');
    testDocId = doc.id;

    // Create test chunks
    const chunks = [
      {
        document_id: testDocId,
        content: 'This is the first section of the test document.',
        metadata: {
          section_title: 'Introduction',
          section_level: 1,
          chunk_index: 0,
          total_chunks: 3
        }
      },
      {
        document_id: testDocId,
        content: 'This is the main content section with important information.',
        metadata: {
          section_title: 'Main Content',
          section_level: 1,
          chunk_index: 1,
          total_chunks: 3
        }
      },
      {
        document_id: testDocId,
        content: 'This is the conclusion section summarizing the document.',
        metadata: {
          section_title: 'Conclusion',
          section_level: 1,
          chunk_index: 2,
          total_chunks: 3
        }
      }
    ];

    const { data: insertedChunks, error: chunksError } = await client
      .from('document_chunks')
      .insert(chunks)
      .select();

    if (chunksError || !insertedChunks) {
      throw chunksError || new Error('No chunks created');
    }
    testChunks = insertedChunks as TestChunk[];

    // Clear test data
    await client
      .from('document_chunks')
      .delete()
      .eq('user_id', testUserId);
  });

  afterEach(async () => {
    if (testDocId) {
      // Clean up document vectors
      await client.from('document_vectors').delete().eq('document_id', testDocId);
      
      // Clean up document chunks
      await client.from('document_chunks').delete().eq('document_id', testDocId);
      
      // Clean up document
      await client.from('documents').delete().eq('id', testDocId);
    }
  });

  it('should generate vectors for document chunks', async () => {
    const result = await processVectors(testUserId, testDocumentId, testChunks);
    expect(result.success).toBe(true);
    expect(result.vectors).toHaveLength(testChunks.length);
  });

  it('should handle missing document', async () => {
    const result = await processVectors(testUserId, 'non-existent-id', []);
    expect(result.success).toBe(false);
    expect(result.error).toContain('Document not found');
  });

  it('should handle missing chunks', async () => {
    const result = await processVectors(testUserId, testDocumentId, []);
    expect(result.success).toBe(false);
    expect(result.error).toContain('No chunks provided');
  });

  it('should handle embedding errors', async () => {
    const invalidChunks = [{ id: 1, content: '', metadata: {} }];
    const result = await processVectors(testUserId, testDocumentId, invalidChunks);
    expect(result.success).toBe(false);
    expect(result.error).toContain('Error generating embeddings');
  });

  it('processes vectors with OpenAI', async () => {
    const vectorService = new VectorService(edgeConfig.openaiApiKey);
    // ... rest of test
  });
}); 