import { test, expect } from '@playwright/test';
import { AuthPage } from '../page-objects/AuthPage';
import { createTestUser, createTestUserWithPrefix } from '../fixtures/test-users';

test.describe('Authentication Flow (PRIORITY #1)', () => {
  let authPage: AuthPage;

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page);
  });

  test('should register new user with email validation', async ({ page }) => {
    const testUser = createTestUser();
    
    await authPage.register(testUser.email, testUser.password);
    
    // Should redirect to dashboard or email verification
    await expect(page).toHaveURL(/dashboard|verify|welcome/i);
    await authPage.expectLoggedIn();
  });

  test('should login existing user with valid credentials', async ({ page }) => {
    // First register a user
    const testUser = createTestUser();
    await authPage.register(testUser.email, testUser.password);
    await authPage.logout();
    
    // Then login
    await authPage.login(testUser.email, testUser.password);
    await expect(page).toHaveURL(/dashboard|welcome/i);
    await authPage.expectLoggedIn();
  });

  test('should reject invalid login credentials', async () => {
    await authPage.goto();
    await authPage.login('nonexistent@example.com', 'wrongpassword');
    
    await authPage.expectError(/invalid.*credentials|login.*failed|incorrect/i);
    await authPage.expectLoggedOut();
  });

  test('should maintain session across browser refresh', async ({ page }) => {
    // Login
    const testUser = createTestUser();
    await authPage.register(testUser.email, testUser.password);
    
    // Refresh page
    await page.reload();
    
    // Should still be logged in
    await authPage.expectLoggedIn();
  });

  test('should redirect unauthenticated users from protected routes', async ({ page }) => {
    await page.goto('/upload');
    
    // Should redirect to login
    await expect(page).toHaveURL(/auth.*login|login/i);
    await authPage.expectLoggedOut();
  });

  test('should complete logout and redirect to login', async ({ page }) => {
    // Login first
    const testUser = createTestUser();
    await authPage.register(testUser.email, testUser.password);
    
    // Logout
    await authPage.logout();
    
    // Should redirect to login page
    await expect(page).toHaveURL(/auth.*login|login/i);
    await authPage.expectLoggedOut();
    
    // Should not be able to access protected routes
    await page.goto('/upload');
    await expect(page).toHaveURL(/auth.*login|login/i);
  });

  test('should handle form validation errors', async ({ page }) => {
    await authPage.goto();
    
    // Try to submit empty form
    await authPage.loginButton.click();
    
    // Should show validation errors
    await expect(page.getByText(/email.*required|password.*required/i)).toBeVisible();
  });

  test('should handle invalid email format', async ({ page }) => {
    await authPage.goto();
    
    // Try to login with invalid email
    await authPage.login('invalid-email', 'password123');
    
    // Should show email validation error
    await expect(page.getByText(/invalid.*email|email.*format/i)).toBeVisible();
  });

  test('should handle weak password', async ({ page }) => {
    await authPage.gotoRegister();
    
    // Try to register with weak password
    await authPage.register('test@example.com', '123');
    
    // Should show password strength error
    await expect(page.getByText(/password.*weak|password.*length/i)).toBeVisible();
  });

  test('should handle duplicate email registration', async ({ page }) => {
    const testUser = createTestUser();
    
    // Register first time
    await authPage.register(testUser.email, testUser.password);
    await authPage.expectLoggedIn();
    await authPage.logout();
    
    // Try to register with same email
    await authPage.gotoRegister();
    await authPage.register(testUser.email, 'differentpassword');
    
    // Should show duplicate email error
    await expect(page.getByText(/email.*exists|already.*registered/i)).toBeVisible();
  });

  test('should handle session expiry gracefully', async ({ page }) => {
    // Login first
    const testUser = createTestUser();
    await authPage.register(testUser.email, testUser.password);
    
    // Simulate session expiry by clearing auth state
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    
    // Try to access protected route
    await page.goto('/upload');
    
    // Should redirect to login
    await expect(page).toHaveURL(/auth.*login|login/i);
    await authPage.expectLoggedOut();
  });

  test('should maintain authentication state across tabs', async ({ page, context }) => {
    // Login in first tab
    const testUser = createTestUser();
    await authPage.register(testUser.email, testUser.password);
    
    // Open new tab
    const newPage = await context.newPage();
    const newAuthPage = new AuthPage(newPage);
    
    // Navigate to protected route in new tab
    await newPage.goto('/upload');
    
    // Should still be authenticated
    await expect(newPage).toHaveURL(/upload/);
    
    // Clean up
    await newPage.close();
  });

  test('should handle concurrent login attempts', async ({ page, context }) => {
    const testUser = createTestUser();
    
    // Open multiple tabs
    const tab1 = page;
    const tab2 = await context.newPage();
    const tab3 = await context.newPage();
    
    const authPage1 = new AuthPage(tab1);
    const authPage2 = new AuthPage(tab2);
    const authPage3 = new AuthPage(tab3);
    
    // Try to login in all tabs simultaneously
    await Promise.all([
      authPage1.login(testUser.email, testUser.password),
      authPage2.login(testUser.email, testUser.password),
      authPage3.login(testUser.email, testUser.password)
    ]);
    
    // At least one should succeed
    const successCount = await Promise.all([
      tab1.url().then(url => url.includes('dashboard') || url.includes('welcome')),
      tab2.url().then(url => url.includes('dashboard') || url.includes('welcome')),
      tab3.url().then(url => url.includes('dashboard') || url.includes('welcome'))
    ]).then(results => results.filter(Boolean).length);
    
    expect(successCount).toBeGreaterThan(0);
    
    // Clean up
    await tab2.close();
    await tab3.close();
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Mock network failure
    await page.route('**/auth/**', route => route.abort('failed'));
    
    await authPage.goto();
    await authPage.login('test@example.com', 'password123');
    
    // Should show network error message
    await expect(page.getByText(/network.*error|connection.*failed|try.*again/i)).toBeVisible();
  });

  test('should handle server errors gracefully', async ({ page }) => {
    // Mock server error
    await page.route('**/auth/**', route => route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Internal server error' })
    }));
    
    await authPage.goto();
    await authPage.login('test@example.com', 'password123');
    
    // Should show server error message
    await expect(page.getByText(/server.*error|internal.*error|try.*later/i)).toBeVisible();
  });
});
