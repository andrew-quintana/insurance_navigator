import { test, expect, devices } from '@playwright/test';
import { AuthPage } from '../page-objects/AuthPage';
import { createTestUserForDevice } from '../fixtures/test-users';

test.use({ ...devices['iPhone 12'] });

test.describe('Mobile Authentication', () => {
  test('authentication works on mobile viewport', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    const testUser = createTestUserForDevice('mobile');
    await authPage.register(testUser.email, testUser.password);
    await authPage.expectLoggedIn();
    
    // Test mobile-specific behaviors
    await expect(page.getByTestId('mobile-menu')).toBeVisible();
  });

  test('mobile form validation works correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    await authPage.goto();
    
    // Test mobile form behavior
    await authPage.emailInput.focus();
    await page.keyboard.type('invalid-email');
    
    // Test mobile keyboard behavior
    await page.keyboard.press('Tab');
    await expect(authPage.passwordInput).toBeFocused();
    
    // Test mobile validation
    await authPage.loginButton.click();
    await expect(page.getByText(/invalid.*email|email.*format/i)).toBeVisible();
  });

  test('mobile touch interactions work correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    await authPage.goto();
    
    // Test touch interactions
    await authPage.emailInput.tap();
    await page.keyboard.type('test@example.com');
    
    await authPage.passwordInput.tap();
    await page.keyboard.type('password123');
    
    // Test touch on button
    await authPage.loginButton.tap();
    
    // Should attempt login
    await expect(page).toHaveURL(/dashboard|welcome|auth/i);
  });

  test('mobile responsive design works correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    await authPage.goto();
    
    // Check if mobile-specific elements are visible
    const isMobileLayout = await page.evaluate(() => {
      return window.innerWidth <= 768; // Mobile breakpoint
    });
    
    if (isMobileLayout) {
      // Mobile-specific elements should be visible
      await expect(page.getByTestId('mobile-menu')).toBeVisible();
      
      // Form should be mobile-optimized
      await expect(authPage.emailInput).toBeVisible();
      await expect(authPage.passwordInput).toBeVisible();
      await expect(authPage.loginButton).toBeVisible();
    }
  });

  test('mobile session management works correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    // Test mobile authentication
    const testUser = createTestUserForDevice('mobile');
    await authPage.register(testUser.email, testUser.password);
    await authPage.expectLoggedIn();
    
    // Test mobile session persistence
    await page.reload();
    await authPage.expectLoggedIn();
    
    // Test mobile logout
    await authPage.logout();
    await authPage.expectLoggedOut();
  });

  test('mobile error handling works correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    await authPage.goto();
    
    // Test mobile error scenarios
    await authPage.login('nonexistent@example.com', 'wrongpassword');
    await authPage.expectError(/invalid.*credentials|login.*failed|incorrect/i);
    
    // Test mobile network error handling
    await page.route('**/auth/**', route => route.abort('failed'));
    await authPage.login('test@example.com', 'password123');
    await expect(page.getByText(/network.*error|connection.*failed|try.*again/i)).toBeVisible();
  });

  test('mobile performance is acceptable', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    // Measure mobile authentication performance
    const startTime = Date.now();
    const testUser = createTestUserForDevice('mobile');
    await authPage.register(testUser.email, testUser.password);
    const registrationTime = Date.now() - startTime;
    
    console.log(`Mobile registration time: ${registrationTime}ms`);
    
    // Mobile registration should complete within reasonable time
    expect(registrationTime).toBeLessThan(15000); // 15 seconds for mobile
    
    // Test mobile login performance
    await authPage.logout();
    
    const loginStartTime = Date.now();
    await authPage.login(testUser.email, testUser.password);
    const loginTime = Date.now() - loginStartTime;
    
    console.log(`Mobile login time: ${loginTime}ms`);
    
    // Mobile login should complete within reasonable time
    expect(loginTime).toBeLessThan(8000); // 8 seconds for mobile
  });

  test('mobile accessibility works correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    await authPage.goto();
    
    // Test mobile accessibility features
    await authPage.emailInput.focus();
    
    // Test mobile screen reader support
    const emailLabel = await authPage.emailInput.getAttribute('aria-label');
    expect(emailLabel).toBeTruthy();
    
    // Test mobile keyboard navigation
    await page.keyboard.press('Tab');
    await expect(authPage.passwordInput).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(authPage.loginButton).toBeFocused();
    
    // Test mobile form submission with keyboard
    await page.keyboard.press('Enter');
    
    // Should attempt login
    await expect(page).toHaveURL(/dashboard|welcome|auth/i);
  });

  test('mobile concurrent operations work correctly', async ({ page, context }) => {
    const authPage = new AuthPage(page);
    
    // Test mobile concurrent operations
    const testUser = createTestUserForDevice('mobile');
    
    // Open multiple mobile tabs
    const tab1 = page;
    const tab2 = await context.newPage();
    
    const authPage1 = new AuthPage(tab1);
    const authPage2 = new AuthPage(tab2);
    
    // Set mobile viewport for second tab
    await tab2.setViewportSize({ width: 375, height: 667 });
    
    // Try to login in both tabs
    await Promise.all([
      authPage1.login(testUser.email, testUser.password),
      authPage2.login(testUser.email, testUser.password)
    ]);
    
    // At least one should succeed
    const successCount = await Promise.all([
      tab1.url().then(url => url.includes('dashboard') || url.includes('welcome')),
      tab2.url().then(url => url.includes('dashboard') || url.includes('welcome'))
    ]).then(results => results.filter(Boolean).length);
    
    expect(successCount).toBeGreaterThan(0);
    
    // Clean up
    await tab2.close();
  });
});
