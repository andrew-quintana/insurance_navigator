/// <reference lib="deno.ns" />
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'
import { OpenAIEmbeddings } from '../_shared/embeddings.ts'

// Performance monitoring
interface ProcessingMetrics {
    startTime: number;
    chunkingTime?: number;
    embeddingTimes: number[];
    batchTimes: number[];
    totalTime?: number;
    chunksCreated: number;
    totalCharsProcessed: number;
    averageChunkSize: number;
    batchSizes: number[];
}

const metrics: ProcessingMetrics = {
    startTime: 0,
    embeddingTimes: [],
    batchTimes: [],
    chunksCreated: 0,
    totalCharsProcessed: 0,
    averageChunkSize: 0,
    batchSizes: []
};

interface VectorRequest {
    documentId: string;
    extractedText: string;
  metadata?: {
        title?: string;
        content_type?: string;
        extraction_method?: string;
        [key: string]: any;
    };
}

interface TextChunk {
    text: string;
    metadata: {
        chunk_index: number;
        total_chunks: number;
        chunk_length: number;
        start_char: number;
        end_char: number;
    };
}

class TextChunker {
    private chunkSize: number;
    private chunkOverlap: number;

    constructor(chunkSize = 1000, chunkOverlap = 200) {
        this.chunkSize = chunkSize;
        this.chunkOverlap = chunkOverlap;
    }

    createChunks(text: string): TextChunk[] {
        console.log(`🔍 Starting text chunking - Total text length: ${text.length} characters`);
        const chunkStartTime = performance.now();
        
        const chunks: TextChunk[] = [];
        let start = 0;
        let chunkIndex = 0;
        let totalChars = 0;

        while (start < text.length) {
            // Calculate end position
            let end = start + this.chunkSize;
            
            // Adjust end to not break words
            if (end < text.length) {
                // Look for next period, question mark, or exclamation point
                const nextSentenceEnd = text.slice(end).search(/[.!?]\s/);
                if (nextSentenceEnd !== -1 && nextSentenceEnd < 100) {
                    end += nextSentenceEnd + 2; // +2 to include the punctuation and space
                    console.log(`📝 Extended chunk ${chunkIndex} to sentence boundary: +${nextSentenceEnd + 2} chars`);
                } else {
                    // If no sentence end found, look for next space
                    const nextSpace = text.slice(end).search(/\s/);
                    if (nextSpace !== -1 && nextSpace < 50) {
                        end += nextSpace;
                        console.log(`📝 Extended chunk ${chunkIndex} to word boundary: +${nextSpace} chars`);
  }
}
            }

            // Create chunk
            const chunkText = text.slice(start, end).trim();
            if (chunkText) {
                totalChars += chunkText.length;
                chunks.push({
                    text: chunkText,
                    metadata: {
                        chunk_index: chunkIndex,
                        total_chunks: -1, // Will be updated after all chunks are created
                        chunk_length: chunkText.length,
                        start_char: start,
                        end_char: end
                    }
                });
                console.log(`📊 Created chunk ${chunkIndex}: ${chunkText.length} chars`);
                chunkIndex++;
            }

            // Move start position
            start = end - this.chunkOverlap;
        }

        // Update total_chunks in metadata
        chunks.forEach(chunk => {
            chunk.metadata.total_chunks = chunks.length;
        });

        const chunkingTime = performance.now() - chunkStartTime;
        console.log(`
🔢 Chunking Statistics:
- Total chunks created: ${chunks.length}
- Average chunk size: ${(totalChars / chunks.length).toFixed(2)} chars
- Chunking time: ${chunkingTime.toFixed(2)}ms
- Processing rate: ${(totalChars / chunkingTime * 1000).toFixed(2)} chars/second
        `);

        // Update metrics
        metrics.chunkingTime = chunkingTime;
        metrics.chunksCreated = chunks.length;
        metrics.totalCharsProcessed = totalChars;
        metrics.averageChunkSize = totalChars / chunks.length;

        return chunks;
    }
}

console.log('🧮 Vector processor starting...')

serve(async (req) => {
    metrics.startTime = performance.now();
    console.log(`🚀 Starting vector processing at ${new Date().toISOString()}`);

  // Handle CORS
  if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders });
    }

    // Health check
    if (req.method === 'GET') {
        return new Response(
            JSON.stringify({ status: 'healthy', timestamp: new Date().toISOString() }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
  }

  try {
        console.log('🧮 Processing request...')
        // Parse request body
        const rawBody = await req.text();
        console.log('📦 Raw request body:', rawBody);
        
        let requestData: VectorRequest;
        try {
            // Try parsing as JSON string first
            requestData = JSON.parse(rawBody);
        } catch (parseError) {
            console.error('❌ Failed to parse request body as JSON:', parseError);
            throw new Error(`Invalid request body: ${parseError.message}`);
        }

        const { documentId, extractedText, metadata = {} } = requestData;

    if (!documentId || !extractedText) {
            console.error('❌ Missing required parameters:', { documentId, hasExtractedText: !!extractedText });
            throw new Error('Missing required parameters: documentId and extractedText');
    }

        console.log(`📄 Processing document ${documentId} - Text length: ${extractedText.length} chars`);

        // Initialize Supabase client
        const supabaseClient = createClient(
            Deno.env.get('SUPABASE_URL') ?? '',
            Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
        );

    // Get document record
    const { data: document, error: docError } = await supabaseClient
      .from('documents')
      .select('*')
      .eq('id', documentId)
            .single();

    if (docError || !document) {
            throw new Error(`Document not found: ${docError?.message || 'Unknown error'}`);
    }

        // Create text chunks
        const chunker = new TextChunker();
        const chunks = chunker.createChunks(extractedText);

    // Initialize OpenAI embeddings
        const embeddings = new OpenAIEmbeddings(Deno.env.get('OPENAI_API_KEY') ?? '');

        // Process chunks in batches to avoid rate limits
        const batchSize = 20;
        const results = [];
        
        for (let i = 0; i < chunks.length; i += batchSize) {
            const batchStartTime = performance.now();
            const batch = chunks.slice(i, Math.min(i + batchSize, chunks.length));
            
            console.log(`
🔄 Processing Batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(chunks.length / batchSize)}:
- Batch size: ${batch.length} chunks
- Total chars in batch: ${batch.reduce((sum, chunk) => sum + chunk.text.length, 0)}
            `);

            try {
                // Generate embeddings for batch
                const embeddingStartTime = performance.now();
                const batchEmbeddings = await embeddings.embedBatch(
                    batch.map(chunk => chunk.text)
                );
                const embeddingTime = performance.now() - embeddingStartTime;
                
                console.log(`
✨ Embedding Generation:
- Time taken: ${embeddingTime.toFixed(2)}ms
- Average time per chunk: ${(embeddingTime / batch.length).toFixed(2)}ms
                `);

                metrics.embeddingTimes.push(embeddingTime);
                metrics.batchSizes.push(batch.length);

                // Store vectors
                const vectorInserts = batch.map((chunk, batchIndex) => ({
                    document_id: documentId,
                    chunk_index: chunk.metadata.chunk_index,
                    content_embedding: batchEmbeddings[batchIndex],
                    chunk_text: chunk.text,
                    chunk_metadata: {
                        ...chunk.metadata,
          ...metadata,
          processed_at: new Date().toISOString(),
                        embedding_method: 'openai',
                        processing_stats: {
                            chunk_processing_time_ms: embeddingTime / batch.length,
                            total_batch_time_ms: performance.now() - batchStartTime
                        }
                    }
                }));

                const { error: insertError } = await supabaseClient
          .from('document_vectors')
                    .insert(vectorInserts);

                if (insertError) {
                    console.error(`❌ Failed to store vectors for batch ${i / batchSize + 1}:`, insertError);
                    throw insertError;
                }

                results.push(...vectorInserts.map(v => ({
                    chunk_index: v.chunk_index,
                    vector_length: v.content_embedding.length
                })));

                const batchTime = performance.now() - batchStartTime;
                metrics.batchTimes.push(batchTime);
                
                console.log(`
✅ Batch Complete:
- Total time: ${batchTime.toFixed(2)}ms
- Storage time: ${(batchTime - embeddingTime).toFixed(2)}ms
                `);

      } catch (error) {
                console.error(`❌ Error processing batch ${i / batchSize + 1}:`, error);
                throw error;
      }
    }

        metrics.totalTime = performance.now() - metrics.startTime;

        console.log(`
📊 Final Processing Statistics:
- Total time: ${metrics.totalTime.toFixed(2)}ms
- Chunking time: ${metrics.chunkingTime?.toFixed(2)}ms (${((metrics.chunkingTime || 0) / metrics.totalTime * 100).toFixed(2)}%)
- Average embedding time per batch: ${(metrics.embeddingTimes.reduce((a, b) => a + b, 0) / metrics.embeddingTimes.length).toFixed(2)}ms
- Average batch processing time: ${(metrics.batchTimes.reduce((a, b) => a + b, 0) / metrics.batchTimes.length).toFixed(2)}ms
- Processing rate: ${(metrics.totalCharsProcessed / metrics.totalTime * 1000).toFixed(2)} chars/second
        `);

    return new Response(
      JSON.stringify({
        success: true,
                document_id: documentId,
                chunks_processed: chunks.length,
                results: results,
                processing_metrics: metrics
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );

  } catch (error) {
        console.error('Error:', error);
    return new Response(
      JSON.stringify({
                error: error.message,
                processing_metrics: metrics 
      }),
            { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
  }
}); 