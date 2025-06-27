import { createClient } from '@supabase/supabase-js'
import * as fs from 'fs'
import * as path from 'path'

// Configuration
const SUPABASE_URL = process.env.SUPABASE_URL || ''
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || ''
const TEST_FILE_PATH = path.join(__dirname, '..', 'test.pdf')

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error('Missing required environment variables')
  process.exit(1)
}

async function testJobProcessor() {
  try {
    // Initialize Supabase client
    const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

    // Sign up a test user
    const { data: authData, error: authError } = await supabase.auth.signUp({
      email: `test${Date.now()}@example.com`,
      password: 'test123!@#'
    })

    if (authError) {
      throw new Error(`Auth failed: ${authError.message}`)
    }

    // Read test file
    const fileData = fs.readFileSync(TEST_FILE_PATH)
    const base64Data = fileData.toString('base64')

    // Call job processor
    const response = await fetch(`${SUPABASE_URL}/functions/v1/job-processor`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authData.session?.access_token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        file: {
          name: 'test.pdf',
          type: 'application/pdf',
          size: fileData.length,
          data: base64Data
        },
        metadata: {
          documentType: 'test',
          tags: ['test']
        }
      })
    })

    if (!response.ok) {
      throw new Error(`Job processor failed: ${await response.text()}`)
    }

    const result = await response.json()
    console.log('Job created:', result)

    // Poll for job completion
    const maxAttempts = 30
    let attempts = 0
    while (attempts < maxAttempts) {
      const { data: job, error: jobError } = await supabase
        .from('jobs')
        .select('*')
        .eq('id', result.jobId)
        .single()

      if (jobError) {
        throw new Error(`Failed to fetch job: ${jobError.message}`)
      }

      console.log(`Job status: ${job.status}`)
      
      if (job.status === 'COMPLETED') {
        console.log('Job completed successfully!')
        break
      }

      if (['UPLOAD_FAILED', 'PARSE_FAILED', 'VECTORIZE_FAILED'].includes(job.status)) {
        throw new Error(`Job failed with status ${job.status}: ${job.error_message}`)
      }

      await new Promise(resolve => setTimeout(resolve, 2000))
      attempts++
    }

    if (attempts >= maxAttempts) {
      throw new Error('Job timed out')
    }

  } catch (error) {
    console.error('Test failed:', error)
    process.exit(1)
  }
}

testJobProcessor().catch(console.error) 
import * as fs from 'fs'
import * as path from 'path'

// Configuration
const SUPABASE_URL = process.env.SUPABASE_URL || ''
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || ''
const TEST_FILE_PATH = path.join(__dirname, '..', 'test.pdf')

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error('Missing required environment variables')
  process.exit(1)
}

async function testJobProcessor() {
  try {
    // Initialize Supabase client
    const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

    // Sign up a test user
    const { data: authData, error: authError } = await supabase.auth.signUp({
      email: `test${Date.now()}@example.com`,
      password: 'test123!@#'
    })

    if (authError) {
      throw new Error(`Auth failed: ${authError.message}`)
    }

    // Read test file
    const fileData = fs.readFileSync(TEST_FILE_PATH)
    const base64Data = fileData.toString('base64')

    // Call job processor
    const response = await fetch(`${SUPABASE_URL}/functions/v1/job-processor`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authData.session?.access_token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        file: {
          name: 'test.pdf',
          type: 'application/pdf',
          size: fileData.length,
          data: base64Data
        },
        metadata: {
          documentType: 'test',
          tags: ['test']
        }
      })
    })

    if (!response.ok) {
      throw new Error(`Job processor failed: ${await response.text()}`)
    }

    const result = await response.json()
    console.log('Job created:', result)

    // Poll for job completion
    const maxAttempts = 30
    let attempts = 0
    while (attempts < maxAttempts) {
      const { data: job, error: jobError } = await supabase
        .from('jobs')
        .select('*')
        .eq('id', result.jobId)
        .single()

      if (jobError) {
        throw new Error(`Failed to fetch job: ${jobError.message}`)
      }

      console.log(`Job status: ${job.status}`)
      
      if (job.status === 'COMPLETED') {
        console.log('Job completed successfully!')
        break
      }

      if (['UPLOAD_FAILED', 'PARSE_FAILED', 'VECTORIZE_FAILED'].includes(job.status)) {
        throw new Error(`Job failed with status ${job.status}: ${job.error_message}`)
      }

      await new Promise(resolve => setTimeout(resolve, 2000))
      attempts++
    }

    if (attempts >= maxAttempts) {
      throw new Error('Job timed out')
    }

  } catch (error) {
    console.error('Test failed:', error)
    process.exit(1)
  }
}

testJobProcessor().catch(console.error) 