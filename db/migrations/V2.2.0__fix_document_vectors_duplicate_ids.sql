-- =============================================================================
-- DOCUMENT VECTORS DUPLICATE ID FIX - V2.2.0 (SIMPLIFIED)
-- Description: Fix potential duplicate ID issues in document_vectors table
-- Addresses: User ID and document ID confusion, missing uniqueness constraints
-- =============================================================================

BEGIN;

-- Add constraint to ensure proper document reference (only one type can be set)
ALTER TABLE document_vectors 
ADD CONSTRAINT chk_document_reference_exclusive CHECK (
    (document_source_type = 'user_document' AND document_record_id IS NOT NULL AND regulatory_document_id IS NULL) OR
    (document_source_type = 'regulatory_document' AND regulatory_document_id IS NOT NULL AND document_record_id IS NULL)
);

-- Add constraint to ensure user_id is set for user documents
ALTER TABLE document_vectors 
ADD CONSTRAINT chk_user_document_requires_user_id CHECK (
    (document_source_type = 'regulatory_document') OR 
    (document_source_type = 'user_document' AND user_id IS NOT NULL)
);

-- Add constraint for encryption consistency
ALTER TABLE document_vectors 
ADD CONSTRAINT chk_encryption_consistency CHECK (
    (encrypted_chunk_text IS NOT NULL AND encrypted_chunk_metadata IS NOT NULL AND encryption_key_id IS NOT NULL) OR
    (encrypted_chunk_text IS NULL AND encrypted_chunk_metadata IS NULL AND encryption_key_id IS NULL)
);

-- Ensure uniqueness for user document chunks (prevent duplicate chunk indexes per document)
CREATE UNIQUE INDEX IF NOT EXISTS idx_document_vectors_user_doc_chunk_unique 
ON document_vectors(document_record_id, chunk_index) 
WHERE document_source_type = 'user_document' AND is_active = true;

-- Ensure uniqueness for regulatory document chunks
CREATE UNIQUE INDEX IF NOT EXISTS idx_document_vectors_regulatory_doc_chunk_unique 
ON document_vectors(regulatory_document_id, chunk_index) 
WHERE document_source_type = 'regulatory_document' AND is_active = true;

-- Function to validate document vector insertion
CREATE OR REPLACE FUNCTION validate_document_vector_insert()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate that exactly one document reference is set
    IF (NEW.document_source_type = 'user_document' AND 
        (NEW.document_record_id IS NULL OR NEW.regulatory_document_id IS NOT NULL)) THEN
        RAISE EXCEPTION 'User document vectors must have document_record_id set and regulatory_document_id NULL';
    END IF;
    
    IF (NEW.document_source_type = 'regulatory_document' AND 
        (NEW.regulatory_document_id IS NULL OR NEW.document_record_id IS NOT NULL)) THEN
        RAISE EXCEPTION 'Regulatory document vectors must have regulatory_document_id set and document_record_id NULL';
    END IF;
    
    -- Validate user_id for user documents
    IF (NEW.document_source_type = 'user_document' AND NEW.user_id IS NULL) THEN
        RAISE EXCEPTION 'User document vectors must have user_id set';
    END IF;
    
    -- Validate chunk_index is non-negative
    IF (NEW.chunk_index < 0) THEN
        RAISE EXCEPTION 'Chunk index must be non-negative, got %', NEW.chunk_index;
    END IF;
    
    -- Validate vector dimensions (should be 1536 for OpenAI embeddings)
    IF (vector_dims(NEW.content_embedding) != 1536) THEN
        RAISE EXCEPTION 'Content embedding must be 1536 dimensions, got %', vector_dims(NEW.content_embedding);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger for validation
DROP TRIGGER IF EXISTS trg_validate_document_vector_insert ON document_vectors;
CREATE TRIGGER trg_validate_document_vector_insert
    BEFORE INSERT OR UPDATE ON document_vectors
    FOR EACH ROW EXECUTE FUNCTION validate_document_vector_insert();

-- Record migration completion
INSERT INTO schema_migrations (version) VALUES ('V2.2.0') ON CONFLICT (version) DO NOTHING;

COMMIT; 