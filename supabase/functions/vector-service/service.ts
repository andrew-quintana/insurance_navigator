import { SupabaseClient } from '@supabase/supabase-js';
import { OpenAIEmbeddings } from '@langchain/openai';

interface VectorResult {
  success: boolean;
  document_id: string;
  status: string;
  metadata?: {
    vector_count: number;
    error?: string;
  };
  error?: string;
}

interface DocumentChunk {
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

export class VectorService {
  constructor(
    private client: SupabaseClient,
    private embeddings: OpenAIEmbeddings
  ) {}

  async processDocument(documentId: string): Promise<VectorResult> {
    try {
      // Get document
      const { data: doc, error: docError } = await this.client
        .from('documents')
        .select()
        .eq('id', documentId)
        .single();

      if (docError || !doc) {
        throw new Error(`Failed to fetch document: ${docError?.message || 'Document not found'}`);
      }

      // Get chunks
      const { data: chunks, error: chunksError } = await this.client
        .from('document_chunks')
        .select()
        .eq('document_id', documentId);

      if (chunksError) {
        throw new Error(`Failed to fetch chunks: ${chunksError.message}`);
      }

      if (!chunks || chunks.length === 0) {
        throw new Error('No chunks found for document');
      }

      // Generate embeddings for all chunks
      const chunkTexts = chunks.map(c => c.content);
      const embeddings = await this.embeddings.embedDocuments(chunkTexts);

      // Store vectors
      const vectors = chunks.map((chunk, i) => ({
        document_id: documentId,
        chunk_id: chunk.id,
        embedding: embeddings[i],
        metadata: chunk.metadata
      }));

      const { error: vectorError } = await this.client
        .from('document_vectors')
        .insert(vectors);

      if (vectorError) {
        throw new Error(`Failed to store vectors: ${vectorError.message}`);
      }

      // Update document status
      await this.client
        .from('documents')
        .update({ status: 'vectorized' })
        .eq('id', documentId);

      // Return result
      return {
        success: true,
        document_id: documentId,
        status: 'vectorized',
        metadata: {
          vector_count: vectors.length
        }
      };

    } catch (error) {
      console.error(`Error processing document ${documentId}:`, error);
      return {
        success: false,
        document_id: documentId,
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
} 