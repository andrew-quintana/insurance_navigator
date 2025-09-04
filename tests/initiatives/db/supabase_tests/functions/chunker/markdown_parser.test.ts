/// <reference lib="deno.ns" />
import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { MarkdownHeaderParser } from "../markdown_parser.ts";
import { DocumentChunker } from "../document_chunker.ts";

const sampleMarkdown = `
# Introduction
This is the introduction section with important background information that provides context for the entire document.

## Background
This section covers the background information needed to understand the problem domain.

### Technical Requirements
Some detailed technical requirements that are critical for implementation.

### Business Requirements
Business requirements that must be met for project success.

## Methodology
This section explains the methodology used in our approach.

### Data Collection
Details about how data was collected and processed.

#### Primary Sources
Information about primary data sources used.

#### Secondary Sources
Information about secondary data sources used.

### Analysis Approach
Description of the analytical methods employed.

## Results
This section presents the results of our analysis.

### Key Findings
The most important findings from our research.

### Performance Metrics
Quantitative results and performance indicators.

# Conclusion
Final thoughts and recommendations based on the analysis.

## Future Work
Suggestions for future research and development.
`;

Deno.test("MarkdownHeaderParser - Basic parsing", () => {
  const parser = new MarkdownHeaderParser();
  const sections = parser.parseMarkdownToSections(sampleMarkdown);
  
  // Should have parsed multiple sections
  assertExists(sections);
  assertEquals(sections.length > 0, true);
  
  // Check first section
  const firstSection = sections[0];
  assertEquals(firstSection.title, "Introduction");
  assertEquals(firstSection.path, [1]);
  assertEquals(firstSection.content.includes("introduction section"), true);
});

Deno.test("MarkdownHeaderParser - Hierarchical paths", () => {
  const parser = new MarkdownHeaderParser();
  const sections = parser.parseMarkdownToSections(sampleMarkdown);
  
  // Find specific sections to test hierarchy
  const backgroundSection = sections.find(s => s.title === "Background");
  const techReqSection = sections.find(s => s.title === "Technical Requirements");
  const primarySourcesSection = sections.find(s => s.title === "Primary Sources");
  
  assertEquals(backgroundSection?.path, [1, 1]);
  assertEquals(techReqSection?.path, [1, 1, 1]);
  assertEquals(primarySourcesSection?.path, [1, 2, 1, 1]);
});

Deno.test("MarkdownHeaderParser - Metadata extraction", () => {
  const parser = new MarkdownHeaderParser();
  const sections = parser.parseMarkdownToSections(sampleMarkdown);
  const metadata = parser.getDocumentMetadata(sections);
  
  assertEquals(metadata.totalSections, sections.length);
  assertEquals(metadata.maxDepth, 4); // Should be 4 levels deep
  assertEquals(metadata.documentTitle, "Introduction");
});

Deno.test("MarkdownHeaderParser - Validation", () => {
  const parser = new MarkdownHeaderParser();
  
  // Test valid markdown
  const validResult = parser.validateMarkdownStructure(sampleMarkdown);
  assertEquals(validResult.isValid, true);
  assertEquals(validResult.hasHeaders, true);
  assertEquals(validResult.headerCount > 0, true);
  
  // Test invalid markdown (no headers)
  const invalidResult = parser.validateMarkdownStructure("Just plain text with no headers");
  assertEquals(invalidResult.isValid, false);
  assertEquals(invalidResult.hasHeaders, false);
  assertEquals(invalidResult.headerCount, 0);
});

Deno.test("DocumentChunker - End-to-end chunking", async () => {
  const chunker = new DocumentChunker();
  const result = await chunker.chunkDocument(sampleMarkdown);
  
  // Should have chunks and metadata
  assertExists(result.chunks);
  assertExists(result.metadata);
  assertEquals(result.chunks.length > 0, true);
  
  // Check chunk structure
  const firstChunk = result.chunks[0];
  assertExists(firstChunk.text);
  assertExists(firstChunk.title);
  assertExists(firstChunk.path);
  assertEquals(typeof firstChunk.chunk_index, "number");
  
  // Metadata should match
  assertEquals(result.metadata.totalSections > 0, true);
  assertEquals(result.metadata.maxDepth, 4);
  assertEquals(result.metadata.documentTitle, "Introduction");
});

Deno.test("DocumentChunker - Large content chunking", async () => {
  // Create a large section to test chunking behavior
  const largeContent = "# Large Section\n" + "This is a very long paragraph. ".repeat(500);
  
  const chunker = new DocumentChunker();
  const result = await chunker.chunkDocument(largeContent);
  
  // Should break large content into multiple chunks
  const largeSectionChunks = result.chunks.filter(c => c.title === "Large Section");
  assertEquals(largeSectionChunks.length > 1, true);
  
  // All chunks should have same path and title
  for (const chunk of largeSectionChunks) {
    assertEquals(chunk.title, "Large Section");
    assertEquals(chunk.path, [1]);
  }
});

Deno.test("DocumentChunker - Error handling", async () => {
  const chunker = new DocumentChunker();
  
  try {
    await chunker.chunkDocument("No headers here, just plain text");
    assertEquals(true, false, "Should have thrown error for content without headers");
  } catch (error) {
    assertEquals((error as Error).message.includes("No headers found"), true);
  }
});