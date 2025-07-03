import { createClient, SupabaseClient } from '@supabase/supabase-js'
import { join, dirname, fromFileUrl } from "https://deno.land/std@0.217.0/path/mod.ts";

// Get project root helper
export function getProjectRoot(): string {
  // Get the directory containing the test file
  const testDir = dirname(fromFileUrl(import.meta.url));
  // Go up two levels to get to the project root (from tests/ to functions/)
  return join(testDir, "..");
}

export async function initializeTestClient() {
  const projectRoot = getProjectRoot();
  const envPath = join(projectRoot, "tests", ".env.test");
  
  try {
    const env = await Deno.readTextFile(envPath);
    for (const line of env.split("\n")) {
      const [key, value] = line.split("=");
      if (key && value) {
        Deno.env.set(key.trim(), value.trim());
      }
    }
  } catch (error) {
    console.error("Failed to load .env.test file:", error);
    console.error("Attempted path:", envPath);
    throw error;
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

  if (!supabaseUrl || !supabaseKey) {
    throw new Error("Missing required environment variables");
  }

  return createClient(supabaseUrl, supabaseKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
      detectSessionInUrl: false
    }
  });
}

// Test configuration
const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''

export const createTestClient = () => {
  if (!supabaseUrl) throw new Error('supabaseUrl is required.')
  if (!supabaseKey) throw new Error('supabaseKey is required.')

  return createClient(supabaseUrl, supabaseKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
      detectSessionInUrl: false,
    },
  })
}

export const createTestDocument = async (client: SupabaseClient, userId: string) => {
  const { data, error } = await client
    .from('documents')
    .insert({
      user_id: userId,
      filename: 'test.pdf',
      content_type: 'application/pdf',
      status: 'uploaded',
      storage_path: 'test/test.pdf'
    })
    .select()
    .single()

  if (error) throw error
  return data
}

export const cleanupTestData = async (client: SupabaseClient) => {
  // Clean up test documents
  const { error: docError } = await client
    .from('documents')
    .delete()
    .eq('filename', 'test.pdf')

  if (docError) console.error('Error cleaning up test documents:', docError)

  // Clean up test users
  const { error: userError } = await client
    .from('users')
    .delete()
    .like('email', 'test%@example.com')

  if (userError) console.error('Error cleaning up test users:', userError)

  // Clean up storage
  const { data: files, error: listError } = await client.storage
    .from('documents')
    .list('test')

  if (!listError && files) {
    for (const file of files) {
      const { error: deleteError } = await client.storage
        .from('documents')
        .remove([`test/${file.name}`])

      if (deleteError) console.error(`Error deleting file ${file.name}:`, deleteError)
    }
  }

  // Clean up processing jobs
  const { error: jobError } = await client
    .from('processing_jobs')
    .delete()
    .eq('status', 'test')

  if (jobError) console.error('Error cleaning up processing jobs:', jobError)

  // Clean up audit logs for test documents
  const { error: auditError } = await client
    .from('audit_logs')
    .delete()
    .like('document_id', 'test%')

  if (auditError) console.error('Error cleaning up audit logs:', auditError)
}

export const setupTestHooks = () => {
  const client = createTestClient()

  // Before each test
  Deno.test({
    name: 'beforeEach',
    fn: async () => {
      await cleanupTestData(client)
    },
    sanitizeResources: false,
    sanitizeOps: false,
  })

  // After all tests
  Deno.test({
    name: 'afterAll',
    fn: async () => {
      await cleanupTestData(client)
    },
    sanitizeResources: false,
    sanitizeOps: false,
  })

  return client
}

// Mock API clients
export const mockLlamaParseClient = {
  parseDocument: async (content: string) => {
    return {
      text: "Mocked parsed content",
      metadata: {
        title: "Test Document",
        pages: 1
      }
    }
  }
}

export const mockOpenAIClient = {
  embeddings: {
    create: async (params: any) => {
      return {
        data: [{
          embedding: new Array(1536).fill(0.1),
          index: 0
        }]
      }
    }
  }
} 