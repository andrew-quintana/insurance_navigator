/**
 * Environment Validation Script Tests
 * 
 * Test suite for the environment validation script
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { EnvironmentValidator } from '../validate-environment';

// Mock console methods
const mockConsole = {
  log: jest.fn(),
  error: jest.fn(),
  warn: jest.fn()
};

// Mock fs methods
const mockFs = {
  existsSync: jest.fn(),
  readFileSync: jest.fn()
};

jest.mock('fs', () => mockFs);
jest.mock('console', () => mockConsole);

describe('EnvironmentValidator', () => {
  let validator: EnvironmentValidator;

  beforeEach(() => {
    jest.clearAllMocks();
    process.env = {};
    mockFs.existsSync.mockReturnValue(true);
    mockFs.readFileSync.mockReturnValue('test content');
  });

  afterEach(() => {
    process.env = {};
  });

  describe('Constructor', () => {
    it('should create validator with default options', () => {
      validator = new EnvironmentValidator();
      expect(validator).toBeDefined();
    });

    it('should create validator with custom options', () => {
      const options = {
        environment: 'production' as const,
        strict: true,
        verbose: true
      };
      validator = new EnvironmentValidator(options);
      expect(validator).toBeDefined();
    });
  });

  describe('Environment File Validation', () => {
    it('should validate required environment files exist', async () => {
      mockFs.existsSync.mockReturnValue(true);
      
      validator = new EnvironmentValidator();
      const result = await validator.validate();
      
      expect(result).toBe(true);
    });

    it('should fail when required files are missing', async () => {
      mockFs.existsSync.mockImplementation((file) => {
        return !file.includes('.env.development');
      });
      
      validator = new EnvironmentValidator();
      const result = await validator.validate();
      
      expect(result).toBe(false);
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('Required file missing')
      );
    });
  });

  describe('Required Secrets Validation', () => {
    it('should pass when all required secrets are present', async () => {
      process.env.SUPABASE_URL = 'https://test.supabase.co';
      process.env.SUPABASE_ANON_KEY = 'test-anon-key';
      process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
      process.env.DATABASE_URL = 'postgresql://localhost:5432/test';
      
      validator = new EnvironmentValidator();
      const result = await validator.validate();
      
      expect(result).toBe(true);
    });

    it('should fail when required secrets are missing', async () => {
      delete process.env.SUPABASE_URL;
      delete process.env.DATABASE_URL;
      
      validator = new EnvironmentValidator();
      const result = await validator.validate();
      
      expect(result).toBe(false);
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('Required environment variable missing')
      );
    });

    it('should warn about missing optional secrets', async () => {
      process.env.SUPABASE_URL = 'https://test.supabase.co';
      process.env.SUPABASE_ANON_KEY = 'test-anon-key';
      process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
      process.env.DATABASE_URL = 'postgresql://localhost:5432/test';
      delete process.env.OPENAI_API_KEY;
      
      validator = new EnvironmentValidator();
      const result = await validator.validate();
      
      expect(result).toBe(true);
      expect(mockConsole.warn).toHaveBeenCalledWith(
        expect.stringContaining('Optional environment variable not set')
      );
    });
  });

  describe('Production Environment Validation', () => {
    it('should require production secrets in production environment', async () => {
      process.env.NODE_ENV = 'production';
      process.env.SUPABASE_URL = 'https://test.supabase.co';
      process.env.SUPABASE_ANON_KEY = 'test-anon-key';
      process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
      process.env.DATABASE_URL = 'postgresql://localhost:5432/test';
      delete process.env.OPENAI_API_KEY;
      
      validator = new EnvironmentValidator({ environment: 'production' });
      const result = await validator.validate();
      
      expect(result).toBe(false);
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('Production environment variable missing')
      );
    });

    it('should detect development secrets in production', async () => {
      process.env.NODE_ENV = 'production';
      process.env.SUPABASE_URL = 'https://test.supabase.co';
      process.env.SUPABASE_ANON_KEY = 'test-anon-key';
      process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
      process.env.DATABASE_URL = 'postgresql://localhost:5432/test';
      process.env.OPENAI_API_KEY = 'sk-test-key';
      process.env.ANTHROPIC_API_KEY = 'sk-ant-test-key';
      process.env.LLAMAPARSE_API_KEY = '${LLAMAPARSE_API_KEY}';
      process.env.RESEND_API_KEY = 're-test-key';
      process.env.JWT_SECRET_KEY = 'dev-jwt-secret-not-for-production';
      
      validator = new EnvironmentValidator({ environment: 'production' });
      const result = await validator.validate();
      
      expect(result).toBe(false);
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('Development secret detected in production')
      );
    });
  });

  describe('Database Connection Validation', () => {
    it('should validate database URL format', async () => {
      process.env.SUPABASE_URL = 'https://test.supabase.co';
      process.env.SUPABASE_ANON_KEY = 'test-anon-key';
      process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
      process.env.DATABASE_URL = 'invalid-url';
      
      validator = new EnvironmentValidator();
      const result = await validator.validate();
      
      expect(result).toBe(false);
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('DATABASE_URL is not a valid URL')
      );
    });

    it('should validate postgresql protocol', async () => {
      process.env.SUPABASE_URL = 'https://test.supabase.co';
      process.env.SUPABASE_ANON_KEY = 'test-anon-key';
      process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
      process.env.DATABASE_URL = 'mysql://user:pass@host:3306/db';
      
      validator = new EnvironmentValidator();
      const result = await validator.validate();
      
      expect(result).toBe(false);
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('DATABASE_URL must use postgresql:// protocol')
      );
    });

    it('should warn about localhost in production', async () => {
      process.env.NODE_ENV = 'production';
      process.env.SUPABASE_URL = 'https://test.supabase.co';
      process.env.SUPABASE_ANON_KEY = 'test-anon-key';
      process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
      process.env.DATABASE_URL = 'postgresql://user:pass@localhost:5432/db';
      process.env.OPENAI_API_KEY = 'sk-test-key';
      process.env.ANTHROPIC_API_KEY = 'sk-ant-test-key';
      process.env.LLAMAPARSE_API_KEY = '${LLAMAPARSE_API_KEY}';
      process.env.RESEND_API_KEY = 're-test-key';
      process.env.JWT_SECRET_KEY = 'test-jwt-secret-32-chars-minimum';
      process.env.ENCRYPTION_KEY = 'test-encryption-key-32-chars-minimum';
      
      validator = new EnvironmentValidator({ environment: 'production' });
      const result = await validator.validate();
      
      expect(result).toBe(true);
      expect(mockConsole.warn).toHaveBeenCalledWith(
        expect.stringContaining('DATABASE_URL contains localhost')
      );
    });
  });

  describe('External API Validation', () => {
    it('should validate OpenAI API key format', async () => {
      process.env.SUPABASE_URL = 'https://test.supabase.co';
      process.env.SUPABASE_ANON_KEY = 'test-anon-key';
      process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
      process.env.DATABASE_URL = 'postgresql://user:pass@host:5432/db';
      process.env.OPENAI_API_KEY = 'invalid-key-format';
      
      validator = new EnvironmentValidator();
      const result = await validator.validate();
      
      expect(result).toBe(true);
      expect(mockConsole.warn).toHaveBeenCalledWith(
        expect.stringContaining('OpenAI API key format may be incorrect')
      );
    });

    it('should validate Anthropic API key format', async () => {
      process.env.SUPABASE_URL = 'https://test.supabase.co';
      process.env.SUPABASE_ANON_KEY = 'test-anon-key';
      process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
      process.env.DATABASE_URL = 'postgresql://user:pass@host:5432/db';
      process.env.ANTHROPIC_API_KEY = 'invalid-key-format';
      
      validator = new EnvironmentValidator();
      const result = await validator.validate();
      
      expect(result).toBe(true);
      expect(mockConsole.warn).toHaveBeenCalledWith(
        expect.stringContaining('Anthropic API key format may be incorrect')
      );
    });

    it('should validate LlamaCloud API key format', async () => {
      process.env.SUPABASE_URL = 'https://test.supabase.co';
      process.env.SUPABASE_ANON_KEY = 'test-anon-key';
      process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
      process.env.DATABASE_URL = 'postgresql://user:pass@host:5432/db';
      process.env.LLAMAPARSE_API_KEY = 'invalid-key-format';
      
      validator = new EnvironmentValidator();
      const result = await validator.validate();
      
      expect(result).toBe(true);
      expect(mockConsole.warn).toHaveBeenCalledWith(
        expect.stringContaining('LlamaCloud API key format may be incorrect')
      );
    });
  });

  describe('Verbose Output', () => {
    it('should provide verbose output when enabled', async () => {
      process.env.SUPABASE_URL = 'https://test.supabase.co';
      process.env.SUPABASE_ANON_KEY = 'test-anon-key';
      process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
      process.env.DATABASE_URL = 'postgresql://user:pass@host:5432/db';
      
      validator = new EnvironmentValidator({ verbose: true });
      const result = await validator.validate();
      
      expect(result).toBe(true);
      expect(mockConsole.log).toHaveBeenCalledWith(
        expect.stringContaining('Environment Details')
      );
    });
  });

  describe('Error Handling', () => {
    it('should handle validation errors gracefully', async () => {
      mockFs.existsSync.mockImplementation(() => {
        throw new Error('File system error');
      });
      
      validator = new EnvironmentValidator();
      const result = await validator.validate();
      
      expect(result).toBe(false);
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('Validation failed with error')
      );
    });
  });
});
