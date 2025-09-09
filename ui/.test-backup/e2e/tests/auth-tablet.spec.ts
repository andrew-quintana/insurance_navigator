import { test, expect, devices } from '@playwright/test';
import { AuthPage } from '../page-objects/AuthPage';
import { createTestUserForDevice } from '../fixtures/test-users';

test.use({ ...devices['iPad (gen 7)'] });

test.describe('Tablet Authentication', () => {
  test('authentication works on tablet viewport', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    const testUser = createTestUserForDevice('tablet');
    await authPage.register(testUser.email, testUser.password);
    await authPage.expectLoggedIn();
    
    // Test tablet-specific behaviors
    await expect(page.getByTestId('tablet-menu')).toBeVisible();
  });

  test('tablet form validation works correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    await authPage.goto();
    
    // Test tablet form behavior
    await authPage.emailInput.focus();
    await page.keyboard.type('invalid-email');
    
    // Test tablet keyboard behavior
    await page.keyboard.press('Tab');
    await expect(authPage.passwordInput).toBeFocused();
    
    // Test tablet validation
    await authPage.loginButton.click();
    await expect(page.getByText(/invalid.*email|email.*format/i)).toBeVisible();
  });

  test('tablet touch and cursor interactions work correctly', async ({ page }) => {
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

  test('tablet responsive design works correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    await authPage.goto();
    
    // Check if tablet-specific elements are visible
    const isTabletLayout = await page.evaluate(() => {
      return window.innerWidth > 768 && window.innerWidth <= 1024; // Tablet breakpoint
    });
    
    if (isTabletLayout) {
      // Tablet-specific elements should be visible
      await expect(page.getByTestId('tablet-menu')).toBeVisible();
      
      // Form should be tablet-optimized
      await expect(authPage.emailInput).toBeVisible();
      await expect(authPage.passwordInput).toBeVisible();
      await expect(authPage.loginButton).toBeVisible();
    }
  });

  test('tablet session management works correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    // Test tablet authentication
    const testUser = createTestUserForDevice('tablet');
    await authPage.register(testUser.email, testUser.password);
    await authPage.expectLoggedIn();
    
    // Test tablet session persistence
    await page.reload();
    await authPage.expectLoggedIn();
    
    // Test tablet logout
    await authPage.logout();
    await authPage.expectLoggedOut();
  });

  test('tablet error handling works correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    await authPage.goto();
    
    // Test tablet error scenarios
    await authPage.login('nonexistent@example.com', 'wrongpassword');
    await authPage.expectError(/invalid.*credentials|login.*failed|incorrect/i);
    
    // Test tablet network error handling
    await page.route('**/auth/**', route => route.abort('failed'));
    await authPage.login('test@example.com', 'password123');
    await expect(page.getByText(/network.*error|connection.*failed|try.*again/i)).toBeVisible();
  });

  test('tablet performance is acceptable', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    // Measure tablet authentication performance
    const startTime = Date.now();
    const testUser = createTestUserForDevice('tablet');
    await authPage.register(testUser.email, testUser.password);
    const registrationTime = Date.now() - startTime;
    
    console.log(`Tablet registration time: ${registrationTime}ms`);
    
    // Tablet registration should complete within reasonable time
    expect(registrationTime).toBeLessThan(12000); // 12 seconds for tablet
    
    // Test tablet login performance
    await authPage.logout();
    
    const loginStartTime = Date.now();
    await authPage.login(testUser.email, testUser.password);
    const loginTime = Date.now() - loginStartTime;
    
    console.log(`Tablet login time: ${loginTime}ms`);
    
    // Tablet login should complete within reasonable time
    expect(loginTime).toBeLessThan(6000); // 6 seconds for tablet
  });

  test('tablet accessibility works correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    await authPage.goto();
    
    // Test tablet accessibility features
    await authPage.emailInput.focus();
    
    // Test tablet screen reader support
    const emailLabel = await authPage.emailInput.getAttribute('aria-label');
    expect(emailLabel).toBeTruthy();
    
    // Test tablet keyboard navigation
    await page.keyboard.press('Tab');
    await expect(authPage.passwordInput).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(authPage.loginButton).toBeFocused();
    
    // Test tablet form submission with keyboard
    await page.keyboard.press('Enter');
    
    // Should attempt login
    await expect(page).toHaveURL(/dashboard|welcome|auth/i);
  });

  test('tablet concurrent operations work correctly', async ({ page, context }) => {
    const authPage = new AuthPage(page);
    
    // Test tablet concurrent operations
    const testUser = createTestUserForDevice('tablet');
    
    // Open multiple tablet tabs
    const tab1 = page;
    const tab2 = await context.newPage();
    
    const authPage1 = new AuthPage(tab1);
    const authPage2 = new AuthPage(tab2);
    
    // Set tablet viewport for second tab
    await tab2.setViewportSize({ width: 768, height: 1024 });
    
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

  test('tablet orientation changes work correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    await authPage.goto();
    
    // Test landscape orientation
    await page.setViewportSize({ width: 1024, height: 768 });
    
    // Form should still be functional
    await expect(authPage.emailInput).toBeVisible();
    await expect(authPage.passwordInput).toBeVisible();
    await expect(authPage.loginButton).toBeVisible();
    
    // Test portrait orientation
    await page.setViewportSize({ width: 768, height: 1024 });
    
    // Form should still be functional
    await expect(authPage.emailInput).toBeVisible();
    await expect(authPage.passwordInput).toBeVisible();
    await expect(authPage.loginButton).toBeVisible();
  });

  test('tablet hybrid input methods work correctly', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    await authPage.goto();
    
    // Test hybrid touch/cursor input
    await authPage.emailInput.tap();
    await page.keyboard.type('test@example.com');
    
    // Test cursor navigation
    await page.mouse.click(100, 200); // Click somewhere else
    await authPage.passwordInput.focus();
    await page.keyboard.type('password123');
    
    // Test hybrid submission
    await authPage.loginButton.click();
    
    // Should attempt login
    await expect(page).toHaveURL(/dashboard|welcome|auth/i);
  });
});
