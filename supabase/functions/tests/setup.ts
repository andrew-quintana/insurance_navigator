import { resolve } from 'path';

// Get project root directory (3 levels up from this file)
const projectRoot = resolve(__dirname, '..', '..', '..');

// Generate a random JWT secret if needed
function generateRandomSecret(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode(...array));
}

// Set default values for required environment variables
const requiredEnvVars = {
  'ENV_LEVEL': 'test',
  'SUPABASE_URL': 'http://127.0.0.1:54321',  // API endpoint
  'SUPABASE_SERVICE_ROLE_KEY': 'mock.jwt.key', // Simple mock value for testing
  'OPENAI_API_KEY': 'sk-mock-key-for-testing',
  'LLAMAPARSE_API_KEY': 'mock-key-for-testing',
  'ANTHROPIC_API_KEY': 'mock-key-for-testing',
  'ENABLE_VECTOR_PROCESSING': 'false',
  'ENABLE_REGULATORY_PROCESSING': 'false',
  'TEST_MODE': 'true',
  'MOCK_EXTERNAL_SERVICES': 'true',
  'NODE_ENV': 'test',
  'LANGCHAIN_CALLBACKS_BACKGROUND': 'true',
  'TEST_USER_ID': '00000000-0000-4000-a000-000000000000', // Valid UUID format for testing
  'TEST_USER_EMAIL': 'test@example.com',
  'TEST_USER_PASSWORD': 'test-password',
  // Add JWT secret if not already set
  'SUPABASE_JWT_SECRET': process.env.SUPABASE_JWT_SECRET || process.env.JWT_SECRET || generateRandomSecret(),
  // Database connection (only if needed)
  'SUPABASE_DB_HOST': '127.0.0.1',
  'SUPABASE_DB_PORT': '54322',
  'SUPABASE_DB_NAME': 'postgres',
  'SUPABASE_DB_USER': 'postgres',
  'SUPABASE_DB_PASSWORD': 'postgres',
  'SUPABASE_DB_URL': 'postgresql://postgres:postgres@127.0.0.1:54322/postgres'
};

// Set environment variables if not already set
Object.entries(requiredEnvVars).forEach(([key, value]) => {
  if (!process.env[key]) {
    process.env[key] = value;
  }
});

// Ensure JWT_SECRET is synchronized with SUPABASE_JWT_SECRET
if (!process.env.JWT_SECRET) {
  process.env.JWT_SECRET = process.env.SUPABASE_JWT_SECRET;
}

// Import environment configuration after setting variables
const { syncEnvironments } = require('../../../scripts/sync-environments');
const { getEnvConfig } = require('../../../config/environment');

export default async function setupTestEnvironment(): Promise<void> {
  try {
    // Sync test environment files
    await syncEnvironments('test');

    // Get environment config
    const envConfig = getEnvConfig();

    // Log test configuration (excluding sensitive data)
    const sanitizedConfig = {
      ...envConfig,
      testUserPassword: '[REDACTED]',
      supabaseKey: '[REDACTED]',
      openaiApiKey: '[REDACTED]',
      llamaparseApiKey: '[REDACTED]'
    };

    // Return config for test use
    return sanitizedConfig;
  } catch (error) {
    console.error('Error setting up test environment:', error);
    throw error;
  }
}

// Run setup if this file is run directly
if (require.main === module) {
  setupTestEnvironment().catch(error => {
    console.error('Setup failed:', error);
    process.exit(1);
  });
} 