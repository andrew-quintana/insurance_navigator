-- -------------------------------
-- CREATE schema
-- -------------------------------
create schema if not exists documents;

-- Create document status enum type
CREATE TYPE documents.document_processing_status AS ENUM (
  'uploaded',
  'parsed',
  'chunked',
  'vectorized',
  'error',
  'unk'
);

-- Add status column to existing table
ALTER TABLE documents.documents 
ADD COLUMN processing_status documents.document_processing_status not null default 'unk';

-- Add index for status queries
CREATE INDEX idx_documents_status ON documents.documents(processing_status);