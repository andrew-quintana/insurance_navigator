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

    // Step 4: Call vector-processor to generate embeddings
    console.log(`🧮 Triggering vector processor for document ${documentId}`)
    
    const { data: vectorResult, error: vectorError } = await supabase.functions.invoke('vector-processor', {
      body: { 
        documentId: documentId,
        extractedText: processedContent,
        documentType: documentType
      }
    })

    if (vectorError) {
      console.error('❌ Vector processor invocation failed:', vectorError)
      
      // Update document to indicate parsing succeeded but vectorization failed
      await supabase
        .from(tableName)
        .update({
          status: 'parsing_complete_vectorization_failed',
          progress_percentage: 85,
          extraction_method: 'llamaparse',
          updated_at: new Date().toISOString()
        })
        .eq(idField, documentId)
      
      return new Response(JSON.stringify({ 
        success: false,
        error: 'Vector processing failed',
        details: vectorError.message,
        documentId: documentId,
        textLength: processedContent.length,
        stage: 'vectorization'
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log('✅ Vector processor triggered successfully')

    // Update document to completed status
    await supabase
      .from(tableName)
      .update({ 
        status: 'processed',
        progress_percentage: 100,
        extraction_method: 'llamaparse',
        updated_at: new Date().toISOString()
      })
      .eq(idField, documentId)
    
    console.log(`🎉 Document ${documentId} processed successfully`)

    return new Response(
      JSON.stringify({ 
        success: true, 
        documentId,
        message: 'Document parsing and vectorization completed successfully',
        processedContent: processedContent.substring(0, 200) + '...',
        extractedText: processedContent,
        vectorResult: vectorResult,
        textLength: processedContent.length,
        extractionMethod: 'llamaparse'
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    )

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