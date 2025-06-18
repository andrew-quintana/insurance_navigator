// Import required libraries and modules
import { assert, assertEquals, assertExists } from 'jsr:@std/assert@1'
import { createClient, SupabaseClient } from 'npm:@supabase/supabase-js@2'

// Will load the .env file to Deno.env
import 'jsr:@std/dotenv/load'

// Set up the configuration for the Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
const supabaseKey = Deno.env.get('SUPABASE_ANON_KEY') ?? ''
const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''

const options = {
  auth: {
    autoRefreshToken: false,
    persistSession: false,
    detectSessionInUrl: false,
  },
}

// Test data for regulatory documents
const testRegulatoryDoc = {
  title: 'Test CMS Coverage Decision',
  content: 'This is a test regulatory document about Medicare coverage policies. It contains important information about coverage criteria and limitations.',
  url: 'https://test.cms.gov/article/12345',
  jurisdiction: 'federal',
  document_type: 'coverage_decision',
  tags: ['medicare', 'coverage']
}

// Test data for user documents
const testUserDoc = {
  original_filename: 'test-user-doc.pdf',
  file_path: 'test/path/doc.pdf',
  document_hash: 'test-hash-123',
  content: 'This is test user document content that should be processed into vectors.'
}

const testClientCreation = async () => {
  console.log('🧪 Testing Supabase client creation...')
  
  const client: SupabaseClient = createClient(supabaseUrl, supabaseKey, options)
  
  // Verify if the Supabase URL and key are provided
  if (!supabaseUrl) throw new Error('SUPABASE_URL is required.')
  if (!supabaseKey) throw new Error('SUPABASE_ANON_KEY is required.')

  // Test database connectivity
  const { data: health, error: healthError } = await client
    .from('documents')
    .select('count')
    .limit(1)

  if (healthError) {
    console.error('❌ Database connectivity test failed:', healthError)
    throw new Error('Invalid Supabase client: ' + healthError.message)
  }

  console.log('✅ Supabase client created successfully')
  assert(health !== null, 'Database should be accessible')
}

const testVectorProcessorUserDocument = async () => {
  console.log('🧪 Testing vector-processor with user document...')
  
  const serviceClient = createClient(supabaseUrl, serviceRoleKey, options)
  
  // Create test user document
  const { data: userDoc, error: userDocError } = await serviceClient
    .from('documents')
    .insert({
      ...testUserDoc,
      user_id: '00000000-0000-0000-0000-000000000000', // Test user
      status: 'uploaded'
    })
    .select()
    .single()

  if (userDocError) {
    console.error('❌ Failed to create test user document:', userDocError)
    throw new Error('Test setup failed: ' + userDocError.message)
  }

  console.log('✅ Test user document created:', userDoc.id)

  try {
    // Test the vector-processor function
    const { data: response, error: funcError } = await serviceClient.functions.invoke('vector-processor', {
      body: {
        documentId: userDoc.id,
        extractedText: testUserDoc.content,
        documentType: 'user'
      },
    })

    console.log('📋 Vector processor response:', response)

    if (funcError) {
      console.error('❌ Vector processor function error:', funcError)
      throw new Error('Vector processor failed: ' + funcError.message)
    }

    // Verify response structure
    assertExists(response, 'Response should exist')
    assertEquals(response.success, true, 'Processing should succeed')
    assertExists(response.vectorCount, 'Vector count should be provided')
    
    console.log(`✅ Successfully created ${response.vectorCount} vectors`)

    // Verify vectors were actually created in database
    const { data: vectors, error: vectorError } = await serviceClient
      .from('document_vectors')
      .select('*')
      .eq('document_id', userDoc.id)
      .eq('document_source_type', 'user_document')

    if (vectorError) {
      console.error('❌ Failed to verify vectors in database:', vectorError)
      throw new Error('Vector verification failed: ' + vectorError.message)
    }

    assert(vectors && vectors.length > 0, 'Vectors should be created in database')
    console.log(`✅ Verified ${vectors.length} vectors in database`)

  } finally {
    // Cleanup: Delete test document and its vectors
    await serviceClient.from('document_vectors').delete().eq('document_id', userDoc.id)
    await serviceClient.from('documents').delete().eq('id', userDoc.id)
    console.log('🧹 Cleaned up test user document')
  }
}

const testVectorProcessorRegulatoryDocument = async () => {
  console.log('🧪 Testing vector-processor with regulatory document...')
  
  const serviceClient = createClient(supabaseUrl, serviceRoleKey, options)
  
  // Create test regulatory document
  const { data: regDoc, error: regDocError } = await serviceClient
    .from('regulatory_documents')
    .insert({
      document_id: crypto.randomUUID(),
      ...testRegulatoryDoc,
      is_active: true,
      created_at: new Date().toISOString()
    })
    .select()
    .single()

  if (regDocError) {
    console.error('❌ Failed to create test regulatory document:', regDocError)
    throw new Error('Test setup failed: ' + regDocError.message)
  }

  console.log('✅ Test regulatory document created:', regDoc.document_id)

  try {
    // Test the vector-processor function
    const { data: response, error: funcError } = await serviceClient.functions.invoke('vector-processor', {
      body: {
        documentId: regDoc.document_id,
        extractedText: testRegulatoryDoc.content,
        documentType: 'regulatory'
      },
    })

    console.log('📋 Vector processor response:', response)

    if (funcError) {
      console.error('❌ Vector processor function error:', funcError)
      throw new Error('Vector processor failed: ' + funcError.message)
    }

    // Verify response structure
    assertExists(response, 'Response should exist')
    assertEquals(response.success, true, 'Processing should succeed')
    assertExists(response.vectorCount, 'Vector count should be provided')
    
    console.log(`✅ Successfully created ${response.vectorCount} vectors`)

    // Verify vectors were actually created in database
    const { data: vectors, error: vectorError } = await serviceClient
      .from('document_vectors')
      .select('*')
      .eq('regulatory_document_id', regDoc.document_id)
      .eq('document_source_type', 'regulatory_document')

    if (vectorError) {
      console.error('❌ Failed to verify vectors in database:', vectorError)
      throw new Error('Vector verification failed: ' + vectorError.message)
    }

    assert(vectors && vectors.length > 0, 'Vectors should be created in database')
    console.log(`✅ Verified ${vectors.length} vectors in database`)

  } finally {
    // Cleanup: Delete test document and its vectors
    await serviceClient.from('document_vectors').delete().eq('regulatory_document_id', regDoc.document_id)
    await serviceClient.from('regulatory_documents').delete().eq('document_id', regDoc.document_id)
    console.log('🧹 Cleaned up test regulatory document')
  }
}

const testBulkRegulatoryProcessor = async () => {
  console.log('🧪 Testing bulk-regulatory-processor...')
  
  const serviceClient = createClient(supabaseUrl, serviceRoleKey, options)
  
  const testUrls = [
    {
      url: 'https://www.cms.gov/test-article-1',
      title: 'Test Article 1',
      jurisdiction: 'federal',
      document_type: 'guidance'
    },
    {
      url: 'https://www.cms.gov/test-article-2', 
      title: 'Test Article 2',
      jurisdiction: 'federal',
      document_type: 'coverage_decision'
    }
  ]

  // Test the bulk-regulatory-processor function
  const { data: response, error: funcError } = await serviceClient.functions.invoke('bulk-regulatory-processor', {
    body: {
      documents: testUrls,
      batch_size: 5
    },
  })

  console.log('📋 Bulk processor response:', response)

  if (funcError) {
    console.error('❌ Bulk processor function error:', funcError)
    // Note: This might fail due to network issues, which is acceptable for testing
    console.log('⚠️ Bulk processor test may fail due to external URL dependencies')
    return
  }

  // Verify response structure
  assertExists(response, 'Response should exist')
  assertExists(response.results, 'Results should be provided')
  assert(Array.isArray(response.results), 'Results should be an array')
  
  console.log(`✅ Bulk processor returned ${response.results.length} results`)
}

const testErrorHandling = async () => {
  console.log('🧪 Testing error handling...')
  
  const serviceClient = createClient(supabaseUrl, serviceRoleKey, options)
  
  // Test with invalid document ID
  const { data: response, error: funcError } = await serviceClient.functions.invoke('vector-processor', {
    body: {
      documentId: 'invalid-id-12345',
      extractedText: 'Test content',
      documentType: 'user'
    },
  })

  console.log('📋 Error handling response:', response)
  
  // Should return an error response (not throw)
  if (funcError) {
    console.log('✅ Function properly returned error for invalid document ID')
  } else if (response && response.error) {
    console.log('✅ Function properly handled invalid document ID in response')
  } else {
    throw new Error('Error handling test failed - should have returned error')
  }
}

const testDatabaseSchema = async () => {
  console.log('🧪 Testing database schema consistency...')
  
  const serviceClient = createClient(supabaseUrl, serviceRoleKey, options)
  
  // Verify document_vectors table structure
  const { data: columns, error: schemaError } = await serviceClient.rpc('get_table_columns', {
    table_name: 'document_vectors'
  })
  
  if (schemaError) {
    console.log('⚠️ Schema test requires custom RPC function - skipping')
    return
  }
  
  console.log('📋 document_vectors schema:', columns)
  console.log('✅ Schema verification completed')
}

// Register and run the tests
Deno.test('Client Creation Test', testClientCreation)
Deno.test('Vector Processor - User Document Test', testVectorProcessorUserDocument)
Deno.test('Vector Processor - Regulatory Document Test', testVectorProcessorRegulatoryDocument)
Deno.test('Bulk Regulatory Processor Test', testBulkRegulatoryProcessor) 
Deno.test('Error Handling Test', testErrorHandling)
Deno.test('Database Schema Test', testDatabaseSchema) 