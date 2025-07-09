-- Enable the vector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

BEGIN;

-- Add embedding column to document_chunks
ALTER TABLE documents.document_chunks
  ADD COLUMN IF NOT EXISTS embedding vector(1536);  -- OpenAI ada-002 uses 1536 dimensions

-- Create an index for similarity search
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
  ON documents.document_chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);  -- Number of lists can be adjusted based on table size

-- Add a function to search similar chunks
CREATE OR REPLACE FUNCTION documents.search_similar_chunks(
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  document_id uuid,
  content text,
  section_path integer[],
  section_title text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.doc_id as document_id,
    dc.content,
    dc.section_path,
    dc.section_title,
    1 - (dc.embedding <=> query_embedding) as similarity
  FROM documents.document_chunks dc
  WHERE 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION documents.search_similar_chunks IS 'Search for similar document chunks using cosine similarity';

COMMIT; 