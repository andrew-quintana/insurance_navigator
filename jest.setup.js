// Jest setup file for environment configuration tests

// Mock console methods to avoid cluttering test output
global.console = {
  ...console,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  info: jest.fn(),
  debug: jest.fn()
};

// Set default environment variables for tests
process.env.NODE_ENV = 'test';
process.env.ENV_LEVEL = 'test';

// Mock environment variables for testing
process.env.SUPABASE_URL = 'https://test.supabase.co';
process.env.SUPABASE_ANON_KEY = 'test-anon-key';
process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
process.env.DATABASE_URL = 'postgresql://test:test@localhost:5432/test';
process.env.OPENAI_API_KEY = 'sk-test-key';
process.env.ANTHROPIC_API_KEY = 'sk-ant-test-key';
process.env.LLAMAPARSE_API_KEY = '${LLAMAPARSE_API_KEY}';
process.env.RESEND_API_KEY = 're-test-key';
process.env.JWT_SECRET_KEY = 'test-jwt-secret-32-chars-minimum';
process.env.ENCRYPTION_KEY = 'test-encryption-key-32-chars-minimum';
