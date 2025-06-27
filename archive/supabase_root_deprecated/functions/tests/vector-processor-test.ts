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

// Test data for documents
const testRegulatoryDoc = {
  original_filename: 'Test CMS Coverage Decision',
  storage_path: 'https://test.cms.gov/article/12345',
  document_type: 'regulatory',
  jurisdiction: 'federal',
  program: ['medicare'],
  source_url: 'https://test.cms.gov/article/12345',
  source_last_checked: new Date().toISOString(),
  priority_score: 1.0,
  metadata: {
    processing_timestamp: new Date().toISOString(),
    source_method: 'test',
    content_length: 100,
    extraction_method: 'test'
  },
  tags: ['medicare', 'coverage'],
  status: 'pending'
}

const testUserDoc = {
  original_filename: 'test-user-doc.pdf',
  storage_path: 'test/path/doc.pdf',
  document_type: 'user_uploaded',
  jurisdiction: 'United States',
  program: ['Healthcare', 'General'],
  source_url: null,
  source_last_checked: new Date().toISOString(),
  priority_score: 1.0,
  metadata: {
    processing_timestamp: new Date().toISOString(),
    source_method: 'test',
    content_length: 100,
    extraction_method: 'test'
  },
  tags: ['test'],
  status: 'pending'
}

const testVectorProcessorRegulatoryDocument = async () => {
  console.log('🧪 Testing vector-processor with regulatory document...')
  
  const serviceClient = createClient(supabaseUrl, serviceRoleKey, options)
  
  // Create test document
  const { data: doc, error: docError } = await serviceClient
    .from('documents')
    .insert({
      ...testRegulatoryDoc,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    })
    .select()
    .single()

  if (docError) {
    console.error('❌ Failed to create test document:', docError)
    throw new Error('Test setup failed: ' + docError.message)
  }

  console.log('✅ Test document created:', doc.id)

  try {
    // Test the vector-processor function
    const { data: response, error: funcError } = await serviceClient.functions.invoke('vector-processor', {
      body: {
        documentId: doc.id,
        extractedText: 'This is a test regulatory document about Medicare coverage policies. It contains important information about coverage criteria and limitations.',
        documentType: 'regulatory',
        metadata: {
          jurisdiction: 'federal',
          programs: ['medicare'],
          tags: ['medicare', 'coverage']
        }
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
      .eq('document_id', doc.id)
      .eq('document_source_type', 'regulatory')

    if (vectorError) {
      console.error('❌ Failed to verify vectors:', vectorError)
      throw new Error('Vector verification failed: ' + vectorError.message)
    }

    assertExists(vectors, 'Vectors should exist')
    assert(vectors.length > 0, 'At least one vector should be created')
    
    // Clean up test data
    await serviceClient
      .from('document_vectors')
      .delete()
      .eq('document_id', doc.id)

    await serviceClient
      .from('documents')
      .delete()
      .eq('id', doc.id)

    console.log('🧹 Test data cleaned up')

  } catch (error) {
    // Clean up test data even if test fails
    try {
      await serviceClient
        .from('document_vectors')
        .delete()
        .eq('document_id', doc.id)

      await serviceClient
        .from('documents')
        .delete()
        .eq('id', doc.id)
    } catch (cleanupError) {
      console.error('❌ Failed to clean up test data:', cleanupError)
    }

    throw error
  }
}

const testVectorProcessorUserDocument = async () => {
  console.log('🧪 Testing vector-processor with user document...')
  
  const serviceClient = createClient(supabaseUrl, serviceRoleKey, options)
  
  // Create test document
  const { data: doc, error: docError } = await serviceClient
    .from('documents')
    .insert({
      ...testUserDoc,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    })
    .select()
    .single()

  if (docError) {
    console.error('❌ Failed to create test document:', docError)
    throw new Error('Test setup failed: ' + docError.message)
  }

  console.log('✅ Test document created:', doc.id)

  try {
    // Test the vector-processor function
    const { data: response, error: funcError } = await serviceClient.functions.invoke('vector-processor', {
      body: {
        documentId: doc.id,
        extractedText: 'This is test user document content that should be processed into vectors.',
        documentType: 'user_uploaded',
        metadata: {
          jurisdiction: 'United States',
          programs: ['Healthcare', 'General'],
          tags: ['test']
        }
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
      .eq('document_id', doc.id)
      .eq('document_source_type', 'user_uploaded')

    if (vectorError) {
      console.error('❌ Failed to verify vectors:', vectorError)
      throw new Error('Vector verification failed: ' + vectorError.message)
    }

    assertExists(vectors, 'Vectors should exist')
    assert(vectors.length > 0, 'At least one vector should be created')
    
    // Clean up test data
    await serviceClient
      .from('document_vectors')
      .delete()
      .eq('document_id', doc.id)

    await serviceClient
      .from('documents')
      .delete()
      .eq('id', doc.id)

    console.log('🧹 Test data cleaned up')

  } catch (error) {
    // Clean up test data even if test fails
    try {
      await serviceClient
        .from('document_vectors')
        .delete()
        .eq('document_id', doc.id)

      await serviceClient
        .from('documents')
        .delete()
        .eq('id', doc.id)
    } catch (cleanupError) {
      console.error('❌ Failed to clean up test data:', cleanupError)
    }

    throw error
  }
}

Deno.test('Vector Processor - Regulatory Document Test', testVectorProcessorRegulatoryDocument)
Deno.test('Vector Processor - User Document Test', testVectorProcessorUserDocument)