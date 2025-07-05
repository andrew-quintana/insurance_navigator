import { ChatOpenAI } from "@langchain/openai";
import { PromptTemplate } from "@langchain/core/prompts";
import { Document } from "@langchain/core/documents";
import { HumanMessage } from "@langchain/core/messages";

interface Section {
  title: string;
  content: string;
  level: number;
}

interface ChunkMetadata {
  section_title: string;
  section_level: number;
  chunk_index: number;
  total_chunks: number;
}

const SECTION_PROMPT = `
Analyze the following document text and identify its logical sections.
For each section, provide:
1. The section title/heading
2. The section level (1 for main sections, 2 for subsections, etc.)
3. The section content

Format your response as a JSON array of sections:
[
  {
    "title": "section title",
    "level": section level number,
    "content": "section content"
  }
]

Document text:
{text}
`;

export class SectionChunker {
  private llm: ChatOpenAI;
  private maxChunkSize: number;
  private chunkOverlap: number;

  constructor(apiKey: string, maxChunkSize = 1000, chunkOverlap = 200) {
    this.llm = new ChatOpenAI({
      modelName: "gpt-3.5-turbo-16k",
      temperature: 0,
      openAIApiKey: apiKey
    });
    this.maxChunkSize = maxChunkSize;
    this.chunkOverlap = chunkOverlap;
  }

  async identifySections(text: string): Promise<Section[]> {
    const prompt = new PromptTemplate({
      template: SECTION_PROMPT,
      inputVariables: ["text"]
    });

    const formattedPrompt = await prompt.format({ text });
    const message = new HumanMessage(formattedPrompt);
    const response = await this.llm.invoke([message]);
    
    try {
      return JSON.parse(response.content) as Section[];
    } catch (error) {
      console.error("Failed to parse sections:", error);
      // Fallback: treat entire text as one section
      return [{
        title: "Main Content",
        level: 1,
        content: text
      }];
    }
  }

  private chunkText(text: string, metadata: Partial<ChunkMetadata>): Document[] {
    const chunks: Document[] = [];
    let start = 0;

    while (start < text.length) {
      const end = Math.min(start + this.maxChunkSize, text.length);
      const chunk = text.slice(start, end);

      chunks.push(new Document({
        pageContent: chunk,
        metadata: {
          ...metadata,
          chunk_index: chunks.length,
          start_char: start,
          end_char: end
        }
      }));

      start = end - this.chunkOverlap;
      if (start >= text.length) break;
    }

    // Update total chunks in metadata
    return chunks.map(chunk => {
      chunk.metadata.total_chunks = chunks.length;
      return chunk;
    });
  }

  async createChunks(text: string): Promise<Document[]> {
    const sections = await this.identifySections(text);
    const allChunks: Document[] = [];

    for (const section of sections) {
      const sectionChunks = this.chunkText(section.content, {
        section_title: section.title,
        section_level: section.level
      });

      allChunks.push(...sectionChunks);
    }

    return allChunks;
  }
} 