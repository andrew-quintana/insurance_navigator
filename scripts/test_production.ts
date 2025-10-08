import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.SUPABASE_URL || 'https://your-project.supabase.co'
const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_JWT_TOKEN

async function testUpload() {
  // Test upload endpoint with service role key
  const response = await fetch(`${supabaseUrl}/functions/v1/upload-handler`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${serviceRoleKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      filename: 'test_production.pdf',
      contentType: 'application/pdf',
      fileSize: 1024
    })
  })

  const result = await response.json()
  console.log('Upload response:', result)
}

testUpload().catch(console.error) 