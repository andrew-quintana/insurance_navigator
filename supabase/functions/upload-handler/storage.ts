import { SupabaseClient } from "@supabase/supabase-js";
import { UploadHandlerError } from "./types";

interface StorageError {
  message: string;
  statusCode?: number;
  originalError?: {
    status?: number;
    statusText?: string;
  };
}

interface RemoveFilesResult {
  error?: string;
}

async function consumeResponseBody(data: unknown): Promise<void> {
  if (!data) {
    console.log('consumeResponseBody: No data to consume');
    return;
  }

  try {
    console.log('consumeResponseBody: Attempting to consume data type:', typeof data);
    
    // Handle Response objects
    if (data instanceof Response) {
      console.log('consumeResponseBody: Handling Response object');
      await data.body?.cancel();
      return;
    }

    // Handle objects with response property
    if (data && typeof data === 'object' && 'originalError' in data) {
      const error = (data as { originalError: Response }).originalError;
      if (error instanceof Response) {
        console.log('consumeResponseBody: Handling error Response object');
        await error.body?.cancel();
        return;
      }
    }

    // Handle objects with body property
    if (data && typeof data === 'object' && 'body' in data) {
      const bodyObj = data as { body?: { cancel?: () => Promise<void> } };
      if (bodyObj.body?.cancel) {
        console.log('consumeResponseBody: Handling object with cancellable body');
        await bodyObj.body.cancel();
        return;
      }
    }

    console.log('consumeResponseBody: Data type not handled:', data);
  } catch (error) {
    console.error('consumeResponseBody: Error consuming response body:', error);
  }
}

async function retryOperation<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  retryDelay = 1000
): Promise<T> {
  let lastError;
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        console.log(`Operation failed, retrying (${i + 1}/${maxRetries}):`, error);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    }
  }
  throw lastError;
}

export async function downloadFile(client: SupabaseClient, path: string): Promise<{ exists: boolean; error?: string }> {
  console.log('downloadFile: Starting download for path:', path);
  
  try {
    const { data, error } = await retryOperation(async () => {
      return await client.storage
      .from('documents')
      .download(path);
    });

    if (error) {
      console.log('downloadFile: Got response:', {
        hasData: !!data,
        dataType: typeof data,
        isResponse: data instanceof Response,
        error
      });

      // Handle 404 errors specifically
      if (error.message?.toLowerCase().includes('not found') || 
          (error as StorageError).originalError?.status === 404 ||
          (error as StorageError).originalError?.statusText?.toLowerCase().includes('not found')) {
        throw new UploadHandlerError(`File not found: ${path}`, 404, error);
      }

      // Consume response body if present
      await consumeResponseBody((error as StorageError).originalError);
      
      return {
        exists: false,
        error: error.message
      };
    }

    return {
      exists: true
    };

  } catch (error) {
    console.log('downloadFile: Got error:', error);
    
    // If it's already a UploadHandlerError, rethrow it
    if (error instanceof UploadHandlerError) {
      throw error;
    }

    // Otherwise wrap it in a UploadHandlerError
    const statusCode = (error as StorageError)?.statusCode || 500;
    throw new UploadHandlerError(
      error instanceof Error ? error.message : 'Unknown error',
      statusCode,
      error instanceof Error ? error : undefined
    );
  }
}

export async function removeFiles(client: SupabaseClient, paths: string[]): Promise<RemoveFilesResult> {
  console.log('removeFiles: Starting removal for paths:', paths);
  
  try {
    const { data, error } = await retryOperation(async () => {
      return await client.storage
      .from('documents')
      .remove(paths);
    });

    console.log('removeFiles: Got response:', {
      hasData: !!data,
      dataType: typeof data,
      isResponse: data instanceof Response,
      error: error ? error.message : 'none'
    });

    if (error) {
      // Consume response body if present
      await consumeResponseBody((error as StorageError).originalError);
      return { error: error.message };
    }

    // Consume response body if present
    await consumeResponseBody(data);
    return {};

  } catch (error) {
    if (error instanceof Error && error instanceof UploadHandlerError) {
      return { error: error.message };
    }
    const statusCode = (error as StorageError)?.statusCode || 500;
    const processError = new UploadHandlerError(
      error instanceof Error ? error.message : 'Unknown error',
      statusCode,
      error instanceof Error ? error : undefined
    );
    return { error: processError.message };
  }
}

export async function uploadFile(
  client: SupabaseClient,
  path: string,
  file: Blob | ArrayBuffer | string,
  options?: { contentType?: string; upsert?: boolean }
): Promise<{ success: boolean; error?: string }> {
  console.log('uploadFile: Starting upload for path:', path);
  
  try {
    const { data, error } = await retryOperation(async () => {
      return await client.storage
      .from('documents')
      .upload(path, file, { ...options, upsert: true });
    });

    console.log('uploadFile: Got response:', {
      hasData: !!data,
      dataType: typeof data,
      isResponse: data instanceof Response,
      error: error ? error.message : 'none'
    });

    if (error) {
      // Consume response body if present
      await consumeResponseBody((error as StorageError).originalError);
      return { success: false, error: error.message };
    }

    // Consume response body if present
    await consumeResponseBody(data);
    return { success: true };

  } catch (error) {
    console.error('uploadFile: Error during upload:', error);
    if (error instanceof Error && error instanceof UploadHandlerError) {
      return { success: false, error: error.message };
    }
    const statusCode = (error as StorageError)?.statusCode || 500;
    const processError = new UploadHandlerError(
      error instanceof Error ? error.message : 'Unknown error',
      statusCode,
      error instanceof Error ? error : undefined
    );
    return { success: false, error: processError.message };
  }
} 