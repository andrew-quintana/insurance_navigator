import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/testing/asserts.ts";
import { delay } from "https://deno.land/std@0.208.0/async/delay.ts";

const FUNCTIONS = [
  "doc-processor",
  "vector-service",
  // Add other functions here
];

const ENVIRONMENTS = ["local", "test", "production"];

interface TestResponse {
  status: number;
  body: any;
}

// Helper to stream process output
async function streamOutput(process: Deno.Process, prefix: string) {
  const decoder = new TextDecoder();
  
  // Stream stdout
  (async () => {
    const stdout = process.stdout!;
    for await (const chunk of stdout.readable) {
      console.log(`${prefix} [stdout]:`, decoder.decode(chunk));
    }
  })();
  
  // Stream stderr
  (async () => {
    const stderr = process.stderr!;
    for await (const chunk of stderr.readable) {
      console.error(`${prefix} [stderr]:`, decoder.decode(chunk));
    }
  })();
}

async function testEndpoint(func: string, endpoint: string = "health"): Promise<TestResponse> {
  const url = `http://localhost:54321/functions/v1/${func}/${endpoint}`;
  console.log(`\nTesting endpoint: ${url}`);
  try {
    const response = await fetch(url);
    const body = await response.json().catch(() => null);
    console.log(`Response status: ${response.status}`);
    if (body) console.log('Response body:', JSON.stringify(body, null, 2));
    return { status: response.status, body };
  } catch (error) {
    console.error(`Error testing endpoint ${url}:`, error);
    throw error;
  }
}

async function setupEnvironment(env: string) {
  console.log(`\n=== Setting up ${env} environment ===`);
  
  // Kill any running function servers
  try {
    const kill = Deno.run({ cmd: ["pkill", "-f", "supabase functions serve"] });
    await kill.status();
    await delay(1000); // Wait for process to fully terminate
  } catch (_) {
    // Ignore errors if no process found
  }
  
  console.log(`Starting functions with .env.${env}...`);
  
  // Start function server with appropriate env file
  const process = Deno.run({
    cmd: ["supabase", "functions", "serve", "--env-file", `../../.env.${env}`, "--no-verify-jwt"],
    stdout: "piped",
    stderr: "piped",
  });

  // Stream output in real-time
  await streamOutput(process, `[${env}]`);
  
  // Wait for server to start
  console.log("Waiting for server to start...");
  await delay(5000);
  
  return process;
}

// Test each function in each environment
for (const env of ENVIRONMENTS) {
  Deno.test({
    name: `Testing functions in ${env} environment`,
    async fn() {
      let process: Deno.Process | null = null;
      
      try {
        process = await setupEnvironment(env);
        
        for (const func of FUNCTIONS) {
          console.log(`\n=== Testing ${func} in ${env} environment ===`);
          
          // Test health endpoint
          console.log("\nTesting health endpoint...");
          const healthResult = await testEndpoint(func);
          assertEquals(healthResult.status, 200, `Health check failed for ${func} in ${env} environment`);
          assertEquals(healthResult.body.status, "healthy");
          assertExists(healthResult.body.timestamp);
          
          // Test environment configuration
          console.log("\nTesting environment configuration...");
          const envResult = await testEndpoint(func, "test-env");
          assertEquals(envResult.status, 200, `Environment test failed for ${func} in ${env} environment`);
          assertEquals(envResult.body.environment, env);
          
          console.log(`\n✓ ${func} tests passed in ${env} environment`);
        }
      } catch (error) {
        console.error(`\n❌ Error in ${env} environment:`, error);
        throw error;
      } finally {
        // Cleanup
        if (process) {
          console.log(`\n=== Cleaning up ${env} environment ===`);
          process.close();
          await delay(1000);
        }
      }
    },
    sanitizeOps: false,
    sanitizeResources: false,
  });
} 