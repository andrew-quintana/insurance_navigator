import { assertEquals, assertRejects } from "https://deno.land/std/testing/asserts.ts";

// Store original env vars to restore after tests
const originalEnv = {
  NODE_ENV: Deno.env.get("NODE_ENV"),
  ENV_LEVEL: Deno.env.get("ENV_LEVEL"),
  ENV_FILE_OVERRIDE: Deno.env.get("ENV_FILE_OVERRIDE"),
  SUPABASE_URL: Deno.env.get("SUPABASE_URL"),
  SUPABASE_SERVICE_ROLE_KEY: Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"),
  OPENAI_API_KEY: Deno.env.get("OPENAI_API_KEY")
};

// Helper to reset environment to a clean state
function resetEnvironment() {
  // Clear all relevant env vars
  Object.keys(originalEnv).forEach(key => {
    try {
      Deno.env.delete(key);
    } catch (error) {
      console.warn(`Failed to delete ${key}:`, error);
    }
  });
  
  // Clear any existing override
  try {
    Deno.env.delete("ENV_FILE_OVERRIDE");
  } catch (error) {
    console.warn("Failed to delete ENV_FILE_OVERRIDE:", error);
  }
}

Deno.test({
  name: "environment configuration - override file test",
  async fn() {
    // Start with a clean environment
    resetEnvironment();
    
    // Create temporary bogey env file
    const bogeyContent = `
NODE_ENV=test
ENV_LEVEL=test
SUPABASE_URL=https://bogey.supabase.co
SUPABASE_SERVICE_ROLE_KEY=bogey-key-123
OPENAI_API_KEY=bogey-openai-key-456
TEST_USER_ID=bogey-user-123
TEST_USER_EMAIL=bogey@test.com
TEST_USER_PASSWORD=bogey-pass-789
ENABLE_VECTOR_PROCESSING=false
ENABLE_REGULATORY_PROCESSING=false
LLAMAPARSE_API_KEY=bogey-llama-key
ANTHROPIC_API_KEY=bogey-claude-key
    `.trim();

    // Ensure fixtures directory exists
    try {
      await Deno.mkdir("tests/fixtures", { recursive: true });
    } catch (error) {
      if (!(error instanceof Deno.errors.AlreadyExists)) {
        throw error;
      }
    }

    // Write temporary bogey file
    const envPath = "tests/fixtures/env.bogey";
    await Deno.writeTextFile(envPath, bogeyContent);

    try {
      // Set up bogey environment values
      Deno.env.set("ENV_FILE_OVERRIDE", envPath);
      
      // For debugging
      console.log("ENV_FILE_OVERRIDE set to:", Deno.env.get("ENV_FILE_OVERRIDE"));
      console.log("Bogey file contents:", await Deno.readTextFile(envPath));

      // Import config after environment is set up
      const { edgeConfig } = await import("../../supabase/functions/_shared/environment.ts?test=override");

      // For debugging
      console.log("Loaded config:", {
        supabaseUrl: edgeConfig.supabaseUrl,
        supabaseKey: edgeConfig.supabaseKey,
        openaiApiKey: edgeConfig.openaiApiKey
      });

      // Test that bogey values were loaded
      assertEquals(edgeConfig.supabaseUrl, "https://bogey.supabase.co");
      assertEquals(edgeConfig.supabaseKey, "bogey-key-123");
      assertEquals(edgeConfig.openaiApiKey, "bogey-openai-key-456");
      assertEquals(edgeConfig.testUserId, "bogey-user-123");
      assertEquals(edgeConfig.testUserEmail, "bogey@test.com");
      assertEquals(edgeConfig.llamaparseApiKey, "bogey-llama-key");
      assertEquals(edgeConfig.anthropicApiKey, "bogey-claude-key");
      assertEquals(edgeConfig.enableVectorProcessing, false);
      assertEquals(edgeConfig.enableRegulatoryProcessing, false);
    } finally {
      // Clean up temporary file
      try {
        await Deno.remove(envPath);
      } catch (error) {
        console.warn("Failed to clean up bogey file:", error);
      }
    }
  },
  sanitizeOps: false,
  sanitizeResources: false
}); 