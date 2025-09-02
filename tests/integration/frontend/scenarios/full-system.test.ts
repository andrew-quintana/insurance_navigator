import { test, expect } from '@playwright/test';
import { AuthPage } from '../../../e2e/page-objects/AuthPage';
import { UploadPage } from '../../../e2e/page-objects/UploadPage';
import { ChatPage } from '../../../e2e/page-objects/ChatPage';
import { FullIntegrationEnvironment } from '../setup/full-environment';
import path from 'path';

const environment = new FullIntegrationEnvironment();

test.describe('Full System Integration', () => {
  test.beforeAll(async () => {
    console.log('🚀 Starting full system integration tests...');
    await environment.start();
  });

  test.afterAll(async () => {
    console.log('🛑 Stopping full system integration tests...');
    await environment.stop();
  });

  test.beforeEach(async () => {
    await environment.resetData();
  });

  test('should complete end-to-end authenticated document processing flow', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    // 1. Authentication
    const testEmail = `e2e-test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'SecureTest123!');
    await authPage.expectLoggedIn();

    // 2. Document Upload with Real Processing
    await uploadPage.goto();
    const testDocument = path.join(__dirname, '../fixtures/sample-insurance-policy.pdf');
    await uploadPage.uploadFile(testDocument);
    
    // Wait for real document processing to complete
    await uploadPage.waitForUploadComplete();
    await uploadPage.expectDocumentInList('sample-insurance-policy.pdf');

    // 3. Real Agent Conversation with Document Context
    await chatPage.goto();
    
    // Ask specific questions about the uploaded document
    await chatPage.sendMessage('What is my annual deductible according to my uploaded policy?');
    await chatPage.waitForResponse();
    
    // Verify agent response includes document-specific information
    await chatPage.expectMessageInHistory(/deductible.*\$[\d,]+/i);

    // 4. Test Multi-turn Conversation
    await chatPage.sendMessage('What about my out-of-pocket maximum?');
    await chatPage.waitForResponse();
    
    await chatPage.expectMessageInHistory(/out.*of.*pocket|maximum/i);

    // 5. Test Document-specific Queries
    await chatPage.sendMessage('Does my policy cover dental work?');
    await chatPage.waitForResponse();
    
    // Should reference the actual document content
    await chatPage.expectMessageInHistory(/dental|coverage|policy/i);
  });

  test('should handle multiple users with document isolation', async ({ browser }) => {
    // Test user data isolation in real system
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

  test('should handle real processing errors gracefully', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);

    await authPage.register(`error-test-${Date.now()}@example.com`, 'ErrorTest123!');
    
    // Upload an invalid/corrupted document
    await uploadPage.goto();
    const corruptedDoc = path.join(__dirname, '../fixtures/corrupted-document.pdf');
    await uploadPage.uploadFile(corruptedDoc);

    // Should show appropriate error message
    await expect(page.getByText(/processing.*failed|unable.*process|invalid.*document/i))
      .toBeVisible({ timeout: 60000 });
  });

  test('should maintain performance under real workload', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    await authPage.register(`perf-test-${Date.now()}@example.com`, 'PerfTest123!');
    
    // Upload a large document
    await uploadPage.goto();
    const largeDoc = path.join(__dirname, '../fixtures/large-insurance-handbook.pdf');
    
    const uploadStart = Date.now();
    await uploadPage.uploadFile(largeDoc);
    await uploadPage.waitForUploadComplete();
    const uploadDuration = Date.now() - uploadStart;

    // Should complete within reasonable time (adjust based on document size)
    expect(uploadDuration).toBeLessThan(120000); // 2 minutes max

    // Chat response should be fast even with large document
    await chatPage.goto();
    
    const chatStart = Date.now();
    await chatPage.sendMessage('Summarize the key benefits in my policy');
    await chatPage.waitForResponse();
    const chatDuration = Date.now() - chatStart;

    expect(chatDuration).toBeLessThan(10000); // 10 seconds max
  });

  test('should handle concurrent user operations', async ({ browser }) => {
    // Test system under concurrent load
    const contexts = [];
    const pages = [];
    
    // Create 5 concurrent users
    for (let i = 0; i < 5; i++) {
      const context = await browser.newContext();
      const page = await context.newPage();
      contexts.push(context);
      pages.push(page);
    }

    const authPages = pages.map(page => new AuthPage(page));
    const uploadPages = pages.map(page => new UploadPage(page));

    // Register all users concurrently
    const registrationPromises = authPages.map((authPage, index) => 
      authPage.register(`concurrent-user-${index}-${Date.now()}@example.com`, 'ConcurrentTest123!')
    );
    
    await Promise.all(registrationPromises);

    // Upload documents concurrently
    const uploadPromises = uploadPages.map(async (uploadPage, index) => {
      await uploadPage.goto();
      const docPath = path.join(__dirname, `../fixtures/concurrent-doc-${index}.pdf`);
      await uploadPage.uploadFile(docPath);
      await uploadPage.waitForUploadComplete();
    });

    const uploadStart = Date.now();
    await Promise.all(uploadPromises);
    const uploadDuration = Date.now() - uploadStart;

    // All uploads should complete within reasonable time
    expect(uploadDuration).toBeLessThan(180000); // 3 minutes max for 5 concurrent uploads

    // Clean up
    await Promise.all(contexts.map(context => context.close()));
  });

  test('should maintain session across browser refresh and navigation', async ({ page }) => {
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

    // Upload a document
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

  test('should handle network interruptions gracefully', async ({ page, context }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);

    await authPage.register(`network-test-${Date.now()}@example.com`, 'NetworkTest123!');
    await uploadPage.goto();

    // Start upload
    const testDocument = path.join(__dirname, '../fixtures/network-test-policy.pdf');
    const uploadPromise = uploadPage.uploadFile(testDocument);

    // Simulate network interruption
    await context.setOffline(true);
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
    await context.setOffline(false);

    // Upload should either complete or show appropriate error
    try {
      await uploadPromise;
      await uploadPage.waitForUploadComplete();
    } catch (error) {
      // Should show network error message
      await expect(page.getByText(/network.*error|connection.*lost|retry/i)).toBeVisible();
    }
  });

  test('should validate real agent conversation quality', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    await authPage.register(`quality-test-${Date.now()}@example.com`, 'QualityTest123!');
    
    // Upload a specific document with known content
    await uploadPage.goto();
    const testDocument = path.join(__dirname, '../fixtures/quality-test-policy.pdf');
    await uploadPage.uploadFile(testDocument);
    await uploadPage.waitForUploadComplete();

    // Test specific questions that should have specific answers
    await chatPage.goto();
    
    // Test 1: Specific benefit question
    await chatPage.sendMessage('What is the copay for specialist visits?');
    await chatPage.waitForResponse();
    await chatPage.expectMessageInHistory(/\$[\d,]+|copay|specialist/i);

    // Test 2: Coverage question
    await chatPage.sendMessage('Is mental health coverage included?');
    await chatPage.waitForResponse();
    await chatPage.expectMessageInHistory(/mental.*health|coverage|included|yes|no/i);

    // Test 3: Policy limits question
    await chatPage.sendMessage('What is the annual maximum benefit?');
    await chatPage.waitForResponse();
    await chatPage.expectMessageInHistory(/\$[\d,]+|annual|maximum|benefit/i);

    // Test 4: Multi-document context (if multiple docs uploaded)
    await chatPage.sendMessage('Compare the benefits across all my uploaded documents');
    await chatPage.waitForResponse();
    await chatPage.expectMessageInHistory(/compare|benefits|documents/i);
  });
});
