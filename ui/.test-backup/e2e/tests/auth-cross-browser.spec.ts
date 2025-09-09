import { test, expect } from '@playwright/test';
import { AuthPage } from '../page-objects/AuthPage';
import { createTestUserForBrowser, createTestUser } from '../fixtures/test-users';

// This test runs across all configured browsers
test.describe('Cross-Browser Authentication', () => {
  test('authentication flow works in all browsers', async ({ page, browserName }) => {
    const authPage = new AuthPage(page);
    
    console.log(`Testing authentication in ${browserName}`);
    
    // Register and login flow
    const testUser = createTestUserForBrowser(browserName);
    await authPage.register(testUser.email, testUser.password);
    await authPage.expectLoggedIn();
    
    // Test logout
    await authPage.logout();
    await authPage.expectLoggedOut();
    
    // Test login
    await authPage.login(testUser.email, testUser.password);
    await authPage.expectLoggedIn();
  });

  test('protected routes work across browsers', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    // Without auth, should redirect
    await page.goto('/upload');
    await expect(page).toHaveURL(/auth.*login|login/i);
    
    // With auth, should access
    const testUser = createTestUser();
    await authPage.register(testUser.email, testUser.password);
    await page.goto('/upload');
    await expect(page).toHaveURL(/upload/);
  });

  test('form validation works across browsers', async ({ page, browserName }) => {
    const authPage = new AuthPage(page);
    
    console.log(`Testing form validation in ${browserName}`);
    
    await authPage.goto();
    
    // Test empty form submission
    await authPage.loginButton.click();
    
    // Should show validation errors
    await expect(page.getByText(/email.*required|password.*required/i)).toBeVisible();
    
    // Test invalid email format
    await authPage.login('invalid-email', 'password123');
    await expect(page.getByText(/invalid.*email|email.*format/i)).toBeVisible();
  });

  test('session persistence works across browsers', async ({ page, browserName }) => {
    const authPage = new AuthPage(page);
    
    console.log(`Testing session persistence in ${browserName}`);
    
    // Register and login
    const testUser = createTestUserForBrowser(browserName);
    await authPage.register(testUser.email, testUser.password);
    await authPage.expectLoggedIn();
    
    // Refresh page
    await page.reload();
    
    // Should still be logged in
    await authPage.expectLoggedIn();
    
    // Navigate to protected route
    await page.goto('/upload');
    await expect(page).toHaveURL(/upload/);
  });

  test('error handling works across browsers', async ({ page, browserName }) => {
    const authPage = new AuthPage(page);
    
    console.log(`Testing error handling in ${browserName}`);
    
    await authPage.goto();
    
    // Test invalid credentials
    await authPage.login('nonexistent@example.com', 'wrongpassword');
    await authPage.expectError(/invalid.*credentials|login.*failed|incorrect/i);
    
    // Test network errors
    await page.route('**/auth/**', route => route.abort('failed'));
    await authPage.login('test@example.com', 'password123');
    await expect(page.getByText(/network.*error|connection.*failed|try.*again/i)).toBeVisible();
  });

  test('authentication state management works across browsers', async ({ page, browserName }) => {
    const authPage = new AuthPage(page);
    
    console.log(`Testing authentication state management in ${browserName}`);
    
    // Test unauthenticated state
    await authPage.goto();
    await authPage.expectLoggedOut();
    
    // Test authenticated state
    const testUser = createTestUserForBrowser(browserName);
    await authPage.register(testUser.email, testUser.password);
    await authPage.expectLoggedIn();
    
    // Test logout state
    await authPage.logout();
    await authPage.expectLoggedOut();
    
    // Test protected route access after logout
    await page.goto('/upload');
    await expect(page).toHaveURL(/auth.*login|login/i);
  });

  test('concurrent authentication works across browsers', async ({ page, browserName, context }) => {
    const authPage = new AuthPage(page);
    
    console.log(`Testing concurrent authentication in ${browserName}`);
    
    // Open multiple tabs
    const tab1 = page;
    const tab2 = await context.newPage();
    const tab3 = await context.newPage();
    
    const authPage1 = new AuthPage(tab1);
    const authPage2 = new AuthPage(tab2);
    const authPage3 = new AuthPage(tab3);
    
    // Create test user
    const testUser = createTestUserForBrowser(browserName);
    
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

  test('browser-specific features work correctly', async ({ page, browserName }) => {
    const authPage = new AuthPage(page);
    
    console.log(`Testing browser-specific features in ${browserName}`);
    
    // Test browser-specific form behavior
    await authPage.goto();
    
    // Test autofill behavior
    await authPage.emailInput.focus();
    await page.keyboard.type('test@example.com');
    
    // Test password visibility toggle (if implemented)
    const passwordToggle = page.getByRole('button', { name: /show.*password|hide.*password/i });
    if (await passwordToggle.isVisible()) {
      await passwordToggle.click();
      // Password should be visible
      await expect(authPage.passwordInput).toHaveAttribute('type', 'text');
      
      await passwordToggle.click();
      // Password should be hidden
      await expect(authPage.passwordInput).toHaveAttribute('type', 'password');
    }
    
    // Test keyboard navigation
    await authPage.emailInput.focus();
    await page.keyboard.press('Tab');
    await expect(authPage.passwordInput).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(authPage.loginButton).toBeFocused();
  });

  test('cookies and storage work across browsers', async ({ page, browserName }) => {
    const authPage = new AuthPage(page);
    
    console.log(`Testing cookies and storage in ${browserName}`);
    
    // Test authentication
    const testUser = createTestUserForBrowser(browserName);
    await authPage.register(testUser.email, testUser.password);
    await authPage.expectLoggedIn();
    
    // Check if authentication tokens are stored
    const hasAuthToken = await page.evaluate(() => {
      return localStorage.getItem('supabase.auth.token') !== null ||
             document.cookie.includes('auth') ||
             sessionStorage.getItem('auth') !== null;
    });
    
    expect(hasAuthToken).toBe(true);
    
    // Test persistence across page reloads
    await page.reload();
    await authPage.expectLoggedIn();
  });

  test('authentication performance is consistent across browsers', async ({ page, browserName }) => {
    const authPage = new AuthPage(page);
    
    console.log(`Testing authentication performance in ${browserName}`);
    
    // Measure registration time
    const startTime = Date.now();
    const testUser = createTestUserForBrowser(browserName);
    await authPage.register(testUser.email, testUser.password);
    const registrationTime = Date.now() - startTime;
    
    console.log(`Registration time in ${browserName}: ${registrationTime}ms`);
    
    // Registration should complete within reasonable time
    expect(registrationTime).toBeLessThan(10000); // 10 seconds
    
    // Test logout
    await authPage.logout();
    
    // Measure login time
    const loginStartTime = Date.now();
    await authPage.login(testUser.email, testUser.password);
    const loginTime = Date.now() - loginStartTime;
    
    console.log(`Login time in ${browserName}: ${loginTime}ms`);
    
    // Login should complete within reasonable time
    expect(loginTime).toBeLessThan(5000); // 5 seconds
  });
});
