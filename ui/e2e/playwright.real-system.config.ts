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
    // Real System Authentication Tests
    {
      name: 'chromium-real-system',
      use: { ...devices['Desktop Chrome'] },
      testMatch: '**/real-system-*.spec.ts',
    },
    
    // Real System Feature Tests  
    {
      name: 'firefox-real-system',
      use: { ...devices['Desktop Firefox'] },
      testMatch: '**/real-system-*.spec.ts',
    },
    
    // Real System Cross-browser
    {
      name: 'safari-real-system', 
      use: { ...devices['Desktop Safari'] },
      testMatch: '**/real-system-*.spec.ts',
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
