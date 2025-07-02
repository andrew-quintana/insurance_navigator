/**
 * Shared OpenAI embeddings module for Edge Functions
 */

export class OpenAIEmbeddings {
  private apiKey: string
  private model: string
  private dimensions: number

  constructor(apiKey: string) {
    this.apiKey = apiKey
    this.model = 'text-embedding-3-small'
    this.dimensions = 1536
  }

  async embedDocuments(texts: string[]): Promise<number[][]> {
    const response = await fetch('https://api.openai.com/v1/embeddings', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        input: texts,
        model: this.model
      })
    })

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${await response.text()}`)
    }

    const result = await response.json()
    return result.data.map((item: any) => item.embedding)
  }

  async embedQuery(text: string): Promise<number[]> {
    const embeddings = await this.embedDocuments([text])
    return embeddings[0]
  }

  getDimensions(): number {
    return this.dimensions
  }
} 