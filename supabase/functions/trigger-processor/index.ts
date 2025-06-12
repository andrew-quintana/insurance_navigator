import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    if (req.method === 'POST') {
      return await processTriggers(supabase)
    }

    if (req.method === 'GET') {
      return await getTriggerStats(supabase)
    }

    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Trigger processor error:', error)
    return new Response(JSON.stringify({ 
      error: 'Internal server error',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})

async function processTriggers(supabase: any): Promise<Response> {
  console.log('🔄 Processing database triggers...')
  
  try {
    // Call the database function to process pending triggers
    const { data: result, error } = await supabase
      .rpc('process_pending_triggers')

    if (error) {
      console.error('❌ Error processing triggers:', error)
      return new Response(JSON.stringify({ 
        error: 'Failed to process triggers',
        details: error.message 
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    const stats = result?.[0] || { processed_count: 0, success_count: 0, error_count: 0 }
    
    console.log(`✅ Processed ${stats.processed_count} triggers: ${stats.success_count} success, ${stats.error_count} failed`)

    // If we processed triggers successfully, schedule the next periodic trigger
    if (stats.processed_count > 0) {
      await scheduleNextPeriodicTrigger(supabase)
    }

    // Clean up old triggers
    const { data: cleanupResult } = await supabase
      .rpc('cleanup_old_triggers')
    
    if (cleanupResult > 0) {
      console.log(`🧹 Cleaned up ${cleanupResult} old triggers`)
    }

    return new Response(JSON.stringify({ 
      message: 'Triggers processed successfully',
      ...stats,
      cleanedUp: cleanupResult || 0,
      timestamp: new Date().toISOString()
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('❌ Trigger processing failed:', error)
    return new Response(JSON.stringify({ 
      error: 'Trigger processing failed',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
}

async function scheduleNextPeriodicTrigger(supabase: any) {
  try {
    // Create the next periodic trigger
    await supabase
      .rpc('create_processing_trigger', {
        trigger_type_param: 'periodic',
        metadata_param: { interval_seconds: 30 },
        delay_seconds: 30
      })
    
    console.log('⏰ Scheduled next periodic trigger in 30 seconds')
  } catch (error) {
    console.warn('⚠️ Failed to schedule next periodic trigger:', error)
  }
}

async function getTriggerStats(supabase: any): Promise<Response> {
  try {
    // Get trigger statistics
    const { data: stats, error: statsError } = await supabase
      .from('processing_trigger_stats')
      .select('*')

    const { data: pendingTriggers, error: pendingError } = await supabase
      .from('processing_triggers')
      .select('*')
      .eq('status', 'pending')
      .order('scheduled_at', { ascending: true })
      .limit(10)

    const { data: recentTriggers, error: recentError } = await supabase
      .from('processing_triggers')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(20)

    if (statsError || pendingError || recentError) {
      console.error('Error fetching trigger stats:', { statsError, pendingError, recentError })
    }

    return new Response(JSON.stringify({
      stats: stats || [],
      pendingTriggers: pendingTriggers || [],
      recentTriggers: recentTriggers || [],
      timestamp: new Date().toISOString()
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Error getting trigger stats:', error)
    return new Response(JSON.stringify({ 
      error: 'Failed to get trigger stats',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
} 