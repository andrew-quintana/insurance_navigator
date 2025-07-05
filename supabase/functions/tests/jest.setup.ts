/// <reference types="jest" />

// Enable background callbacks for LangChain
process.env.LANGCHAIN_CALLBACKS_BACKGROUND = 'true';

// Set up bogey environment for testing
process.env.NODE_ENV = 'test';  // Set this first for proper environment detection
process.env.ENV_LEVEL = 'bogey';
process.env.SUPABASE_URL = 'http://bogey.local:54321';
process.env.SUPABASE_SERVICE_ROLE_KEY = 'bogey-key';
process.env.TEST_USER_ID = 'bogey-user';
process.env.TEST_USER_EMAIL = 'bogey@example.com';
process.env.TEST_USER_PASSWORD = 'bogey-password';

import { initializeTestSuite, cleanupTestSuite } from './test-helpers/setup-env';

beforeAll(async () => {
  const { config } = await initializeTestSuite();
  
  // Make config available globally for tests
  (global as any).testConfig = config;
  
  // Increase test timeout for slower operations
  jest.setTimeout(30000);
});

afterAll(async () => {
  await cleanupTestSuite();
}); 