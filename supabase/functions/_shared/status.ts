import { SupabaseClient } from 'https://esm.sh/@supabase/supabase-js@2';

/**
 * Valid document processing status values
 */
export type ProcessingStatus = 
    | 'uploaded'    // Initial status after file upload
    | 'parsing' | 'parsing-failed' | 'parsed'  // LlamaParse processing
    | 'processing'  // Intermediate state during LlamaParse job
    | 'chunking' | 'chunking-failed' | 'chunked'  // Document chunking
    | 'embedding' | 'embedding-failed' | 'embedded'  // Vector embedding
    | 'failed';  // Generic failure state

/**
 * Updates a document's processing status and logs any errors
 * @param supabase - Supabase client instance
 * @param docId - Document ID to update
 * @param status - New processing status to set
 * @param error - Optional error object or message to log
 * @param context - Additional context for error logging
 */
export async function updateDocumentStatus(
    supabase: SupabaseClient,
    docId: string,
    status: ProcessingStatus,
    error?: unknown,
    context?: string
): Promise<void> {
    // If there's an error, log it with context
    if (error) {
        let errorMessage: string;
        if (error instanceof Error) {
            errorMessage = error.message;
        } else if (typeof error === 'string') {
            errorMessage = error;
        } else if (error && typeof error === 'object' && 'message' in error) {
            errorMessage = String(error.message);
        } else {
            errorMessage = 'Unknown error';
        }
        console.error(`❌ ${context || 'Error'}: ${errorMessage}`);
    }
    
    // Update document status
    const { error: updateError } = await supabase
        .schema('documents')
        .from('documents')
        .update({ 
            processing_status: status
        })
        .eq("id", docId);

    if (updateError) {
        console.error(`❌ Failed to update document status to ${status}:`, updateError);
    } else if (!error) {
        // Log success for non-error status updates
        console.log(`✅ Document status updated to '${status}'`);
    }
} 