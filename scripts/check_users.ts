import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.SUPABASE_URL || 'https://jhrespvvhbnloxrieycf.supabase.co'
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || ''

const supabase = createClient(supabaseUrl, supabaseServiceKey)

async function checkUsers() {
  console.log('Checking users...')
  
  const { data: publicUsers, error: publicError } = await supabase
    .from('users')
    .select('*')
    .eq('id', '11111111-1111-1111-1111-111111111111')

  if (publicError) {
    console.error('Error fetching from public.users:', publicError)
  } else {
    console.log('public.users:', publicUsers)
  }

  const { data: authUsers, error: authError } = await supabase
    .auth.admin.listUsers()

  if (authError) {
    console.error('Error fetching from auth.users:', authError)
  } else {
    console.log('auth.users:', authUsers)
  }
}

checkUsers().catch(console.error) 

const supabaseUrl = process.env.SUPABASE_URL || 'https://jhrespvvhbnloxrieycf.supabase.co'
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || ''

const supabase = createClient(supabaseUrl, supabaseServiceKey)

async function checkUsers() {
  console.log('Checking users...')
  
  const { data: publicUsers, error: publicError } = await supabase
    .from('users')
    .select('*')
    .eq('id', '11111111-1111-1111-1111-111111111111')

  if (publicError) {
    console.error('Error fetching from public.users:', publicError)
  } else {
    console.log('public.users:', publicUsers)
  }

  const { data: authUsers, error: authError } = await supabase
    .auth.admin.listUsers()

  if (authError) {
    console.error('Error fetching from auth.users:', authError)
  } else {
    console.log('auth.users:', authUsers)
  }
}

checkUsers().catch(console.error) 