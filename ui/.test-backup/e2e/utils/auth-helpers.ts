import { Page } from '@playwright/test';

export interface TestUser {
  email: string;
  password: string;
}

export const createTestUser = (): TestUser => ({
  email: `test-${Date.now()}-${Math.random().toString(36).substring(2, 8)}@example.com`,
  password: 'SecureTestPassword123!'
});

export const createTestUserWithPrefix = (prefix: string): TestUser => ({
  email: `${prefix}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}@example.com`,
  password: 'SecureTestPassword123!'
});

export const setupAuthenticatedSession = async (page: Page, user?: TestUser): Promise<TestUser> => {
  const testUser = user || createTestUser();
  
  // Navigate to registration page
  await page.goto('/auth/register');
  
  // Fill registration form
  await page.getByLabel(/email/i).fill(testUser.email);
  await page.getByLabel(/password/i).fill(testUser.password);
  await page.getByRole('button', { name: /register|sign up/i }).click();
  
  // Wait for successful registration (redirect to dashboard or verification)
  await page.waitForURL(/dashboard|verify|welcome/i, { timeout: 10000 });
  
  return testUser;
};

export const loginUser = async (page: Page, user: TestUser): Promise<void> => {
  // Navigate to login page
  await page.goto('/auth/login');
  
  // Fill login form
  await page.getByLabel(/email/i).fill(user.email);
  await page.getByLabel(/password/i).fill(user.password);
  await page.getByRole('button', { name: /login|sign in/i }).click();
  
  // Wait for successful login
  await page.waitForURL(/dashboard|welcome/i, { timeout: 10000 });
};

export const logoutUser = async (page: Page): Promise<void> => {
  // Find and click logout button
  const logoutButton = page.getByRole('button', { name: /logout|sign out/i });
  if (await logoutButton.isVisible()) {
    await logoutButton.click();
    
    // Wait for redirect to login page
    await page.waitForURL(/auth.*login|login/i, { timeout: 10000 });
  }
};

export const clearAuthState = async (page: Page): Promise<void> => {
  // Clear localStorage and sessionStorage
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  
  // Clear cookies
  const context = page.context();
  await context.clearCookies();
};

export const isAuthenticated = async (page: Page): Promise<boolean> => {
  try {
    // Check if we're on a protected page or if auth elements are visible
    const currentUrl = page.url();
    
    if (currentUrl.includes('/auth/login') || currentUrl.includes('/auth/register')) {
      return false;
    }
    
    // Check for authenticated user indicators
    const welcomeText = page.getByText(/welcome|dashboard/i);
    const logoutButton = page.getByRole('button', { name: /logout|sign out/i });
    
    return await welcomeText.isVisible() || await logoutButton.isVisible();
  } catch {
    return false;
  }
};
