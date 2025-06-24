-- =============================================================================
-- CREATE DOCUMENT VECTORS TABLE V3.0.0.1
-- Description: Create the document_vectors table for storing vector embeddings
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- Create document_vectors table
CREATE TABLE IF NOT EXISTS document_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    chunk_index INTEGER NOT NULL,
    content_embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    encrypted_chunk_text TEXT,
    encrypted_chunk_metadata TEXT,
    encryption_key_id UUID,
    document_record_id UUID,
    regulatory_document_id UUID,
    document_source_type TEXT NOT NULL,
    CONSTRAINT chk_document_reference_exclusive CHECK (
        (document_source_type = 'user_document' AND document_record_id IS NOT NULL AND regulatory_document_id IS NULL) OR
        (document_source_type = 'regulatory_document' AND regulatory_document_id IS NOT NULL AND document_record_id IS NULL)
    ),
    CONSTRAINT chk_user_document_requires_user_id CHECK (
        (document_source_type = 'regulatory_document') OR 
        (document_source_type = 'user_document' AND user_id IS NOT NULL)
    ),
    CONSTRAINT chk_encryption_consistency CHECK (
        (encrypted_chunk_text IS NOT NULL AND encrypted_chunk_metadata IS NOT NULL AND encryption_key_id IS NOT NULL) OR
        (encrypted_chunk_text IS NULL AND encrypted_chunk_metadata IS NULL AND encryption_key_id IS NULL)
    )
);

-- Create indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_document_vectors_user_doc_chunk_unique 
ON document_vectors(document_record_id, chunk_index) 
WHERE document_source_type = 'user_document' AND is_active = true;

CREATE UNIQUE INDEX IF NOT EXISTS idx_document_vectors_regulatory_doc_chunk_unique 
ON document_vectors(regulatory_document_id, chunk_index) 
WHERE document_source_type = 'regulatory_document' AND is_active = true;

CREATE INDEX IF NOT EXISTS document_vectors_embedding_idx 
ON document_vectors USING ivfflat (content_embedding vector_cosine_ops)
WITH (lists = 100);

-- Record migration completion
INSERT INTO schema_migrations (version) VALUES ('V3.0.0.1') ON CONFLICT (version) DO NOTHING;

COMMIT; 