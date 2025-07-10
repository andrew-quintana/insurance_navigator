import { describe, it, expect, beforeEach } from 'vitest';
import { DocumentChunker } from '../document_chunker';

describe('DocumentChunker', () => {
  let chunker: DocumentChunker;

  beforeEach(() => {
    // Initialize with test API key
    chunker = new DocumentChunker('test-api-key');
  });

  it('should chunk a simple document correctly', async () => {
    const sampleDocument = `
# Introduction
This is the introduction section of our document.

## Background
Here is some background information about our topic.
It spans multiple lines to test paragraph handling.

### Technical Details
This section contains technical information.
- Point 1
- Point 2

## Conclusion
Finally, we conclude with a summary.
    `.trim();

    const result = await chunker.chunkDocument(sampleDocument);

    // Verify structure
    expect(result.chunks).toBeDefined();
    expect(result.metadata).toBeDefined();
    expect(result.metadata.totalSections).toBe(4);
    expect(result.metadata.maxDepth).toBe(3);

    // Verify chunks
    expect(result.chunks.length).toBeGreaterThan(0);
    
    // Verify first chunk has correct structure
    const firstChunk = result.chunks[0];
    expect(firstChunk).toMatchObject({
      text: expect.any(String),
      path: expect.arrayContaining([expect.any(Number)]),
      title: expect.any(String),
      chunk_index: expect.any(Number)
    });

    // Verify hierarchical structure
    const paths = result.chunks.map(c => c.path);
    expect(paths).toContainEqual([1]); // Introduction
    expect(paths).toContainEqual([1, 1]); // Background
    expect(paths).toContainEqual([1, 1, 1]); // Technical Details
    expect(paths).toContainEqual([1, 2]); // Conclusion
  });

  it('should handle empty documents', async () => {
    const result = await chunker.chunkDocument('');
    
    expect(result.chunks).toHaveLength(0);
    expect(result.metadata).toMatchObject({
      totalSections: 0,
      maxDepth: 0
    });
  });

  it('should respect chunk size limits', async () => {
    // Create a large document with repeated content
    const largeSection = 'This is a test sentence. '.repeat(500);
    const largeDocument = `
# Large Section
${largeSection}

## Subsection
${largeSection}
    `.trim();

    const result = await chunker.chunkDocument(largeDocument);

    // Verify chunks are within size limit
    const maxChunkSize = 6000; // From CHUNK_SIZE constant
    result.chunks.forEach(chunk => {
      expect(chunk.text.length).toBeLessThanOrEqual(maxChunkSize);
    });
  });
}); 