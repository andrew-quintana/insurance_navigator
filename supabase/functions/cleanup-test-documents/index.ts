import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.7.1'
import { edgeConfig } from "../_  shared/environment";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      edgeConfig.supabaseUrl,
      edgeConfig.supabaseKey
    )

    // Delete test users
    const { error: userError } = await supabaseClient
      .from('users')
      .delete()
      .like('email', 'test%@example.com')

    if (userError) throw userError

    // Delete test documents
    const { error: docError } = await supabaseClient
      .from('documents')
      .delete()
      .eq('is_test', true)

    if (docError) throw docError

    return new Response(
      JSON.stringify({ message: 'Test data cleaned successfully' }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500,
      }
    )
  }
}) 