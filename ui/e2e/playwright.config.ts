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
    screenshot: 'only-on-failure',
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

    // Mobile Authentication Testing
    {
      name: 'mobile-auth',
      use: { ...devices['iPhone 12'] },
      testMatch: '**/auth-mobile.spec.ts',
    },

    // Tablet Authentication Testing
    {
      name: 'tablet-auth',
      use: { ...devices['iPad (gen 7)'] },
      testMatch: '**/auth-tablet.spec.ts',
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000, // 2 minutes timeout for dev server startup
  },

  // Global test timeout
  timeout: 60000, // 1 minute per test

  // Expect timeout for assertions
  expect: {
    timeout: 10000, // 10 seconds for expect operations
  },

  // Global setup and teardown
  globalSetup: require.resolve('./utils/global-setup'),
  globalTeardown: require.resolve('./utils/global-teardown'),
});
