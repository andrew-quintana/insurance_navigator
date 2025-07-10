import { z } from "zod";

// Define the section schema
export const SectionSchema = z.object({
  path: z.array(z.number()).describe("Hierarchy path e.g. [1], [1,2], [1,2,3]"),
  title: z.string().describe("Section heading"),
  content: z.string().describe("Section text content"),
  pages: z.tuple([z.number(), z.number()]).optional()
    .describe("Optional [startPage, endPage]"),
});

// Define the document structure schema
export const DocumentStructureSchema = z.object({
  sections: z.array(SectionSchema),
  metadata: z.object({
    totalSections: z.number(),
    maxDepth: z.number(),
    documentTitle: z.string().optional(),
  }),
});

// Export TypeScript types
export type Section = z.infer<typeof SectionSchema>;
export type DocumentStructure = z.infer<typeof DocumentStructureSchema>;

// Define chunk output schema
export const ChunkSchema = z.object({
  text: z.string(),
  path: z.array(z.number()),
  title: z.string(),
  chunk_index: z.number(),
});

export type Chunk = z.infer<typeof ChunkSchema>;

// Define the response schema for the edge function
export const ChunkerResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  chunks: z.number(),
  metadata: z.object({
    totalSections: z.number(),
    maxDepth: z.number(),
  }).optional(),
  error: z.string().optional(),
});

export type ChunkerResponse = z.infer<typeof ChunkerResponseSchema>; 