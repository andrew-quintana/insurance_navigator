import { edgeConfigPromise } from "../../_shared/environment.ts";

export async function setupTestEnvironment() {
  // Set test environment
  Deno.env.set('NODE_ENV', 'test');
  
  try {
    // Initialize config - this will load .env.test
    const config = await edgeConfigPromise;
    
    if (config.environment !== 'test') {
      throw new Error(`Expected test environment, got ${config.environment}`);
    }
    
    return config;
  } catch (error) {
    console.error('Failed to setup test environment:', error);
    throw error;
  }
}

// For use in beforeAll blocks
export async function initializeTestSuite() {
  const config = await setupTestEnvironment();
  return { config };
}

// For use in afterAll blocks
export function cleanupTestSuite() {
  // Clean up any test-specific state here
  Deno.env.delete('NODE_ENV');
} 