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

// Define types for tools functionality
interface ToolChoice {
    type: "auto" | "any" | "tool" | "none";
    name?: string;
}

interface Tool {
    name: string;
    description: string;
    input_schema: {
        type: string;
        properties: Record<string, unknown>;
        required: string[];
    };
}

interface MessageWithTools {
    model: string;
    max_tokens: number;
    temperature: number;
    system?: string;
    messages: { role: "user" | "assistant" | "system"; content: string }[];
    tools: Tool[];
    tool_choice: ToolChoice;
    betas: string[];
}

interface ToolCallResponse {
    tool_call: {
        output: string;
    };
}

interface ToolUseResponse {
    type: "tool_use";
    id: string;
    name: string;
    input: any;
}

interface TextResponse {
    text: string;
}

type ClaudeContent = ToolUseResponse | TextResponse;

/**
 * Analyzes document structure using Claude to identify section boundaries and hierarchy
 */
async function analyzeSections(content: string, anthropic: Anthropic): Promise<DocumentData> {
    // Get the function schema
    const functionSchema = {
        name: "extract_document_structure",
        description: "Extract hierarchical section information from a document",
        input_schema: {
            type: "object",
            properties: {
                content: {
                    type: "string",
                    description: "The full parsed text as one string"
                },
                sections: {
                    type: "array",
                    items: {
                        type: "object",
                        properties: {
                            path: {
                                type: "array",
                                items: { type: "number" },
                                description: "Hierarchy path e.g. [1], [1,2], [1,2,3]"
                            },
                            title: {
                                type: "string",
                                description: "Section heading"
                            },
                            content: {
                                type: "string",
                                description: "Section text content"
                            },
                            pages: {
                                type: "array",
                                items: { type: "number" },
                                minItems: 2,
                                maxItems: 2,
                                description: "Optional [startPage, endPage]"
                            }
                        },
                        required: ["path", "title", "content"]
                    }
                }
            },
            required: ["content", "sections"]
        }
    };

    try {
        const messageParams: MessageWithTools = {
            model: 'claude-3-haiku-20240307',
            max_tokens: 4096,
            temperature: 0,
            system: `You are a document structure analysis agent that extracts hierarchical section information from documents.
Guidelines for section extraction:
- Path depth can vary (e.g., [1], [1,2], [1,2,1,1]) to represent the true document hierarchy
- Only include meaningful content, filtering out noise
- Skip footers, repeated headers, and other non-content elements
- Each section must have a clear title and content
- Page ranges should be included when they can be reliably determined`,
            messages: [{
                role: 'user',
                content: `Please analyze this document and extract its section hierarchy:\n\n${content}`
            }],
            tools: [functionSchema],
            tool_choice: {
                type: "tool",
                name: "extract_document_structure"
            },
            betas: ["tools-2024-03-14"]
        };

        const message = await anthropic.messages.create(messageParams as any);
        console.log("📄 Claude response:", JSON.stringify(message.content[0], null, 2));

        // Check if we got a tool use response
        const response = message.content[0] as ClaudeContent;
        
        if ('type' in response && response.type === 'tool_use') {
            return JSON.parse(response.input.content) as DocumentData;
        }

        if ('text' in response) {
            return JSON.parse(response.text) as DocumentData;
        }

        throw new Error("Unexpected response format from Claude");
    } catch (error) {
        console.error("❌ Failed to analyze document sections:", error);
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

// Export the function
export { analyzeSections, type DocumentData, type Section };
