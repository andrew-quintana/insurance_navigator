/**
 * Development Environment Configuration
 * 
 * This configuration is optimized for local development with relaxed security
 * and enhanced debugging capabilities.
 */

import { EnvironmentConfig } from './types';

export const developmentConfig: EnvironmentConfig = {
  environment: 'development',
  
  api: {
    host: '0.0.0.0',
    port: 8000,
    corsOrigins: [
      'http://localhost:3000',
      'http://localhost:3001',
      'http://127.0.0.1:3000',
      'http://127.0.0.1:3001'
    ],
    rateLimiting: false,
    timeout: 30000
  },

  database: {
    url: process.env.DATABASE_URL || 'postgresql://postgres:password@localhost:5432/insurance_navigator_dev',
    poolSize: 5,
    connectionTimeout: 10000,
    schema: 'upload_pipeline'
  },

  frontend: {
    appUrl: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
    analyticsEnabled: false,
    debugMode: true
  },

  external: {
    openaiApiKey: process.env.OPENAI_API_KEY || '',
    anthropicApiKey: process.env.ANTHROPIC_API_KEY || '',
    llamaCloudApiKey: process.env.LLAMAPARSE_API_KEY || '',
    resendApiKey: process.env.RESEND_API_KEY || ''
  },

  security: {
    jwtSecret: process.env.JWT_SECRET_KEY || 'dev-jwt-secret-not-for-production',
    encryptionKey: process.env.ENCRYPTION_KEY || 'dev-encryption-key-not-for-production',
    bypassEnabled: true,
    allowedOrigins: [
      'http://localhost:3000',
      'http://localhost:3001',
      'http://127.0.0.1:3000',
      'http://127.0.0.1:3001'
    ]
  },

  monitoring: {
    enabled: true,
    logLevel: 'DEBUG',
    metricsEnabled: true,
    healthCheckInterval: 30000
  }
};
