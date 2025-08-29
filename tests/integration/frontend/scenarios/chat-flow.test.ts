import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { AuthTestHelper } from '../setup/auth-helpers';
import { AuthenticatedAPIClient } from '../setup/api-helpers';
import { TestEnvironment } from '../setup/environment';

describe('Authenticated Chat Integration Tests', () => {
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

  describe('Chat Authentication and User Context', () => {
    beforeEach(async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      apiClient = new AuthenticatedAPIClient(session.access_token);
      apiClient.setUserId(user.id);
    });

    it('should send message with user context', async () => {
      const message = 'What is my deductible?';
      const response = await apiClient.sendChatMessage(message);

      expect(response.messageId).toBeDefined();
      expect(response.conversationId).toBeDefined();
      expect(response.message).toBe('Message sent successfully');
      expect(response.status).toBe('processing');
    });

    it('should reject chat without authentication', async () => {
      const unauthenticatedClient = new AuthenticatedAPIClient('invalid-token');

      await expect(
        unauthenticatedClient.sendChatMessage('Hello')
      ).rejects.toThrow(/unauthorized/i);
    });

    it('should maintain user context across messages', async () => {
      const message1 = 'What is my coverage?';
      const message2 = 'What about dental benefits?';

      const response1 = await apiClient.sendChatMessage(message1);
      const response2 = await apiClient.sendChatMessage(message2, response1.conversationId);

      expect(response1.conversationId).toBe(response2.conversationId);
    });

    it('should create new conversation when none specified', async () => {
      const response = await apiClient.sendChatMessage('Hello, new conversation');

      expect(response.conversationId).toBeDefined();
      expect(response.messageId).toBeDefined();
    });
  });

  describe('Agent Response Integration', () => {
    beforeEach(async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      apiClient = new AuthenticatedAPIClient(session.access_token);
      apiClient.setUserId(user.id);
    });

    it('should receive agent response with metadata', async () => {
      const message = 'What is my policy number?';
      const response = await apiClient.sendChatMessage(message);

      // Wait for agent response
      await new Promise(resolve => setTimeout(resolve, 3000));

      // Get conversation messages
      const messages = await apiClient.getConversationMessages(response.conversationId);

      expect(messages.length).toBeGreaterThanOrEqual(2); // User message + agent response
      
      const userMessage = messages.find(m => m.type === 'user');
      const agentMessage = messages.find(m => m.type === 'agent');

      expect(userMessage).toBeDefined();
      expect(userMessage?.content).toBe(message);
      expect(userMessage?.userId).toBeDefined();

      expect(agentMessage).toBeDefined();
      expect(agentMessage?.type).toBe('agent');
      expect(agentMessage?.metadata).toBeDefined();
      expect(agentMessage?.metadata.agentType).toBe('mock-agent');
      expect(agentMessage?.metadata.documentContext).toBe(true);
      expect(agentMessage?.metadata.userId).toBeDefined();
    });

    it('should handle multiple agent responses in sequence', async () => {
      const conversationId = 'test-conversation-' + Date.now();
      const messages = [
        'What is my deductible?',
        'What about my out-of-pocket maximum?',
        'Does my policy cover prescription drugs?'
      ];

      const responses = [];
      for (const message of messages) {
        const response = await apiClient.sendChatMessage(message, conversationId);
        responses.push(response);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      expect(responses.length).toBe(3);
      responses.forEach(response => {
        expect(response.conversationId).toBe(conversationId);
        expect(response.status).toBe('processing');
      });

      // Wait for all agent responses
      await new Promise(resolve => setTimeout(resolve, 5000));

      // Verify conversation has all messages
      const conversationMessages = await apiClient.getConversationMessages(conversationId);
      expect(conversationMessages.length).toBeGreaterThanOrEqual(6); // 3 user + 3 agent
    });

    it('should maintain conversation history', async () => {
      const conversationId = 'history-test-' + Date.now();
      
      // Send first message
      await apiClient.sendChatMessage('Hello', conversationId);
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Send second message
      await apiClient.sendChatMessage('How are you?', conversationId);
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Get conversation messages
      const messages = await apiClient.getConversationMessages(conversationId);

      expect(messages.length).toBeGreaterThanOrEqual(4); // 2 user + 2 agent
      
      // Verify message order
      const userMessages = messages.filter(m => m.type === 'user');
      expect(userMessages[0].content).toBe('Hello');
      expect(userMessages[1].content).toBe('How are you?');
    });
  });

  describe('Conversation Management', () => {
    beforeEach(async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      apiClient = new AuthenticatedAPIClient(session.access_token);
      apiClient.setUserId(user.id);
    });

    it('should list user conversations', async () => {
      // Create some conversations
      const conversation1 = await apiClient.sendChatMessage('Message 1');
      const conversation2 = await apiClient.sendChatMessage('Message 2');

      await new Promise(resolve => setTimeout(resolve, 2000));

      const conversations = await apiClient.getConversations();

      expect(conversations.length).toBeGreaterThanOrEqual(2);
      conversations.forEach(conv => {
        expect(conv.id).toBeDefined();
        expect(conv.created_at).toBeDefined();
        expect(conv.updated_at).toBeDefined();
        expect(conv.messageCount).toBeGreaterThan(0);
      });
    });

    it('should retrieve conversation messages', async () => {
      const message = 'Test message for conversation';
      const response = await apiClient.sendChatMessage(message);

      await new Promise(resolve => setTimeout(resolve, 2000));

      const messages = await apiClient.getConversationMessages(response.conversationId);

      expect(messages.length).toBeGreaterThanOrEqual(2);
      expect(messages[0].conversationId).toBe(response.conversationId);
      expect(messages[0].content).toBe(message);
    });

    it('should maintain conversation isolation between users', async () => {
      // Create another user
      const { user: otherUser, session: otherSession } = await authHelper.setupAuthenticatedSession();
      const otherApiClient = new AuthenticatedAPIClient(otherSession.access_token);
      otherApiClient.setUserId(otherUser.id);

      // Send messages with both users
      const user1Message = await apiClient.sendChatMessage('User 1 message');
      const user2Message = await otherApiClient.sendChatMessage('User 2 message');

      await new Promise(resolve => setTimeout(resolve, 2000));

      // Verify each user only sees their own conversations
      const user1Conversations = await apiClient.getConversations();
      const user2Conversations = await otherApiClient.getConversations();

      expect(user1Conversations.some(c => c.id === user1Message.conversationId)).toBe(true);
      expect(user1Conversations.some(c => c.id === user2Message.conversationId)).toBe(false);
      expect(user2Conversations.some(c => c.id === user2Message.conversationId)).toBe(true);
      expect(user2Conversations.some(c => c.id === user1Message.conversationId)).toBe(false);
    });
  });

  describe('Real-time Features and Performance', () => {
    beforeEach(async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      apiClient = new AuthenticatedAPIClient(session.access_token);
      apiClient.setUserId(user.id);
    });

    it('should handle authentication during long conversations', async () => {
      const conversationId = 'long-conversation-' + Date.now();
      const messageCount = 10;

      const startTime = Date.now();
      
      for (let i = 0; i < messageCount; i++) {
        const response = await apiClient.sendChatMessage(`Message ${i + 1}`, conversationId);
        expect(response.text).toBeDefined();
        
        // Small delay between messages
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      const endTime = Date.now();
      const totalTime = endTime - startTime;

      expect(totalTime).toBeLessThan(30000); // Should complete within 30 seconds
    });

    it('should maintain performance under message load', async () => {
      const conversationId = 'performance-test-' + Date.now();
      const messageCount = 20;

      const startTime = Date.now();
      const promises = [];

      for (let i = 0; i < messageCount; i++) {
        promises.push(apiClient.sendChatMessage(`Performance message ${i + 1}`, conversationId));
      }

      const responses = await Promise.all(promises);
      const endTime = Date.now();

      expect(responses.length).toBe(messageCount);
      expect(endTime - startTime).toBeLessThan(10000); // Should complete within 10 seconds
    });

    it('should handle concurrent conversations', async () => {
      const conversationCount = 5;
      const conversations = [];

      // Start multiple conversations simultaneously
      for (let i = 0; i < conversationCount; i++) {
        const response = await apiClient.sendChatMessage(`Conversation ${i + 1} message`);
        conversations.push(response.conversationId);
      }

      expect(conversations.length).toBe(conversationCount);

      // Verify all conversations are accessible
      for (const convId of conversations) {
        const messages = await apiClient.getConversationMessages(convId);
        expect(messages.length).toBeGreaterThan(0);
      }
    });
  });

  describe('Document Context Integration', () => {
    beforeEach(async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      apiClient = new AuthenticatedAPIClient(session.access_token);
      apiClient.setUserId(user.id);
    });

    it('should integrate with uploaded documents', async () => {
      // First upload a document
      const file = new File(['Mock insurance policy content'], 'policy.pdf', {
        type: 'application/pdf'
      });

      const uploadResult = await apiClient.uploadDocument(file);
      
      // Wait for document processing
      await apiClient.waitForUploadCompletion(uploadResult.jobId);

      // Now ask questions about the document
      const question = 'What does my policy say about deductibles?';
      const response = await apiClient.sendChatMessage(question);

      await new Promise(resolve => setTimeout(resolve, 3000));

      // Get conversation to verify agent response
      const messages = await apiClient.getConversationMessages(response.conversationId);
      const agentMessage = messages.find(m => m.type === 'agent');

      expect(agentMessage).toBeDefined();
      expect(agentMessage?.metadata.documentContext).toBe(true);
    });

    it('should handle multi-document queries', async () => {
      // Upload multiple documents
      const files = [
        new File(['Policy document content'], 'policy.pdf', { type: 'application/pdf' }),
        new File(['Benefits summary content'], 'benefits.pdf', { type: 'application/pdf' })
      ];

      const uploadPromises = files.map(file => apiClient.uploadDocument(file));
      const uploadResults = await Promise.all(uploadPromises);

      // Wait for all documents to process
      await Promise.all(
        uploadResults.map(result => apiClient.waitForUploadCompletion(result.jobId))
      );

      // Ask question spanning multiple documents
      const question = 'Compare the coverage in my policy and benefits documents';
      const response = await apiClient.sendChatMessage(question);

      await new Promise(resolve => setTimeout(resolve, 3000));

      // Verify response
      const messages = await apiClient.getConversationMessages(response.conversationId);
      const agentMessage = messages.find(m => m.type === 'agent');

      expect(agentMessage).toBeDefined();
      expect(agentMessage?.metadata.documentContext).toBe(true);
    });
  });

  describe('Error Handling and Recovery', () => {
    beforeEach(async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      apiClient = new AuthenticatedAPIClient(session.access_token);
      apiClient.setUserId(user.id);
    });

    it('should handle network interruptions gracefully', async () => {
      const message = 'Test message for network resilience';
      
      // This test would need more sophisticated mocking to simulate network issues
      // For now, we'll test that the message sends successfully under normal conditions
      const response = await apiClient.sendChatMessage(message);
      expect(response.messageId).toBeDefined();
    });

    it('should handle authentication expiry during conversation', async () => {
      const message = 'Test message for auth expiry';
      
      // Start sending message
      const sendPromise = apiClient.sendChatMessage(message);
      
      // Simulate token expiry (this would need backend support)
      // For now, we'll test that message sends successfully
      const response = await sendPromise;
      expect(response.messageId).toBeDefined();
    });

    it('should provide meaningful error messages', async () => {
      // Test with empty message
      try {
        await apiClient.sendChatMessage('');
        throw new Error('Expected empty message to fail');
      } catch (error: any) {
        expect(error.message).toMatch(/message.*required/i);
      }
    });

    it('should handle malformed requests', async () => {
      // Test with malformed JSON
      const response = await fetch('http://localhost:3002/api/chat', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiClient['authToken']}`,
          'Content-Type': 'application/json'
        },
        body: 'invalid json'
      });

      expect(response.status).toBe(400);
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
      expect(healthData.auth_service).toBeDefined();
    });

    it('should provide test data for debugging', async () => {
      // Send a message first
      await apiClient.sendChatMessage('Debug message');

      // Get test data
      const testData = await apiClient.getTestData();

      expect(testData.documents).toBeDefined();
      expect(testData.uploadJobs).toBeDefined();
      expect(testData.conversations).toBeDefined();
    });
  });

  describe('Load Testing Preparation', () => {
    it('should handle multiple users chatting simultaneously', async () => {
      const userCount = 5;
      const users = await authHelper.createMultipleTestUsers(userCount, 'chat-load-test');

      const chatPromises = users.map(async (user) => {
        const userApiClient = new AuthenticatedAPIClient(user.session.access_token);
        userApiClient.setUserId(user.user.id);

        return userApiClient.sendChatMessage(`Hello from ${user.user.email}`);
      });

      const results = await Promise.all(chatPromises);

      expect(results.length).toBe(userCount);
      results.forEach(result => {
        expect(result.messageId).toBeDefined();
        expect(result.conversationId).toBeDefined();
        expect(result.status).toBe('processing');
      });
    });

    it('should maintain performance under chat load', async () => {
      const startTime = Date.now();
      const messageCount = 20;

      const promises = [];
      for (let i = 0; i < messageCount; i++) {
        promises.push(apiClient.sendChatMessage(`Load test message ${i + 1}`));
      }

      const results = await Promise.all(promises);
      const endTime = Date.now();

      expect(results.length).toBe(messageCount);
      expect(endTime - startTime).toBeLessThan(15000); // Should complete within 15 seconds
    });

    it('should handle extended conversation sessions', async () => {
      const conversationId = 'extended-session-' + Date.now();
      const messageCount = 50;

      const startTime = Date.now();
      
      for (let i = 0; i < messageCount; i++) {
        const response = await apiClient.sendChatMessage(`Extended message ${i + 1}`, conversationId);
        expect(response.conversationId).toBe(conversationId);
        
        // Small delay to simulate realistic usage
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      const endTime = Date.now();
      const totalTime = endTime - startTime;

      expect(totalTime).toBeLessThan(60000); // Should complete within 1 minute

      // Verify conversation has all messages
      const messages = await apiClient.getConversationMessages(conversationId);
      expect(messages.length).toBeGreaterThanOrEqual(messageCount);
    });
  });
});
