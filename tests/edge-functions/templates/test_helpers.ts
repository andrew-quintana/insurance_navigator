/// <reference lib="deno.ns" />
/// <reference lib="dom" />

import { createClient, SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2.39.7";
import { assert, assertEquals } from "https://deno.land/std@0.217.0/testing/asserts.ts";

/**
 * Environment configuration interface following the project standards
 */
export interface EnvironmentConfig {
  // Required variables
  supabaseUrl: string;
  supabaseKey: string;
  openaiApiKey: string;
  nodeEnv: string;

  // Optional variables
  llamaparseApiKey?: string;
  anthropicApiKey?: string;
  debug?: boolean;

  // Boolean feature flags
  enableVectorProcessing: boolean;
  enableRegulatoryProcessing: boolean;

  // Test configuration
  testUserId: string;
  testMode: boolean;
  mockExternalServices: boolean;
}

/**
 * Parse boolean environment variable
 */
function parseBoolean(value: string | undefined): boolean {
  if (!value) return false;
  return ['true', '1', 'yes'].includes(value.toLowerCase());
}

/**
 * Load and validate environment variables following the hierarchy
 */
export async function loadTestEnvironment(): Promise<EnvironmentConfig> {
  try {
    // Set default values
    const defaults = {
      SUPABASE_URL: 'http://127.0.0.1:54321',
      SUPABASE_SERVICE_ROLE_KEY: 'test-key',
      OPENAI_API_KEY: 'test-key',
      NODE_ENV: 'test',
      TEST_MODE: 'true',
      MOCK_EXTERNAL_SERVICES: 'true',
      ENABLE_VECTOR_PROCESSING: 'false',
      ENABLE_REGULATORY_PROCESSING: 'false',
      DEBUG: 'true'
    };

    // Apply defaults
    Object.entries(defaults).forEach(([key, value]) => {
      if (!Deno.env.get(key)) {
        Deno.env.set(key, value);
      }
    });

    // Try to load environment files if they exist
    try {
      const override = Deno.env.get('ENV_FILE_OVERRIDE');
      if (override) {
        console.log('Using environment override:', override);
        const overrideContent = await Deno.readTextFile(override);
        applyEnvFile(overrideContent);
      } else {
        try {
          const testEnv = await Deno.readTextFile('.env.test');
          applyEnvFile(testEnv);
        } catch (error) {
          console.log('No .env.test file found, using defaults');
        }

        try {
          const baseEnv = await Deno.readTextFile('.env');
          applyEnvFile(baseEnv);
        } catch (error) {
          console.log('No base .env file found, using defaults');
        }
      }
    } catch (error) {
      console.log('Error loading environment files, using defaults:', error);
    }

    // Validate and return environment config
    return validateEnvironment();
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('Failed to load test environment:', errorMessage);
    throw new Error(`Environment loading failed: ${errorMessage}`);
  }
}

/**
 * Apply environment file contents
 */
function applyEnvFile(content: string) {
  for (const line of content.split('\n')) {
    if (line && !line.startsWith('#')) {
      const [key, value] = line.split('=');
      if (key && value) {
        Deno.env.set(key.trim(), value.trim());
      }
    }
  }
}

/**
 * Validate environment configuration
 */
function validateEnvironment(): EnvironmentConfig {
  // Required variables
  const supabaseUrl = Deno.env.get('SUPABASE_URL');
  const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  const openaiApiKey = Deno.env.get('OPENAI_API_KEY');
  const nodeEnv = Deno.env.get('NODE_ENV');

  if (!supabaseUrl) throw new Error('SUPABASE_URL is required');
  if (!supabaseKey) throw new Error('SUPABASE_SERVICE_ROLE_KEY is required');
  if (!openaiApiKey) throw new Error('OPENAI_API_KEY is required');
  if (!nodeEnv) throw new Error('NODE_ENV is required');

  // Create config object
  const config: EnvironmentConfig = {
    supabaseUrl,
    supabaseKey,
    openaiApiKey,
    nodeEnv,
    testUserId: '00000000-0000-4000-a000-000000000000',
    testMode: parseBoolean(Deno.env.get('TEST_MODE')),
    mockExternalServices: parseBoolean(Deno.env.get('MOCK_EXTERNAL_SERVICES')),
    enableVectorProcessing: parseBoolean(Deno.env.get('ENABLE_VECTOR_PROCESSING')),
    enableRegulatoryProcessing: parseBoolean(Deno.env.get('ENABLE_REGULATORY_PROCESSING')),
  };

  // Optional variables
  const llamaparseApiKey = Deno.env.get('LLAMAPARSE_API_KEY');
  if (llamaparseApiKey) config.llamaparseApiKey = llamaparseApiKey;

  const anthropicApiKey = Deno.env.get('ANTHROPIC_API_KEY');
  if (anthropicApiKey) config.anthropicApiKey = anthropicApiKey;

  const debug = Deno.env.get('DEBUG');
  if (debug) config.debug = parseBoolean(debug);

  return config;
}

/**
 * Create a mock Supabase client for testing
 */
export function createMockClient(mockData: any = {}): SupabaseClient {
  return {
    storage: {
      from: () => ({
        download: () => Promise.resolve({
          data: mockData.downloadData || null,
          error: mockData.storageError || null
        }),
        upload: () => Promise.resolve({
          data: mockData.uploadData || null,
          error: mockData.storageError || null
        }),
        remove: () => Promise.resolve({
          data: mockData.removeData || null,
          error: mockData.storageError || null
        }),
        list: () => Promise.resolve({
          data: mockData.listData || [],
          error: mockData.storageError || null
        }),
        move: () => Promise.resolve({
          data: mockData.moveData || { path: mockData.uploadData?.path },
          error: mockData.storageError || null
        })
      })
    },
    from: (table: string) => ({
      select: () => ({
        eq: (field: string, value: string) => ({
          eq: (field2: string, value2: string) => ({
            single: () => Promise.resolve({
              data: mockData.dbData || null,
              error: mockData.dbError ? {
                ...mockData.dbError,
                code: mockData.dbError.code || (mockData.dbError.message?.includes("not found") ? "PGRST116" : "PGRST999")
              } : null
            })
          })
        })
      }),
      update: (data: any) => ({
        eq: (field: string, value: string) => {
          if (mockData.updateHandler) {
            return mockData.updateHandler(table, data, field, value);
          }
          return Promise.resolve({
            data: mockData.updateData || null,
            error: mockData.updateError || null
          });
        }
      }),
      insert: () => ({
        select: () => ({
          single: () => Promise.resolve({
            data: mockData.insertData || null,
            error: mockData.insertError || null
          })
        })
      }),
      delete: () => ({
        eq: (field: string, value: string) => Promise.resolve({
          data: mockData.deleteData || null,
          error: mockData.deleteError || null
        })
      })
    })
  } as unknown as SupabaseClient;
}

/**
 * Create a test user and set up necessary resources
 */
export async function setupTestUser(supabase: SupabaseClient): Promise<void> {
  const testUser = {
    id: "00000000-0000-4000-a000-000000000000",
    email: Deno.env.get("TEST_USER_EMAIL") || "test@example.com",
    name: "Test User",
    created_at: new Date().toISOString()
  };

  // Insert test user
  const { data: insertedUser, error: insertError } = await supabase
    .from("users")
    .insert(testUser)
    .select()
    .single();

  if (insertError) {
    throw insertError;
  }

  if (parseBoolean(Deno.env.get('DEBUG'))) {
    console.log("Inserted user:", insertedUser);
  }

  // Verify user was created
  const { data: verifiedUser, error: verifyError } = await supabase
    .from("users")
    .select()
    .eq("id", testUser.id)
    .single();

  if (verifyError) {
    throw verifyError;
  }

  if (parseBoolean(Deno.env.get('DEBUG'))) {
    console.log("Verified user:", verifiedUser);
  }
}

/**
 * Clean up test resources
 */
export async function cleanup(supabase: SupabaseClient): Promise<void> {
  try {
    // Clean up test user
    await supabase
      .from("users")
      .delete()
      .eq("id", "00000000-0000-4000-a000-000000000000");

    // Clean up storage
    const storagePath = Deno.env.get("SUPABASE_TEMP_STORAGE_PATH");
    if (storagePath) {
      await supabase.storage
        .from(Deno.env.get("SUPABASE_STORAGE_BUCKET") || "")
        .remove([storagePath]);
    }

    if (parseBoolean(Deno.env.get('DEBUG'))) {
      console.log("Cleanup completed successfully");
    }
  } catch (error) {
    console.error("Error during cleanup:", error);
    throw error;
  }
}

/**
 * Test helper assertions
 */
export function assertSuccess(result: any, message = "Operation should succeed"): void {
  assert(result.success, message);
  assertEquals(result.error, undefined, "Should not have error");
}

export function assertError(
  result: any,
  expectedStatus: number,
  message = "Operation should fail"
): void {
  assert(!result.success, message);
  assert(result.error, "Should have error message");
  assertEquals(result.statusCode, expectedStatus, "Should have correct status code");
}

/**
 * Wait for a condition to be true
 */
export async function waitForCondition(
  condition: () => Promise<boolean>,
  timeout = 5000,
  interval = 100
): Promise<void> {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    if (await condition()) {
      return;
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  throw new Error("Condition not met within timeout");
} 