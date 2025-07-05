import { EnvConfig, DeploymentEnvironment } from './types';

// Helper function to validate environment level
function validateEnvLevel(level: string | undefined): DeploymentEnvironment {
  const validLevels: DeploymentEnvironment[] = ['test', 'development', 'staging', 'production'];
  const defaultLevel: DeploymentEnvironment = 'development';
  
  if (!level) {
    return defaultLevel;
  }
  
  return validLevels.includes(level as DeploymentEnvironment) 
    ? level as DeploymentEnvironment 
    : defaultLevel;
}

export const envConfig: EnvConfig = {
  runtime: typeof window === 'undefined' ? 'node' : 'browser',
  deploymentEnv: validateEnvLevel(process.env.ENV_LEVEL),
  supabaseUrl: process.env.SUPABASE_URL || 'http://127.0.0.1:54321',
  supabaseKey: process.env.SUPABASE_SERVICE_ROLE_KEY || '',
  openaiApiKey: process.env.OPENAI_API_KEY || '',
  llamaparseApiKey: process.env.LLAMAPARSE_API_KEY || '',
  anthropicApiKey: process.env.ANTHROPIC_API_KEY || '',
  enableVectorProcessing: process.env.ENABLE_VECTOR_PROCESSING === 'true',
  enableRegulatoryProcessing: process.env.ENABLE_REGULATORY_PROCESSING === 'true',
  logLevel: process.env.ENV_LEVEL === 'production' ? 'INFO' : 'DEBUG',
  testMode: process.env.TEST_MODE === 'true',
  mockExternalServices: process.env.MOCK_EXTERNAL_SERVICES === 'true',
  // Test credentials only available in non-production environments
  ...(validateEnvLevel(process.env.ENV_LEVEL) !== 'production' && {
    testUserId: process.env.TEST_USER_ID,
    testUserEmail: process.env.TEST_USER_EMAIL,
    testUserPassword: process.env.TEST_USER_PASSWORD
  })
};

export function getEnvConfig(): EnvConfig {
  return envConfig;
}

// Export type for use in other files
export type { EnvConfig } from './types'; 