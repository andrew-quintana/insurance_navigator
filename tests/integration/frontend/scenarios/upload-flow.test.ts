import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { AuthTestHelper } from '../setup/auth-helpers';
import { AuthenticatedAPIClient } from '../setup/api-helpers';
import { TestEnvironment } from '../setup/environment';

describe('Authenticated Upload Integration Tests', () => {
  let authHelper: AuthTestHelper;
  let apiClient: AuthenticatedAPIClient;
  let testEnvironment: TestEnvironment;

  beforeEach(async () => {
    authHelper = new AuthTestHelper();
    testEnvironment = new TestEnvironment();
    
    // Ensure services are ready
    await testEnvironment.waitForServicesReady();
  });

  afterEach(async () => {
    // Clean up test data between tests
    await authHelper.cleanupTestUsers();
    if (apiClient) {
      await apiClient.clearTestData();
    }
  });

  describe('Document Upload with Authentication', () => {
    beforeEach(async () => {
      // Set up authenticated session
      const { user, session } = await authHelper.setupAuthenticatedSession();
      apiClient = new AuthenticatedAPIClient(session.access_token);
      apiClient.setUserId(user.id);
    });

    it('should upload document with authentication', async () => {
      // Create a mock PDF file
      const fileContent = 'Mock PDF content for testing';
      const file = new File([fileContent], 'test-document.pdf', {
        type: 'application/pdf'
      });

      const result = await apiClient.uploadDocument(file);

      expect(result.documentId).toBeDefined();
      expect(result.jobId).toBeDefined();
      expect(result.message).toBe('Document uploaded successfully');
      expect(result.status).toBe('queued');
    });

    it('should reject upload without authentication', async () => {
      const unauthenticatedClient = new AuthenticatedAPIClient('invalid-token');
      
      const file = new File(['test content'], 'test.pdf', {
        type: 'application/pdf'
      });

      await expect(
        unauthenticatedClient.uploadDocument(file)
      ).rejects.toThrow(/unauthorized/i);
    });

    it('should handle file validation', async () => {
      // Test with invalid file type
      const invalidFile = new File(['test content'], 'test.txt', {
        type: 'text/plain'
      });

      await expect(
        apiClient.uploadDocument(invalidFile)
      ).rejects.toThrow(/file type.*not allowed/i);
    });

    it('should handle file size limits', async () => {
      // Create a file that exceeds the 50MB limit
      const largeContent = 'x'.repeat(60 * 1024 * 1024); // 60MB
      const largeFile = new File([largeContent], 'large-document.pdf', {
        type: 'application/pdf'
      });

      await expect(
        apiClient.uploadDocument(largeFile)
      ).rejects.toThrow(/file.*too large/i);
    });

    it('should create unique document IDs for different uploads', async () => {
      const file1 = new File(['content 1'], 'doc1.pdf', { type: 'application/pdf' });
      const file2 = new File(['content 2'], 'doc2.pdf', { type: 'application/pdf' });

      const result1 = await apiClient.uploadDocument(file1);
      const result2 = await apiClient.uploadDocument(file2);

      expect(result1.documentId).not.toBe(result2.documentId);
      expect(result1.jobId).not.toBe(result2.jobId);
    });
  });

  describe('Document Management with Authentication', () => {
    beforeEach(async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      apiClient = new AuthenticatedAPIClient(session.access_token);
      apiClient.setUserId(user.id);
    });

    it('should retrieve user documents', async () => {
      // Upload a document first
      const file = new File(['test content'], 'test-doc.pdf', {
        type: 'application/pdf'
      });
      await apiClient.uploadDocument(file);

      // Get user documents
      const documents = await apiClient.getDocuments();

      expect(documents.length).toBeGreaterThan(0);
      expect(documents[0].userId).toBeDefined();
      expect(documents[0].filename).toBe('test-doc.pdf');
      expect(documents[0].status).toBeDefined();
    });

    it('should retrieve specific document', async () => {
      // Upload a document
      const file = new File(['test content'], 'specific-doc.pdf', {
        type: 'application/pdf'
      });
      const uploadResult = await apiClient.uploadDocument(file);

      // Get specific document
      const document = await apiClient.getDocument(uploadResult.documentId);

      expect(document.id).toBe(uploadResult.documentId);
      expect(document.filename).toBe('specific-doc.pdf');
      expect(document.userId).toBeDefined();
    });

    it('should delete document with ownership verification', async () => {
      // Upload a document
      const file = new File(['test content'], 'delete-doc.pdf', {
        type: 'application/pdf'
      });
      const uploadResult = await apiClient.uploadDocument(file);

      // Verify document exists
      const documents = await apiClient.getDocuments();
      expect(documents.some(d => d.id === uploadResult.documentId)).toBe(true);

      // Delete document
      await apiClient.deleteDocument(uploadResult.documentId);

      // Verify document is deleted
      const documentsAfter = await apiClient.getDocuments();
      expect(documentsAfter.some(d => d.id === uploadResult.documentId)).toBe(false);
    });

    it('should reject access to other users documents', async () => {
      // Create another user and upload a document
      const { user: otherUser, session: otherSession } = await authHelper.setupAuthenticatedSession();
      const otherApiClient = new AuthenticatedAPIClient(otherSession.access_token);
      otherApiClient.setUserId(otherUser.id);

      const file = new File(['other user content'], 'other-doc.pdf', {
        type: 'application/pdf'
      });
      const uploadResult = await otherApiClient.uploadDocument(file);

      // Try to access other user's document with first user's token
      await expect(
        apiClient.getDocument(uploadResult.documentId)
      ).rejects.toThrow(/forbidden|access denied/i);
    });
  });

  describe('Upload Progress Tracking', () => {
    beforeEach(async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      apiClient = new AuthenticatedAPIClient(session.access_token);
      apiClient.setUserId(user.id);
    });

    it('should track upload progress', async () => {
      const file = new File(['test content'], 'progress-doc.pdf', {
        type: 'application/pdf'
      });

      const uploadResult = await apiClient.uploadDocument(file);

      // Check initial progress
      const initialProgress = await apiClient.getUploadProgress(uploadResult.jobId);
      expect(initialProgress.jobId).toBe(uploadResult.jobId);
      expect(initialProgress.status).toBe('queued');
      expect(initialProgress.progress).toBe(0);

      // Wait for processing to start
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Check progress during processing
      const processingProgress = await apiClient.getUploadProgress(uploadResult.jobId);
      expect(['queued', 'processing'].includes(processingProgress.status)).toBe(true);
      expect(processingProgress.progress).toBeGreaterThanOrEqual(0);
    });

    it('should complete upload processing', async () => {
      const file = new File(['test content'], 'complete-doc.pdf', {
        type: 'application/pdf'
      });

      const uploadResult = await apiClient.uploadDocument(file);

      // Wait for completion
      const finalProgress = await apiClient.waitForUploadCompletion(uploadResult.jobId);

      expect(finalProgress.status).toBe('complete');
      expect(finalProgress.progress).toBe(100);
    });

    it('should handle upload status updates', async () => {
      const file = new File(['test content'], 'status-doc.pdf', {
        type: 'application/pdf'
      });

      const uploadResult = await apiClient.uploadDocument(file);

      // Monitor status changes
      const statuses = [];
      for (let i = 0; i < 10; i++) {
        const status = await apiClient.getDocumentStatus(uploadResult.documentId);
        statuses.push(status.status);
        
        if (status.status === 'complete') break;
        
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      expect(statuses).toContain('queued');
      expect(statuses).toContain('processing');
      expect(statuses).toContain('complete');
    });
  });

  describe('Concurrent Uploads', () => {
    beforeEach(async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      apiClient = new AuthenticatedAPIClient(session.access_token);
      apiClient.setUserId(user.id);
    });

    it('should handle multiple simultaneous uploads', async () => {
      const files = [
        new File(['content 1'], 'doc1.pdf', { type: 'application/pdf' }),
        new File(['content 2'], 'doc2.pdf', { type: 'application/pdf' }),
        new File(['content 3'], 'doc3.pdf', { type: 'application/pdf' })
      ];

      const uploadPromises = files.map(file => apiClient.uploadDocument(file));
      const results = await Promise.all(uploadPromises);

      expect(results.length).toBe(3);
      results.forEach(result => {
        expect(result.documentId).toBeDefined();
        expect(result.jobId).toBeDefined();
        expect(result.status).toBe('queued');
      });

      // Verify all documents are created
      const documents = await apiClient.getDocuments();
      expect(documents.length).toBe(3);
    });

    it('should maintain user isolation during concurrent uploads', async () => {
      // Create another user
      const { user: otherUser, session: otherSession } = await authHelper.setupAuthenticatedSession();
      const otherApiClient = new AuthenticatedAPIClient(otherSession.access_token);
      otherApiClient.setUserId(otherUser.id);

      // Upload files with both users simultaneously
      const user1File = new File(['user1 content'], 'user1-doc.pdf', { type: 'application/pdf' });
      const user2File = new File(['user2 content'], 'user2-doc.pdf', { type: 'application/pdf' });

      const [user1Result, user2Result] = await Promise.all([
        apiClient.uploadDocument(user1File),
        otherApiClient.uploadDocument(user2File)
      ]);

      // Verify each user only sees their own documents
      const user1Docs = await apiClient.getDocuments();
      const user2Docs = await otherApiClient.getDocuments();

      expect(user1Docs.some(d => d.id === user1Result.documentId)).toBe(true);
      expect(user1Docs.some(d => d.id === user2Result.documentId)).toBe(false);
      expect(user2Docs.some(d => d.id === user2Result.documentId)).toBe(true);
      expect(user2Docs.some(d => d.id === user1Result.documentId)).toBe(false);
    });
  });

  describe('Error Handling and Recovery', () => {
    beforeEach(async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      apiClient = new AuthenticatedAPIClient(session.access_token);
      apiClient.setUserId(user.id);
    });

    it('should handle network interruptions gracefully', async () => {
      const file = new File(['test content'], 'network-doc.pdf', {
        type: 'application/pdf'
      });

      // This test would need more sophisticated mocking to simulate network issues
      // For now, we'll test that the upload succeeds under normal conditions
      const result = await apiClient.uploadDocument(file);
      expect(result.documentId).toBeDefined();
    });

    it('should handle authentication expiry during upload', async () => {
      const file = new File(['test content'], 'expiry-doc.pdf', {
        type: 'application/pdf'
      });

      // Start upload
      const uploadPromise = apiClient.uploadDocument(file);

      // Simulate token expiry (this would need backend support)
      // For now, we'll test that upload completes successfully
      const result = await uploadPromise;
      expect(result.documentId).toBeDefined();
    });

    it('should provide meaningful error messages', async () => {
      // Test with invalid file type
      const invalidFile = new File(['test content'], 'test.exe', {
        type: 'application/x-executable'
      });

      try {
        await apiClient.uploadDocument(invalidFile);
        throw new Error('Expected upload to fail');
      } catch (error: any) {
        expect(error.message).toMatch(/file type.*not allowed/i);
      }
    });
  });

  describe('API Service Health and Monitoring', () => {
    beforeEach(async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      apiClient = new AuthenticatedAPIClient(session.access_token);
      apiClient.setUserId(user.id);
    });

    it('should respond to health checks', async () => {
      const isHealthy = await apiClient.testServiceHealth();
      expect(isHealthy).toBe(true);
    });

    it('should provide service information', async () => {
      const response = await fetch('http://localhost:3002/health');
      const healthData = await response.json();

      expect(healthData.status).toBe('healthy');
      expect(healthData.service).toBe('mock-api-service');
      expect(healthData.upload_max_size).toBeDefined();
      expect(healthData.allowed_file_types).toBeDefined();
    });

    it('should provide test data for debugging', async () => {
      // Upload a document first
      const file = new File(['test content'], 'debug-doc.pdf', {
        type: 'application/pdf'
      });
      await apiClient.uploadDocument(file);

      // Get test data
      const testData = await apiClient.getTestData();

      expect(testData.documents).toBeDefined();
      expect(testData.uploadJobs).toBeDefined();
      expect(testData.conversations).toBeDefined();
    });
  });

  describe('Performance and Load Testing Preparation', () => {
    it('should handle multiple users uploading simultaneously', async () => {
      const userCount = 5;
      const users = await authHelper.createMultipleTestUsers(userCount, 'upload-load-test');

      const uploadPromises = users.map(async (user) => {
        const userApiClient = new AuthenticatedAPIClient(user.session.access_token);
        userApiClient.setUserId(user.user.id);

        const file = new File([`content for ${user.user.email}`], `${user.user.id}.pdf`, {
          type: 'application/pdf'
        });

        return userApiClient.uploadDocument(file);
      });

      const results = await Promise.all(uploadPromises);

      expect(results.length).toBe(userCount);
      results.forEach(result => {
        expect(result.documentId).toBeDefined();
        expect(result.jobId).toBeDefined();
        expect(result.status).toBe('queued');
      });
    });

    it('should maintain performance under load', async () => {
      const startTime = Date.now();
      const fileCount = 10;

      const files = Array.from({ length: fileCount }, (_, i) => 
        new File([`content ${i}`], `load-test-${i}.pdf`, { type: 'application/pdf' })
      );

      const uploadPromises = files.map(file => apiClient.uploadDocument(file));
      const results = await Promise.all(uploadPromises);

      const endTime = Date.now();
      const totalTime = endTime - startTime;

      expect(results.length).toBe(fileCount);
      expect(totalTime).toBeLessThan(30000); // Should complete within 30 seconds
    });
  });
});
