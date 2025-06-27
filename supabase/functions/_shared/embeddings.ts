/**
 * Shared OpenAI embeddings module for Edge Functions
 */

export class OpenAIEmbeddings {
    private apiKey: string;
    private model: string;
    private dimensions: number;

    constructor(apiKey: string) {
        this.apiKey = apiKey;
        this.model = 'text-embedding-ada-002';
        this.dimensions = 1536; // Used only for zero vectors when errors occur
    }

    async embedText(text: string): Promise<number[]> {
        try {
            // Clean and validate text before sending to OpenAI
            const cleanedText = text.trim()
                .replace(/[^\x20-\x7E\n]/g, '') // Keep only printable ASCII chars and newlines
                .replace(/\s+/g, ' ') // Normalize whitespace
                .slice(0, 8000); // OpenAI has a token limit, roughly 8000 chars

            if (!cleanedText || cleanedText.length < 10) {
                throw new Error('Text is too short or empty after cleaning');
            }

            const response = await fetch('https://api.openai.com/v1/embeddings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify({
                    input: cleanedText,
                    model: this.model
                })
            });

            if (!response.ok) {
                if (response.status === 429) {
                    throw new Error('OpenAI rate limit exceeded');
                }
                const errorBody = await response.text();
                throw new Error(`OpenAI API error: ${response.status} - ${errorBody}`);
            }

            const result = await response.json();
            return result.data[0].embedding;
        } catch (error) {
            console.error('Error generating embedding:', error);
            throw error;
        }
    }

    async embedBatch(texts: string[]): Promise<number[][]> {
        const embeddings: number[][] = [];
        
        // Process in batches of 20 to avoid rate limits
        const batchSize = 20;
        for (let i = 0; i < texts.length; i += batchSize) {
            const batch = texts.slice(i, Math.min(i + batchSize, texts.length));
            const batchPromises = batch.map(text => this.embedText(text));
            
            try {
                const batchResults = await Promise.all(batchPromises);
                embeddings.push(...batchResults);
            } catch (error) {
                console.error(`Error in batch ${i}-${i + batchSize}:`, error);
                // Use zero vectors for failed embeddings
                const zeroVectors = batch.map(() => new Array(this.dimensions).fill(0));
                embeddings.push(...zeroVectors);
            }
        }
        
        return embeddings;
    }
} 