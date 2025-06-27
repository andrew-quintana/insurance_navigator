/**
 * Shared OpenAI embeddings module for Edge Functions
 */ export class OpenAIEmbeddings {
  apiKey;
  model;
  dimensions;
  constructor(apiKey){
    this.apiKey = apiKey;
    this.model = 'text-embedding-3-small';
    this.dimensions = 1536;
  }
  async embedText(text) {
    try {
      const response = await fetch('https://api.openai.com/v1/embeddings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          input: text,
          model: this.model,
          dimensions: this.dimensions
        })
      });
      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('OpenAI rate limit exceeded');
        }
        throw new Error(`OpenAI API error: ${response.status}`);
      }
      const result = await response.json();
      return result.data[0].embedding;
    } catch (error) {
      console.error('Error generating embedding:', error);
      throw error;
    }
  }
  async embedBatch(texts) {
    const embeddings = [];
    // Process in batches of 20 to avoid rate limits
    const batchSize = 20;
    for(let i = 0; i < texts.length; i += batchSize){
      const batch = texts.slice(i, Math.min(i + batchSize, texts.length));
      const batchPromises = batch.map((text)=>this.embedText(text));
      try {
        const batchResults = await Promise.all(batchPromises);
        embeddings.push(...batchResults);
      } catch (error) {
        console.error(`Error in batch ${i}-${i + batchSize}:`, error);
        // Use zero vectors for failed embeddings
        const zeroVectors = batch.map(()=>new Array(this.dimensions).fill(0));
        embeddings.push(...zeroVectors);
      }
    }
    return embeddings;
  }
}
