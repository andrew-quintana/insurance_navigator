# Phase 3: Authentication E2E Testing - Cursor Implementation Prompt

## Context
You are implementing Phase 3 of frontend integration testing. Phases 1-2 should be complete with unit tests and integration tests passing. This phase implements end-to-end testing using Playwright to validate complete authenticated user journeys across browsers.

## Prerequisites
- Phase 1 complete: Authentication unit tests passing
- Phase 2 complete: Authentication integration tests with mock services
- Mock services running reliably
- All authentication flows validated at integration level

## Phase 3 Goals
1. Set up Playwright for cross-browser authentication testing
2. Implement authentication flow as critical user journey #1
3. Test complete authenticated upload → chat flow
4. Validate cross-browser authentication compatibility  
5. Achieve 100% pass rate on critical authenticated user journeys

## Implementation Tasks

### Task 3.1: Authentication Playwright E2E Setup
**Priority**: CRITICAL - Foundation for all E2E testing

**Installation & Configuration**:
```bash
cd ui
npm install --save-dev @playwright/test
npx playwright install
```

**Files to Create**:

1. **`e2e/playwright.config.ts`**:
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    video: 'retain-on-failure',
  },

  projects: [
    // Authentication Foundation Tests (PRIORITY #1)
    {
      name: 'chromium-auth',
      use: { ...devices['Desktop Chrome'] },
      testMatch: '**/auth-*.spec.ts',
    },
    
    // Authenticated Feature Tests  
    {
      name: 'chromium-features',
      use: { ...devices['Desktop Chrome'] },
      testMatch: '**/authenticated-*.spec.ts',
      dependencies: ['chromium-auth'], // Run after auth tests pass
    },
    
    // Cross-browser Authentication
    {
      name: 'firefox-auth',
      use: { ...devices['Desktop Firefox'] },
      testMatch: '**/auth-*.spec.ts',
    },
    
    {
      name: 'safari-auth', 
      use: { ...devices['Desktop Safari'] },
      testMatch: '**/auth-*.spec.ts',
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

2. **Authentication Page Objects** (`e2e/page-objects/`):

**`e2e/page-objects/AuthPage.ts`** (PRIORITY #1):
```typescript
import { Page, Locator, expect } from '@playwright/test';

export class AuthPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly registerButton: Locator;
  readonly errorMessage: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel(/email/i);
    this.passwordInput = page.getByLabel(/password/i);
    this.loginButton = page.getByRole('button', { name: /login|sign in/i });
    this.registerButton = page.getByRole('button', { name: /register|sign up/i });
    this.errorMessage = page.getByRole('alert');
    this.logoutButton = page.getByRole('button', { name: /logout|sign out/i });
  }

  async goto() {
    await this.page.goto('/auth/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  async register(email: string, password: string) {
    await this.page.goto('/auth/register');
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.registerButton.click();
  }

  async logout() {
    await this.logoutButton.click();
  }

  async expectLoggedIn() {
    await expect(this.page.getByText(/welcome|dashboard/i)).toBeVisible();
  }

  async expectLoggedOut() {
    await expect(this.loginButton).toBeVisible();
  }

  async expectError(message: RegExp) {
    await expect(this.errorMessage).toContainText(message);
  }
}
```

### Task 3.2: Authentication Flow E2E Tests (PRIORITY #1)
**Priority**: CRITICAL - Foundation for all other features

**Test File: `e2e/tests/auth-flow.spec.ts`**

```typescript
import { test, expect } from '@playwright/test';
import { AuthPage } from '../page-objects/AuthPage';

test.describe('Authentication Flow (PRIORITY #1)', () => {
  let authPage: AuthPage;

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page);
  });

  test('should register new user with email validation', async ({ page }) => {
    const testEmail = `test-${Date.now()}@example.com`;
    
    await authPage.register(testEmail, 'SecurePassword123!');
    
    // Should redirect to dashboard or email verification
    await expect(page).toHaveURL(/dashboard|verify/);
    await authPage.expectLoggedIn();
  });

  test('should login existing user with valid credentials', async ({ page }) => {
    // First register a user
    const testEmail = `test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'SecurePassword123!');
    await authPage.logout();
    
    // Then login
    await authPage.login(testEmail, 'SecurePassword123!');
    await expect(page).toHaveURL(/dashboard/);
    await authPage.expectLoggedIn();
  });

  test('should reject invalid login credentials', async () => {
    await authPage.goto();
    await authPage.login('nonexistent@example.com', 'wrongpassword');
    
    await authPage.expectError(/invalid.*credentials|login.*failed/i);
    await authPage.expectLoggedOut();
  });

  test('should maintain session across browser refresh', async ({ page }) => {
    // Login
    const testEmail = `test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'SecurePassword123!');
    
    // Refresh page
    await page.reload();
    
    // Should still be logged in
    await authPage.expectLoggedIn();
  });

  test('should redirect unauthenticated users from protected routes', async ({ page }) => {
    await page.goto('/upload');
    
    // Should redirect to login
    await expect(page).toHaveURL(/auth.*login|login/);
    await authPage.expectLoggedOut();
  });

  test('should complete logout and redirect to login', async ({ page }) => {
    // Login first
    const testEmail = `test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'SecurePassword123!');
    
    // Logout
    await authPage.logout();
    
    // Should redirect to login page
    await expect(page).toHaveURL(/auth.*login|login/);
    await authPage.expectLoggedOut();
    
    // Should not be able to access protected routes
    await page.goto('/upload');
    await expect(page).toHaveURL(/auth.*login|login/);
  });
});
```

### Task 3.3: Authenticated Upload → Chat E2E Flow
**Priority**: HIGH - Core user journey with authentication

**Page Objects for Authenticated Features**:

**`e2e/page-objects/UploadPage.ts`**:
```typescript
import { Page, Locator, expect } from '@playwright/test';

export class UploadPage {
  readonly page: Page;
  readonly fileInput: Locator;
  readonly uploadButton: Locator;
  readonly progressBar: Locator;
  readonly successMessage: Locator;
  readonly documentList: Locator;

  constructor(page: Page) {
    this.page = page;
    this.fileInput = page.getByLabel(/upload|file/i);
    this.uploadButton = page.getByRole('button', { name: /upload/i });
    this.progressBar = page.getByRole('progressbar');
    this.successMessage = page.getByText(/upload.*complete|success/i);
    this.documentList = page.getByTestId('document-list');
  }

  async goto() {
    await this.page.goto('/upload');
  }

  async uploadFile(filePath: string) {
    await this.fileInput.setInputFiles(filePath);
    await this.uploadButton.click();
  }

  async waitForUploadComplete() {
    await expect(this.successMessage).toBeVisible({ timeout: 30000 });
  }

  async expectDocumentInList(filename: string) {
    await expect(this.documentList.getByText(filename)).toBeVisible();
  }
}
```

**`e2e/page-objects/ChatPage.ts`**:
```typescript
import { Page, Locator, expect } from '@playwright/test';

export class ChatPage {
  readonly page: Page;
  readonly messageInput: Locator;
  readonly sendButton: Locator;
  readonly chatHistory: Locator;
  readonly lastMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.messageInput = page.getByLabel(/message|chat/i);
    this.sendButton = page.getByRole('button', { name: /send/i });
    this.chatHistory = page.getByTestId('chat-history');
    this.lastMessage = this.chatHistory.locator('.message').last();
  }

  async goto() {
    await this.page.goto('/chat');
  }

  async sendMessage(message: string) {
    await this.messageInput.fill(message);
    await this.sendButton.click();
  }

  async waitForResponse() {
    await expect(this.lastMessage).toBeVisible({ timeout: 10000 });
  }

  async expectMessageInHistory(text: string) {
    await expect(this.chatHistory.getByText(text)).toBeVisible();
  }
}
```

**Test File: `e2e/tests/authenticated-upload-chat.spec.ts`**:
```typescript
import { test, expect } from '@playwright/test';
import { AuthPage } from '../page-objects/AuthPage';
import { UploadPage } from '../page-objects/UploadPage';
import { ChatPage } from '../page-objects/ChatPage';
import path from 'path';

test.describe('Authenticated Upload → Chat Flow', () => {
  let authPage: AuthPage;
  let uploadPage: UploadPage;
  let chatPage: ChatPage;

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page);
    uploadPage = new UploadPage(page);
    chatPage = new ChatPage(page);

    // Authenticate before each test
    const testEmail = `test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'SecurePassword123!');
    await authPage.expectLoggedIn();
  });

  test('should complete full authenticated upload to chat flow', async () => {
    // Upload document
    await uploadPage.goto();
    
    const testFilePath = path.join(__dirname, '../fixtures/sample-policy.pdf');
    await uploadPage.uploadFile(testFilePath);
    await uploadPage.waitForUploadComplete();
    await uploadPage.expectDocumentInList('sample-policy.pdf');

    // Navigate to chat
    await chatPage.goto();
    
    // Ask question about uploaded document
    await chatPage.sendMessage('What is my deductible based on my uploaded policy?');
    await chatPage.waitForResponse();
    
    // Verify response mentions document content
    await chatPage.expectMessageInHistory(/deductible|policy|document/i);
  });

  test('should maintain authentication throughout long operations', async () => {
    // Upload large document
    await uploadPage.goto();
    const largeFilePath = path.join(__dirname, '../fixtures/large-policy.pdf');
    await uploadPage.uploadFile(largeFilePath);
    
    // Should complete without auth errors
    await uploadPage.waitForUploadComplete();
    
    // Should still be able to access chat
    await chatPage.goto();
    await chatPage.sendMessage('Hello');
    await chatPage.waitForResponse();
  });

  test('should handle session expiry gracefully during operations', async ({ page }) => {
    await uploadPage.goto();
    
    // Simulate session expiry (this would need backend support)
    await page.evaluate(() => {
      localStorage.removeItem('supabase.auth.token');
    });
    
    // Attempt upload
    const testFilePath = path.join(__dirname, '../fixtures/sample-policy.pdf');
    await uploadPage.uploadFile(testFilePath);
    
    // Should redirect to login or show auth error
    await expect(page).toHaveURL(/auth.*login|login/);
  });
});
```

### Task 3.4: Cross-Browser Authentication Testing
**Priority**: HIGH - Ensure auth works across browsers

**Test File: `e2e/tests/auth-cross-browser.spec.ts`**:
```typescript
import { test, expect, devices } from '@playwright/test';
import { AuthPage } from '../page-objects/AuthPage';

// This test runs across all configured browsers
test.describe('Cross-Browser Authentication', () => {
  test('authentication flow works in all browsers', async ({ page, browserName }) => {
    const authPage = new AuthPage(page);
    
    console.log(`Testing authentication in ${browserName}`);
    
    // Register and login flow
    const testEmail = `test-${browserName}-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'SecurePassword123!');
    await authPage.expectLoggedIn();
    
    // Test logout
    await authPage.logout();
    await authPage.expectLoggedOut();
    
    // Test login
    await authPage.login(testEmail, 'SecurePassword123!');
    await authPage.expectLoggedIn();
  });

  test('protected routes work across browsers', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    // Without auth, should redirect
    await page.goto('/upload');
    await expect(page).toHaveURL(/auth.*login|login/);
    
    // With auth, should access
    const testEmail = `test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'SecurePassword123!');
    await page.goto('/upload');
    await expect(page).toHaveURL(/upload/);
  });
});
```

### Task 3.5: Mobile Authentication Testing
**Priority**: MEDIUM - Responsive authentication

**Test File: `e2e/tests/auth-mobile.spec.ts`**:
```typescript
import { test, expect, devices } from '@playwright/test';
import { AuthPage } from '../page-objects/AuthPage';

test.use({ ...devices['iPhone 12'] });

test.describe('Mobile Authentication', () => {
  test('authentication works on mobile viewport', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    const testEmail = `mobile-test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'SecurePassword123!');
    await authPage.expectLoggedIn();
    
    // Test mobile-specific behaviors
    await expect(page.getByTestId('mobile-menu')).toBeVisible();
  });
});
```

## Implementation Guidelines

### Authentication Test Data Management
```typescript
// e2e/fixtures/test-users.ts
export const createTestUser = () => ({
  email: `test-${Date.now()}-${Math.random()}@example.com`,
  password: 'SecureTestPassword123!'
});
```

### Session State Management
```typescript
// Helper for maintaining auth state across tests
export const setupAuthenticatedSession = async (page: Page) => {
  const authPage = new AuthPage(page);
  const user = createTestUser();
  await authPage.register(user.email, user.password);
  return user;
};
```

## Success Criteria
- [ ] Authentication flow tests pass 100% across all browsers
- [ ] Upload → chat flow works with authentication
- [ ] Cross-browser authentication compatibility verified
- [ ] Protected route access control working
- [ ] Session persistence and expiry handled correctly
- [ ] Mobile authentication responsive and functional
- [ ] Test execution completes in < 20 minutes
- [ ] No flaky tests (< 2% failure rate)

## File Structure Expected
```
e2e/
├── playwright.config.ts
├── tests/
│   ├── auth-flow.spec.ts
│   ├── authenticated-upload-chat.spec.ts
│   ├── auth-cross-browser.spec.ts
│   └── auth-mobile.spec.ts
├── page-objects/
│   ├── AuthPage.ts
│   ├── UploadPage.ts
│   └── ChatPage.ts
├── fixtures/
│   ├── sample-policy.pdf
│   ├── large-policy.pdf
│   └── test-users.ts
└── utils/
    └── auth-helpers.ts
```

## Next Phase
After Phase 3 completion, you'll move to Phase 4: Authentication Performance Testing with load testing and performance metrics collection.

Start with Task 3.1 (Playwright setup) and focus on getting the authentication flow tests working first - they're the foundation for all other E2E tests.