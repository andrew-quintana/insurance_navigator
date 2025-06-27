import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};
serve(async (req)=>{
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', {
      headers: corsHeaders
    });
  }
  try {
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    const supabase = createClient(supabaseUrl, supabaseKey);
    if (req.method === 'POST') {
      return await handleProgressUpdate(req, supabase);
    } else if (req.method === 'GET') {
      return await handleProgressQuery(req, supabase);
    } else if (req.method === 'DELETE') {
      return await handleProgressReset(req, supabase);
    }
    return new Response(JSON.stringify({
      error: 'Method not allowed'
    }), {
      status: 405,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Progress tracker error:', error);
    return new Response(JSON.stringify({
      error: 'Internal server error',
      details: error.message
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
});
async function handleProgressUpdate(req, supabase) {
  const progressData = await req.json();
  if (!progressData.documentId) {
    return new Response(JSON.stringify({
      error: 'Document ID required'
    }), {
      status: 400,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
  // Verify document exists
  const { data: document, error: docError } = await supabase.from('documents').select('*').eq('id', progressData.documentId).single();
  if (docError || !document) {
    return new Response(JSON.stringify({
      error: 'Document not found'
    }), {
      status: 404,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
  // Prepare update data
  const updateData = {
    updated_at: new Date().toISOString()
  };
  if (progressData.status) {
    updateData.status = progressData.status;
    // Handle status-specific updates
    if (progressData.status === 'processing') {
      updateData.processing_started_at = new Date().toISOString();
    } else if (progressData.status === 'completed') {
      updateData.processing_completed_at = new Date().toISOString();
      updateData.progress_percentage = 100;
    } else if (progressData.status === 'failed') {
      updateData.error_message = progressData.errorMessage || 'Processing failed';
    }
  }
  if (progressData.progress !== undefined) {
    updateData.progress_percentage = Math.min(100, Math.max(0, progressData.progress));
  }
  if (progressData.chunksProcessed !== undefined) {
    updateData.processed_chunks = progressData.chunksProcessed;
  }
  if (progressData.chunksFailed !== undefined) {
    updateData.failed_chunks = progressData.chunksFailed;
  }
  if (progressData.errorMessage) {
    updateData.error_message = progressData.errorMessage;
  }
  if (progressData.metadata) {
    updateData.metadata = {
      ...document.metadata,
      ...progressData.metadata
    };
  }
  // Update document record
  const { data: updatedDoc, error: updateError } = await supabase.from('documents').update(updateData).eq('id', progressData.documentId).select().single();
  if (updateError) {
    console.error('Error updating document progress:', updateError);
    return new Response(JSON.stringify({
      error: 'Failed to update progress',
      details: updateError.message
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
  // Prepare realtime payload
  const realtimePayload = {
    type: determineUpdateType(progressData, updatedDoc),
    documentId: updatedDoc.id,
    progress: updatedDoc.progress_percentage,
    status: updatedDoc.status,
    timestamp: new Date().toISOString(),
    details: {
      filename: updatedDoc.original_filename,
      fileSize: updatedDoc.file_size,
      processedChunks: updatedDoc.processed_chunks,
      totalChunks: updatedDoc.total_chunks,
      failedChunks: updatedDoc.failed_chunks,
      errorMessage: updatedDoc.error_message
    }
  };
  // Send realtime update (Supabase Realtime)
  try {
    await sendRealtimeUpdate(supabase, updatedDoc.user_id, realtimePayload);
  } catch (realtimeError) {
    console.warn('Failed to send realtime update:', realtimeError);
  // Don't fail the request if realtime fails
  }
  return new Response(JSON.stringify({
    success: true,
    documentId: updatedDoc.id,
    status: updatedDoc.status,
    progress: updatedDoc.progress_percentage,
    realtimePayload: realtimePayload
  }), {
    status: 200,
    headers: {
      ...corsHeaders,
      'Content-Type': 'application/json'
    }
  });
}
async function handleProgressQuery(req, supabase) {
  const url = new URL(req.url);
  const documentId = url.searchParams.get('documentId');
  const userId = url.searchParams.get('userId');
  if (!documentId) {
    return new Response(JSON.stringify({
      error: 'Document ID required'
    }), {
      status: 400,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
  let query = supabase.from('documents').select('id, status, progress_percentage, processed_chunks, total_chunks, failed_chunks, error_message, original_filename, file_size, created_at, updated_at').eq('id', documentId);
  if (userId) {
    query = query.eq('user_id', userId);
  }
  const { data: document, error } = await query.single();
  if (error || !document) {
    return new Response(JSON.stringify({
      error: 'Document not found'
    }), {
      status: 404,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
  // Calculate additional metrics
  const isStuck = document.status === 'processing' && new Date().getTime() - new Date(document.updated_at).getTime() > 1800000 // 30 minutes
  ;
  const estimatedTimeRemaining = calculateETA(document);
  return new Response(JSON.stringify({
    documentId: document.id,
    status: document.status,
    progress: document.progress_percentage,
    processedChunks: document.processed_chunks,
    totalChunks: document.total_chunks,
    failedChunks: document.failed_chunks,
    errorMessage: document.error_message,
    filename: document.original_filename,
    fileSize: document.file_size,
    isStuck: isStuck,
    estimatedTimeRemaining: estimatedTimeRemaining,
    lastUpdated: document.updated_at
  }), {
    status: 200,
    headers: {
      ...corsHeaders,
      'Content-Type': 'application/json'
    }
  });
}
async function handleProgressReset(req, supabase) {
  const url = new URL(req.url);
  const documentId = url.searchParams.get('documentId');
  if (!documentId) {
    return new Response(JSON.stringify({
      error: 'Document ID required'
    }), {
      status: 400,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
  // Reset document progress
  const { data: updatedDoc, error: updateError } = await supabase.from('documents').update({
    status: 'pending',
    progress_percentage: 0,
    processed_chunks: 0,
    failed_chunks: 0,
    error_message: null,
    processing_started_at: null,
    processing_completed_at: null,
    updated_at: new Date().toISOString()
  }).eq('id', documentId).select().single();
  if (updateError) {
    return new Response(JSON.stringify({
      error: 'Failed to reset progress',
      details: updateError.message
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
  return new Response(JSON.stringify({
    success: true,
    documentId: updatedDoc.id,
    status: updatedDoc.status,
    message: 'Progress reset successfully'
  }), {
    status: 200,
    headers: {
      ...corsHeaders,
      'Content-Type': 'application/json'
    }
  });
}
function determineUpdateType(progressData, document) {
  if (document.status === 'failed' || progressData.errorMessage) {
    return 'error';
  } else if (document.status === 'completed' || document.progress_percentage === 100) {
    return 'complete';
  } else if (progressData.status && progressData.status !== document.status) {
    return 'status_change';
  } else {
    return 'progress_update';
  }
}
async function sendRealtimeUpdate(supabase, userId, payload) {
  // Use Supabase Realtime to send updates
  const channel = `user_${userId}_progress`;
  // Insert into a realtime table for live updates
  const { error } = await supabase.from('realtime_progress_updates').insert({
    user_id: userId,
    document_id: payload.documentId,
    payload: payload,
    created_at: new Date().toISOString()
  });
  if (error) {
    console.error('Failed to send realtime update:', error);
    throw error;
  }
}
function calculateETA(document) {
  if (!document.total_chunks || document.processed_chunks === 0) {
    return null;
  }
  const timeElapsed = new Date().getTime() - new Date(document.created_at).getTime();
  const progressRatio = document.processed_chunks / document.total_chunks;
  if (progressRatio === 0) return null;
  const totalEstimatedTime = timeElapsed / progressRatio;
  const remainingTime = totalEstimatedTime - timeElapsed;
  return Math.max(0, Math.round(remainingTime / 1000)) // Return seconds
  ;
}
