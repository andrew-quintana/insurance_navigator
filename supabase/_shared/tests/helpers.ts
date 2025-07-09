/// <reference lib="deno.ns" />

// Test environment type
export interface TestEnv {
  SERVICE_ROLE_KEY: string;
  NODE_ENV: string;
}

/**
 * Helper function to run tests with a temporary environment configuration
 * @param fn The test function to run
 * @param testEnv The environment variables to set
 */
export async function withTestEnv<T>(
  fn: (env: TestEnv) => Promise<T>,
  testEnv: TestEnv
): Promise<T> {
  const originalEnv = {
    SERVICE_ROLE_KEY: Deno.env.get('SERVICE_ROLE_KEY'),
    NODE_ENV: Deno.env.get('NODE_ENV'),
  };

  // Set test environment
  for (const [key, value] of Object.entries(testEnv)) {
    Deno.env.set(key, value);
  }

  try {
    return await fn(testEnv);
  } finally {
    // Restore original environment
    for (const [key, value] of Object.entries(originalEnv)) {
      if (value === undefined) {
        Deno.env.delete(key);
      } else {
        Deno.env.set(key, value);
      }
    }
  }
} 