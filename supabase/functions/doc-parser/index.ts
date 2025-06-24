import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// TODO: Implement proper error classification and recovery strategies
// TODO: Add document format validation before processing
// TODO: Implement concurrent processing for large documents
// TODO: Add progress tracking with more granular updates

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
}

// LlamaParse integration function
async function parseDocumentWithLlamaParse(supabase: any, filePath: string, documentId: string): Promise<string> {
  try {
    const llamaParseApiKey = Deno.env.get('LLAMA_PARSE_API_KEY');
    if (!llamaParseApiKey) {
      throw new Error('LLAMA_PARSE_API_KEY environment variable is required');
    }

    console.log(`🔍 Downloading file from storage: ${filePath}`);
    
    // Download file from Supabase storage
    const { data: fileData, error: downloadError } = await supabase.storage
      .from('raw_documents')
      .download(filePath);

    if (downloadError) {
      console.error('File download error:', downloadError);
      throw new Error(`Failed to download file: ${downloadError.message}`);
    }

    if (!fileData) {
      throw new Error('No file data received from storage');
    }

    console.log(`📄 File downloaded, size: ${fileData.size} bytes`);

    // Convert blob to array buffer for direct FormData usage
    const arrayBuffer = await fileData.arrayBuffer();

    console.log(`🚀 Sending to LlamaParse for processing...`);

    // Call LlamaParse API
    const formData = new FormData();
    formData.append('file', new Blob([arrayBuffer], { type: 'application/pdf' }), 'document.pdf');
    
    const parseResponse = await fetch('https://api.cloud.llamaindex.ai/api/parsing/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${llamaParseApiKey}`,
      },
      body: formData
    });

    if (!parseResponse.ok) {
      const errorText = await parseResponse.text();
      throw new Error(`LlamaParse API error: ${parseResponse.status} - ${errorText}`);
    }

    const parseResult = await parseResponse.json();
    console.log(`📋 LlamaParse job created: ${parseResult.id}`);

    // Poll for results
    let attempts = 0;
    const maxAttempts = 30; // 30 attempts with 2-second intervals = 1 minute max
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
      attempts++;
      
      const statusResponse = await fetch(`https://api.cloud.llamaindex.ai/api/parsing/job/${parseResult.id}`, {
        headers: {
          'Authorization': `Bearer ${llamaParseApiKey}`,
        }
      });

      if (!statusResponse.ok) {
        console.error(`Status check failed: ${statusResponse.status}`);
        continue;
      }

      const statusResult = await statusResponse.json();
      console.log(`🔄 Parse status: ${statusResult.status} (attempt ${attempts}/${maxAttempts})`);

      if (statusResult.status === 'SUCCESS') {
        const resultResponse = await fetch(`https://api.cloud.llamaindex.ai/api/parsing/job/${parseResult.id}/result/markdown`, {
          headers: {
            'Authorization': `Bearer ${llamaParseApiKey}`,
          }
        });

        if (resultResponse.ok) {
          const extractedText = await resultResponse.text();
          console.log(`✅ Text extraction completed, length: ${extractedText.length} characters`);
          return extractedText;
        } else {
          throw new Error(`Failed to get parse results: ${resultResponse.status}`);
        }
      } else if (statusResult.status === 'ERROR') {
        throw new Error(`LlamaParse job failed: ${statusResult.error || 'Unknown error'}`);
      }
      
      // Continue polling for PENDING status
    }

    throw new Error('LlamaParse job timed out after 1 minute');

  } catch (error) {
    console.error('LlamaParse error:', error);
    throw error;
  }
}

// Retry mechanism for vector processing with exponential backoff
async function retryVectorProcessing(supabase: any, documentId: string, extractedText: string, documentType: string, maxRetries: number = 3): Promise<{ data: any, error: any }> {
  const baseDelay = 1000; // Start with 1 second
  
  // Get environment variables for direct HTTP call
  const supabaseUrl = Deno.env.get('SUPABASE_URL')
  const serviceRoleKey = Deno.env.get('CUSTOM_SERVICE_ROLE_KEY')
  
  if (!supabaseUrl || !serviceRoleKey) {
    return { data: null, error: new Error('Missing environment variables for vector processing') }
  }
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    console.log(`🔄 Vector processing attempt ${attempt}/${maxRetries} for document ${documentId}`);
    
    try {
      // Use direct HTTP fetch instead of supabase.functions.invoke() to avoid timeout issues
      const vectorProcessorUrl = `${supabaseUrl}/functions/v1/vector-processor`
      const payload = {
        documentId: documentId,
        extractedText: extractedText,
        documentType: documentType
      }
      
      console.log(`🌐 Making direct HTTP call to vector-processor (attempt ${attempt})`)
      
      const response = await fetch(vectorProcessorUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${serviceRoleKey}`,
          'Content-Type': 'application/json',
          'apikey': serviceRoleKey
        },
        body: JSON.stringify(payload)
      })
      
      if (response.ok) {
        const result = await response.json()
        console.log(`✅ Vector processing succeeded on attempt ${attempt}`)
        return { data: result, error: null }
      }
      
      // Handle non-2xx responses
      const errorText = await response.text()
      console.error(`❌ Vector processing attempt ${attempt} failed with status ${response.status}:`, errorText)
      
      const error = {
        message: `HTTP ${response.status}: ${errorText}`,
        status: response.status,
        details: errorText
      }
      
      // If this is the last attempt, return the error
      if (attempt === maxRetries) {
        console.error(`💥 All ${maxRetries} vector processing attempts failed for document ${documentId}`)
        return { data: null, error }
      }
      
      // Calculate exponential backoff delay
      const delay = baseDelay * Math.pow(2, attempt - 1)
      console.log(`⏱️ Waiting ${delay}ms before retry attempt ${attempt + 1}`)
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay))
      
    } catch (invokeError) {
      console.error(`❌ Vector processing invocation error on attempt ${attempt}:`, invokeError)
      
      // If this is the last attempt, return the error
      if (attempt === maxRetries) {
        return { data: null, error: invokeError }
      }
      
      // Calculate exponential backoff delay
      const delay = baseDelay * Math.pow(2, attempt - 1)
      console.log(`⏱️ Waiting ${delay}ms before retry attempt ${attempt + 1}`)
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  
  // This should never be reached, but just in case
  return { data: null, error: new Error('Unexpected retry loop exit') }
}

// Configuration for chunking
const CHUNK_CONFIG = {
  maxCharsPerChunk: 1500,  // ~1.5KB per chunk to stay under limits
  maxConcurrentChunks: 3,  // Process 3 chunks at a time to avoid overwhelming
  retryDelayMs: 1000,      // Start with 1 second delay
  maxRetries: 3            // Maximum 3 retries per chunk
};

// Process document in chunks with status tracking
async function processLargeDocument(content: string, documentId: string) {
  // Split content into chunks
  const chunks = [];
  for (let i = 0; i < content.length; i += CHUNK_CONFIG.maxCharsPerChunk) {
    chunks.push(content.slice(i, i + CHUNK_CONFIG.maxCharsPerChunk));
  }
  
  console.log(`📄 Processing document ${documentId} in ${chunks.length} chunks`);
  
  // Update document status
  await supabase.from('documents')
    .update({ 
      status: 'processing',
      progress_percentage: 0,
      total_chunks: chunks.length,
      processed_chunks: 0
    })
    .eq('id', documentId);

  // Process chunks in batches
  for (let i = 0; i < chunks.length; i += CHUNK_CONFIG.maxConcurrentChunks) {
    const batch = chunks.slice(i, i + CHUNK_CONFIG.maxConcurrentChunks);
    
    try {
      // Process batch with retries
      await Promise.all(batch.map(async (chunk, idx) => {
        const chunkIndex = i + idx;
        let retries = 0;
        
        while (retries < CHUNK_CONFIG.maxRetries) {
          try {
            await processChunk(chunk, documentId, chunkIndex);
            break;
          } catch (error) {
            retries++;
            if (retries === CHUNK_CONFIG.maxRetries) {
              throw error;
            }
            await new Promise(resolve => setTimeout(resolve, CHUNK_CONFIG.retryDelayMs * Math.pow(2, retries)));
          }
        }
      }));

      // Update progress
      const processedCount = Math.min(i + CHUNK_CONFIG.maxConcurrentChunks, chunks.length);
      const progress = Math.round((processedCount / chunks.length) * 100);
      
      await supabase.from('documents')
        .update({ 
          progress_percentage: progress,
          processed_chunks: processedCount
        })
        .eq('id', documentId);

    } catch (error) {
      console.error(`❌ Error processing batch starting at chunk ${i}:`, error);
      
      await supabase.from('documents')
        .update({ 
          status: 'failed',
          error_details: JSON.stringify({
            error: error.message,
            failedAt: `chunk ${i}/${chunks.length}`,
            progress: Math.round((i / chunks.length) * 100)
          })
        })
        .eq('id', documentId);
      
      throw error;
    }
  }

  // Mark as complete
  await supabase.from('documents')
    .update({ 
      status: 'completed',
      progress_percentage: 100,
      processed_chunks: chunks.length
    })
    .eq('id', documentId);

  return { success: true, chunks_processed: chunks.length };
}

// Process a single chunk
async function processChunk(chunk: string, documentId: string, chunkIndex: number) {
  const response = await supabase.functions.invoke('vector-processor', {
    body: { 
      content: chunk,
      documentId,
      chunkIndex,
      isPartial: true
    }
  });

  if (!response.data?.success) {
    throw new Error(`Failed to process chunk ${chunkIndex}: ${response.error?.message || 'Unknown error'}`);
  }

  return response.data;
}

serve(async (req: Request) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  // Handle GET requests (health checks)
  if (req.method === 'GET') {
    return new Response(
      JSON.stringify({ 
        service: 'doc-parser',
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    )
  }

  try {
    // Get environment variables
    const supabaseUrl = Deno.env.get('SUPABASE_URL')
    const serviceRoleKey = Deno.env.get('CUSTOM_SERVICE_ROLE_KEY')

    if (!supabaseUrl || !serviceRoleKey) {
      throw new Error('Missing environment variables')
    }

    // Create Supabase client
    const supabase = createClient(supabaseUrl, serviceRoleKey)

    // Parse request with proper error handling
    let requestBody;
    try {
      const bodyText = await req.text();
      if (!bodyText || bodyText.trim() === '') {
        throw new Error('Request body is empty');
      }
      requestBody = JSON.parse(bodyText);
    } catch (parseError) {
      console.error('JSON parsing error:', parseError);
      return new Response(
        JSON.stringify({ 
          error: 'Invalid JSON in request body',
          details: parseError.message
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400 
        }
      );
    }

    const { documentId, document_path, title, documentType } = requestBody;
    console.log(`📄 Processing document: ${documentId} (type: ${documentType})`)

    if (!documentId) {
      return new Response(
        JSON.stringify({ 
          error: 'Document ID and storage path are required',
          details: 'documentId parameter is missing'
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400 
        }
      );
    }

    // Determine which table to query based on document type
    const tableName = documentType === 'regulatory' ? 'regulatory_documents' : 'documents';
    const idField = documentType === 'regulatory' ? 'document_id' : 'id';
    
    console.log(`🗄️ Querying table: ${tableName} with field: ${idField} = ${documentId}`)

    // Get document info from database (use appropriate table)
    const { data: documents, error: docError } = await supabase
      .from(tableName)
      .select('*')
      .eq(idField, documentId)

    console.log(`📊 Query result: found ${documents?.length || 0} documents`)
    
    if (docError) {
      console.error('Database query error:', docError)
      return new Response(
        JSON.stringify({ 
          error: 'Database query failed',
          details: docError?.message || 'Database error occurred'
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 500 
        }
      );
    }

    if (!documents || documents.length === 0) {
      console.error(`No documents found in ${tableName} with ${idField} = ${documentId}`)
      return new Response(
        JSON.stringify({ 
          error: 'Document not found in database',
          details: `No document found in ${tableName} table with ${idField} = ${documentId}`
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 404 
        }
      );
    }

    if (documents.length > 1) {
      console.error(`Multiple documents found in ${tableName} with ${idField} = ${documentId}:`, documents.length)
      return new Response(
        JSON.stringify({ 
          error: 'Multiple documents found',
          details: `Found ${documents.length} documents with the same ID in ${tableName}`
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 409 
        }
      );
    }

    const document = documents[0];

    // TODO: Add file size validation and optimization for large files
    // TODO: Implement virus scanning before processing
    
    // Use different file path fields for different document types
    let filePath;
    if (documentType === 'regulatory') {
      filePath = document.raw_document_path || document_path;
    } else {
      filePath = document.storage_path || document_path;
    }
    
    if (!filePath) {
      console.error('No file path found for document:', documentId)
      return new Response(
        JSON.stringify({ 
          error: 'Document file path not found',
          details: 'No storage path available for processing'
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400 
        }
      );
    }

    console.log(`📁 Using file path: ${filePath}`)

    // Update document status to parsing with progress
    await supabase
      .from(tableName)
      .update({ 
        status: 'parsing',
        progress_percentage: 20,
        updated_at: new Date().toISOString()
      })
      .eq(idField, documentId)

    // Extract text using LlamaParse
    console.log(`🔄 Starting document processing with LlamaParse...`)
    
    let processedContent: string;
    try {
      processedContent = await parseDocumentWithLlamaParse(supabase, filePath, documentId);
      
      // Update progress to 60%
      await supabase
        .from(tableName)
        .update({ 
          progress_percentage: 60,
          updated_at: new Date().toISOString()
        })
        .eq(idField, documentId)
        
    } catch (parseError) {
      console.error('❌ Document parsing failed:', parseError);
      
      // Update document status to indicate parsing failed
      await supabase
        .from(tableName)
        .update({
          status: 'parsing_failed',
          progress_percentage: 30,
          error_message: parseError.message,
          updated_at: new Date().toISOString()
        })
        .eq(idField, documentId)
      
      return new Response(JSON.stringify({ 
        success: false,
        error: 'Document parsing failed',
        details: parseError.message,
        documentId: documentId,
        stage: 'text_extraction'
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log(`✅ Document processing completed, extracted ${processedContent.length} characters`)

    // ✅ AUTOMATIC PIPELINE: Trigger vector processor
    console.log('🚀 Triggering vector-processor for document:', documentId)
    const { data: vectorResult, error: vectorError } = await supabase.functions.invoke('vector-processor', {
      body: { 
        documentId,
        extractedText,
        documentType: 'user',
        userId: document.user_id  // Pass the actual user_id
      }
    })

    // Step 4: Start async vector processing and return immediately for production MVP
    console.log(`🧮 Starting async vector processor for document ${documentId}`)
    
    // Update document status to 'vectorizing' immediately
    await supabase
      .from('documents')
      .update({ 
        status: 'vectorizing',
        processing_progress: 0,
        processing_stage: 'vectorization_started',
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)
    
    // For large documents, process asynchronously to avoid timeouts
    const maxCharsPerCall = 1500 // ~1.5KB per call to stay under 2KB limit
    
    if (processedContent.length > maxCharsPerCall) {
      console.log(`📄 Large document detected (${processedContent.length} chars), starting async processing`)
      
      // Split content into smaller chunks for async processing
      const contentChunks = []
      for (let i = 0; i < processedContent.length; i += maxCharsPerCall) {
        contentChunks.push(processedContent.slice(i, i + maxCharsPerCall))
      }
      
      console.log(`📦 Split into ${contentChunks.length} chunks for async processing`)
      
      // Return immediately with processing status
      const response = {
        success: true,
        message: 'Document processing started',
        documentId,
        textLength: processedContent.length,
        totalChunks: contentChunks.length,
        stage: 'async_vectorization_started',
        status: 'processing'
      }
      
      // Start background processing
      EdgeRuntime.waitUntil(
        processLargeDocument(processedContent, documentId)
        .catch(error => {
          console.error(`❌ Async processing failed for ${documentId}:`, error)
          // Update document with error status
            return supabase
            .from('documents')
            .update({ 
              status: 'failed',
              error_message: `Async processing failed: ${error.message}`,
              updated_at: new Date().toISOString()
            })
            .eq('id', documentId)
            .then(() => console.log(`📝 Updated document ${documentId} with error status`))
        })
      )
      
      return new Response(JSON.stringify(response), {
        status: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'application/json'
        }
      })
    } else {
      // Small documents - process synchronously for immediate results
      console.log(`📄 Small document (${processedContent.length} chars), processing synchronously`)
      
      const result = await retryVectorProcessing(supabase, documentId, processedContent, documentType)
      
      if (result.error) {
        console.error(`❌ Vector processing failed:`, result.error)
        
        await supabase
          .from('documents')
          .update({ 
            status: 'failed',
            error_message: `Vector processing failed: ${result.error.message}`,
            updated_at: new Date().toISOString()
          })
          .eq('id', documentId)
        
        return new Response(JSON.stringify({
          success: false,
          error: 'Vector processing failed',
          details: result.error.message,
          documentId,
          textLength: processedContent.length,
          stage: 'vectorization'
        }), { 
          status: 500,
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
          }
        })
      }
      
      console.log(`✅ Vector processing completed for small document`)
      
      await supabase
        .from('documents')
        .update({ 
          status: 'completed',
          processing_progress: 100,
          processing_stage: 'completed',
          updated_at: new Date().toISOString()
        })
        .eq('id', documentId)
      
      return new Response(JSON.stringify({
        success: true,
        message: 'Document processed successfully',
        documentId,
        textLength: processedContent.length,
        stage: 'completed'
      }), {
        status: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'application/json'
        }
      })
    }

  } catch (error) {
    console.error('Doc parser error:', error)
    
    // TODO: Implement proper error classification
    // TODO: Add retry logic for transient failures
    // TODO: Store error details for debugging
    
    return new Response(
      JSON.stringify({ 
        error: 'Document parsing failed',
        details: error.message,
        timestamp: new Date().toISOString()
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500 
      }
    )
  }
}) 