import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient, SupabaseClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

interface ProcessingRequest {
  urls: string[]
  metadata?: {
    jurisdiction?: string
    programs?: string[]
    tags?: string[]
    [key: string]: any
  }
}

interface ProcessingResult {
  status: 'processed' | 'duplicate' | 'failed'
  url: string
  document_id?: string
  existing_document_id?: string
  message?: string
  processing_result?: any
  error?: string
}

interface BatchResults {
  processed: ProcessingResult[]
  failed: ProcessingResult[]
  duplicates: ProcessingResult[]
  total_vectors_created: number
  processing_time: number | null
  start_time: string
}

serve(async (req: Request) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Create Supabase client
    const supabaseClient: SupabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Parse request body
    const { urls, metadata = {} } = await req.json() as ProcessingRequest

    if (!urls || !Array.isArray(urls) || urls.length === 0) {
      throw new Error('No URLs provided')
    }

    // Process URLs in batches to avoid timeouts
    const batchSize = 3
    const results: BatchResults = {
      processed: [],
      failed: [],
      duplicates: [],
      total_vectors_created: 0,
      processing_time: null,
      start_time: new Date().toISOString()
    }

    for (let i = 0; i < urls.length; i += batchSize) {
      const batch = urls.slice(i, i + batchSize)
      console.log(`Processing batch ${i/batchSize + 1}: ${batch.length} URLs`)

      const batchPromises = batch.map(async (url): Promise<ProcessingResult> => {
        try {
          // Check for existing document
          const { data: existingDoc } = await supabaseClient
            .from('documents')
            .select('id')
            .eq('source_url', url)
            .eq('document_type', 'regulatory')
            .single()

          if (existingDoc) {
            console.log(`Duplicate found for ${url}`)
            return {
              status: 'duplicate',
              url,
              existing_document_id: existingDoc.id,
              message: 'Document already exists with same URL'
            }
          }

          // Create document record
          const { data: doc, error: docError } = await supabaseClient
            .from('documents')
            .insert({
              storage_path: url,
              original_filename: url.split('/').pop() || 'regulatory_document',
              document_type: 'regulatory',
              jurisdiction: metadata.jurisdiction || 'United States',
              program: metadata.programs || ['Healthcare', 'General'],
              source_url: url,
              source_last_checked: new Date().toISOString(),
              priority_score: 1.0,
              metadata: {
                processing_timestamp: new Date().toISOString(),
                source_method: 'bulk_processor',
                extraction_method: 'edge_function',
                metadata_override: metadata
              },
              tags: metadata.tags || ['healthcare', 'regulatory'],
              status: 'pending'
            })
            .select()
            .single()

          if (docError) {
            throw new Error(`Failed to create document record: ${docError.message}`)
          }

          // Call doc-parser to process the document
          const processingResponse = await fetch(
            `${Deno.env.get('SUPABASE_URL')}/functions/v1/doc-parser`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`
              },
              body: JSON.stringify({
                documentId: doc.id,
                url,
                documentType: 'regulatory',
                metadata: {
                  jurisdiction: metadata.jurisdiction,
                  programs: metadata.programs,
                  tags: metadata.tags
                }
              })
            }
          )

          const processingResult = await processingResponse.json()

          if (!processingResponse.ok) {
            throw new Error(`Processing failed: ${processingResult.error || 'Unknown error'}`)
          }

          return {
            status: 'processed',
            url,
            document_id: doc.id,
            processing_result: processingResult
          }

        } catch (error) {
          console.error(`Failed to process ${url}: ${error}`)
          return {
            status: 'failed',
            url,
            error: error.message
          }
        }
      })

      const batchResults = await Promise.all(batchPromises)

      for (const result of batchResults) {
        if (result.status === 'processed') {
          results.processed.push(result)
          results.total_vectors_created += result.processing_result?.vector_count || 0
        } else if (result.status === 'duplicate') {
          results.duplicates.push(result)
        } else {
          results.failed.push(result)
        }
      }

      // Small delay between batches
      if (i + batchSize < urls.length) {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }

    results.processing_time = (new Date().getTime() - new Date(results.start_time).getTime()) / 1000

    return new Response(
      JSON.stringify(results),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Bulk processing failed:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}) 