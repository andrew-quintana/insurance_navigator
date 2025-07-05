import { envConfig } from '../';
import type { EnvConfig } from '../types';

describe('Environment Configuration', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = {
      ...originalEnv,
      ENV_LEVEL: 'test',
      SUPABASE_URL: 'http://127.0.0.1:54321',
      SUPABASE_SERVICE_ROLE_KEY: 'mock.jwt.key',
      TEST_USER_ID: '00000000-0000-4000-a000-000000000000',
      TEST_USER_EMAIL: 'test@example.com',
      TEST_USER_PASSWORD: 'test-password',
      ENABLE_VECTOR_PROCESSING: 'false',
      ENABLE_REGULATORY_PROCESSING: 'false',
      NODE_ENV: 'test'
    };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('should detect Node.js runtime', () => {
    expect(envConfig.runtime).toBe('node');
  });

  it('should load test environment configuration', () => {
    expect(envConfig.deploymentEnv).toBe('test');
    expect(envConfig.supabaseUrl).toBe('http://127.0.0.1:54321');
    expect(envConfig.supabaseKey).toBeTruthy();
    expect(envConfig.supabaseKey).toBe(process.env.SUPABASE_SERVICE_ROLE_KEY);
  });

  it('should include test user credentials in non-production environments', () => {
    expect(envConfig.testUserId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
    expect(envConfig.testUserEmail).toMatch(/^[^@]+@[^@]+\.[^@]+$/);
    expect(envConfig.testUserPassword).toBeTruthy();
  });

  it('should respect feature flags', () => {
    expect(envConfig.enableVectorProcessing).toBe(false);
    expect(envConfig.enableRegulatoryProcessing).toBe(false);
    expect(envConfig.logLevel).toBe('DEBUG');
  });

  describe('Production Environment', () => {
    beforeEach(() => {
      process.env = {
        ...originalEnv,
        ENV_LEVEL: 'production',
        ENABLE_VECTOR_PROCESSING: 'false',
        ENABLE_REGULATORY_PROCESSING: 'false',
        NODE_ENV: 'production'
      };
    });

    it('should disable development features in production', () => {
      const prodConfig = require('../').envConfig as EnvConfig;
      expect(prodConfig.enableVectorProcessing).toBe(false);
      expect(prodConfig.enableRegulatoryProcessing).toBe(false);
      expect(prodConfig.logLevel).toBe('INFO');
    });

    it('should not include test credentials in production', () => {
      const prodConfig = require('../').envConfig as EnvConfig;
      expect(prodConfig.testUserId).toBeUndefined();
      expect(prodConfig.testUserEmail).toBeUndefined();
      expect(prodConfig.testUserPassword).toBeUndefined();
    });
  });
}); 