import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface BulkRegulatoryRequest {
  documents: Array<{
    url: string;
    title?: string;
    jurisdiction?: string;
    document_type?: string;
    tags?: string[];
  }>;
  batch_size?: number;
}

interface ProcessingResult {
  success: boolean;
  document_id?: string;
  title: string;
  url: string;
  vector_count?: number;
  error?: string;
}

// Utility function to extract content from URL
async function extractContentFromUrl(url: string): Promise<{ content: string; title: string; filename: string }> {
  try {
    console.log(`🌐 Fetching content from: ${url}`)
    
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; SupabaseBot/1.0)'
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const contentType = response.headers.get('content-type') || ''
    const text = await response.text()
    
    let title = url.split('/').pop() || 'Regulatory Document'
    let content = text
    
    // Basic HTML parsing for title extraction
    if (contentType.includes('text/html')) {
      const titleMatch = text.match(/<title[^>]*>([^<]+)<\/title>/i)
      if (titleMatch) {
        title = titleMatch[1].trim()
      }
      
      // Remove HTML tags for content
      content = text
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
        .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
        .replace(/<[^>]+>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
    }
    
    if (content.length < 100) {
      throw new Error('Content too short after extraction')
    }
    
    return {
      content,
      title,
      filename: url.split('/').pop() || 'document.html'
    }
  } catch (error) {
    console.error(`❌ Content extraction failed for ${url}:`, error)
    throw error
  }
}

// Generate content hash for deduplication
function generateContentHash(content: string): string {
  const encoder = new TextEncoder()
  const data = encoder.encode(content)
  
  // Simple hash implementation (for demo - use crypto.subtle in production)
  let hash = 0
  for (let i = 0; i < data.length; i++) {
    const char = data[i]
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32-bit integer
  }
  
  return Math.abs(hash).toString(16)
}

Deno.serve(async (req) => {
  try {
    console.log('🚀 bulk-regulatory-processor started')
    
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      (Deno.env.get('SERVICE_ROLE_KEY') || Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')) ?? ''
    )

    const requestBody: BulkRegulatoryRequest = await req.json()
    const { documents, batch_size = 3 } = requestBody
    
    console.log(`📥 Bulk processing request: ${documents.length} documents, batch size: ${batch_size}`)
    
    if (!documents || documents.length === 0) {
      return new Response(
        JSON.stringify({ error: 'No documents provided' }),
        { status: 400 }
      )
    }

    const results: ProcessingResult[] = []
    
    // Process documents in batches
    for (let i = 0; i < documents.length; i += batch_size) {
      const batch = documents.slice(i, i + batch_size)
      console.log(`📦 Processing batch ${Math.floor(i / batch_size) + 1}/${Math.ceil(documents.length / batch_size)}`)
      
      const batchPromises = batch.map(async (doc) => {
        try {
          // Step 1: Extract content from URL
          const { content, title, filename } = await extractContentFromUrl(doc.url)
          
          // Step 2: Generate content hash for deduplication
          const contentHash = generateContentHash(content)
          
          // Step 3: Check for duplicates
          const { data: existingDoc } = await supabase
            .from('regulatory_documents')
            .select('document_id, title')
            .eq('content_hash', contentHash)
            .single()
          
          if (existingDoc) {
            console.log(`🔄 Duplicate found for ${doc.url}: ${existingDoc.title}`)
            return {
              success: false,
              title: title,
              url: doc.url,
              error: `Duplicate document exists: ${existingDoc.title}`
            }
          }
          
          // Step 4: Create regulatory document record
          const { data: newDoc, error: createError } = await supabase
            .from('regulatory_documents')
            .insert({
              raw_document_path: doc.url,
              title: doc.title || title,
              jurisdiction: doc.jurisdiction || 'United States',
              program: ['Healthcare', 'General'],
              document_type: doc.document_type || 'regulatory',
              structured_contents: JSON.stringify({
                content,
                title,
                url: doc.url,
                filename,
                processing_timestamp: new Date().toISOString()
              }),
              source_url: doc.url,
              content_hash: contentHash,
              extraction_method: 'bulk_edge_processing',
              priority_score: 1.0,
              search_metadata: JSON.stringify({
                processing_timestamp: new Date().toISOString(),
                source_method: 'bulk_edge_processor',
                content_length: content.length,
                extraction_metadata: { filename, content_type: 'text/html' }
              }),
              tags: doc.tags || ['healthcare', 'regulatory'],
              processing_status: 'pending',
              status: 'pending',
              vectors_generated: false
            })
            .select('document_id')
            .single()
          
          if (createError) {
            throw new Error(`Database insert failed: ${createError.message}`)
          }
          
          console.log(`✅ Created regulatory document: ${newDoc.document_id}`)
          
          // Step 5: Trigger vector processing via the existing vector-processor
          const vectorResponse = await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/vector-processor`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${Deno.env.get('SERVICE_ROLE_KEY') || Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`
            },
            body: JSON.stringify({
              documentId: newDoc.document_id,
              extractedText: content,
              documentType: 'regulatory'
            })
          })
          
          if (!vectorResponse.ok) {
            const errorText = await vectorResponse.text()
            console.error(`❌ Vector processing failed for ${newDoc.document_id}:`, errorText)
            // Don't fail the whole operation, just mark as needing retry
            await supabase
              .from('regulatory_documents')
              .update({ 
                processing_status: 'failed',
                error_message: `Vector processing failed: ${errorText}`
              })
              .eq('document_id', newDoc.document_id)
            
            return {
              success: false,
              title: title,
              url: doc.url,
              error: `Vector processing failed: ${errorText}`
            }
          }
          
          const vectorResult = await vectorResponse.json()
          console.log(`✅ Vector processing completed for ${newDoc.document_id}: ${vectorResult.chunksProcessed} vectors`)
          
          return {
            success: true,
            document_id: newDoc.document_id,
            title: title,
            url: doc.url,
            vector_count: vectorResult.chunksProcessed
          }
          
        } catch (error) {
          console.error(`❌ Failed to process ${doc.url}:`, error)
          return {
            success: false,
            title: doc.title || doc.url,
            url: doc.url,
            error: error.message
          }
        }
      })
      
      const batchResults = await Promise.all(batchPromises)
      results.push(...batchResults)
      
      // Small delay between batches to be respectful
      if (i + batch_size < documents.length) {
        await new Promise(resolve => setTimeout(resolve, 2000))
      }
    }
    
    // Compile final results
    const successful = results.filter(r => r.success)
    const failed = results.filter(r => !r.success)
    const totalVectors = successful.reduce((sum, r) => sum + (r.vector_count || 0), 0)
    
    console.log(`🎉 Bulk processing completed: ${successful.length} success, ${failed.length} failed, ${totalVectors} vectors`)
    
    return new Response(JSON.stringify({
      success: true,
      summary: {
        total_documents: documents.length,
        successful: successful.length,
        failed: failed.length,
        total_vectors_created: totalVectors
      },
      results: {
        successful: successful,
        failed: failed
      }
    }))
    
  } catch (error) {
    console.error('❌ Bulk processor error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Bulk processing failed',
        details: error.message 
      }),
      { status: 500 }
    )
  }
}) 