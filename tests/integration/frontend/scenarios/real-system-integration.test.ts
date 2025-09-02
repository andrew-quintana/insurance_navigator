import { test, expect } from '@playwright/test';
import { AuthPage } from '../../../e2e/page-objects/AuthPage';
import { UploadPage } from '../../../e2e/page-objects/UploadPage';
import { ChatPage } from '../../../e2e/page-objects/ChatPage';
import { FullIntegrationEnvironment } from '../setup/full-environment';
import path from 'path';

const environment = new FullIntegrationEnvironment();

test.describe('Real System Integration (Phase 5)', () => {
  test.beforeAll(async () => {
    console.log('🚀 Starting real system integration tests...');
    await environment.start();
  });

  test.afterAll(async () => {
    console.log('🛑 Stopping real system integration tests...');
    await environment.stop();
  });

  test.beforeEach(async () => {
    await environment.resetData();
  });

  test('should complete end-to-end with real document processing', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    // 1. Real Authentication with Supabase
    const testEmail = `real-test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'RealTest123!');
    await authPage.expectLoggedIn();

    // 2. Real Document Upload with Actual Processing
    await uploadPage.goto();
    const testDocument = path.join(__dirname, '../fixtures/sample-insurance-policy.pdf');
    await uploadPage.uploadFile(testDocument);
    
    // Wait for real document processing (this will take longer with real services)
    await uploadPage.waitForUploadComplete();
    await uploadPage.expectDocumentInList('sample-insurance-policy.pdf');

    // 3. Real Agent Conversation with Actual RAG Retrieval
    await chatPage.goto();
    
    // Ask specific questions that require real document processing
    await chatPage.sendMessage('What is my annual deductible according to my uploaded policy?');
    await chatPage.waitForResponse();
    
    // Verify agent response includes actual document content (not mocked)
    await chatPage.expectMessageInHistory(/deductible|policy|document/i);

    // 4. Test Real Multi-turn Conversation
    await chatPage.sendMessage('What about my out-of-pocket maximum?');
    await chatPage.waitForResponse();
    
    await chatPage.expectMessageInHistory(/out.*of.*pocket|maximum/i);

    // 5. Test Real Document-specific Queries
    await chatPage.sendMessage('Does my policy cover dental work?');
    await chatPage.waitForResponse();
    
    // Should reference the actual processed document content
    await chatPage.expectMessageInHistory(/dental|coverage|policy/i);
  });

  test('should handle real document processing with LlamaParse', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    await authPage.register(`llamaparse-test-${Date.now()}@example.com`, 'LlamaParseTest123!');
    
    // Upload a complex document that requires real parsing
    await uploadPage.goto();
    const complexDocument = path.join(__dirname, '../fixtures/complex-insurance-policy.pdf');
    await uploadPage.uploadFile(complexDocument);
    
    // Real LlamaParse processing will take longer
    await uploadPage.waitForUploadComplete();
    await uploadPage.expectDocumentInList('complex-insurance-policy.pdf');

    // Test that the document was actually parsed and indexed
    await chatPage.goto();
    await chatPage.sendMessage('What are the specific coverage details in my policy?');
    await chatPage.waitForResponse();
    
    // Should have detailed, specific information from the parsed document
    await chatPage.expectMessageInHistory(/coverage|benefits|specific/i);
  });

  test('should handle real OpenAI agent responses', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    await authPage.register(`openai-test-${Date.now()}@example.com`, 'OpenAITest123!');
    
    // Upload document for context
    await uploadPage.goto();
    const testDocument = path.join(__dirname, '../fixtures/openai-test-policy.pdf');
    await uploadPage.uploadFile(testDocument);
    await uploadPage.waitForUploadComplete();

    // Test real OpenAI agent responses
    await chatPage.goto();
    
    // Ask complex questions that require real AI processing
    await chatPage.sendMessage('Based on my policy, what would be the best strategy for maximizing my benefits?');
    await chatPage.waitForResponse();
    
    // Should get intelligent, contextual responses from real OpenAI
    await chatPage.expectMessageInHistory(/strategy|benefits|recommend/i);

    // Test follow-up questions
    await chatPage.sendMessage('Can you explain that in simpler terms?');
    await chatPage.waitForResponse();
    
    // Should get a simplified explanation
    await chatPage.expectMessageInHistory(/simpl|explain|understand/i);
  });

  test('should validate real RAG retrieval accuracy', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    await authPage.register(`rag-test-${Date.now()}@example.com`, 'RAGTest123!');
    
    // Upload multiple documents for RAG testing
    await uploadPage.goto();
    const doc1 = path.join(__dirname, '../fixtures/rag-test-doc1.pdf');
    const doc2 = path.join(__dirname, '../fixtures/rag-test-doc2.pdf');
    
    await uploadPage.uploadFile(doc1);
    await uploadPage.waitForUploadComplete();
    
    await uploadPage.uploadFile(doc2);
    await uploadPage.waitForUploadComplete();

    // Test RAG retrieval across multiple documents
    await chatPage.goto();
    
    // Ask questions that require information from specific documents
    await chatPage.sendMessage('What is the difference between the coverage in my two documents?');
    await chatPage.waitForResponse();
    
    // Should retrieve and compare information from both documents
    await chatPage.expectMessageInHistory(/difference|compare|both|documents/i);

    // Test specific document queries
    await chatPage.sendMessage('What does the first document say about emergency coverage?');
    await chatPage.waitForResponse();
    
    // Should retrieve specific information from the first document
    await chatPage.expectMessageInHistory(/emergency|first|document/i);
  });

  test('should handle real system performance under load', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    await authPage.register(`performance-test-${Date.now()}@example.com`, 'PerformanceTest123!');
    
    // Upload a large document for performance testing
    await uploadPage.goto();
    const largeDocument = path.join(__dirname, '../fixtures/large-insurance-handbook.pdf');
    
    const uploadStart = Date.now();
    await uploadPage.uploadFile(largeDocument);
    await uploadPage.waitForUploadComplete();
    const uploadDuration = Date.now() - uploadStart;

    // Real processing should complete within reasonable time
    expect(uploadDuration).toBeLessThan(300000); // 5 minutes max for real processing

    // Test chat performance with real AI processing
    await chatPage.goto();
    
    const chatStart = Date.now();
    await chatPage.sendMessage('Summarize the key benefits in my policy');
    await chatPage.waitForResponse();
    const chatDuration = Date.now() - chatStart;

    // Real AI responses should be reasonable
    expect(chatDuration).toBeLessThan(30000); // 30 seconds max for real AI
  });

  test('should validate real error handling with external services', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);

    await authPage.register(`error-test-${Date.now()}@example.com`, 'ErrorTest123!');
    
    // Test with corrupted document that should fail real processing
    await uploadPage.goto();
    const corruptedDoc = path.join(__dirname, '../fixtures/corrupted-document.pdf');
    await uploadPage.uploadFile(corruptedDoc);

    // Should show appropriate error message from real processing
    await expect(page.getByText(/processing.*failed|unable.*process|invalid.*document/i))
      .toBeVisible({ timeout: 120000 }); // Longer timeout for real processing
  });

  test('should maintain real session management across operations', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    // Register and login
    const testEmail = `session-test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'SessionTest123!');
    await authPage.expectLoggedIn();

    // Navigate to upload page
    await uploadPage.goto();
    await authPage.expectLoggedIn(); // Should still be logged in

    // Upload a document (this will take longer with real processing)
    const testDocument = path.join(__dirname, '../fixtures/session-test-policy.pdf');
    await uploadPage.uploadFile(testDocument);
    await uploadPage.waitForUploadComplete();

    // Refresh the page
    await page.reload();
    await authPage.expectLoggedIn(); // Should still be logged in

    // Navigate to chat
    await chatPage.goto();
    await authPage.expectLoggedIn(); // Should still be logged in

    // Send a message
    await chatPage.sendMessage('Hello, I uploaded a document earlier');
    await chatPage.waitForResponse();
  });

  test('should validate real user data isolation', async ({ browser }) => {
    // Test user data isolation with real backend services
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    const authPage1 = new AuthPage(page1);
    const authPage2 = new AuthPage(page2);
    const uploadPage1 = new UploadPage(page1);
    const uploadPage2 = new UploadPage(page2);

    // Register two different users
    const user1Email = `user1-${Date.now()}@example.com`;
    const user2Email = `user2-${Date.now()}@example.com`;

    await authPage1.register(user1Email, 'User1Test123!');
    await authPage2.register(user2Email, 'User2Test123!');

    // User 1 uploads a document
    await uploadPage1.goto();
    const doc1Path = path.join(__dirname, '../fixtures/user1-policy.pdf');
    await uploadPage1.uploadFile(doc1Path);
    await uploadPage1.waitForUploadComplete();

    // User 2 uploads a different document  
    await uploadPage2.goto();
    const doc2Path = path.join(__dirname, '../fixtures/user2-policy.pdf');
    await uploadPage2.uploadFile(doc2Path);
    await uploadPage2.waitForUploadComplete();

    // Verify each user only sees their own documents
    await uploadPage1.expectDocumentInList('user1-policy.pdf');
    await expect(page1.getByText('user2-policy.pdf')).not.toBeVisible();

    await uploadPage2.expectDocumentInList('user2-policy.pdf');
    await expect(page2.getByText('user1-policy.pdf')).not.toBeVisible();

    await context1.close();
    await context2.close();
  });
});
