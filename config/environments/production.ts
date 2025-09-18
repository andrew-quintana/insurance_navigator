/**
 * Production Environment Configuration
 * 
 * This configuration is optimized for production with enhanced security,
 * performance, and monitoring capabilities.
 */

import { EnvironmentConfig } from './types';

export const productionConfig: EnvironmentConfig = {
  environment: 'production',
  
  api: {
    host: '0.0.0.0',
    port: parseInt(process.env.PORT || '8000', 10),
    corsOrigins: [
      'https://insurance-navigator.vercel.app',
      'https://www.insurance-navigator.vercel.app',
      'https://insurance-navigator.com',
      'https://www.insurance-navigator.com'
    ],
    rateLimiting: true,
    timeout: 15000
  },

  database: {
    url: process.env.DATABASE_URL || '',
    poolSize: 10,
    connectionTimeout: 5000,
    schema: 'upload_pipeline'
  },

  frontend: {
    appUrl: process.env.NEXT_PUBLIC_APP_URL || 'https://insurance-navigator.vercel.app',
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || '***REMOVED***',
    analyticsEnabled: true,
    debugMode: false
  },

  external: {
    openaiApiKey: process.env.OPENAI_API_KEY || '',
    anthropicApiKey: process.env.ANTHROPIC_API_KEY || '',
    llamaCloudApiKey: process.env.LLAMAPARSE_API_KEY || '',
    resendApiKey: process.env.RESEND_API_KEY || ''
  },

  security: {
    jwtSecret: process.env.JWT_SECRET || process.env.JWT_SECRET_KEY || '',
    encryptionKey: process.env.DOCUMENT_ENCRYPTION_KEY || process.env.ENCRYPTION_KEY || '',
    bypassEnabled: false,
    allowedOrigins: [
      'https://insurance-navigator.vercel.app',
      'https://www.insurance-navigator.vercel.app',
      'https://insurance-navigator.com',
      'https://www.insurance-navigator.com'
    ]
  },

  monitoring: {
    enabled: true,
    logLevel: 'INFO',
    metricsEnabled: true,
    healthCheckInterval: 60000
  }
};
