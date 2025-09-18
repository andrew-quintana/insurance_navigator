/**
 * Environment Detection and Loading Logic
 * 
 * This module provides environment detection, configuration loading,
 * and validation utilities for the Insurance Navigator application.
 */

import { EnvironmentConfig, Environment, EnvironmentValidationResult } from './types';
import { developmentConfig } from './development';
import { productionConfig } from './production';

/**
 * Detects the current environment based on NODE_ENV and other indicators
 */
export function detectEnvironment(): Environment {
  const nodeEnv = process.env.NODE_ENV;
  const envLevel = process.env.ENV_LEVEL;
  
  // Check explicit environment level first
  if (envLevel === 'production' || envLevel === 'development') {
    return envLevel;
  }
  
  // Fall back to NODE_ENV
  if (nodeEnv === 'production') {
    return 'production';
  }
  
  // Default to development for safety
  return 'development';
}

/**
 * Loads the appropriate environment configuration
 */
export function loadEnvironmentConfig(): EnvironmentConfig {
  const environment = detectEnvironment();
  
  switch (environment) {
    case 'production':
      return productionConfig;
    case 'development':
    default:
      return developmentConfig;
  }
}

/**
 * Validates the current environment configuration
 */
export function validateEnvironmentConfig(config: EnvironmentConfig): EnvironmentValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  
  // Validate required environment variables for production
  if (config.environment === 'production') {
    if (!config.database.url) {
      errors.push('DATABASE_URL is required for production environment');
    }
    
    if (!config.external.openaiApiKey) {
      errors.push('OPENAI_API_KEY is required for production environment');
    }
    
    if (!config.external.anthropicApiKey) {
      errors.push('ANTHROPIC_API_KEY is required for production environment');
    }
    
    if (!config.external.llamaCloudApiKey) {
      errors.push('LLAMAPARSE_API_KEY is required for production environment');
    }
    
    if (!config.external.resendApiKey) {
      errors.push('RESEND_API_KEY is required for production environment');
    }
    
    if (!config.security.jwtSecret || config.security.jwtSecret === 'dev-jwt-secret-not-for-production') {
      errors.push('JWT_SECRET_KEY must be set to a secure value for production');
    }
    
    if (!config.security.encryptionKey || config.security.encryptionKey === 'dev-encryption-key-not-for-production') {
      errors.push('ENCRYPTION_KEY must be set to a secure value for production');
    }
    
    if (config.security.bypassEnabled) {
      warnings.push('Security bypass is enabled in production - this should be disabled');
    }
  }
  
  // Validate database configuration
  if (!config.database.url) {
    errors.push('Database URL is required');
  }
  
  // Validate API configuration
  if (config.api.port < 1 || config.api.port > 65535) {
    errors.push('API port must be between 1 and 65535');
  }
  
  if (config.api.corsOrigins.length === 0) {
    warnings.push('No CORS origins configured - API may not be accessible from frontend');
  }
  
  // Validate frontend configuration
  if (!config.frontend.appUrl) {
    errors.push('Frontend app URL is required');
  }
  
  if (!config.frontend.apiBaseUrl) {
    errors.push('Frontend API base URL is required');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    environment: config.environment
  };
}

/**
 * Gets the current environment configuration with validation
 */
export function getEnvironmentConfig(): EnvironmentConfig {
  const config = loadEnvironmentConfig();
  const validation = validateEnvironmentConfig(config);
  
  if (!validation.isValid) {
    console.error('Environment configuration validation failed:');
    validation.errors.forEach(error => console.error(`  ❌ ${error}`));
    validation.warnings.forEach(warning => console.warn(`  ⚠️  ${warning}`));
    
    if (config.environment === 'production') {
      throw new Error('Production environment configuration is invalid');
    }
  } else if (validation.warnings.length > 0) {
    console.warn('Environment configuration warnings:');
    validation.warnings.forEach(warning => console.warn(`  ⚠️  ${warning}`));
  }
  
  return config;
}

/**
 * Exports for external use
 */
export { EnvironmentConfig, Environment, EnvironmentValidationResult } from './types';
export { developmentConfig } from './development';
export { productionConfig } from './production';
