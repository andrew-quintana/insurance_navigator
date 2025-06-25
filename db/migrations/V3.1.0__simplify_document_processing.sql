-- =============================================================================
-- SIMPLIFY DOCUMENT PROCESSING V3.1.0
-- Description: Add minimal processing fields to documents table
-- =============================================================================

BEGIN;

-- Add processing fields to documents table
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS processing_status TEXT DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS processing_error TEXT,
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ;

-- Add index for status queries
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);

-- Create document vectors table for semantic search
CREATE TABLE IF NOT EXISTS document_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    document_record_id UUID NOT NULL REFERENCES documents(id),
    document_source_type TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content_embedding vector(1536),
    encrypted_chunk_text TEXT,
    encrypted_chunk_metadata TEXT,
    encryption_key_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for vector search
CREATE INDEX IF NOT EXISTS idx_document_vectors_document_id ON document_vectors(document_record_id);
CREATE INDEX IF NOT EXISTS idx_document_vectors_user_id ON document_vectors(user_id);

COMMIT;