export interface Document {
  id: string;
  userId: string;
  filename: string;
  mimetype: string;
  size: number;
  status: 'queued' | 'processing' | 'complete' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface UploadResponse {
  documentId: string;
  jobId: string;
  message: string;
  status: string;
}

export interface ChatResponse {
  messageId: string;
  conversationId: string;
  message: string;
  status: string;
}

export interface UploadProgress {
  jobId: string;
  status: string;
  progress: number;
  updated_at: string;
}

export interface Conversation {
  id: string;
  created_at: string;
  updated_at: string;
  messageCount: number;
}

export interface ChatMessage {
  id: string;
  conversationId: string;
  userId: string;
  content: string;
  type: 'user' | 'agent';
  metadata?: any;
  created_at: string;
}

export class AuthenticatedAPIClient {
  private baseUrl: string;
  private authToken: string;
  private userId?: string;

  constructor(authToken: string, baseUrl: string = 'http://localhost:3002') {
    this.baseUrl = baseUrl;
    this.authToken = authToken;
  }

  /**
   * Set the user ID for context-aware operations
   */
  setUserId(userId: string): void {
    this.userId = userId;
  }

  /**
   * Get authentication headers
   */
  private getAuthHeaders(): Record<string, string> {
    return {
      'Authorization': `Bearer ${this.authToken}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Upload a document with authentication
   */
  async uploadDocument(file: File): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${this.baseUrl}/api/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.authToken}`
          // Note: Don't set Content-Type for FormData, let browser set it
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Upload failed: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error uploading document:', error);
      throw error;
    }
  }

  /**
   * Get user's documents
   */
  async getDocuments(): Promise<Document[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/documents`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to get documents: ${response.status}`);
      }

      const documents = await response.json();
      return documents;
    } catch (error) {
      console.error('Error getting documents:', error);
      throw error;
    }
  }

  /**
   * Get specific document
   */
  async getDocument(documentId: string): Promise<Document> {
    try {
      const response = await fetch(`${this.baseUrl}/api/documents/${documentId}`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to get document: ${response.status}`);
      }

      const document = await response.json();
      return document;
    } catch (error) {
      console.error('Error getting document:', error);
      throw error;
    }
  }

  /**
   * Delete a document
   */
  async deleteDocument(documentId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/documents/${documentId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to delete document: ${response.status}`);
      }

      console.log('Document deleted successfully');
    } catch (error) {
      console.error('Error deleting document:', error);
      throw error;
    }
  }

  /**
   * Get document processing status
   */
  async getDocumentStatus(documentId: string): Promise<UploadProgress> {
    try {
      const response = await fetch(`${this.baseUrl}/api/documents/${documentId}/status`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to get document status: ${response.status}`);
      }

      const status = await response.json();
      return status;
    } catch (error) {
      console.error('Error getting document status:', error);
      throw error;
    }
  }

  /**
   * Send a chat message
   */
  async sendChatMessage(message: string, conversationId?: string): Promise<ChatResponse> {
    try {
      const payload: any = { message };
      
      if (conversationId) {
        payload.conversationId = conversationId;
      }
      
      if (this.userId) {
        payload.userId = this.userId;
      }

      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to send chat message: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error sending chat message:', error);
      throw error;
    }
  }

  /**
   * Get user's conversations
   */
  async getConversations(): Promise<Conversation[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/conversations`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to get conversations: ${response.status}`);
      }

      const conversations = await response.json();
      return conversations;
    } catch (error) {
      console.error('Error getting conversations:', error);
      throw error;
    }
  }

  /**
   * Get conversation messages
   */
  async getConversationMessages(conversationId: string): Promise<ChatMessage[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/conversations/${conversationId}/messages`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to get conversation messages: ${response.status}`);
      }

      const messages = await response.json();
      return messages;
    } catch (error) {
      console.error('Error getting conversation messages:', error);
      throw error;
    }
  }

  /**
   * Get upload progress for a job
   */
  async getUploadProgress(jobId: string): Promise<UploadProgress> {
    try {
      const response = await fetch(`${this.baseUrl}/api/ws/upload-progress/${jobId}`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to get upload progress: ${response.status}`);
      }

      const progress = await response.json();
      return progress;
    } catch (error) {
      console.error('Error getting upload progress:', error);
      throw error;
    }
  }

  /**
   * Poll upload progress until completion
   */
  async waitForUploadCompletion(jobId: string, maxAttempts: number = 60, delay: number = 1000): Promise<UploadProgress> {
    console.log(`⏳ Waiting for upload completion for job ${jobId}...`);
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const progress = await this.getUploadProgress(jobId);
        
        console.log(`📊 Upload progress ${attempt}/${maxAttempts}: ${progress.progress}% (${progress.status})`);
        
        if (progress.status === 'complete') {
          console.log(`✅ Upload completed for job ${jobId}`);
          return progress;
        }
        
        if (progress.status === 'failed') {
          throw new Error(`Upload failed for job ${jobId}`);
        }
        
        if (attempt >= maxAttempts) {
          throw new Error(`Upload did not complete within ${maxAttempts * delay / 1000} seconds`);
        }
        
        await new Promise(resolve => setTimeout(resolve, delay));
      } catch (error) {
        if (attempt >= maxAttempts) {
          throw error;
        }
        console.warn(`Attempt ${attempt} failed, retrying...`, error);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    throw new Error('Upload completion check failed');
  }

  /**
   * Test API service health
   */
  async testServiceHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, { timeout: 5000 });
      return response.ok;
    } catch (error) {
      console.error('API service health check failed:', error);
      return false;
    }
  }

  /**
   * Get test data for debugging
   */
  async getTestData(): Promise<any> {
    try {
      const [documents, uploadJobs, conversations] = await Promise.all([
        fetch(`${this.baseUrl}/test/documents`).then(r => r.json()),
        fetch(`${this.baseUrl}/test/upload-jobs`).then(r => r.json()),
        fetch(`${this.baseUrl}/test/conversations`).then(r => r.json())
      ]);

      return { documents, uploadJobs, conversations };
    } catch (error) {
      console.error('Failed to get test data:', error);
      return {};
    }
  }

  /**
   * Clear all test data
   */
  async clearTestData(): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/test/clear`, {
        method: 'DELETE'
      });

      if (response.ok) {
        console.log('✅ Test data cleared');
      } else {
        console.warn('Failed to clear test data');
      }
    } catch (error) {
      console.error('Error clearing test data:', error);
    }
  }
}
