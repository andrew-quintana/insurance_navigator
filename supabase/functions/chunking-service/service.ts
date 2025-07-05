import { SupabaseClient } from "@supabase/supabase-js";
import { SectionChunker } from "./section_chunker.ts";
import { ChunkMetadata } from "./types.ts";

export interface ChunkingResult {
  success: boolean;
  document_id?: string;
  status?: string;
  error?: string;
  metadata?: {
    chunk_count: number;
    sections: string[];
  };
}

export class ChunkingService {
  private client: SupabaseClient;
  private chunker: SectionChunker;

  constructor(client: SupabaseClient, chunker: SectionChunker) {
    this.client = client;
    this.chunker = chunker;
  }

  async processDocument(documentId: string): Promise<ChunkingResult> {
    try {
      // Get document
      const { data: doc, error: docError } = await this.client
        .from('documents')
        .select()
        .eq('id', documentId)
        .single();

      if (docError || !doc) {
        return {
          success: false,
          document_id: documentId,
          status: 'error',
          error: docError?.message || 'Document not found'
        };
      }

      // Get parsed content
      const { data: parsedFile, error: fileError } = await this.client
        .storage
        .from('documents')
        .download(`buckets/parsed/${doc.user_id}/test.pdf`);

      if (fileError || !parsedFile) {
        return {
          success: false,
          document_id: documentId,
          status: 'error',
          error: fileError?.message || 'Content not found'
        };
      }

      const parsedContent = JSON.parse(await parsedFile.text());
      const chunks = await this.chunker.createChunks(parsedContent.text);

      // Store chunks
      const chunkData = chunks.map((chunk, index) => ({
        document_id: documentId,
        content: chunk.pageContent,
        metadata: {
          ...chunk.metadata,
          chunk_index: index,
          total_chunks: chunks.length
        } as ChunkMetadata
      }));

      const { error: insertError } = await this.client
        .from('document_chunks')
        .insert(chunkData);

      if (insertError) {
        return {
          success: false,
          document_id: documentId,
          status: 'error',
          error: insertError.message
        };
      }

      // Update document status
      const { error: updateError } = await this.client
        .from('documents')
        .update({ status: 'chunked' })
        .eq('id', documentId);

      if (updateError) {
        return {
          success: false,
          document_id: documentId,
          status: 'error',
          error: updateError.message
        };
      }

      return {
        success: true,
        document_id: documentId,
        status: 'chunked',
        metadata: {
          chunk_count: chunks.length,
          sections: [...new Set(chunks.map(c => c.metadata.section_title))]
        }
      };
    } catch (error: unknown) {
      return {
        success: false,
        document_id: documentId,
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
} 