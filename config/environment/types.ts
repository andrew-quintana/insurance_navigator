export type RuntimeEnvironment = 'node' | 'deno' | 'browser';
export type DeploymentEnvironment = 'test' | 'development' | 'staging' | 'production';

export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

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