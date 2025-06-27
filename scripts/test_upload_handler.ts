import { createClient } from '@supabase/supabase-js'
import { readFileSync } from 'fs'
import { join } from 'path'

// Get environment variables
const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing required environment variables')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseKey)

async function testUploadHandler() {
  try {
    // Read the test PDF
    const filePath = join(process.cwd(), 'examples', 'test_serverless_processing.pdf')
    const fileContent = readFileSync(filePath)
    
    // Create FormData
    const formData = new FormData()
    formData.append('file', new Blob([fileContent], { type: 'application/pdf' }), 'test_serverless_processing.pdf')
    formData.append('userId', '3e2d9e16-b722-4a05-9fc2-f8e4eb5e4cbe')
    
    // Call the upload-handler function
    const { data, error } = await supabase.functions.invoke('upload-handler', {
      body: formData,
    })
    
    if (error) {
      console.error('Error:', error)
      return
    }
    
    console.log('Success:', data)
  } catch (err) {
    console.error('Unexpected error:', err)
  }
}

testUploadHandler() 
 