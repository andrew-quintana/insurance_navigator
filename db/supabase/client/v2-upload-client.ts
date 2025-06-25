import { createClient, SupabaseClient } from '@supabase/supabase-js'

export interface UploadProgress {
  documentId: string;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'chunking' | 'embedding' | 'completed' | 'failed' | 'cancelled';
  filename: string;
  fileSize: number;
  processedChunks: number;
  totalChunks: number;
  failedChunks: number;
  errorMessage?: string;
  isStuck?: boolean;
  estimatedTimeRemaining?: number;
  lastUpdated: string;
}

export interface UploadConfig {
  maxFileSize?: number; // Default: 50MB
  allowedTypes?: string[]; // Default: PDF, DOCX, TXT
  chunkSize?: number; // Default: 5MB
  enableRealtime?: boolean; // Default: true
}

export interface UploadResult {
  documentId: string;
  uploadUrl: string;
  token: string;
  storagePath: string;
  totalChunks: number;
  chunkSize: number;
  message: string;
}

export class V2UploadClient {
  private supabase: SupabaseClient;
  private baseUrl: string;
  private config: Required<UploadConfig>;
  private progressCallbacks: Map<string, (progress: UploadProgress) => void> = new Map();
  private realtimeChannel?: any;

  constructor(
    supabaseUrl: string, 
    supabaseKey: string, 
    config: UploadConfig = {}
  ) {
    this.supabase = createClient(supabaseUrl, supabaseKey);
    this.baseUrl = `${supabaseUrl}/functions/v1`;
    this.config = {
      maxFileSize: config.maxFileSize || 52428800, // 50MB
      allowedTypes: config.allowedTypes || [
        'application/pdf', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
        'text/plain'
      ],
      chunkSize: config.chunkSize || 5242880, // 5MB
      enableRealtime: config.enableRealtime !== false
    };

    if (this.config.enableRealtime) {
      this.initializeRealtime();
    }
  }

  /**
   * Initialize a file upload
   */
  async initializeUpload(file: File): Promise<UploadResult> {
    // Validate file
    this.validateFile(file);

    const { data: { session }, error: authError } = await this.supabase.auth.getSession();
    if (authError || !session) {
      throw new Error('Authentication required');
    }

    // Generate file hash
    const fileHash = await this.generateFileHash(file);

    const response = await fetch(`${this.baseUrl}/upload-handler`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        filename: file.name,
        contentType: file.type,
        fileSize: file.size,
        fileHash
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Upload initialization failed');
    }

    return await response.json();
  }

  /**
   * Complete the upload and trigger processing
   */
  async completeUpload(documentId: string, path: string): Promise<{ success: boolean; message: string }> {
    const { data: { session }, error: authError } = await this.supabase.auth.getSession();
    if (authError || !session) {
      throw new Error('Authentication required');
    }

    const response = await fetch(`${this.baseUrl}/upload-handler`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        documentId,
        path
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Upload completion failed');
    }

    return await response.json();
  }

  /**
   * Upload a file with automatic LlamaParse integration
   */
  async uploadFile(
    file: File, 
    onProgress?: (progress: UploadProgress) => void
  ): Promise<{ documentId: string; success: boolean }> {
    try {
      // Initialize upload
      const uploadResult = await this.initializeUpload(file);
      
      // Start progress monitoring
      if (onProgress) {
        this.startProgressMonitoring(uploadResult.documentId, onProgress);
      }

      // Upload file to Supabase Storage
      const uploadResponse = await fetch(uploadResult.uploadUrl, {
        method: 'PUT',
        headers: {
          'Content-Type': file.type
        },
        body: file
      });

      if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.status}`);
      }

      // Complete upload and trigger processing
      const completionResult = await this.completeUpload(uploadResult.documentId, uploadResult.path);

      return {
        documentId: uploadResult.documentId,
        success: completionResult.success
      };

    } catch (error) {
      throw new Error(`File upload failed: ${error.message}`);
    }
  }

  /**
   * Get current upload progress
   */
  async getProgress(documentId: string): Promise<UploadProgress> {
    const { data: { session }, error: authError } = await this.supabase.auth.getSession();
    if (authError || !session) {
      throw new Error('Authentication required');
    }

    const response = await fetch(
      `${this.baseUrl}/progress-tracker?documentId=${documentId}`,
      {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get progress');
    }

    return await response.json();
  }

  /**
   * Reset upload progress (for retry)
   */
  async resetProgress(documentId: string): Promise<void> {
    const { data: { session }, error: authError } = await this.supabase.auth.getSession();
    if (authError || !session) {
      throw new Error('Authentication required');
    }

    const response = await fetch(
      `${this.baseUrl}/progress-tracker?documentId=${documentId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to reset progress');
    }
  }

  /**
   * Subscribe to real-time progress updates
   */
  subscribeToProgress(userId: string, callback: (progress: UploadProgress) => void): () => void {
    if (!this.realtimeChannel) {
      console.warn('Realtime not initialized');
      return () => {};
    }

    const channel = this.supabase
      .channel(`user_${userId}_progress`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'realtime_progress_updates',
          filter: `user_id=eq.${userId}`
        },
        (payload) => {
          if (payload.new?.payload) {
            callback(this.transformRealtimePayload(payload.new.payload));
          }
        }
      )
      .subscribe();

    return () => {
      this.supabase.removeChannel(channel);
    };
  }

  /**
   * Get user's upload statistics
   */
  async getUserStats(): Promise<any> {
    const { data, error } = await this.supabase
      .from('user_upload_stats')
      .select('*')
      .single();

    if (error) {
      throw new Error(`Failed to get user stats: ${error.message}`);
    }

    return data;
  }

  /**
   * Get failed documents for retry
   */
  async getFailedDocuments(): Promise<any[]> {
    const { data, error } = await this.supabase
      .from('failed_documents')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      throw new Error(`Failed to get failed documents: ${error.message}`);
    }

    return data || [];
  }

  // Private methods

  private validateFile(file: File): void {
    if (file.size > this.config.maxFileSize) {
      throw new Error(`File too large. Maximum size: ${this.config.maxFileSize / 1024 / 1024}MB`);
    }

    if (!this.config.allowedTypes.includes(file.type)) {
      throw new Error(`File type not supported. Allowed: ${this.config.allowedTypes.join(', ')}`);
    }
  }

  private async uploadSingleFile(file: File, uploadUrl: string): Promise<void> {
    const response = await fetch(uploadUrl, {
      method: 'PUT',
      body: file,
      headers: {
        'Content-Type': file.type,
        'Content-Length': file.size.toString()
      }
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
  }

  private async uploadFileInChunks(file: File, uploadResult: UploadResult): Promise<void> {
    const { documentId, chunkSize, totalChunks } = uploadResult;

    for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
      const start = chunkIndex * chunkSize;
      const end = Math.min(start + chunkSize, file.size);
      const chunk = file.slice(start, end);

      // Upload chunk
      await this.uploadChunk(chunk, uploadResult, chunkIndex);

      // Update progress
      await this.updateChunkProgress(documentId, chunkIndex);
    }
  }

  private async uploadChunk(chunk: Blob, uploadResult: UploadResult, chunkIndex: number): Promise<void> {
    const { uploadUrl } = uploadResult;
    
    const response = await fetch(`${uploadUrl}?chunk=${chunkIndex}`, {
      method: 'PUT',
      body: chunk
    });

    if (!response.ok) {
      throw new Error(`Chunk ${chunkIndex} upload failed: ${response.statusText}`);
    }
  }

  private async updateChunkProgress(documentId: string, chunkIndex: number): Promise<void> {
    const { data: { session } } = await this.supabase.auth.getSession();
    if (!session) return;

    await fetch(`${this.baseUrl}/upload-handler?documentId=${documentId}&chunkIndex=${chunkIndex}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
  }

  private async reportError(documentId: string, errorMessage: string): Promise<void> {
    const { data: { session } } = await this.supabase.auth.getSession();
    if (!session) return;

    await fetch(`${this.baseUrl}/progress-tracker`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        documentId,
        status: 'failed',
        errorMessage
      })
    });
  }

  private initializeRealtime(): void {
    this.realtimeChannel = this.supabase.channel('v2-upload-progress');
  }

  private transformRealtimePayload(payload: any): UploadProgress {
    const details = payload.details || {};
    return {
      documentId: payload.documentId,
      progress: payload.progress || 0,
      status: payload.status || 'processing',
      filename: details.filename || 'Unknown',
      fileSize: details.fileSize || 0,
      processedChunks: details.processedChunks || 0,
      totalChunks: details.totalChunks || 1,
      failedChunks: details.failedChunks || 0,
      errorMessage: details.errorMessage,
      lastUpdated: payload.timestamp || new Date().toISOString()
    };
  }

  /**
   * Generate a file hash for deduplication
   */
  private async generateFileHash(file: File): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(`${file.name}-${file.size}-${Date.now()}`);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }
}

// Export singleton instance for convenience
export function createUploadClient(
  supabaseUrl: string, 
  supabaseKey: string, 
  config?: UploadConfig
): V2UploadClient {
  return new V2UploadClient(supabaseUrl, supabaseKey, config);
} 