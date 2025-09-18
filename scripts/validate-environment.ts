#!/usr/bin/env node

/**
 * Environment Configuration Validation Script
 * 
 * This script validates environment configuration for both development
 * and production environments, ensuring all required variables are set
 * and configuration is valid.
 */

import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { getEnvironmentConfig, validateEnvironmentConfig, detectEnvironment } from '../config/environments';

// Load environment variables from .env files
function loadEnvFile(filePath: string) {
  if (existsSync(filePath)) {
    const content = readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        const value = valueParts.join('=');
        if (key && value) {
          process.env[key.trim()] = value.trim();
        }
      }
    }
  }
}

interface ValidationOptions {
  environment?: 'development' | 'production';
  strict?: boolean;
  verbose?: boolean;
}

class EnvironmentValidator {
  private options: ValidationOptions;
  private errors: string[] = [];
  private warnings: string[] = [];

  constructor(options: ValidationOptions = {}) {
    this.options = {
      environment: options.environment || detectEnvironment(),
      strict: options.strict || false,
      verbose: options.verbose || false
    };

    // Load environment variables based on target environment
    const envFile = this.options.environment === 'production' ? '.env.production' : '.env.development';
    loadEnvFile(envFile);

    // Debug: Check if environment variables are loaded
    if (this.options.verbose) {
      console.log('Debug - Environment variables loaded in validator:');
      console.log('DATABASE_URL:', process.env.DATABASE_URL ? 'SET' : 'NOT SET');
      console.log('OPENAI_API_KEY:', process.env.OPENAI_API_KEY ? 'SET' : 'NOT SET');
      console.log('JWT_SECRET:', process.env.JWT_SECRET ? 'SET' : 'NOT SET');
    }
  }

  /**
   * Validates environment configuration
   */
  async validate(): Promise<boolean> {
    console.log(`🔍 Validating ${this.options.environment} environment configuration...\n`);

    try {
      // Load and validate configuration
      const config = getEnvironmentConfig();
      const validation = validateEnvironmentConfig(config);

      this.errors = validation.errors;
      this.warnings = validation.warnings;

      // Additional validations
      await this.validateEnvironmentFiles();
      await this.validateRequiredSecrets();
      await this.validateDatabaseConnection();
      await this.validateExternalApis();

      // Print results
      this.printResults();

      return this.errors.length === 0;
    } catch (error) {
      console.error('❌ Validation failed with error:', error);
      return false;
    }
  }

  /**
   * Validates that required environment files exist
   */
  private async validateEnvironmentFiles(): Promise<void> {
    const envFiles = [
      '.env.development',
      '.env.production',
      'config/environments/development.ts',
      'config/environments/production.ts',
      'config/environments/index.ts',
      'config/environments/types.ts'
    ];

    for (const file of envFiles) {
      if (!existsSync(file)) {
        this.errors.push(`Required file missing: ${file}`);
      }
    }
  }

  /**
   * Validates that required secrets are present
   */
  private async validateRequiredSecrets(): Promise<void> {
    const requiredSecrets = [
      'SUPABASE_URL',
      'SUPABASE_ANON_KEY',
      'SUPABASE_SERVICE_ROLE_KEY',
      'DATABASE_URL'
    ];

    const optionalSecrets = [
      'OPENAI_API_KEY',
      'ANTHROPIC_API_KEY',
      'LLAMAPARSE_API_KEY',
      'RESEND_API_KEY',
      'JWT_SECRET_KEY',
      'ENCRYPTION_KEY'
    ];

    // Check required secrets
    for (const secret of requiredSecrets) {
      if (!process.env[secret]) {
        this.errors.push(`Required environment variable missing: ${secret}`);
      }
    }

    // Check optional secrets with warnings
    for (const secret of optionalSecrets) {
      if (!process.env[secret]) {
        this.warnings.push(`Optional environment variable not set: ${secret}`);
      }
    }

    // Production-specific validations
    if (this.options.environment === 'production') {
      const productionSecrets = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'LLAMAPARSE_API_KEY',
        'RESEND_API_KEY',
        'JWT_SECRET_KEY',
        'ENCRYPTION_KEY'
      ];

      for (const secret of productionSecrets) {
        if (!process.env[secret]) {
          this.errors.push(`Production environment variable missing: ${secret}`);
        }
      }

      // Check for development secrets in production
      const devSecrets = [
        'dev-jwt-secret-not-for-production',
        'dev-encryption-key-not-for-production'
      ];

      for (const secret of devSecrets) {
        if (process.env.JWT_SECRET_KEY === secret || process.env.ENCRYPTION_KEY === secret) {
          this.errors.push(`Development secret detected in production: ${secret}`);
        }
      }
    }
  }

  /**
   * Validates database connection configuration
   */
  private async validateDatabaseConnection(): Promise<void> {
    const dbUrl = process.env.DATABASE_URL;
    
    if (!dbUrl) {
      this.errors.push('DATABASE_URL is not set');
      return;
    }

    // Basic URL format validation
    try {
      const url = new URL(dbUrl);
      if (url.protocol !== 'postgresql:') {
        this.errors.push('DATABASE_URL must use postgresql:// protocol');
      }
    } catch (error) {
      this.errors.push('DATABASE_URL is not a valid URL');
    }

    // Check for localhost in production
    if (this.options.environment === 'production' && dbUrl.includes('localhost')) {
      this.warnings.push('DATABASE_URL contains localhost - ensure this is correct for production');
    }
  }

  /**
   * Validates external API configurations
   */
  private async validateExternalApis(): Promise<void> {
    const apis = [
      { key: 'OPENAI_API_KEY', name: 'OpenAI' },
      { key: 'ANTHROPIC_API_KEY', name: 'Anthropic' },
      { key: 'LLAMAPARSE_API_KEY', name: 'LlamaCloud' },
      { key: 'RESEND_API_KEY', name: 'Resend' }
    ];

    for (const api of apis) {
      const value = process.env[api.key];
      
      if (value) {
        // Basic format validation
        if (api.key.includes('OPENAI') && !value.startsWith('sk-')) {
          this.warnings.push(`${api.name} API key format may be incorrect (should start with 'sk-')`);
        }
        
        if (api.key.includes('ANTHROPIC') && !value.startsWith('sk-ant-')) {
          this.warnings.push(`${api.name} API key format may be incorrect (should start with 'sk-ant-')`);
        }
        
        if (api.key.includes('LLAMAPARSE') && !value.startsWith('llx-')) {
          this.warnings.push(`${api.name} API key format may be incorrect (should start with 'llx-')`);
        }
      }
    }
  }

  /**
   * Prints validation results
   */
  private printResults(): void {
    console.log('📋 Validation Results:\n');

    if (this.errors.length === 0) {
      console.log('✅ Environment configuration is valid!');
    } else {
      console.log('❌ Environment configuration has errors:');
      this.errors.forEach(error => console.log(`  • ${error}`));
    }

    if (this.warnings.length > 0) {
      console.log('\n⚠️  Warnings:');
      this.warnings.forEach(warning => console.log(`  • ${warning}`));
    }

    console.log(`\n📊 Summary: ${this.errors.length} errors, ${this.warnings.length} warnings`);

    if (this.options.verbose) {
      console.log('\n🔧 Environment Details:');
      console.log(`  Environment: ${this.options.environment}`);
      console.log(`  Node Environment: ${process.env.NODE_ENV || 'not set'}`);
      console.log(`  Strict Mode: ${this.options.strict ? 'enabled' : 'disabled'}`);
    }
  }
}

/**
 * Main execution function
 */
async function main() {
  const args = process.argv.slice(2);
  const options: ValidationOptions = {};

  // Parse command line arguments
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--environment':
      case '-e':
        options.environment = args[++i] as 'development' | 'production';
        break;
      case '--strict':
      case '-s':
        options.strict = true;
        break;
      case '--verbose':
      case '-v':
        options.verbose = true;
        break;
      case '--help':
      case '-h':
        console.log(`
Environment Configuration Validator

Usage: npm run validate:environment [options]

Options:
  -e, --environment <env>  Target environment (development|production)
  -s, --strict            Enable strict validation mode
  -v, --verbose           Enable verbose output
  -h, --help              Show this help message

Examples:
  npm run validate:environment
  npm run validate:environment -- --environment production --strict
  npm run validate:environment -- --verbose
        `);
        process.exit(0);
        break;
    }
  }

  // Debug: Check if environment variables are loaded
  if (options.verbose) {
    console.log('Debug - Environment variables will be loaded by validator');
  }

  const validator = new EnvironmentValidator(options);
  const isValid = await validator.validate();

  process.exit(isValid ? 0 : 1);
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Validation script failed:', error);
    process.exit(1);
  });
}

export { EnvironmentValidator };
