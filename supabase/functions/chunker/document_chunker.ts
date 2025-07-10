import { ChatAnthropic } from "npm:@langchain/anthropic@0.1.1";
import { PromptTemplate } from "npm:@langchain/core@0.1.1/prompts";
import { StructuredOutputParser } from "npm:langchain@0.1.1/output_parsers";
import { 
  DocumentStructure, 
  DocumentStructureSchema, 
  Chunk,
  Section 
} from "./types.ts";

const CHUNK_SIZE = 6000;

export class DocumentChunker {
  private model: ChatAnthropic;
  private parser: StructuredOutputParser<DocumentStructure>;
  private prompt: PromptTemplate;

  constructor(apiKey: string) {
    this.model = new ChatAnthropic({
      modelName: "claude-3-haiku-20240307",
      anthropicApiKey: apiKey,
      temperature: 0,
    });

    this.parser = StructuredOutputParser.fromZodSchema(DocumentStructureSchema);

    this.prompt = PromptTemplate.fromTemplate(`
      You are a document structure analysis agent that extracts hierarchical section information from documents.
      
      Guidelines for section extraction:
      - Path depth can vary (e.g., [1], [1,2], [1,2,1,1]) to represent the true document hierarchy
      - Only include meaningful content, filtering out noise
      - Skip footers, repeated headers, and other non-content elements
      - Each section must have a clear title and content
      - Page ranges should be included when they can be reliably determined
      
      {format_instructions}
      
      Please analyze this document and extract its section hierarchy:
      
      {text}
    `);
  }

  /**
   * Splits text into chunks while preserving semantic boundaries
   */
  private splitIntoChunks(text: string, maxChunkSize: number = CHUNK_SIZE): string[] {
    const chunks: string[] = [];
    let currentChunk = "";
    
    // Split into paragraphs
    const paragraphs = text.split(/\n\n+/);
    
    for (const paragraph of paragraphs) {
      if (currentChunk.length + paragraph.length > maxChunkSize && currentChunk.length > 0) {
        chunks.push(currentChunk.trim());
        currentChunk = "";
      }
      
      if (paragraph.length > maxChunkSize) {
        const sentences = paragraph.match(/[^.!?]+[.!?]+/g) || [paragraph];
        for (const sentence of sentences) {
          if (currentChunk.length + sentence.length > maxChunkSize && currentChunk.length > 0) {
            chunks.push(currentChunk.trim());
            currentChunk = "";
          }
          currentChunk += sentence + " ";
        }
      } else {
        currentChunk += paragraph + "\n\n";
      }
    }
    
    if (currentChunk.trim().length > 0) {
      chunks.push(currentChunk.trim());
    }
    
    return chunks;
  }

  /**
   * Converts sections into chunks with metadata
   */
  private sectionsToChunks(sections: Section[]): Chunk[] {
    const chunks: Chunk[] = [];
    
    for (const section of sections) {
      const sectionChunks = this.splitIntoChunks(section.content);
      
      for (let i = 0; i < sectionChunks.length; i++) {
        chunks.push({
          text: sectionChunks[i],
          path: section.path,
          title: section.title,
          chunk_index: i
        });
      }
    }
    
    return chunks;
  }

  /**
   * Process a document into semantically meaningful chunks with hierarchy information
   */
  async chunkDocument(content: string): Promise<{
    chunks: Chunk[];
    metadata: DocumentStructure["metadata"];
  }> {
    // Create the chain
    const chain = this.prompt
      .pipe(this.model)
      .pipe(this.parser);

    // Run the chain
    const result = await chain.invoke({
      format_instructions: this.parser.getFormatInstructions(),
      text: content
    });

    // Convert sections to chunks
    const chunks = this.sectionsToChunks(result.sections);

    return {
      chunks,
      metadata: result.metadata
    };
  }
} 