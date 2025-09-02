import { test, expect } from '@playwright/test';
import { AuthPage } from '../page-objects/AuthPage';
import { UploadPage } from '../page-objects/UploadPage';
import { ChatPage } from '../page-objects/ChatPage';
import path from 'path';

test.describe('Real System Authentication Flow', () => {
  let authPage: AuthPage;
  let uploadPage: UploadPage;
  let chatPage: ChatPage;

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page);
    uploadPage = new UploadPage(page);
    chatPage = new ChatPage(page);
  });

  test('should complete real system authentication flow', async ({ page }) => {
    const testEmail = `real-system-test-${Date.now()}@example.com`;
    
    // Register with real Supabase
    await authPage.register(testEmail, 'RealSystemTest123!');
    await authPage.expectLoggedIn();
    
    // Verify session persistence
    await page.reload();
    await authPage.expectLoggedIn();
    
    // Test logout
    await authPage.logout();
    await authPage.expectLoggedOut();
    
    // Test login
    await authPage.login(testEmail, 'RealSystemTest123!');
    await authPage.expectLoggedIn();
  });

  test('should handle real system protected routes', async ({ page }) => {
    // Try to access protected route without auth
    await page.goto('/upload');
    await expect(page).toHaveURL(/auth.*login|login/);
    
    // Register and access protected route
    const testEmail = `protected-test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'ProtectedTest123!');
    
    await page.goto('/upload');
    await expect(page).toHaveURL(/upload/);
  });

  test('should complete real system upload to chat flow', async ({ page }) => {
    // Register user
    const testEmail = `upload-chat-test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'UploadChatTest123!');
    
    // Upload document with real processing
    await uploadPage.goto();
    const testDocument = path.join(__dirname, '../fixtures/sample-insurance-policy.pdf');
    await uploadPage.uploadFile(testDocument);
    
    // Wait for real document processing
    await uploadPage.waitForUploadComplete();
    await uploadPage.expectDocumentInList('sample-insurance-policy.pdf');
    
    // Test chat with real AI
    await chatPage.goto();
    await chatPage.sendMessage('What is my deductible?');
    await chatPage.waitForResponse();
    
    // Should get real AI response
    await chatPage.expectMessageInHistory(/deductible|policy|document/i);
  });

  test('should handle real system session management', async ({ page }) => {
    // Register user
    const testEmail = `session-test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'SessionTest123!');
    
    // Perform operations that require session
    await uploadPage.goto();
    const testDocument = path.join(__dirname, '../fixtures/session-test-policy.pdf');
    await uploadPage.uploadFile(testDocument);
    await uploadPage.waitForUploadComplete();
    
    // Session should persist across operations
    await chatPage.goto();
    await chatPage.sendMessage('Hello');
    await chatPage.waitForResponse();
    
    // Session should persist across page reloads
    await page.reload();
    await authPage.expectLoggedIn();
  });

  test('should handle real system error scenarios', async ({ page }) => {
    // Test invalid login
    await authPage.goto();
    await authPage.login('nonexistent@example.com', 'wrongpassword');
    await authPage.expectError(/invalid.*credentials|login.*failed/i);
    
    // Test duplicate registration
    const testEmail = `duplicate-test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'DuplicateTest123!');
    await authPage.logout();
    
    // Try to register again with same email
    await authPage.goto();
    await authPage.register(testEmail, 'DuplicateTest123!');
    await authPage.expectError(/email.*already|user.*exists/i);
  });
});
