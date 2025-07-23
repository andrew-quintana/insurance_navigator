import { 
  DocumentStructure, 
  Chunk,
  Section 
} from "./types.ts";
import { MarkdownHeaderParser } from "./markdown_parser.ts";

const CHUNK_SIZE = 6000;

export class DocumentChunker {
  private markdownParser: MarkdownHeaderParser;

  constructor(apiKey?: string) {
    this.markdownParser = new MarkdownHeaderParser();
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
   * Now uses direct markdown parsing instead of LLM to avoid context window issues
   */
  async chunkDocument(content: string): Promise<{
    chunks: Chunk[];
    metadata: DocumentStructure["metadata"];
  }> {
    console.log("🔍 Parsing markdown content directly (no LLM)");
    
    // Validate markdown structure
    const validation = this.markdownParser.validateMarkdownStructure(content);
    if (!validation.isValid) {
      console.warn("⚠️ Markdown validation issues:", validation.issues);
      if (!validation.hasHeaders) {
        throw new Error("No headers found in markdown content - cannot chunk without structure");
      }
    }
    
    console.log(`📊 Found ${validation.headerCount} headers in markdown`);
    
    // Parse markdown content into sections
    const sections = this.markdownParser.parseMarkdownToSections(content);
    console.log(`✅ Parsed into ${sections.length} sections`);
    
    // Generate metadata
    const metadata = this.markdownParser.getDocumentMetadata(sections);
    console.log(`📈 Document metadata:`, metadata);

    // Convert sections to chunks
    const chunks = this.sectionsToChunks(sections);
    console.log(`🧩 Generated ${chunks.length} chunks from sections`);

    return {
      chunks,
      metadata
    };
  }
} 