import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { corsHeaders } from '../_shared/cors.ts';
Deno.serve(async (req)=>{
  console.log('🚀 doc-processor invoked:', {
    method: req.method,
    url: req.url,
    headers: Object.fromEntries(req.headers.entries())
  });
  if (req.method === 'OPTIONS') {
    console.log('✅ CORS preflight handled');
    return new Response('ok', {
      headers: corsHeaders
    });
  }
  try {
    console.log('🔧 Initializing Supabase client with service role...');
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    console.log('🔑 Environment check:', {
      hasUrl: !!supabaseUrl,
      hasServiceKey: !!supabaseServiceKey,
      urlPrefix: supabaseUrl?.substring(0, 20) + '...'
    });
    // Use service role for bypassing RLS during MVP phase
    const supabase = createClient(supabaseUrl ?? '', supabaseServiceKey ?? '', {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    });
    // TODO: SECURITY UPGRADE NEEDED
    // Current: Simple service authentication for MVP testing
    // Future: Implement proper dual-auth system:
    //   1. Validate Render backend JWT token against backend API
    //   2. Use Supabase RLS with proper user context
    //   3. Add request signing/validation between frontend and Edge Functions
    //   4. Implement rate limiting per user
    //   5. Add audit logging for all document operations
    console.log('🔐 Checking authorization header...');
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      console.log('❌ No authorization header found');
      return new Response(JSON.stringify({
        error: 'Authorization header required'
      }), {
        status: 401,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    // TODO: Replace with proper token validation
    // For now, accept any Bearer token as service auth
    const token = authHeader.replace('Bearer ', '');
    if (!token || token.trim().length === 0) {
      console.log('❌ Empty or invalid token');
      return new Response(JSON.stringify({
        error: 'Invalid authorization token'
      }), {
        status: 401,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    console.log('✅ Token validation passed, token length:', token.length);
    console.log('📥 Parsing request body...');
    const requestBody = await req.text();
    console.log('📋 Raw request body:', requestBody);
    let parsedBody;
    try {
      parsedBody = JSON.parse(requestBody);
      console.log('✅ JSON parsed successfully:', parsedBody);
    } catch (parseError) {
      console.log('❌ JSON parse error:', parseError);
      return new Response(JSON.stringify({
        error: 'Invalid JSON in request body'
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    const { filename, contentType, fileSize, userId } = parsedBody;
    // Validate userId is a valid UUID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    if (!userId || !uuidRegex.test(userId)) {
      console.log('❌ Invalid userId format:', userId);
      return new Response(JSON.stringify({
        error: 'Invalid user ID format. Must be a valid UUID.',
        provided: userId
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    console.log('✅ Valid UUID format for userId:', userId);
    // TODO: Validate userId against authenticated user from proper token
    if (!userId) {
      return new Response(JSON.stringify({
        error: 'User ID required'
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    // Validate file size (50MB limit)
    if (fileSize > 52428800) {
      return new Response(JSON.stringify({
        error: 'File too large',
        maxSize: '50MB'
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain'
    ];
    if (!allowedTypes.includes(contentType)) {
      return new Response(JSON.stringify({
        error: 'File type not supported',
        allowedTypes: [
          'PDF',
          'DOCX',
          'DOC',
          'TXT'
        ]
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    console.log('🔍 Generating file hash for deduplication...');
    const fileHash = await generateFileHash(filename, fileSize, userId);
    console.log('✅ File hash generated:', fileHash);
    console.log('🔍 Checking for existing file with same hash...');
    const { data: existingDoc, error: checkError } = await supabase.from('documents').select('id, status, original_filename').eq('file_hash', fileHash).eq('user_id', userId).single();
    if (checkError && checkError.code !== 'PGRST116') {
      console.log('❌ Error checking for existing document:', checkError);
      return new Response(JSON.stringify({
        error: 'Database error checking for duplicates'
      }), {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    if (existingDoc && existingDoc.status === 'completed') {
      console.log('⚠️ File already exists and completed:', existingDoc);
      return new Response(JSON.stringify({
        error: 'File already uploaded',
        documentId: existingDoc.id,
        filename: existingDoc.original_filename
      }), {
        status: 409,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    console.log('📝 Creating document record...');
    const storagePath = `${userId}/${fileHash}/${filename}`;
    const documentData = {
      user_id: userId,
      original_filename: filename,
      content_type: contentType,
      file_size: fileSize,
      file_hash: fileHash,
      storage_path: storagePath,
      status: 'uploading',
      progress_percentage: 0,
      processed_chunks: 0,
      failed_chunks: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    console.log('📋 Document data to insert:', documentData);
    const { data: document, error: docError } = await supabase.from('documents').insert(documentData).select().single();
    if (docError) {
      console.error('❌ Error creating document record:', docError);
      console.error('❌ Full error details:', JSON.stringify(docError, null, 2));
      return new Response(JSON.stringify({
        error: 'Failed to create document record',
        details: docError.message || 'Unknown database error'
      }), {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    console.log('✅ Document record created:', document);
    // Generate signed upload URL
    const { data: uploadData, error: uploadError } = await supabase.storage.from('documents').createSignedUploadUrl(storagePath);
    if (uploadError) {
      console.error('Error generating upload URL:', uploadError);
      return new Response(JSON.stringify({
        error: 'Failed to generate upload URL'
      }), {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    return new Response(JSON.stringify({
      documentId: document.id,
      uploadUrl: uploadData.signedUrl,
      uploadPath: uploadData.path,
      storagePath: storagePath
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('doc-processor error:', error);
    return new Response(JSON.stringify({
      error: 'Internal server error'
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
});
async function generateFileHash(filename, fileSize, userId) {
  const data = `${filename}-${fileSize}-${userId}-${Date.now()}`;
  const encoder = new TextEncoder();
  const dataBytes = encoder.encode(data);
  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBytes);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b)=>b.toString(16).padStart(2, '0')).join('');
}
