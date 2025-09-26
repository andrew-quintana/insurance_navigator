import { createClient } from '@supabase/supabase-js'

// Create a single supabase client for interacting with your database
// Use environment variables from the root directory (.env.development, .env.staging, .env.production)
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables. Please check your .env.development, .env.staging, or .env.production file.')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey) 