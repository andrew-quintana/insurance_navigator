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

    const { documentId, document_path, title } = requestBody;
    console.log(`📄 Processing document: ${documentId}`)

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

    // Get document info from database (use regulatory_documents table)
    const { data: document, error: docError } = await supabase
      .from('regulatory_documents')
      .select('*')
      .eq('document_id', documentId)
      .single()

    if (docError || !document) {
      console.error('Document not found:', docError)
      return new Response(
        JSON.stringify({ 
          error: 'Document not found in database',
          details: docError?.message || 'No document found'
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 404 
        }
      );
    }

    // TODO: Add file size validation and optimization for large files
    // TODO: Implement virus scanning before processing
    
    // Use both file_path and storage_path for compatibility
    const filePath = document.raw_document_path || document_path
    if (!filePath) {
      console.error('No file path found for document:', document.document_id)
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
      .from('regulatory_documents')
      .update({ 
        status: 'parsing',
        progress_percentage: 20,
        updated_at: new Date().toISOString()
      })
      .eq('document_id', documentId)

    // TODO: Replace with actual document processing logic
    // TODO: Implement text extraction based on file type (PDF, DOC, etc.)
    // TODO: Add OCR support for scanned documents
    // TODO: Implement chunking strategy for vector storage
    
    // Simulate document processing
    console.log(`🔄 Processing document content...`)
    
    // For now, create mock processed content
    const processedContent = `Processed content for document: ${document.title || title}
    
This is a mock processing result. In production, this would contain:
- Extracted text from the document
- Structured data extraction
- Policy information parsing
- Coverage details analysis

Document metadata:
- Title: ${document.title || title}
- File path: ${filePath}
- Upload date: ${document.created_at}
`

    // TODO: Implement vector embedding generation
    // TODO: Store embeddings in vector database for semantic search
    
    // Update progress to 60%
    await supabase
      .from('regulatory_documents')
      .update({ 
        progress_percentage: 60,
        updated_at: new Date().toISOString()
      })
      .eq('document_id', documentId)

    // TODO: Store processed chunks in database
    // TODO: Create searchable index for document content
    
    // Simulate final processing
    console.log(`✅ Document processing completed`)

    // Step 4: Call vector-processor to generate embeddings
    console.log(`🧮 Triggering vector processor for document ${documentId}`)
    
    const { data: vectorResult, error: vectorError } = await supabase.functions.invoke('vector-processor', {
      body: { 
        documentId: documentId,
        extractedText: processedContent,
        documentType: 'regulatory'
      }
    })

    if (vectorError) {
      console.error('❌ Vector processor invocation failed:', vectorError)
      
      // Update document to indicate parsing succeeded but vectorization failed
      await supabase
        .from('regulatory_documents')
        .update({
          status: 'parsing_complete_vectorization_failed',
          progress_percentage: 85,
          extraction_method: 'edge_function_processing',
          updated_at: new Date().toISOString()
        })
        .eq('document_id', documentId)
      
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
      .from('regulatory_documents')
      .update({ 
        status: 'processed',
        progress_percentage: 100,
        extraction_method: 'edge_function_processing',
        updated_at: new Date().toISOString()
      })
      .eq('document_id', documentId)
    
    console.log(`🎉 Document ${documentId} processed successfully`)

    return new Response(
      JSON.stringify({ 
        success: true, 
        documentId,
        message: 'Document parsing and vectorization completed successfully',
        processedContent: processedContent.substring(0, 200) + '...',
        extractedText: processedContent,
        vectorResult: vectorResult
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