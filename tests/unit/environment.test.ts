import { assertEquals, assertRejects } from "std/testing/asserts.ts";

// Store original env vars to restore after tests
const originalEnv = {
  NODE_ENV: Deno.env.get("NODE_ENV"),
  ENV_LEVEL: Deno.env.get("ENV_LEVEL"),
  SUPABASE_URL: Deno.env.get("SUPABASE_URL"),
  SUPABASE_SERVICE_ROLE_KEY: Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"),
  OPENAI_API_KEY: Deno.env.get("OPENAI_API_KEY"),
  TEST_USER_ID: Deno.env.get("TEST_USER_ID"),
  TEST_USER_EMAIL: Deno.env.get("TEST_USER_EMAIL"),
  TEST_USER_PASSWORD: Deno.env.get("TEST_USER_PASSWORD"),
  ENABLE_VECTOR_PROCESSING: Deno.env.get("ENABLE_VECTOR_PROCESSING"),
  ENABLE_REGULATORY_PROCESSING: Deno.env.get("ENABLE_REGULATORY_PROCESSING"),
  SUPABASE_FUNCTION_NAME: Deno.env.get("SUPABASE_FUNCTION_NAME"),
  LLAMAPARSE_API_KEY: Deno.env.get("LLAMAPARSE_API_KEY"),
  ANTHROPIC_API_KEY: Deno.env.get("ANTHROPIC_API_KEY")
};

// Helper to reset environment to a clean state
function resetEnvironment() {
  // Clear all relevant env vars
  Object.keys(originalEnv).forEach(key => Deno.env.delete(key));
  
  // Restore original values if they existed
  Object.entries(originalEnv).forEach(([key, value]) => {
    if (value !== undefined) {
      Deno.env.set(key, value);
    }
  });
}

Deno.test({
  name: "environment configuration - basic setup",
  async fn() {
    // Start with a clean environment
    resetEnvironment();
    
    // Set test environment
    Deno.env.set("NODE_ENV", "test");
    Deno.env.set("ENV_LEVEL", "test");
    Deno.env.set("SUPABASE_URL", "https://test.supabase.co");
    Deno.env.set("SUPABASE_SERVICE_ROLE_KEY", "test-key");
    Deno.env.set("OPENAI_API_KEY", "test-openai-key");
    Deno.env.set("TEST_USER_ID", "test-user-id");
    Deno.env.set("TEST_USER_EMAIL", "test@example.com");
    Deno.env.set("TEST_USER_PASSWORD", "test-password");
    Deno.env.set("ENABLE_VECTOR_PROCESSING", "true");
    Deno.env.set("ENABLE_REGULATORY_PROCESSING", "true");

    // Import config after environment is set up
    const { edgeConfig } = await import("@shared/environment.ts?test=basic");

    // Test required fields
    assertEquals(edgeConfig.supabaseUrl, "https://test.supabase.co");
    assertEquals(edgeConfig.supabaseKey, "test-key");
    assertEquals(edgeConfig.openaiApiKey, "test-openai-key");
    
    // Test environment-specific settings
    assertEquals(edgeConfig.environment, "test");
    assertEquals(edgeConfig.logLevel, "DEBUG");
    assertEquals(edgeConfig.enableVectorProcessing, true);
    assertEquals(edgeConfig.enableRegulatoryProcessing, true);

    // Test test-specific fields
    assertEquals(edgeConfig.testUserId, "test-user-id");
    assertEquals(edgeConfig.testUserEmail, "test@example.com");
    assertEquals(edgeConfig.testUserPassword, "test-password");
  },
  sanitizeOps: false,
  sanitizeResources: false
});

Deno.test({
  name: "environment configuration - missing required fields",
  async fn() {
    // Start with a clean environment
    resetEnvironment();
    
    // Set minimal environment without required fields
    Deno.env.set("NODE_ENV", "test");
    Deno.env.set("ENV_LEVEL", "test");

    // Should throw when required fields are missing
    await assertRejects(
      async () => {
        const { edgeConfigPromise } = await import("@shared/environment.ts?test=missing");
        await edgeConfigPromise;
      },
      Error,
      "Missing required configuration fields"
    );
  },
  sanitizeOps: false,
  sanitizeResources: false
});

Deno.test({
  name: "environment configuration - optional fields",
  async fn() {
    // Start with a clean environment
    resetEnvironment();
    
    // Set test environment with only required fields
    Deno.env.set("NODE_ENV", "test");
    Deno.env.set("ENV_LEVEL", "test");
    Deno.env.set("SUPABASE_URL", "https://test.supabase.co");
    Deno.env.set("SUPABASE_SERVICE_ROLE_KEY", "test-key");
    Deno.env.set("OPENAI_API_KEY", "test-openai-key");

    // Import config after environment is set up
    const { edgeConfig } = await import("@shared/environment.ts?test=optional");

    // Optional fields should be undefined
    assertEquals(edgeConfig.llamaparseApiKey, undefined);
    assertEquals(edgeConfig.anthropicApiKey, undefined);
  },
  sanitizeOps: false,
  sanitizeResources: false
});

Deno.test({
  name: "environment configuration - production settings",
  async fn() {
    // Start with a clean environment
    resetEnvironment();
    
    // Simulate production environment
    Deno.env.set("SUPABASE_FUNCTION_NAME", "test-function");
    Deno.env.set("ENV_LEVEL", "production");
    Deno.env.set("SUPABASE_URL", "https://prod.supabase.co");
    Deno.env.set("SUPABASE_SERVICE_ROLE_KEY", "prod-key");
    Deno.env.set("OPENAI_API_KEY", "prod-openai-key");

    // Import config after environment is set up
    const { edgeConfig } = await import("@shared/environment.ts?test=prod");

    // Test production-specific settings
    assertEquals(edgeConfig.environment, "production");
    assertEquals(edgeConfig.logLevel, "INFO");
    assertEquals(edgeConfig.enableVectorProcessing, false);
    assertEquals(edgeConfig.enableRegulatoryProcessing, false);

    // Test credentials are loaded from environment
    assertEquals(edgeConfig.supabaseUrl, "https://prod.supabase.co");
    assertEquals(edgeConfig.supabaseKey, "prod-key");
    assertEquals(edgeConfig.openaiApiKey, "prod-openai-key");

    // Test-specific fields should be undefined in production
    assertEquals(edgeConfig.testUserId, undefined);
    assertEquals(edgeConfig.testUserEmail, undefined);
    assertEquals(edgeConfig.testUserPassword, undefined);
  },
  sanitizeOps: false,
  sanitizeResources: false
}); 