interface TestConfig {
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

export function getTestConfig(): TestConfig {
  return {
    supabaseUrl: process.env.SUPABASE_URL || '',
    supabaseKey: process.env.SUPABASE_SERVICE_ROLE_KEY || '',
    openaiApiKey: process.env.OPENAI_API_KEY,
    llamaparseApiKey: process.env.LLAMAPARSE_API_KEY,
    logLevel: 'DEBUG',
    enableVectorProcessing: true,
    enableRegulatoryProcessing: true,
    testUserId: process.env.TEST_USER_ID,
    testUserEmail: process.env.TEST_USER_EMAIL,
    testUserPassword: process.env.TEST_USER_PASSWORD
  };
}

export const testConfig = getTestConfig(); 