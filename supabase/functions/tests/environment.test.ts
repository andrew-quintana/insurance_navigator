import { assertEquals, assertRejects } from "std/assert/mod.ts";
import { edgeConfig } from "_shared/environment.ts";

Deno.test("Environment Configuration", async (t) => {
  await t.step("loads test environment correctly", async () => {
    const config = await edgeConfig;
    assertEquals(config.environment, "test");
    assertEquals(typeof config.supabaseUrl, "string");
    assertEquals(typeof config.supabaseKey, "string");
    assertEquals(typeof config.openaiApiKey, "string");
    assertEquals(typeof config.testUserId, "string");
    assertEquals(typeof config.testUserEmail, "string");
    assertEquals(typeof config.testUserPassword, "string");
  });

  await t.step("enables non-production features in test", async () => {
    const config = await edgeConfig;
    assertEquals(config.enableVectorProcessing, true);
    assertEquals(config.enableRegulatoryProcessing, true);
    assertEquals(config.logLevel, "DEBUG");
  });

  await t.step("validates required fields", async () => {
    const env = Deno.env.toObject();
    Deno.env.delete("SUPABASE_URL");
    Deno.env.delete("SUPABASE_SERVICE_ROLE_KEY");
    
    await assertRejects(
      async () => await edgeConfig,
      Error,
      "Missing required configuration fields"
    );

    // Restore environment
    for (const [key, value] of Object.entries(env)) {
      Deno.env.set(key, value);
    }
  });
}); 