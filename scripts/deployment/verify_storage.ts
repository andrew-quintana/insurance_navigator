import { createClient } from '@supabase/supabase-js'
import * as fs from 'fs'
import * as path from 'path'

// Load environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing required environment variables')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseKey)

async function verifyStorage() {
  console.log('Starting storage verification...')

  try {
    // Create test file
    const testFile = new Uint8Array(Buffer.from('test content'))
    const testFileName = `test-${Date.now()}.txt`

    // Test upload
    console.log('Testing upload...')
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('documents')
      .upload(testFileName, testFile)

    if (uploadError) {
      throw new Error(`Upload failed: ${uploadError.message}`)
    }
    console.log('Upload successful:', uploadData)

    // Test download
    console.log('Testing download...')
    const { data: downloadData, error: downloadError } = await supabase.storage
      .from('documents')
      .download(testFileName)

    if (downloadError) {
      throw new Error(`Download failed: ${downloadError.message}`)
    }
    console.log('Download successful')

    // Test deletion
    console.log('Testing deletion...')
    const { error: deleteError } = await supabase.storage
      .from('documents')
      .remove([testFileName])

    if (deleteError) {
      throw new Error(`Deletion failed: ${deleteError.message}`)
    }
    console.log('Deletion successful')

    console.log('All storage tests passed!')
    return true
  } catch (error) {
    console.error('Storage verification failed:', error)
    return false
  }
}

// Run verification
verifyStorage()
  .then(success => process.exit(success ? 0 : 1))
  .catch(error => {
    console.error('Unexpected error:', error)
    process.exit(1)
  }) 