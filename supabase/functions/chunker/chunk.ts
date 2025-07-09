import { Anthropic } from '@anthropic-ai/sdk';

interface Section {
    path: number[];
    title: string;
    content: string;
    pages?: [number, number];
}

interface DocumentData {
    content: string;
    sections: Section[];
}

/**
 * Analyzes document structure using Claude to identify section boundaries and hierarchy
 */
async function analyzeSections(content: string, anthropic: Anthropic): Promise<DocumentData> {
    const message = await anthropic.messages.create({
        model: 'claude-3-haiku-20240307',
        max_tokens: 4096,
        messages: [{
            role: 'user',
            content: `You are a document structure analysis agent. Analyze the following document and extract its section hierarchy with content and page ranges.

Return a JSON object with:
- "content": the full parsed text (as one string)
- "sections": an array of objects, each with:
  - "path": array of integers for hierarchy (e.g. [1], [1,2], [1,2,3])
  - "title": section heading as string
  - "content": the parsed text under this section
  - "pages": [startPage, endPage] if available, otherwise omit

Guidelines:
- Path depth can vary (e.g., [1], [1,2], [1,2,1,1])
- Only include meaningful content
- Skip footers, repeated headers, and noise
- Ensure valid JSON only (no prose, no wrapping)

Document:
${content}`
        }],
        temperature: 0
    });

    try {
        const response = message.content[0].text;
        return JSON.parse(response) as DocumentData;
    } catch (error) {
        console.error("❌ Failed to parse LLM response:", error);
        throw new Error("Failed to analyze document sections");
    }
}

/**
 * Splits a section into chunks of roughly equal size, preserving semantic boundaries
 */
function splitIntoChunks(text: string, maxChunkSize: number = 6000): string[] {
    const chunks: string[] = [];
    let currentChunk = "";
    
    // Split into paragraphs
    const paragraphs = text.split(/\n\n+/);
    
    for (const paragraph of paragraphs) {
        // If adding this paragraph would exceed chunk size, start new chunk
        if (currentChunk.length + paragraph.length > maxChunkSize && currentChunk.length > 0) {
            chunks.push(currentChunk.trim());
            currentChunk = "";
        }
        
        // If single paragraph is larger than chunk size, split on sentences
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
    
    // Add final chunk if not empty
    if (currentChunk.trim().length > 0) {
        chunks.push(currentChunk.trim());
    }
    
    return chunks;
}

/**
 * Processes a document into semantically meaningful chunks with hierarchy information
 */
export async function chunkDocument(
    documentData: { markdown: string },
    anthropic: Anthropic
): Promise<{
    text: string;
    path: number[];
    title: string;
    chunk_index: number;
}[]> {
    console.log("📊 Analyzing document structure");
    const analyzed = await analyzeSections(documentData.markdown, anthropic);
    
    console.log(`✅ Found ${analyzed.sections.length} sections`);
    
    const chunks: {
        text: string;
        path: number[];
        title: string;
        chunk_index: number;
    }[] = [];
    
    for (const section of analyzed.sections) {
        const sectionChunks = splitIntoChunks(section.content);
        
        console.log(`📄 Processing section "${section.title}" with ${sectionChunks.length} chunks`);
        
        for (const [index, chunkText] of sectionChunks.entries()) {
            chunks.push({
                text: chunkText,
                path: section.path,
                title: section.title,
                chunk_index: index
            });
        }
    }
    
    console.log(`✅ Generated ${chunks.length} total chunks`);
    return chunks;
}
