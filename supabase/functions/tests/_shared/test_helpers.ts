/// <reference lib="deno.ns" />
import { initializeConfig } from "../../_shared/environment.ts";
import { createServiceRoleJWT } from "../../_shared/jwt.ts";

export interface TestConfig {
  supabaseUrl: string;
  supabaseKey: string;
  serviceRoleKey: string;
  jwtSecret: string;
}

export async function loadTestConfig(): Promise<TestConfig> {
  const config = await initializeConfig();
  
  // Validate required configuration
  if (!config.supabaseUrl) {
    throw new Error("SUPABASE_URL is required in test configuration");
  }
  if (!config.supabaseKey) {
    throw new Error("SUPABASE_KEY is required in test configuration");
  }
  
  return {
    supabaseUrl: config.supabaseUrl,
    supabaseKey: config.supabaseKey,
    serviceRoleKey: config.supabaseKey, // Use the same key for service role
    jwtSecret: config.jwtSecret
  };
}

export function createMockClient(config: Partial<TestConfig> = {}) {
  return {
    from: (table: string) => ({
      select: () => ({
        eq: (field: string, value: string) => ({
          eq: (field2: string, value2: string) => ({
            single: async () => ({
              data: {
                id: value,
                user_id: value2,
                storage_path: `test/raw/${value}.pdf`,
                content_type: "application/pdf",
                filename: `${value}.pdf`,
                status: "pending"
              },
              error: null
            })
          }),
          single: async () => ({
            data: {
              id: value,
              storage_path: `test/raw/${value}.pdf`,
              content_type: "application/pdf",
              filename: `${value}.pdf`,
              status: "pending"
            },
            error: null
          })
        })
      }),
      update: () => ({
        eq: () => ({
          single: async () => ({ data: { id: "test-doc" }, error: null })
        })
      }),
      insert: () => ({
        single: async () => ({ data: { id: "test-doc" }, error: null })
      })
    }),
    storage: {
      from: () => ({
        download: async () => ({ data: new Uint8Array([1, 2, 3]), error: null, exists: true }),
        upload: async () => ({ data: { path: "test/processed/test.pdf" }, error: null }),
        remove: async () => ({ data: null, error: null })
      })
    },
    auth: {
      getUser: async () => ({
        data: { id: "test-user", role: "authenticated" },
        error: null
      })
    }
  };
}

export async function setupTestUser(client: any) {
  return {
    id: "test-user",
    role: "authenticated"
  };
}

export async function createTestJWT(userId: string) {
  return await createServiceRoleJWT();
}

export async function retryOperation<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  retryDelay = 1000
): Promise<T> {
  let lastError;
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        console.log(`Operation failed, retrying (${i + 1}/${maxRetries}):`, error);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    }
  }
  throw lastError;
} 