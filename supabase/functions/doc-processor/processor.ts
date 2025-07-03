import { SupabaseClient } from "@supabase/supabase-js";
import { ProcessingMetadata, ProcessingLog } from "./types.ts";

interface ProcessingResult {
  success: boolean;
  document_id: string;
  status: string;
  error?: string;
}

async function logProcessingStep(
  supabase: SupabaseClient,
  document_id: string,
  stage: string,
  status: string,
  metadata: Partial<ProcessingMetadata> = {},
  error_message?: string
) {
  try {
    const memoryUsage = globalThis?.performance?.memory?.usedJSHeapSize || 0;
    await supabase
      .from('processing_logs')
      .insert({
        document_id,
        stage,
        status,
        error_message,
        metadata: {
          ...metadata,
          timestamp: new Date().toISOString(),
          memory_usage: memoryUsage
        }
      });
  } catch (e) {
    console.error('Failed to log processing step:', e);
  }
}

export async function processDocument(
  document_id: string,
  supabase: SupabaseClient
): Promise<ProcessingResult> {
  try {
    console.log(`[${document_id}] Starting document processing`);
    
    // Get document metadata
    console.log(`[${document_id}] Fetching document metadata`);
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', document_id)
      .single();

    if (docError) {
      console.error(`[${document_id}] Failed to fetch document:`, docError);
      throw docError;
    }
    if (!document) {
      console.error(`[${document_id}] Document not found`);
      throw new Error('Document not found');
    }

    // Update document status to processing
    console.log(`[${document_id}] Updating status to processing`);
    const { error: updateError } = await supabase
      .from('documents')
      .update({ status: 'processing' })
      .eq('id', document_id);

    if (updateError) {
      console.error(`[${document_id}] Failed to update status:`, updateError);
      throw updateError;
    }

    await logProcessingStep(supabase, document_id, 'processing_start', 'success', {
      document_type: document.content_type,
      filename: document.filename
    });

    // 1. Download document from storage
    console.log(`[${document_id}] Downloading document from storage`);
    const { data: fileData, error: downloadError } = await supabase
      .storage
      .from('documents')
      .download(document.storage_path);

    if (downloadError) {
      console.error(`[${document_id}] Failed to download document:`, downloadError);
      throw downloadError;
    }

    await logProcessingStep(supabase, document_id, 'download', 'success', {
      size: fileData.size,
      content_type: fileData.type
    });

    // 2. For testing, create a single chunk with mock content
    console.log(`[${document_id}] Creating test document chunk`);
    const mockContent = `Test content for document ${document_id}. This is a mock chunk for testing purposes.`;
    const chunks = [mockContent];

    console.log(`[${document_id}] Created ${chunks.length} chunks`);
    await logProcessingStep(supabase, document_id, 'chunking', 'success', {
      chunk_count: chunks.length,
      avg_chunk_size: mockContent.length
    });

    // 3. Store chunks
    console.log(`[${document_id}] Storing chunks in database`);
    for (let i = 0; i < chunks.length; i++) {
      console.log(`[${document_id}] Storing chunk ${i + 1}/${chunks.length}`);
      const { error: chunkError } = await supabase
        .from('document_chunks')
        .insert({
          document_id,
          chunk_index: i,
          content: chunks[i]
        });

      if (chunkError) {
        console.error(`[${document_id}] Failed to store chunk ${i}:`, chunkError);
        throw chunkError;
      }
    }

    await logProcessingStep(supabase, document_id, 'chunk_storage', 'success', {
      chunks_stored: chunks.length
    });

    // 4. Generate vectors (using mock vectors for testing)
    console.log(`[${document_id}] Generating vectors for chunks`);
    for (let i = 0; i < chunks.length; i++) {
      console.log(`[${document_id}] Generating vector for chunk ${i + 1}/${chunks.length}`);
      const { data: chunk, error: chunkError } = await supabase
        .from('document_chunks')
        .select('id')
        .eq('document_id', document_id)
        .eq('chunk_index', i)
        .single();

      if (chunkError || !chunk) {
        console.error(`[${document_id}] Failed to get chunk ${i}:`, chunkError);
        throw new Error(`Failed to get chunk ${i}: ${chunkError?.message || 'Chunk not found'}`);
      }

      const mockVector = new Array(1536).fill(0.1);
      const { error: vectorError } = await supabase
        .from('document_vectors')
        .insert({
          chunk_id: chunk.id,
          vector_data: mockVector
        });

      if (vectorError) {
        console.error(`[${document_id}] Failed to store vector for chunk ${i}:`, vectorError);
        throw vectorError;
      }
    }

    await logProcessingStep(supabase, document_id, 'vector_generation', 'success', {
      vectors_generated: chunks.length
    });

    // 5. Update document status to processed
    console.log(`[${document_id}] Updating status to completed`);
    const { error: finalUpdateError } = await supabase
      .from('documents')
      .update({ status: 'completed' })
      .eq('id', document_id);

    if (finalUpdateError) {
      console.error(`[${document_id}] Failed to update final status:`, finalUpdateError);
      throw finalUpdateError;
    }

    await logProcessingStep(supabase, document_id, 'processing_complete', 'success', {
      total_chunks: chunks.length,
      total_vectors: chunks.length,
      processing_time: `${Date.now() - new Date(document.created_at).getTime()}ms`
    });

    console.log(`[${document_id}] Document processing completed successfully`);
    return {
      success: true,
      document_id,
      status: 'completed'
    };

  } catch (error) {
    console.error(`[${document_id}] Document processing failed:`, error);
    
    // Log the error
    await logProcessingStep(supabase, document_id, 'error', 'failed', {
      error_type: error instanceof Error ? error.name : 'UnknownError'
    }, error instanceof Error ? error.message : 'Unknown error');
    
    // Update document status to error
    try {
      await supabase
        .from('documents')
        .update({
          status: 'error',
          error_message: error instanceof Error ? error.message : 'Unknown error'
        })
        .eq('id', document_id);
    } catch (updateError) {
      console.error(`[${document_id}] Failed to update error status:`, updateError);
    }

    return {
      success: false,
      document_id,
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
} 