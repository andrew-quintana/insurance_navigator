export type RuntimeEnvironment = 'node' | 'deno' | 'browser';
export type DeploymentEnvironment = 'test' | 'development' | 'staging' | 'production';

export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

export interface Environment {
  SUPABASE_URL: string;
  SUPABASE_ANON_KEY: string;
  SUPABASE_SERVICE_ROLE_KEY: string;
  ENVIRONMENT: 'development' | 'staging' | 'production';
  NGROK_URL?: string; // Optional, only needed in development
}

export interface EnvConfig {
  // Runtime information
  runtime: RuntimeEnvironment;
  deploymentEnv: DeploymentEnvironment;

  // Core configuration
  supabaseUrl: string;
  supabaseKey: string;
  openaiApiKey?: string;
  llamaparseApiKey?: string;
  anthropicApiKey?: string;
  logLevel: LogLevel;

  // Feature flags
  enableVectorProcessing: boolean;
  enableRegulatoryProcessing: boolean;

  // Test configuration (only in non-production)
  testMode?: boolean;
  mockExternalServices?: boolean;
  testUserId?: string;
  testUserEmail?: string;
  testUserPassword?: string;
} 