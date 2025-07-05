import { assertEquals } from "https://deno.land/std@0.217.0/testing/asserts.ts";
import { edgeConfig } from "../_shared/environment.ts";

Deno.test("Environment Configuration", async (t) => {
  const originalEnv = Deno.env.toObject();

  await t.step("setup", () => {
    Deno.env.set("ENV_LEVEL", "bogey");
    Deno.env.set("SUPABASE_URL", "http://bogey.local:54321");
    Deno.env.set("SUPABASE_SERVICE_ROLE_KEY", "bogey-key");
    Deno.env.set("OPENAI_API_KEY", "bogey-openai-key");
    Deno.env.set("SUPABASE_JWT_SECRET", "bogey-jwt-secret");
    Deno.env.set("TEST_USER_ID", "bogey-user");
    Deno.env.set("TEST_USER_EMAIL", "bogey@example.com");
    Deno.env.set("TEST_USER_PASSWORD", "bogey-password");
  });

  await t.step("loads bogey environment correctly", async () => {
    assertEquals(Deno.env.get("ENV_LEVEL"), "bogey");
    assertEquals(edgeConfig.supabaseUrl, "http://bogey.local:54321");
    assertEquals(edgeConfig.supabaseKey, "bogey-key");
    assertEquals(edgeConfig.testUserId, "bogey-user");
    assertEquals(edgeConfig.testUserEmail, "bogey@example.com");
    assertEquals(edgeConfig.testUserPassword, "bogey-password");
  });

  await t.step("detects runtime environment correctly", () => {
    assertEquals(typeof Deno !== 'undefined', true);
    assertEquals(!!Deno.env.get('SUPABASE_FUNCTION_NAME'), false);
    assertEquals(Deno.env.get('ENV_LEVEL') === 'test' || Deno.env.get('NODE_ENV') === 'test', false);
  });

  await t.step("enables non-production features in bogey environment", async () => {
    assertEquals(edgeConfig.enableVectorProcessing, true);
    assertEquals(edgeConfig.enableRegulatoryProcessing, true);
    assertEquals(edgeConfig.logLevel, "DEBUG");
  });

  await t.step("cleanup", () => {
    // Restore original environment
    for (const [key] of Object.entries(originalEnv)) {
      Deno.env.delete(key);
    }
    for (const [key, value] of Object.entries(originalEnv)) {
      Deno.env.set(key, value);
    }
  });
}); 