/// <reference lib="deno.ns" />
import { join } from "https://deno.land/std@0.208.0/path/mod.ts";

export const ENV_TYPES = ['development', 'test', 'staging', 'production'] as const;
type DeploymentEnvironment = typeof ENV_TYPES[number];

interface EdgeFunctionConfig {
  // Required in all environments
  supabaseUrl: string;
  supabaseKey: string;
  openaiApiKey: string;
  jwtSecret: string;

  // Optional in all environments
  llamaparseApiKey?: string;
  anthropicApiKey?: string;

  // Environment-specific settings
  environment: DeploymentEnvironment;
  logLevel: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  enableVectorProcessing: boolean;
  enableRegulatoryProcessing: boolean;

  // Test-only settings
  testUserId?: string;
  testUserEmail?: string;
  testUserPassword?: string;
}

// Runtime environment detection
const runtimeContext = {
  isDeno: typeof Deno !== 'undefined',
  isEdgeFunction: typeof Deno !== 'undefined' && !!Deno.env.get('SUPABASE_FUNCTION_NAME'),
  isTest: typeof Deno !== 'undefined' && (
    Deno.env.get('NODE_ENV') === 'test' || 
    Deno.env.get('ENV_LEVEL') === 'test'
  )
};

function getDeploymentEnvironment(): DeploymentEnvironment {
  if (runtimeContext.isEdgeFunction) {
    return 'production';
  }

  const envLevel = Deno.env.get('ENV_LEVEL');
  if (envLevel && ENV_TYPES.includes(envLevel as DeploymentEnvironment)) {
    return envLevel as DeploymentEnvironment;
  }

  if (runtimeContext.isTest) {
    return 'test';
  }

  return 'development';
}

function getRequiredEnvVar(name: string, environment: string, fallbackNames?: string[]): string {
  // Try the primary name first
  const value = Deno.env.get(name);
  if (value && value.trim() !== '') {
    // Strip quotes from JWT secrets
    if (name === 'SUPABASE_JWT_SECRET' || name === 'JWT_SECRET') {
      return value.replace(/^["']|["']$/g, '');
    }
    return value;
  }

  // Try fallback names if provided
  if (fallbackNames) {
    for (const fallbackName of fallbackNames) {
      const fallbackValue = Deno.env.get(fallbackName);
      if (fallbackValue && fallbackValue.trim() !== '') {
        // Strip quotes from JWT secrets
        if (name === 'SUPABASE_JWT_SECRET' || name === 'JWT_SECRET') {
          return fallbackValue.replace(/^["']|["']$/g, '');
        }
        return fallbackValue;
      }
    }
  }

  throw new Error(`Missing required configuration field: ${name} in ${environment} environment`);
}

function getOptionalEnvVar(name: string): string | undefined {
  const value = Deno.env.get(name);
  return value && value.trim() !== '' ? value : undefined;
}

function getEnvFileOverride(): string | undefined {
  return Deno.env.get('ENV_FILE_OVERRIDE');
}

async function loadEnvFile(environment: DeploymentEnvironment): Promise<void> {
  // Skip loading .env files in production edge functions
  if (runtimeContext.isEdgeFunction && environment === 'production') {
    return;
  }

  try {
    // Calculate path to root .env file
    const currentDir = Deno.cwd();
    const rootDir = currentDir.includes('supabase/functions') 
      ? join(currentDir, '..', '..') 
      : currentDir;
    
    // Check for override first
    const envFileOverride = Deno.env.get('ENV_FILE_OVERRIDE');
    const envPath = envFileOverride 
      ? join(rootDir, envFileOverride)
      : join(rootDir, `.env.${environment}`);

    console.log('Loading environment from:', envPath); // Debug log
    
    const envContent = await Deno.readTextFile(envPath);
    const envVars = envContent.split('\n');

    // Clear existing env vars before loading new ones
    if (envFileOverride) {
      console.log('Override detected, clearing existing env vars');
      const varsToPreserve = ['DENO_DEPLOYMENT_ID', 'SUPABASE_FUNCTION_NAME', 'TEST_USER_ID', 'JWT_SECRET', 'SUPABASE_JWT_SECRET'];
      const preserved = varsToPreserve.reduce((acc, key) => {
        acc[key] = Deno.env.get(key);
        return acc;
      }, {} as Record<string, string | undefined>);

      // Clear all env vars except preserved ones
      for (const key of Object.keys(Deno.env.toObject())) {
        if (!varsToPreserve.includes(key)) {
          Deno.env.delete(key);
        }
      }

      // Restore preserved vars
      for (const [key, value] of Object.entries(preserved)) {
        if (value !== undefined) {
          Deno.env.set(key, value);
        }
      }
    }

    for (const line of envVars) {
      const [key, ...valueParts] = line.split('=');
      if (key && valueParts.length > 0) {
        const value = valueParts.join('=').trim();
        if (value) {
          // Skip setting TEST_USER_ID if it's already set
          if (key.trim() === 'TEST_USER_ID' && Deno.env.get('TEST_USER_ID')) {
            continue;
          }
          Deno.env.set(key.trim(), value);
          console.log(`Set env var: ${key.trim()}=${value}`); // Debug log
        }
      }
    }
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    
    if (environment === 'test') {
      throw new Error(`Failed to load test environment file: ${errorMessage}`);
    }
    // For non-test environments, log but don't fail
    console.warn(`Warning: Could not load .env.${environment}: ${errorMessage}`);
  }
}

function parseBoolean(value: string | undefined): boolean {
  if (!value) return false;
  return value.toLowerCase() !== 'false' && value !== '0';
}

export async function initializeConfig(): Promise<EdgeFunctionConfig> {
  const environment = getDeploymentEnvironment();
  
  // Load environment file if not in production edge function
  if (!runtimeContext.isEdgeFunction || environment !== 'production') {
    await loadEnvFile(environment);
  }

  // Get required fields first to fail fast
  const supabaseUrl = getRequiredEnvVar('SUPABASE_URL', environment);
  const supabaseKey = getRequiredEnvVar('SUPABASE_SERVICE_ROLE_KEY', environment);
  const openaiApiKey = getRequiredEnvVar('OPENAI_API_KEY', environment);
  const jwtSecret = getRequiredEnvVar('SUPABASE_JWT_SECRET', environment, ['JWT_SECRET']);

  const config: EdgeFunctionConfig = {
    environment,
    supabaseUrl,
    supabaseKey,
    openaiApiKey,
    jwtSecret,
    llamaparseApiKey: getOptionalEnvVar('LLAMAPARSE_API_KEY'),
    anthropicApiKey: getOptionalEnvVar('ANTHROPIC_API_KEY'),
    logLevel: environment === 'production' ? 'INFO' : 'DEBUG',
    enableVectorProcessing: environment !== 'production' && parseBoolean(Deno.env.get('ENABLE_VECTOR_PROCESSING')),
    enableRegulatoryProcessing: environment !== 'production' && parseBoolean(Deno.env.get('ENABLE_REGULATORY_PROCESSING'))
  };

  // Add test credentials in non-production environments
  if (environment !== 'production') {
    config.testUserId = getOptionalEnvVar('TEST_USER_ID');
    config.testUserEmail = getOptionalEnvVar('TEST_USER_EMAIL');
    config.testUserPassword = getOptionalEnvVar('TEST_USER_PASSWORD');
  }

  return config;
}

// Export a promise that resolves to the config
export const edgeConfigPromise = initializeConfig();

// For backwards compatibility and simpler usage in most cases
export const edgeConfig = await edgeConfigPromise; 