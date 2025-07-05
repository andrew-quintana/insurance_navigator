import { SupabaseClient, createClient } from "https://esm.sh/@supabase/supabase-js@2.39.3";
import { edgeConfig } from "../_shared/environment.ts";
import { createServiceRoleJWT } from "../_shared/jwt.ts";

export interface ParsedContent {
  content: string;
  metadata: {
    extractionMethod: string;
    timestamp?: string;
    filename: string;
    contentType?: string;
    size?: number;
  };
}

export interface ProcessingResult {
  success: boolean;
  document_id: string;
  status: 'completed' | 'error';
  error?: string;
  statusCode?: number;
}

export class UploadHandlerError extends Error {
  statusCode: number;
  originalError?: Error;

  constructor(message: string, statusCode = 500, originalError?: Error) {
    super(message);
    this.name = 'UploadHandlerError';
    this.statusCode = statusCode;
    this.originalError = originalError;
  }
}

export class DocumentNotFoundError extends UploadHandlerError {
  constructor(message: string, originalError?: Error) {
    super(message, 404, originalError);
    this.name = 'DocumentNotFoundError';
  }
}

export class ValidationError extends UploadHandlerError {
  constructor(message: string, originalError?: Error) {
    super(message, 400, originalError);
    this.name = 'ValidationError';
  }
}

import {
  getDocument,
  updateDocumentStatus,
  logProcessingStep,
  getMemoryUsage,
  validatePath
} from "./utils.ts";
import { downloadFile, uploadFile } from "./storage.ts";

async function initializeClient(): Promise<SupabaseClient> {
  const serviceRoleJWT = await createServiceRoleJWT();
  const serviceRoleKey = edgeConfig.supabaseKey as string;
  
  if (!serviceRoleKey) {
    throw new UploadHandlerError('Supabase service role key not found in config', 503);
  }

  return createClient(
    edgeConfig.supabaseUrl,
    serviceRoleKey,
    {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
        detectSessionInUrl: false
      },
      global: {
        headers: {
          Authorization: `Bearer ${serviceRoleJWT}`
        }
      }
    }
  );
}

export async function handleUpload(
  userId: string,
  documentId: string,
  parsedContent: ParsedContent,
  testClient?: SupabaseClient
): Promise<ProcessingResult> {
  const startTime = Date.now();
  let client: SupabaseClient;

  try {
    // Validate input
    if (!userId || !documentId || !parsedContent?.metadata?.filename) {
      return {
        success: false,
        document_id: documentId,
        status: 'error',
        error: 'Missing required fields',
        statusCode: 400
      };
    }

    // Validate path
    if (!validatePath(parsedContent.metadata.filename)) {
      return {
        success: false,
        document_id: documentId,
        status: 'error',
        error: 'Invalid path',
        statusCode: 400
      };
    }

    try {
      client = testClient || await initializeClient();
    } catch (error) {
      console.error('Failed to initialize Supabase client:', error);
      return {
        success: false,
        document_id: documentId,
        status: 'error',
        error: error instanceof Error ? error.message : 'Service unavailable',
        statusCode: error instanceof UploadHandlerError ? error.statusCode : 503
      };
    }

    // Check authentication
    const { data: user, error: authError } = await client.auth.getUser();
    if (authError || !user) {
      return {
        success: false,
        document_id: documentId,
        status: 'error',
        error: authError?.message || 'Authentication failed',
        statusCode: 401
      };
    }

    // Get document
    const document = await getDocument(client, userId, documentId);
    if (!document) {
      const error = new DocumentNotFoundError(documentId);
      await logProcessingStep(client, documentId, 'error', {
        timestamp: new Date().toISOString(),
        memory_usage: getMemoryUsage(),
        duration_ms: Date.now() - startTime,
        content_type: 'unknown',
        filename: 'unknown',
        extractionMethod: parsedContent.metadata.extractionMethod
      }, error.message);

      return {
        success: false,
        document_id: documentId,
        status: 'error',
        error: error.message,
        statusCode: error.statusCode
      };
    }

    // Check if file exists using storage utility
    try {
      const { exists, error: fileError } = await downloadFile(client, document.storage_path);
      if (!exists) {
        const error = new UploadHandlerError(fileError || "Raw file not found", 404);
        console.log('File check error:', error); // Debug log
        await logProcessingStep(client, documentId, 'error', {
          timestamp: new Date().toISOString(),
          memory_usage: getMemoryUsage(),
          duration_ms: Date.now() - startTime,
          content_type: document.content_type,
          filename: document.filename,
          extractionMethod: parsedContent.metadata.extractionMethod
        }, error.message);

        await updateDocumentStatus(client, documentId, 'error', error.message);

        return {
          success: false,
          document_id: documentId,
          status: 'error',
          error: error.message,
          statusCode: error.statusCode
        };
      }
    } catch (error) {
      if (error instanceof UploadHandlerError && error.statusCode === 404) {
        console.log('File not found error:', error); // Debug log
        await logProcessingStep(client, documentId, 'error', {
          timestamp: new Date().toISOString(),
          memory_usage: getMemoryUsage(),
          duration_ms: Date.now() - startTime,
          content_type: document.content_type,
          filename: document.filename,
          extractionMethod: parsedContent.metadata.extractionMethod
        }, error.message);

        await updateDocumentStatus(client, documentId, 'error', error.message);

        return {
          success: false,
          document_id: documentId,
          status: 'error',
          error: error.message,
          statusCode: error.statusCode
        };
      }
      throw error;
    }

    // Process the document...
    const processedPath = document.storage_path.replace('/raw/', '/processed/');
    const { success: uploadSuccess, error: uploadError } = await uploadFile(
      client,
      processedPath,
      parsedContent.content,
      {
        contentType: document.content_type,
        upsert: true
      }
    );

    if (!uploadSuccess) {
      const error = new UploadHandlerError(uploadError || "Failed to upload processed file", 500);
      await logProcessingStep(client, documentId, 'error', {
        timestamp: new Date().toISOString(),
        memory_usage: getMemoryUsage(),
        duration_ms: Date.now() - startTime,
        content_type: document.content_type,
        filename: document.filename,
        extractionMethod: parsedContent.metadata.extractionMethod
      }, error.message);

      await updateDocumentStatus(client, documentId, 'error', error.message);

      return {
        success: false,
        document_id: documentId,
        status: 'error',
        error: error.message,
        statusCode: error.statusCode
      };
    }

    // Update document status
    await updateDocumentStatus(client, documentId, 'completed');

    return {
      success: true,
      document_id: documentId,
      status: 'completed'
    };

  } catch (error) {
    const processError = error instanceof UploadHandlerError ? error : new UploadHandlerError(
      error instanceof Error ? error.message : 'Unknown error',
      error instanceof DocumentNotFoundError ? 404 : 500
    );

    await logProcessingStep(client!, documentId, 'error', {
      timestamp: new Date().toISOString(),
      memory_usage: getMemoryUsage(),
      duration_ms: Date.now() - startTime,
      content_type: 'unknown',
      filename: parsedContent?.metadata?.filename || 'unknown',
      extractionMethod: parsedContent?.metadata?.extractionMethod || 'unknown'
    }, processError.message);

    await updateDocumentStatus(client!, documentId, 'error', processError.message);

    return {
      success: false,
      document_id: documentId,
      status: 'error',
      error: processError.message,
      statusCode: processError.statusCode
    };
  }
} 