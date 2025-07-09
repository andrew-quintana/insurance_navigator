-- Update document_chunks and documents table structure
BEGIN;

-- Update documents table
ALTER TABLE documents.documents
  ADD COLUMN IF NOT EXISTS parsed_path text;

-- Drop existing columns that are no longer needed
ALTER TABLE documents.document_chunks 
  DROP COLUMN IF EXISTS level_1,
  DROP COLUMN IF EXISTS level_2,
  DROP COLUMN IF EXISTS level_3,
  DROP COLUMN IF EXISTS full_chunk_id,
  DROP COLUMN IF EXISTS tokens,
  DROP COLUMN IF EXISTS vector;

-- Add new columns
ALTER TABLE documents.document_chunks
  ADD COLUMN IF NOT EXISTS section_path integer[],
  ADD COLUMN IF NOT EXISTS section_title text,
  ADD COLUMN IF NOT EXISTS page_start int,
  ADD COLUMN IF NOT EXISTS page_end int;

-- Rename timestamp columns
ALTER TABLE documents.document_chunks 
  RENAME COLUMN created_at TO chunked_at;
ALTER TABLE documents.document_chunks 
  RENAME COLUMN updated_at TO embedded_at;

-- Rename text column to content
ALTER TABLE documents.document_chunks 
  RENAME COLUMN text TO content;

-- Create index for chunk_index if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_index 
  ON documents.document_chunks(chunk_index);

-- Create GIN index for array operations on section_path
CREATE INDEX IF NOT EXISTS idx_document_chunks_section_path 
  ON documents.document_chunks USING GIN (section_path);

-- Create index for parsed_path if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_documents_parsed_path 
  ON documents.documents(parsed_path);

COMMIT; 