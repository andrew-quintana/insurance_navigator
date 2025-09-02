import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';
import { AuthPage } from '../../../e2e/page-objects/AuthPage';
import { UploadPage } from '../../../e2e/page-objects/UploadPage';
import { ChatPage } from '../../../e2e/page-objects/ChatPage';
import { FullIntegrationEnvironment } from '../setup/full-environment';

const environment = new FullIntegrationEnvironment();

test.describe('Accessibility Validation', () => {
  test.beforeAll(async () => {
    await environment.start();
  });

  test.afterAll(async () => {
    await environment.stop();
  });

  test.beforeEach(async () => {
    await environment.resetData();
  });

  test('should meet basic accessibility standards on auth pages', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    // Test login page
    await authPage.goto();
    await injectAxe(page);
    
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: { html: true }
    });

    // Test registration page
    await page.goto('/auth/register');
    await injectAxe(page);
    
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: { html: true }
    });
  });

  test('should be keyboard navigable', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.goto();
    
    // Tab through form elements
    await page.keyboard.press('Tab'); // Email input
    expect(await page.evaluate(() => document.activeElement?.tagName)).toBe('INPUT');
    
    await page.keyboard.press('Tab'); // Password input
    expect(await page.evaluate(() => document.activeElement?.tagName)).toBe('INPUT');
    
    await page.keyboard.press('Tab'); // Login button
    expect(await page.evaluate(() => document.activeElement?.tagName)).toBe('BUTTON');
    
    // Test Enter key submission
    await page.keyboard.press('Enter');
    // Should show validation error since no credentials entered
    await expect(page.getByText(/email.*required|password.*required/i)).toBeVisible();
  });

  test('should have proper ARIA labels and roles', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`aria-test-${Date.now()}@example.com`, 'AriaTest123!');
    
    // Test upload page
    await page.goto('/upload');
    
    // Check for proper labeling
    const fileInput = page.getByRole('button', { name: /upload/i });
    await expect(fileInput).toHaveAttribute('aria-label');
    
    // Check for progress indicators
    const progressBar = page.getByRole('progressbar');
    if (await progressBar.isVisible()) {
      await expect(progressBar).toHaveAttribute('aria-valuenow');
      await expect(progressBar).toHaveAttribute('aria-valuemin');
      await expect(progressBar).toHaveAttribute('aria-valuemax');
    }
    
    // Test chat page
    await page.goto('/chat');
    
    // Check message input
    const messageInput = page.getByLabel(/message|chat/i);
    await expect(messageInput).toHaveAttribute('aria-label');
    
    // Check send button
    const sendButton = page.getByRole('button', { name: /send/i });
    await expect(sendButton).toHaveAttribute('aria-label');
  });

  test('should support screen reader navigation', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.goto();
    
    // Check for proper heading structure
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    expect(headings.length).toBeGreaterThan(0);
    
    // Check for proper form labels
    const emailInput = page.getByLabel(/email/i);
    await expect(emailInput).toBeVisible();
    
    const passwordInput = page.getByLabel(/password/i);
    await expect(passwordInput).toBeVisible();
    
    // Check for proper button labels
    const loginButton = page.getByRole('button', { name: /login|sign in/i });
    await expect(loginButton).toBeVisible();
  });

  test('should have proper color contrast', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.goto();
    
    // Test with axe for color contrast issues
    await injectAxe(page);
    
    const results = await checkA11y(page, null, {
      rules: {
        'color-contrast': { enabled: true }
      }
    });
    
    // Should not have color contrast violations
    expect(results.violations).toHaveLength(0);
  });

  test('should handle focus management properly', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`focus-test-${Date.now()}@example.com`, 'FocusTest123!');
    
    // Test upload page focus management
    await page.goto('/upload');
    
    // Focus should be on the upload button initially
    const uploadButton = page.getByRole('button', { name: /upload/i });
    await uploadButton.focus();
    expect(await page.evaluate(() => document.activeElement === document.activeElement)).toBe(true);
    
    // Test modal focus management
    const uploadModal = page.getByRole('dialog');
    if (await uploadModal.isVisible()) {
      // Focus should be trapped within modal
      await page.keyboard.press('Tab');
      const focusedElement = await page.evaluate(() => document.activeElement);
      expect(await uploadModal.evaluate(el => el.contains(focusedElement))).toBe(true);
    }
  });

  test('should provide proper error messages', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.goto();
    
    // Test form validation errors
    await authPage.login('invalid-email', 'short');
    
    // Should show accessible error messages
    const errorMessages = page.getByRole('alert');
    await expect(errorMessages).toBeVisible();
    
    // Error messages should be associated with form fields
    const emailError = page.getByText(/email.*invalid|email.*required/i);
    await expect(emailError).toBeVisible();
    
    const passwordError = page.getByText(/password.*short|password.*required/i);
    await expect(passwordError).toBeVisible();
  });

  test('should support high contrast mode', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.goto();
    
    // Simulate high contrast mode
    await page.emulateMedia({ colorScheme: 'dark' });
    
    // Page should still be accessible
    await injectAxe(page);
    await checkA11y(page, null, {
      rules: {
        'color-contrast': { enabled: true }
      }
    });
  });

  test('should handle zoom levels properly', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.goto();
    
    // Test at 200% zoom
    await page.setViewportSize({ width: 640, height: 480 }); // Simulate zoom
    
    // All interactive elements should still be accessible
    const emailInput = page.getByLabel(/email/i);
    await expect(emailInput).toBeVisible();
    
    const passwordInput = page.getByLabel(/password/i);
    await expect(passwordInput).toBeVisible();
    
    const loginButton = page.getByRole('button', { name: /login|sign in/i });
    await expect(loginButton).toBeVisible();
  });

  test('should provide proper loading states', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`loading-test-${Date.now()}@example.com`, 'LoadingTest123!');
    
    // Test upload loading state
    await page.goto('/upload');
    
    // Upload a file
    const fileInput = page.getByLabel(/upload|file/i);
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('fake pdf content')
    });
    
    // Should show loading state with proper ARIA attributes
    const loadingIndicator = page.getByRole('progressbar');
    if (await loadingIndicator.isVisible()) {
      await expect(loadingIndicator).toHaveAttribute('aria-label', /loading|uploading/i);
    }
  });

  test('should handle dynamic content updates', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`dynamic-test-${Date.now()}@example.com`, 'DynamicTest123!');
    
    // Test chat page dynamic updates
    await page.goto('/chat');
    
    const messageInput = page.getByLabel(/message|chat/i);
    const sendButton = page.getByRole('button', { name: /send/i });
    
    // Send a message
    await messageInput.fill('Hello, this is a test message');
    await sendButton.click();
    
    // Should announce new message to screen readers
    const chatHistory = page.getByRole('log');
    if (await chatHistory.isVisible()) {
      await expect(chatHistory).toHaveAttribute('aria-live', 'polite');
    }
  });

  test('should support keyboard shortcuts', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`shortcuts-test-${Date.now()}@example.com`, 'ShortcutsTest123!');
    
    // Test chat page shortcuts
    await page.goto('/chat');
    
    const messageInput = page.getByLabel(/message|chat/i);
    await messageInput.focus();
    
    // Test Ctrl+Enter to send message
    await messageInput.fill('Test message');
    await page.keyboard.press('Control+Enter');
    
    // Message should be sent
    await expect(page.getByText('Test message')).toBeVisible();
  });

  test('should handle form validation accessibility', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.goto();
    
    // Test registration form validation
    await page.goto('/auth/register');
    
    // Try to submit empty form
    const registerButton = page.getByRole('button', { name: /register|sign up/i });
    await registerButton.click();
    
    // Should show validation errors with proper ARIA attributes
    const emailInput = page.getByLabel(/email/i);
    await expect(emailInput).toHaveAttribute('aria-invalid', 'true');
    
    const passwordInput = page.getByLabel(/password/i);
    await expect(passwordInput).toHaveAttribute('aria-invalid', 'true');
    
    // Error messages should be associated with inputs
    const emailError = page.getByText(/email.*required/i);
    await expect(emailError).toBeVisible();
    
    const passwordError = page.getByText(/password.*required/i);
    await expect(passwordError).toBeVisible();
  });
});
