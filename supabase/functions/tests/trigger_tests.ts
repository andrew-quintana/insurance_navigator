import { describe, it, beforeAll, beforeEach, afterEach, expect } from '@jest/globals';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { edgeConfig } from '../_shared/environment';

interface TestDocument {
  id: string;
  user_id: string;
  filename: string;
  content_type: string;
  status: string;
  storage_path: string;
}

describe('Document Processing Triggers', () => {
  let client: SupabaseClient;
  let testDocId: string;
  const testUserId = `test-user-${Math.random().toString(36).substring(7)}`;

  beforeAll(() => {
    client = createClient(edgeConfig.supabaseUrl, edgeConfig.supabaseKey);
  });

  beforeEach(async () => {
    // Create test document
    const { data: doc, error: docError } = await client
      .from('documents')
      .insert({
        user_id: testUserId,
        filename: 'test.pdf',
        content_type: 'application/pdf',
        status: 'pending',
        storage_path: `${testUserId}/test.pdf`
      })
      .select()
      .single<TestDocument>();

    if (docError || !doc) throw docError || new Error('No document created');
    testDocId = doc.id;
  });

  afterEach(async () => {
    if (testDocId) {
      // Clean up document vectors
      await client.from('document_vectors').delete().eq('document_id', testDocId);
      
      // Clean up document chunks
      await client.from('document_chunks').delete().eq('document_id', testDocId);
      
      // Clean up document
      await client.from('documents').delete().eq('id', testDocId);
      
      // Clean up storage
      await client.storage.from('documents').remove([
        `buckets/raw/${testUserId}/test.pdf`,
        `buckets/parsed/${testUserId}/test.pdf`
      ]);
    }
  });

  describe('Document Upload Trigger', () => {
    it('should trigger document processing on file upload', async () => {
      // Upload test file to trigger processing
      const testContent = new Blob(['Test PDF content'], { type: 'application/pdf' });
      const { error: uploadError } = await client
        .storage
        .from('documents')
        .upload(`buckets/raw/${testUserId}/test.pdf`, testContent);

      expect(uploadError).toBeNull();

      // Wait for processing to complete (adjust timeout as needed)
      let processedDoc: TestDocument | null = null;
      for (let i = 0; i < 10; i++) {
        const { data: doc } = await client
          .from('documents')
          .select()
          .eq('id', testDocId)
          .single<TestDocument>();

        if (doc?.status === 'parsed' || doc?.status === 'error') {
          processedDoc = doc;
          break;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      expect(processedDoc).not.toBeNull();
      expect(['parsed', 'error']).toContain(processedDoc?.status);
    });

    it('should handle invalid file upload gracefully', async () => {
      // Upload invalid file to test error handling
      const invalidContent = new Blob(['Invalid PDF'], { type: 'application/pdf' });
      const { error: uploadError } = await client
        .storage
        .from('documents')
        .upload(`buckets/raw/${testUserId}/invalid.pdf`, invalidContent);

      expect(uploadError).toBeNull();

      // Wait for error status
      let errorDoc: TestDocument | null = null;
      for (let i = 0; i < 10; i++) {
        const { data: doc } = await client
          .from('documents')
          .select()
          .eq('id', testDocId)
          .single<TestDocument>();

        if (doc?.status === 'error') {
          errorDoc = doc;
          break;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      expect(errorDoc).not.toBeNull();
      expect(errorDoc?.status).toBe('error');
    });
  });

  describe('Chunking Trigger', () => {
    it('should trigger chunking when document is parsed', async () => {
      // Update document status to parsed to trigger chunking
      await client
        .from('documents')
        .update({ status: 'parsed' })
        .eq('id', testDocId);

      // Wait for chunking to complete
      let chunkedDoc: TestDocument | null = null;
      for (let i = 0; i < 10; i++) {
        const { data: doc } = await client
          .from('documents')
          .select()
          .eq('id', testDocId)
          .single<TestDocument>();

        if (doc?.status === 'chunked' || doc?.status === 'error') {
          chunkedDoc = doc;
          break;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      expect(chunkedDoc).not.toBeNull();
      expect(['chunked', 'error']).toContain(chunkedDoc?.status);

      if (chunkedDoc?.status === 'chunked') {
        // Verify chunks were created
        const { data: chunks } = await client
          .from('document_chunks')
          .select()
          .eq('document_id', testDocId);

        expect(chunks).toBeDefined();
        expect(chunks?.length).toBeGreaterThan(0);
      }
    });
  });

  describe('Vector Generation Trigger', () => {
    it('should trigger vector generation when document is chunked', async () => {
      // Create test chunks
      const chunks = [
        {
          document_id: testDocId,
          content: 'Test content chunk 1',
          metadata: {
            section_title: 'Test Section',
            section_level: 1,
            chunk_index: 0,
            total_chunks: 2
          }
        },
        {
          document_id: testDocId,
          content: 'Test content chunk 2',
          metadata: {
            section_title: 'Test Section',
            section_level: 1,
            chunk_index: 1,
            total_chunks: 2
          }
        }
      ];

      await client.from('document_chunks').insert(chunks);

      // Update document status to chunked to trigger vector generation
      await client
        .from('documents')
        .update({ status: 'chunked' })
        .eq('id', testDocId);

      // Wait for vector generation to complete
      let vectorizedDoc: TestDocument | null = null;
      for (let i = 0; i < 10; i++) {
        const { data: doc } = await client
          .from('documents')
          .select()
          .eq('id', testDocId)
          .single<TestDocument>();

        if (doc?.status === 'vectorized' || doc?.status === 'error') {
          vectorizedDoc = doc;
          break;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      expect(vectorizedDoc).not.toBeNull();
      expect(['vectorized', 'error']).toContain(vectorizedDoc?.status);

      if (vectorizedDoc?.status === 'vectorized') {
        // Verify vectors were created
        const { data: vectors } = await client
          .from('document_vectors')
          .select()
          .eq('document_id', testDocId);

        expect(vectors).toBeDefined();
        expect(vectors?.length).toBe(2); // Should match number of chunks
      }
    });
  });
}); 