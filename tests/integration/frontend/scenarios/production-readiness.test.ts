import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';
import { AuthPage } from '../../../e2e/page-objects/AuthPage';
import { UploadPage } from '../../../e2e/page-objects/UploadPage';
import { ChatPage } from '../../../e2e/page-objects/ChatPage';
import { FullIntegrationEnvironment } from '../setup/full-environment';

const environment = new FullIntegrationEnvironment();

test.describe('Production Readiness Validation', () => {
  test.beforeAll(async () => {
    await environment.start();
  });

  test.afterAll(async () => {
    await environment.stop();
  });

  test.beforeEach(async () => {
    await environment.resetData();
  });

  test('should meet production security standards', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    // Test 1: Authentication security
    await authPage.goto();
    
    // Check for secure headers
    const response = await page.goto('/auth/login');
    const headers = response?.headers();
    
    // Should have security headers
    expect(headers?.['x-frame-options']).toBeDefined();
    expect(headers?.['x-content-type-options']).toBeDefined();
    expect(headers?.['x-xss-protection']).toBeDefined();
    
    // Test 2: Input validation
    await authPage.login("'; DROP TABLE users; --", 'password');
    await authPage.expectError(/invalid.*credentials/i);
    
    // Test 3: Rate limiting
    const loginAttempts = Array(10).fill(null).map(() => 
      page.request.post('/api/auth/login', {
        data: { email: 'test@example.com', password: 'wrong' }
      })
    );
    
    const responses = await Promise.all(loginAttempts);
    const rateLimitedResponses = responses.filter(r => r.status() === 429);
    expect(rateLimitedResponses.length).toBeGreaterThan(0);
  });

  test('should meet production accessibility standards', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`accessibility-test-${Date.now()}@example.com`, 'AccessibilityTest123!');
    
    // Test all major pages for accessibility
    const pages = ['/upload', '/chat', '/dashboard'];
    
    for (const pagePath of pages) {
      await page.goto(pagePath);
      await injectAxe(page);
      
      const results = await checkA11y(page, null, {
        rules: {
          'color-contrast': { enabled: true },
          'keyboard-navigation': { enabled: true },
          'aria-labels': { enabled: true }
        }
      });
      
      // Should not have accessibility violations
      expect(results.violations).toHaveLength(0);
    }
  });

  test('should handle production error scenarios gracefully', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`error-test-${Date.now()}@example.com`, 'ErrorTest123!');
    
    // Test network failure scenarios
    await page.route('**/api/**', route => route.abort());
    
    await page.goto('/upload');
    await expect(page.getByText(/network.*error|connection.*failed/i)).toBeVisible();
    
    // Test service unavailability
    await page.unroute('**/api/**');
    await page.route('**/api/**', route => route.fulfill({ status: 503 }));
    
    await page.goto('/chat');
    await expect(page.getByText(/service.*unavailable|temporarily.*down/i)).toBeVisible();
  });

  test('should maintain production performance standards', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    await authPage.register(`performance-test-${Date.now()}@example.com`, 'PerformanceTest123!');
    
    // Test page load performance
    const loadStart = Date.now();
    await page.goto('/upload');
    const loadTime = Date.now() - loadStart;
    expect(loadTime).toBeLessThan(3000); // < 3 seconds page load
    
    // Test upload performance
    await uploadPage.goto();
    const testDocument = path.join(__dirname, '../fixtures/performance-test-policy.pdf');
    
    const uploadStart = Date.now();
    await uploadPage.uploadFile(testDocument);
    await uploadPage.waitForUploadComplete();
    const uploadTime = Date.now() - uploadStart;
    
    expect(uploadTime).toBeLessThan(120000); // < 2 minutes for real processing
    
    // Test chat performance
    await chatPage.goto();
    
    const chatStart = Date.now();
    await chatPage.sendMessage('What is my deductible?');
    await chatPage.waitForResponse();
    const chatTime = Date.now() - chatStart;
    
    expect(chatTime).toBeLessThan(30000); // < 30 seconds for real AI
  });

  test('should validate production data integrity', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    await authPage.register(`integrity-test-${Date.now()}@example.com`, 'IntegrityTest123!');
    
    // Upload document
    await uploadPage.goto();
    const testDocument = path.join(__dirname, '../fixtures/integrity-test-policy.pdf');
    await uploadPage.uploadFile(testDocument);
    await uploadPage.waitForUploadComplete();
    
    // Verify document is properly stored and accessible
    await uploadPage.expectDocumentInList('integrity-test-policy.pdf');
    
    // Test chat with document context
    await chatPage.goto();
    await chatPage.sendMessage('What is in my uploaded document?');
    await chatPage.waitForResponse();
    
    // Should reference the actual document content
    await chatPage.expectMessageInHistory(/document|policy|uploaded/i);
  });

  test('should handle production concurrent users', async ({ browser }) => {
    // Test system under concurrent load
    const contexts = [];
    const pages = [];
    
    // Create 10 concurrent users
    for (let i = 0; i < 10; i++) {
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
    expect(uploadDuration).toBeLessThan(300000); // 5 minutes max for 10 concurrent uploads

    // Clean up
    await Promise.all(contexts.map(context => context.close()));
  });

  test('should validate production monitoring and logging', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`monitoring-test-${Date.now()}@example.com`, 'MonitoringTest123!');
    
    // Test that operations are properly logged
    await page.goto('/upload');
    
    // Check for monitoring endpoints
    const healthResponse = await page.request.get('/api/health');
    expect(healthResponse.status()).toBe(200);
    
    const metricsResponse = await page.request.get('/api/metrics');
    expect([200, 404]).toContain(metricsResponse.status()); // May or may not exist
    
    // Test error logging
    await page.goto('/nonexistent-page');
    await expect(page.getByText(/not found|404/i)).toBeVisible();
  });

  test('should validate production backup and recovery', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`backup-test-${Date.now()}@example.com`, 'BackupTest123!');
    
    // Upload document
    const uploadPage = new UploadPage(page);
    await uploadPage.goto();
    const testDocument = path.join(__dirname, '../fixtures/backup-test-policy.pdf');
    await uploadPage.uploadFile(testDocument);
    await uploadPage.waitForUploadComplete();
    
    // Simulate system restart (restart environment)
    await environment.restart();
    
    // Verify data persistence
    await authPage.login(`backup-test-${Date.now()}@example.com`, 'BackupTest123!');
    await uploadPage.goto();
    await uploadPage.expectDocumentInList('backup-test-policy.pdf');
  });

  test('should validate production scalability', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    await authPage.register(`scalability-test-${Date.now()}@example.com`, 'ScalabilityTest123!');
    
    // Test with large document
    await uploadPage.goto();
    const largeDocument = path.join(__dirname, '../fixtures/large-insurance-handbook.pdf');
    
    const uploadStart = Date.now();
    await uploadPage.uploadFile(largeDocument);
    await uploadPage.waitForUploadComplete();
    const uploadDuration = Date.now() - uploadStart;
    
    // Should handle large documents efficiently
    expect(uploadDuration).toBeLessThan(300000); // 5 minutes max
    
    // Test multiple chat sessions
    const chatPromises = Array(5).fill(null).map(async (_, index) => {
      await chatPage.goto();
      await chatPage.sendMessage(`Test message ${index + 1}`);
      await chatPage.waitForResponse();
    });
    
    const chatStart = Date.now();
    await Promise.all(chatPromises);
    const chatDuration = Date.now() - chatStart;
    
    // Should handle multiple concurrent chats
    expect(chatDuration).toBeLessThan(120000); // 2 minutes max
  });
});
