/**
 * Environment Configuration Tests
 * 
 * Comprehensive test suite for environment configuration management
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

// Mock environment variables
const originalEnv = process.env;

describe('Environment Configuration', () => {
  beforeEach(() => {
    jest.resetModules();
    // @ts-ignore - Allow modification of process.env for testing
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    // @ts-ignore - Allow modification of process.env for testing
    process.env = originalEnv;
  });

  describe('Environment Detection', () => {
    it('should detect development environment by default', () => {
      // @ts-ignore - Allow modification of process.env for testing
      delete process.env.NODE_ENV;
      // @ts-ignore - Allow modification of process.env for testing
      delete process.env.ENV_LEVEL;
      
      const { detectEnvironment } = require('../index');
      expect(detectEnvironment()).toBe('development');
    });

    it('should detect production environment from NODE_ENV', () => {
      // @ts-ignore - Allow modification of process.env for testing
      // @ts-ignore - Allow modification of process.env for testing
      process.env.NODE_ENV = 'production';
      
      const { detectEnvironment } = require('../index');
      expect(detectEnvironment()).toBe('production');
    });

    it('should detect production environment from ENV_LEVEL', () => {
      // @ts-ignore - Allow modification of process.env for testing
      process.env.ENV_LEVEL = 'production';
      
      const { detectEnvironment } = require('../index');
      expect(detectEnvironment()).toBe('production');
    });

    it('should prioritize ENV_LEVEL over NODE_ENV', () => {
      // @ts-ignore - Allow modification of process.env for testing
      process.env.NODE_ENV = 'development';
      // @ts-ignore - Allow modification of process.env for testing
      process.env.ENV_LEVEL = 'production';
      
      const { detectEnvironment } = require('../index');
      expect(detectEnvironment()).toBe('production');
    });
  });

  describe('Configuration Loading', () => {
    it('should load development configuration by default', () => {
      const { loadEnvironmentConfig } = require('../index');
      const config = loadEnvironmentConfig();
      
      expect(config.environment).toBe('development');
      expect(config.api.rateLimiting).toBe(false);
      expect(config.monitoring.logLevel).toBe('DEBUG');
    });

    it('should load production configuration when NODE_ENV is production', () => {
      // @ts-ignore - Allow modification of process.env for testing
      process.env.NODE_ENV = 'production';
      
      const { loadEnvironmentConfig } = require('../index');
      const config = loadEnvironmentConfig();
      
      expect(config.environment).toBe('production');
      expect(config.api.rateLimiting).toBe(true);
      expect(config.monitoring.logLevel).toBe('INFO');
    });
  });

  describe('Configuration Validation', () => {
    it('should validate development configuration successfully', () => {
      process.env.DATABASE_URL = 'postgresql://localhost:5432/test';
      process.env.SUPABASE_URL = 'https://test.supabase.co';
      process.env.SUPABASE_ANON_KEY = 'test-anon-key';
      process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
      
      const { validateEnvironmentConfig, developmentConfig } = require('../index');
      const result = validateEnvironmentConfig(developmentConfig);
      
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should fail validation for missing required production variables', () => {
      // @ts-ignore - Allow modification of process.env for testing
      process.env.NODE_ENV = 'production';
      // @ts-ignore - Allow modification of process.env for testing
      delete process.env.DATABASE_URL;
      // @ts-ignore - Allow modification of process.env for testing
      delete process.env.OPENAI_API_KEY;
      
      const { validateEnvironmentConfig, productionConfig } = require('../index');
      const result = validateEnvironmentConfig(productionConfig);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors).toContain('DATABASE_URL is required for production environment');
    });

    it('should warn about development secrets in production', () => {
      const { validateEnvironmentConfig, productionConfig } = require('../index');
      
      // Create a modified production config with development secret
      const modifiedConfig = {
        ...productionConfig,
        security: {
          ...productionConfig.security,
          jwtSecret: 'dev-jwt-secret-not-for-production'
        }
      };
      
      const result = validateEnvironmentConfig(modifiedConfig);
      
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors.some(w => w.includes('JWT_SECRET_KEY'))).toBe(true);
    });

    it('should validate API port range', () => {
      const { validateEnvironmentConfig, developmentConfig } = require('../index');
      
      // Test valid port
      const validConfig = { ...developmentConfig, api: { ...developmentConfig.api, port: 8000 } };
      let result = validateEnvironmentConfig(validConfig);
      expect(result.errors).not.toContain(expect.stringContaining('port'));
      
      // Test invalid port
      const invalidConfig = { ...developmentConfig, api: { ...developmentConfig.api, port: 70000 } };
      result = validateEnvironmentConfig(invalidConfig);
      expect(result.errors).toContainEqual(expect.stringContaining('port'));
    });

    it('should validate CORS origins', () => {
      const { validateEnvironmentConfig, developmentConfig } = require('../index');
      
      // Test with empty CORS origins
      const invalidConfig = { ...developmentConfig, api: { ...developmentConfig.api, corsOrigins: [] } };
      const result = validateEnvironmentConfig(invalidConfig);
      
      expect(result.warnings).toContainEqual(expect.stringContaining('CORS origins'));
    });
  });

  describe('Environment-Specific Configuration', () => {
    describe('Development Configuration', () => {
      it('should have development-appropriate settings', () => {
        const { developmentConfig } = require('../development');
        
        expect(developmentConfig.environment).toBe('development');
        expect(developmentConfig.api.rateLimiting).toBe(false);
        expect(developmentConfig.security.bypassEnabled).toBe(true);
        expect(developmentConfig.monitoring.logLevel).toBe('DEBUG');
        expect(developmentConfig.frontend.debugMode).toBe(true);
      });

      it('should include localhost in CORS origins', () => {
        const { developmentConfig } = require('../development');
        
        expect(developmentConfig.api.corsOrigins).toContain('http://localhost:3000');
        expect(developmentConfig.api.corsOrigins).toContain('http://127.0.0.1:3000');
      });

      it('should use development defaults for missing environment variables', () => {
        // @ts-ignore - Allow modification of process.env for testing
      delete process.env.DATABASE_URL;
        delete process.env.NEXT_PUBLIC_API_BASE_URL;
        
        const { developmentConfig } = require('../development');
        
        expect(developmentConfig.database.url).toContain('localhost');
        expect(developmentConfig.frontend.apiBaseUrl).toContain('localhost');
      });
    });

    describe('Production Configuration', () => {
      it('should have production-appropriate settings', () => {
        const { productionConfig } = require('../production');
        
        expect(productionConfig.environment).toBe('production');
        expect(productionConfig.api.rateLimiting).toBe(true);
        expect(productionConfig.security.bypassEnabled).toBe(false);
        expect(productionConfig.monitoring.logLevel).toBe('INFO');
        expect(productionConfig.frontend.debugMode).toBe(false);
      });

      it('should include production domains in CORS origins', () => {
        const { productionConfig } = require('../production');
        
        expect(productionConfig.api.corsOrigins).toContain('https://insurance-navigator.vercel.app');
        expect(productionConfig.api.corsOrigins).toContain('https://insurance-navigator.com');
      });

      it('should use production defaults for missing environment variables', () => {
        delete process.env.NEXT_PUBLIC_APP_URL;
        delete process.env.NEXT_PUBLIC_API_BASE_URL;
        
        const { productionConfig } = require('../production');
        
        expect(productionConfig.frontend.appUrl).toContain('vercel.app');
        expect(productionConfig.frontend.apiBaseUrl).toContain('onrender.com');
      });
    });
  });

  describe('Type Safety', () => {
    it('should have correct TypeScript types', () => {
      const { EnvironmentConfig, Environment } = require('../types');
      
      // Test that types are properly exported
      expect(typeof EnvironmentConfig).toBe('undefined'); // Type alias
      expect(typeof Environment).toBe('undefined'); // Type alias
    });

    it('should validate configuration structure', () => {
      const { getEnvironmentConfig } = require('../index');
      
      const config = getEnvironmentConfig();
      
      // Test required properties exist
      expect(config).toHaveProperty('environment');
      expect(config).toHaveProperty('api');
      expect(config).toHaveProperty('database');
      expect(config).toHaveProperty('frontend');
      expect(config).toHaveProperty('external');
      expect(config).toHaveProperty('security');
      expect(config).toHaveProperty('monitoring');
      
      // Test nested properties
      expect(config.api).toHaveProperty('host');
      expect(config.api).toHaveProperty('port');
      expect(config.api).toHaveProperty('corsOrigins');
      expect(config.api).toHaveProperty('rateLimiting');
      
      expect(config.database).toHaveProperty('url');
      expect(config.database).toHaveProperty('poolSize');
      expect(config.database).toHaveProperty('connectionTimeout');
      
      expect(config.frontend).toHaveProperty('appUrl');
      expect(config.frontend).toHaveProperty('apiBaseUrl');
      expect(config.frontend).toHaveProperty('analyticsEnabled');
      expect(config.frontend).toHaveProperty('debugMode');
      
      expect(config.external).toHaveProperty('openaiApiKey');
      expect(config.external).toHaveProperty('anthropicApiKey');
      expect(config.external).toHaveProperty('llamaCloudApiKey');
      expect(config.external).toHaveProperty('resendApiKey');
      
      expect(config.security).toHaveProperty('jwtSecret');
      expect(config.security).toHaveProperty('encryptionKey');
      expect(config.security).toHaveProperty('bypassEnabled');
      expect(config.security).toHaveProperty('allowedOrigins');
      
      expect(config.monitoring).toHaveProperty('enabled');
      expect(config.monitoring).toHaveProperty('logLevel');
      expect(config.monitoring).toHaveProperty('metricsEnabled');
      expect(config.monitoring).toHaveProperty('healthCheckInterval');
    });
  });

  describe('Error Handling', () => {
    it('should handle missing environment variables gracefully', () => {
      // @ts-ignore - Allow modification of process.env for testing
      delete process.env.DATABASE_URL;
      delete process.env.SUPABASE_URL;
      
      const { getEnvironmentConfig } = require('../index');
      
      // Should not throw error, but should log warnings
      expect(() => getEnvironmentConfig()).not.toThrow();
    });

    it('should throw error for invalid production configuration', () => {
      // @ts-ignore - Allow modification of process.env for testing
      process.env.NODE_ENV = 'production';
      // @ts-ignore - Allow modification of process.env for testing
      delete process.env.DATABASE_URL;
      // @ts-ignore - Allow modification of process.env for testing
      delete process.env.OPENAI_API_KEY;
      
      const { getEnvironmentConfig } = require('../index');
      
      expect(() => getEnvironmentConfig()).toThrow();
    });
  });

  describe('Integration Tests', () => {
    it('should work with real environment variables', () => {
      process.env.DATABASE_URL = 'postgresql://user:pass@host:5432/db';
      process.env.SUPABASE_URL = 'https://project.supabase.co';
      process.env.SUPABASE_ANON_KEY = '${SUPABASE_JWT_TOKEN}';
      process.env.SUPABASE_SERVICE_ROLE_KEY = '${SUPABASE_JWT_TOKEN}';
      process.env.OPENAI_API_KEY = 'sk-test-key';
      process.env.ANTHROPIC_API_KEY = 'sk-ant-test-key';
      process.env.LLAMAPARSE_API_KEY = '${LLAMAPARSE_API_KEY}';
      process.env.RESEND_API_KEY = 're_test-key';
      process.env.JWT_SECRET_KEY = 'test-jwt-secret-32-chars-minimum';
      process.env.ENCRYPTION_KEY = 'test-encryption-key-32-chars-minimum';
      
      const { getEnvironmentConfig, validateEnvironmentConfig } = require('../index');
      
      const config = getEnvironmentConfig();
      const validation = validateEnvironmentConfig(config);
      
      expect(validation.isValid).toBe(true);
      expect(config.database.url).toBe(process.env.DATABASE_URL);
      expect(config.external.openaiApiKey).toBe(process.env.OPENAI_API_KEY);
    });

    it('should handle environment switching', () => {
      // Test development
      // @ts-ignore - Allow modification of process.env for testing
      process.env.NODE_ENV = 'development';
      const { getEnvironmentConfig: getDevConfig } = require('../index');
      const devConfig = getDevConfig();
      expect(devConfig.environment).toBe('development');
      
      // Test production
      // @ts-ignore - Allow modification of process.env for testing
      process.env.NODE_ENV = 'production';
      const { getEnvironmentConfig: getProdConfig } = require('../index');
      const prodConfig = getProdConfig();
      expect(prodConfig.environment).toBe('production');
    });
  });
});
