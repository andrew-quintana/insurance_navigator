import { assertEquals, assertExists } from "https://deno.land/std@0.217.0/testing/asserts.ts";
import { SectionChunker } from "chunking-service/section_chunker.ts";
import { edgeConfig } from "_shared/environment.ts";

interface TestContext {
  step(name: string, fn: () => Promise<void>): Promise<void>;
}

const TEST_TEXT = `
# Introduction
This is an introduction to the document. It contains important information about the topic.

## Background
Some background information about the topic. This section provides context for understanding the main content.

### Historical Context
A deeper dive into the history. This subsection explores the historical development of the topic.

# Main Content
The main content of the document. This section contains the core information and analysis.

## Section 1
First main section with important information. This part discusses key concepts and ideas.

## Section 2
Second main section with more details. This section provides additional analysis and examples.

# Conclusion
Final thoughts and summary. This section wraps up the main points and provides recommendations.
`;

Deno.test("Section Chunker", async (t: TestContext) => {
  let chunker: SectionChunker;

  // Setup
  chunker = new SectionChunker(edgeConfig.openaiApiKey);

  await t.step("should create chunks with proper metadata", async () => {
    const chunks = await chunker.createChunks(TEST_TEXT);
    assertExists(chunks, "Chunks should be created");
    assertEquals(chunks.length > 0, true, "Should have at least one chunk");

    chunks.forEach(chunk => {
      assertExists(chunk.metadata.section_title, "Section title should exist");
      assertExists(chunk.metadata.section_level, "Section level should exist");
      assertExists(chunk.metadata.chunk_index, "Chunk index should exist");
      assertExists(chunk.metadata.total_chunks, "Total chunks should exist");

      assertEquals(typeof chunk.metadata.section_level === 'number', true, "Section level should be a number");
      assertEquals(chunk.metadata.section_level > 0, true, "Section level should be positive");
      assertEquals(chunk.metadata.section_level <= 3, true, "Section level should be <= 3");
    });
  });

  await t.step("should preserve all content in chunks", async () => {
    const chunks = await chunker.createChunks(TEST_TEXT);
    const allContent = chunks.map(c => c.pageContent).join("");
    const normalizedContent = allContent.replace(/\s+/g, ' ').trim();
    const normalizedTestText = TEST_TEXT.replace(/\s+/g, ' ').trim();

    assertEquals(normalizedContent.includes(normalizedTestText), true, "All content should be preserved");
  });

  await t.step("should identify sections correctly", async () => {
    const chunks = await chunker.createChunks(TEST_TEXT);

    // Check main sections (level 1)
    const mainSections = chunks.filter(c =>
      c.metadata.section_level === 1
    );
    assertEquals(mainSections.length > 0, true, "Should have main sections");

    // Check subsections (level 2)
    const subSections = chunks.filter(c =>
      c.metadata.section_level === 2
    );
    assertEquals(subSections.length > 0, true, "Should have subsections");

    // Check sub-subsections (level 3)
    const subSubSections = chunks.filter(c =>
      c.metadata.section_level === 3
    );
    assertEquals(subSubSections.length > 0, true, "Should have sub-subsections");
  });
}); 