import { createClient, SupabaseClient } from '@supabase/supabase-js'
import { join, dirname, fromFileUrl } from "https://deno.land/std@0.217.0/path/mod.ts";
import { load } from "https://deno.land/std@0.217.0/dotenv/mod.ts";

// Get project root directory
export function getProjectRoot(): string {
  const currentDir = new URL(".", import.meta.url).pathname;
  return join(currentDir, "..", "..", "..");
}

// Load environment variables based on current environment
export async function loadEnvironment() {
  const projectRoot = getProjectRoot();
  const env = Deno.env.get("ENV") || "test";
  
  // Define environment file priorities
  const envFiles = [
    `.env.${env}.local`,  // First priority: environment-specific local overrides
    `.env.${env}`,        // Second priority: environment-specific defaults
    '.env.local',         // Third priority: local overrides
    '.env'                // Fourth priority: default fallback
  ];
  
  // Load each env file in order of priority
  for (const file of envFiles) {
    try {
      const envPath = join(projectRoot, file);
      const fileInfo = await Deno.stat(envPath);
      
      if (fileInfo.isFile) {
        console.log(`Loading environment from ${file}`);
        const env = await load({ envPath });
        
        // Set environment variables
        for (const [key, value] of Object.entries(env)) {
          if (!Deno.env.get(key)) {  // Don't override existing env vars
            Deno.env.set(key, value);
          }
        }
      }
    } catch (error) {
      if (!(error instanceof Deno.errors.NotFound)) {
        console.warn(`Warning: Error loading ${file}:`, error);
      }
    }
  }
  
  // Validate required environment variables
  const requiredVars = [
    'SUPABASE_URL',
    'SUPABASE_SERVICE_ROLE_KEY',
    'OPENAI_API_KEY',
    'LLAMAPARSE_API_KEY'
  ];
  
  const missingVars = requiredVars.filter(varName => !Deno.env.get(varName));
  if (missingVars.length > 0) {
    throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
  }
}

// Initialize test client with proper configuration
export async function initializeTestClient() {
  await loadEnvironment();
  
  const supabaseUrl = Deno.env.get('SUPABASE_URL');
  const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  
  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Failed to initialize test client: Missing Supabase configuration');
  }
  
  return createClient(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
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

export async function getEdgeFunctionLogs(client: SupabaseClient, functionName: string, requestId?: string) {
  try {
    let query = client
      .schema('monitoring')
      .from('edge_function_logs')
      .select('*')
      .eq('function_name', functionName)
      .order('created_at', { ascending: false });

    if (requestId) {
      query = query.eq('request_id', requestId);
    }

    const { data, error } = await query.limit(10);
    
    if (error) {
      console.error('Failed to fetch edge function logs:', error);
      return [];
    }

    return data;
  } catch (error) {
    console.error('Error fetching edge function logs:', error);
    return [];
  }
} 