import { SupabaseClient } from "@supabase/supabase-js";
import { Document, ProcessingMetadata, DocumentNotFoundError } from "./types.ts";

export async function getDocument(
  client: SupabaseClient,
  userId: string,
  documentId: string
): Promise<Document | null> {
  try {
    const { data, error } = await client
      .from("documents")
      .select("*")
      .eq("id", documentId)
      .eq("user_id", userId)
      .single();

    if (error) {
      if (error.code === '23505') {
        // Duplicate key error - this means the document exists but we can't access it
        throw new DocumentNotFoundError(documentId);
      }
      throw error;
    }

    if (!data) {
      throw new DocumentNotFoundError(documentId);
    }

    return data as Document;
  } catch (error) {
    if (error instanceof DocumentNotFoundError) {
      throw error;
    }
    throw new DocumentNotFoundError(documentId);
  }
}

export async function checkFileExists(
  client: SupabaseClient,
  storagePath: string
): Promise<boolean> {
  const { data, error } = await client.storage
    .from('documents')
    .download(storagePath);

  try {
    // Case 1: Response object
    if (data instanceof Response) {
      await data.body?.cancel();
      return data.ok;
    }

    // Case 2: Blob or ArrayBuffer
    if (data instanceof Blob || data instanceof ArrayBuffer) {
      return true;
    }

    // Case 3: Object with arrayBuffer method
    if (data && typeof data === 'object' && 'arrayBuffer' in data) {
      await data.arrayBuffer();
      return true;
    }

    // Case 4: ReadableStream
    if (data && typeof data === 'object' && 'getReader' in data) {
      const reader = (data as ReadableStream).getReader();
      await reader.cancel();
      return true;
    }

    // Case 5: Simple object with data property
    if (data && typeof data === 'object') {
      return true;
    }

    return false;
  } catch (e) {
    console.error('Error checking file existence:', e);
    return false;
  } finally {
    // Extra safety: try to clean up any potential response body
    if (data && typeof data === 'object') {
      try {
        if ('body' in data && data.body?.cancel) {
          await data.body.cancel();
        }
        if ('getReader' in data) {
          await (data as ReadableStream).getReader().cancel();
        }
      } catch {
        // Ignore cleanup errors
      }
    }
  }
}

export async function updateDocumentStatus(
  client: SupabaseClient,
  documentId: string,
  status: string,
  error?: string
): Promise<void> {
  try {
    const updateData = {
      status,
      error_message: error,
      updated_at: new Date().toISOString()
    };

    const { error: updateError } = await client
      .from('documents')
      .update(updateData)
      .eq('id', documentId);

    if (updateError) {
      console.error('Failed to update document status:', updateError);
      throw updateError;
    }
  } catch (error) {
    console.error('Error updating document status:', error);
    throw error;
  }
}

export async function logProcessingStep(
  client: SupabaseClient,
  documentId: string,
  status: string,
  metadata: Record<string, unknown>,
  error?: string
): Promise<void> {
  try {
    const { error: logError } = await client
      .from('document_processing_logs')
      .insert({
        document_id: documentId,
        status,
        metadata,
        error_message: error,
        created_at: new Date().toISOString()
      });

    if (logError) {
      console.error('Failed to log processing step:', logError);
    }
  } catch (error) {
    console.error('Error logging processing step:', error);
  }
}

export function getMemoryUsage(): number {
  try {
    return Deno.memoryUsage().heapUsed / 1024 / 1024; // Convert to MB
  } catch (error) {
    console.error('Error getting memory usage:', error);
    return 0;
  }
}

async function consumeResponseBody(data: unknown): Promise<void> {
  if (!data) {
    console.log('consumeResponseBody: No data to consume');
    return;
  }

  try {
    console.log('consumeResponseBody: Attempting to consume data type:', typeof data);
    
    // Case 1: Blob or ArrayBuffer
    if (typeof data === 'object' && data !== null) {
      if ('arrayBuffer' in data) {
        console.log('consumeResponseBody: Handling object with arrayBuffer');
        await (data as { arrayBuffer: () => Promise<ArrayBuffer> }).arrayBuffer();
        return;
      }

      if ('getReader' in data) {
        console.log('consumeResponseBody: Handling ReadableStream');
        await (data as { getReader: () => { cancel: () => Promise<void> } })
          .getReader()
          .cancel();
        return;
      }

      if ('body' in data) {
        const bodyObj = data as { body?: { cancel?: () => Promise<void> } };
        if (bodyObj.body?.cancel) {
          console.log('consumeResponseBody: Handling object with cancellable body');
          await bodyObj.body.cancel();
          return;
        }
      }
    }

    console.log('consumeResponseBody: Data type not handled:', data);
  } catch (e) {
    console.error('Error consuming response body:', e);
  }
}

export { consumeResponseBody };

export function validatePath(path: string): boolean {
  if (!path) return false;
  
  // Check for path traversal attempts
  if (path.includes('..') || path.startsWith('/') || path.startsWith('\\')) {
    return false;
  }

  // Check for valid file name
  const validFileNameRegex = /^[a-zA-Z0-9-_. ]+\.[a-zA-Z0-9]+$/;
  return validFileNameRegex.test(path);
} 