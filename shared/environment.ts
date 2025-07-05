export const ENV_TYPES = ['local', 'test', 'development', 'staging', 'production'] as const;
type DeploymentEnvironment = typeof ENV_TYPES[number];

interface EdgeFunctionConfig {
  supabaseUrl: string;
  supabaseKey: string;
  openaiApiKey?: string;
  llamaparseApiKey?: string;
  logLevel: string;
  enableVectorProcessing: boolean;
  enableRegulatoryProcessing: boolean;
  testUserId?: string;
  testUserEmail?: string;
  testUserPassword?: string;
}

// Runtime environment detection
export const runtimeEnvironment = {
  isDeno: typeof Deno !== 'undefined',
  isNode: typeof process !== 'undefined' && !!process.versions?.node,
  isEdgeFunction: typeof Deno !== 'undefined' && !!Deno.env.get('SUPABASE_FUNCTION_NAME'),
  isTest: typeof process !== 'undefined' && process.env.NODE_ENV === 'test' || 
          typeof Deno !== 'undefined' && Deno.env.get('NODE_ENV') === 'test'
};

// Enhanced environment variable getter that handles multiple sources
export function getEnvVar(key: string): string | undefined {
  if (runtimeEnvironment.isEdgeFunction) {
    // Edge functions should use Deno.env
    return Deno.env.get(key);
  } else if (runtimeEnvironment.isDeno) {
    // Local Deno development
    return Deno.env.get(key);
  } else if (runtimeEnvironment.isNode) {
    // Node.js environment (local development, testing)
    return process.env[key];
  }
  return undefined;
}

function getDeploymentEnvironment(): DeploymentEnvironment {
  // For edge functions, default to the function's deployment environment
  if (runtimeEnvironment.isEdgeFunction) {
    const functionEnv = Deno.env.get('FUNCTION_ENV') || 'production';
    return functionEnv as DeploymentEnvironment;
  }

  // For local development and testing
  const env = getEnvVar('ENV_LEVEL');
  if (env && ENV_TYPES.includes(env as DeploymentEnvironment)) {
    return env as DeploymentEnvironment;
  }

  // Default environments based on context
  if (runtimeEnvironment.isTest) return 'test';
  return 'development';
}

// Enhanced validation with context-aware requirements
function validateConfig(config: EdgeFunctionConfig): void {
  const requiredFields = ['supabaseUrl', 'supabaseKey'] as const;
  
  // Add additional required fields based on environment
  if (runtimeEnvironment.isEdgeFunction && getDeploymentEnvironment() === 'production') {
    requiredFields.push('openaiApiKey' as const);
  }

  const missingFields = requiredFields.filter(field => !config[field]);
  if (missingFields.length > 0) {
    throw new Error(
      `Missing required configuration fields: ${missingFields.join(', ')} in ` +
      `${runtimeEnvironment.isEdgeFunction ? 'edge function' : 'local'} environment`
    );
  }
}

export function getEnvConfig(): EdgeFunctionConfig {
  const env = getDeploymentEnvironment();
  
  const config: EdgeFunctionConfig = {
    supabaseUrl: getEnvVar('SUPABASE_URL') || '',
    supabaseKey: getEnvVar('SUPABASE_SERVICE_ROLE_KEY') || '',
    openaiApiKey: getEnvVar('OPENAI_API_KEY'),
    llamaparseApiKey: getEnvVar('LLAMAPARSE_API_KEY'),
    logLevel: env === 'production' ? 'INFO' : 'DEBUG',
    enableVectorProcessing: env !== 'production',
    enableRegulatoryProcessing: env !== 'production'
  };

  // Only add test credentials in non-production environments
  if (env !== 'production') {
    config.testUserId = getEnvVar('TEST_USER_ID');
    config.testUserEmail = getEnvVar('TEST_USER_EMAIL');
    config.testUserPassword = getEnvVar('TEST_USER_PASSWORD');
  }

  validateConfig(config);
  return config;
}

// Export the config for use across the application
export const edgeConfig = getEnvConfig(); 