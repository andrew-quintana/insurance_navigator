/// <reference lib="deno.ns" />
// @deno-types="https://deno.land/x/types/deno.ns.d.ts"
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
        vector_length?: number;
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

    try {
        // Handle CORS preflight
        if (req.method === 'OPTIONS') {
            return new Response('ok', { 
                headers: {
                    ...corsHeaders,
                    'Allow': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                }
            })
        }

        // Handle unsupported methods
        if (!['GET', 'POST', 'OPTIONS'].includes(req.method)) {
            return new Response('Method not allowed', { 
                status: 405,
                headers: {
                    ...corsHeaders,
                    'Allow': 'GET, POST, OPTIONS',
                    'Content-Type': 'text/plain'
                }
            })
        }

        // Health check
        if (req.method === 'GET') {
            return new Response(
                JSON.stringify({ status: 'healthy', timestamp: new Date().toISOString() }),
                { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            );
        }

        console.log('🧮 Processing request...')
        
        // Parse request body
        const requestData: VectorRequest = await req.json();
        console.log(`📄 Processing document ${requestData.documentId} - Text length: ${requestData.extractedText.length} chars`);

        const { documentId, extractedText, metadata = {} } = requestData;

        // Clean and validate text
        const cleanedText = extractedText.trim()
            .replace(/[^\x20-\x7E\n]/g, '') // Keep only printable ASCII chars and newlines
            .replace(/\s+/g, ' '); // Normalize whitespace

        console.log(`📄 Cleaned text length: ${cleanedText.length} chars`);
        console.log(`📄 First 100 chars of cleaned text: "${cleanedText.slice(0, 100)}..."`);

        // Create chunks from cleaned text
        const chunker = new TextChunker();
        const chunks = chunker.createChunks(cleanedText);

        // Initialize OpenAI embeddings
        const openaiKey = Deno.env.get('OPENAI_API_KEY');
        if (!openaiKey) {
            throw new Error('OpenAI API key not found');
        }
        const embeddings = new OpenAIEmbeddings(openaiKey);

        // Initialize Supabase client
        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        if (!supabaseUrl || !supabaseKey) {
            throw new Error('Supabase credentials not found');
        }
        const supabase = createClient(supabaseUrl, supabaseKey);

        // Process chunks in batches
        const batchSize = 10;
        let totalVectors = 0;
        let batchStartTime = performance.now();

        console.log(`🔄 Processing Batch 1/1:
- Batch size: ${chunks.length} chunks
- Total chars in batch: ${chunks.reduce((sum, chunk) => sum + chunk.text.length, 0)}
            `);

        // Generate embeddings for all chunks
        const embeddingStartTime = performance.now();
        const batchEmbeddings = await embeddings.embedTexts(chunks.map(chunk => chunk.text));
        const embeddingTime = performance.now() - embeddingStartTime;
        metrics.embeddingTimes.push(embeddingTime);

        console.log(`
✨ Embedding Generation:
- Time taken: ${embeddingTime.toFixed(2)}ms
- Average time per chunk: ${(embeddingTime / chunks.length).toFixed(2)}ms
                `);

        // Store vectors in database
        const vectorData = chunks.map((chunk, idx) => ({
            document_record_id: documentId,
            chunk_index: chunk.metadata.chunk_index,
            content_embedding: batchEmbeddings[idx],
            chunk_text: chunk.text,
            metadata: chunk.metadata
        }));

        const { error: insertError } = await supabase
            .from('document_vectors')
            .insert(vectorData);

        if (insertError) {
            throw new Error(`Failed to store vectors: ${insertError.message}`);
        }

        totalVectors += chunks.length;
        const batchTime = performance.now() - batchStartTime;
        metrics.batchTimes.push(batchTime);
        metrics.batchSizes.push(chunks.length);

        console.log(`
✅ Batch Complete:
- Total time: ${batchTime.toFixed(2)}ms
- Storage time: ${(batchTime - embeddingTime).toFixed(2)}ms
                `);

        // Verify vectors were created
        const { data: verifyData, error: verifyError } = await supabase
            .from('document_vectors')
            .select('document_record_id, chunk_index')
            .eq('document_record_id', documentId);

        if (verifyError) {
            throw new Error(`Failed to verify vectors: ${verifyError.message}`);
        }

        console.log(`
✅ Vector Creation Verified:
- Expected vectors: ${chunks.length}
- Created vectors: ${verifyData.length}
- First vector dimensions: ${batchEmbeddings[0].length}
        `);

        // Calculate final metrics
        const totalTime = performance.now() - metrics.startTime;
        metrics.totalTime = totalTime;

        console.log(`
📊 Final Processing Statistics:
- Total time: ${totalTime.toFixed(2)}ms
- Chunking time: ${metrics.chunkingTime?.toFixed(2)}ms (${((metrics.chunkingTime || 0) / totalTime * 100).toFixed(2)}%)
- Average embedding time per batch: ${(metrics.embeddingTimes.reduce((a, b) => a + b, 0) / metrics.embeddingTimes.length).toFixed(2)}ms
- Average batch processing time: ${(metrics.batchTimes.reduce((a, b) => a + b, 0) / metrics.batchTimes.length).toFixed(2)}ms
- Processing rate: ${(metrics.totalCharsProcessed / totalTime * 1000).toFixed(2)} chars/second
        `);

        return new Response(
            JSON.stringify({
                success: true,
                vectors_created: totalVectors,
                processing_time_ms: totalTime
            }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );

    } catch (error) {
        console.error('❌ Error:', error);
        return new Response(
            JSON.stringify({
                error: error.message
            }),
            { 
                status: 500,
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            }
        );
    }
}); 