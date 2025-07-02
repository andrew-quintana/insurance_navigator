import { SupabaseClient } from "@supabase/supabase-js";

interface ProcessingResult {
  success: boolean;
  document_id: string;
  status: string;
  error?: string;
}

export async function processDocument(
  document_id: string,
  supabase: SupabaseClient
): Promise<ProcessingResult> {
  try {
    // Get document metadata
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', document_id)
      .single();

    if (docError) throw docError;
    if (!document) throw new Error('Document not found');

    // Update document status to processing
    const { error: updateError } = await supabase
      .from('documents')
      .update({ status: 'processing' })
      .eq('id', document_id);

    if (updateError) throw updateError;

    // Log processing start
    await supabase
      .from('monitoring.processing_logs')
      .insert({
        document_id,
        stage: 'processing_start',
        status: 'success',
        processing_time: '0 seconds',
        metadata: { document_type: document.content_type }
      });

    return {
      success: true,
      document_id,
      status: 'processing'
    };

  } catch (error) {
    // Log error
    await supabase
      .from('monitoring.processing_logs')
      .insert({
        document_id,
        stage: 'processing_start',
        status: 'error',
        error_message: error instanceof Error ? error.message : 'Unknown error',
        metadata: { error_type: error instanceof Error ? error.name : 'Unknown' }
      });

    return {
      success: false,
      document_id,
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
} 