-- =============================================================================
-- Migration: Add Regulatory Document Vector Support
-- Version: 015
-- Description: Enhance document_vectors table to support regulatory documents
-- =============================================================================

BEGIN;

-- Add missing columns to regulatory_documents table if they don't exist
ALTER TABLE regulatory_documents 
ADD COLUMN IF NOT EXISTS content_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(100),
ADD COLUMN IF NOT EXISTS priority_score DECIMAL DEFAULT 1.0,
ADD COLUMN IF NOT EXISTS search_metadata JSONB DEFAULT '{}';

-- Add foreign key for regulatory documents  
ALTER TABLE document_vectors 
ADD COLUMN IF NOT EXISTS regulatory_document_id UUID REFERENCES regulatory_documents(document_id) ON DELETE CASCADE;

-- Add document source type to distinguish vector sources
ALTER TABLE document_vectors 
ADD COLUMN IF NOT EXISTS document_source_type TEXT DEFAULT 'user_document' 
CHECK (document_source_type IN ('user_document', 'regulatory_document'));

-- Update existing records to set source type
UPDATE document_vectors 
SET document_source_type = 'user_document' 
WHERE document_source_type IS NULL;

-- Make document_source_type NOT NULL after setting defaults
ALTER TABLE document_vectors 
ALTER COLUMN document_source_type SET NOT NULL;

-- Add constraint to ensure proper referencing
ALTER TABLE document_vectors 
ADD CONSTRAINT chk_document_reference CHECK (
    (document_source_type = 'user_document' AND document_record_id IS NOT NULL AND regulatory_document_id IS NULL) OR
    (document_source_type = 'regulatory_document' AND regulatory_document_id IS NOT NULL AND document_record_id IS NULL)
);

-- Create indexes for regulatory document vectors
CREATE INDEX idx_document_vectors_regulatory_doc ON document_vectors(regulatory_document_id) 
WHERE regulatory_document_id IS NOT NULL;

CREATE INDEX idx_document_vectors_source_type ON document_vectors(document_source_type);

-- Composite index for efficient regulatory vector queries
CREATE INDEX idx_document_vectors_regulatory_search 
ON document_vectors(regulatory_document_id, document_source_type, is_active) 
WHERE document_source_type = 'regulatory_document';

-- Add function to search regulatory documents
CREATE OR REPLACE FUNCTION search_regulatory_documents(
    search_query TEXT,
    search_embedding vector(1536) DEFAULT NULL,
    limit_results INTEGER DEFAULT 10
) RETURNS TABLE (
    document_id UUID,
    title TEXT,
    jurisdiction TEXT,
    source_url TEXT,
    document_type TEXT,
    similarity_score FLOAT,
    chunk_content TEXT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    IF search_embedding IS NOT NULL THEN
        -- Vector similarity search
        RETURN QUERY
        SELECT 
            rd.document_id,
            rd.title,
            rd.jurisdiction,
            rd.source_url,
            rd.document_type,
            (dv.content_embedding <=> search_embedding)::FLOAT as similarity_score,
            dv.encrypted_chunk_text as chunk_content
        FROM document_vectors dv
        JOIN regulatory_documents rd ON dv.regulatory_document_id = rd.document_id
        WHERE dv.document_source_type = 'regulatory_document'
        AND dv.is_active = true
        ORDER BY dv.content_embedding <=> search_embedding
        LIMIT limit_results;
    ELSE
        -- Text-based search fallback
        RETURN QUERY
        SELECT 
            rd.document_id,
            rd.title,
            rd.jurisdiction,
            rd.source_url,
            rd.document_type,
            1.0::FLOAT as similarity_score,
            ''::TEXT as chunk_content
        FROM regulatory_documents rd
        WHERE (
            rd.title ILIKE '%' || search_query || '%' OR
            rd.document_type ILIKE '%' || search_query || '%' OR
            rd.jurisdiction ILIKE '%' || search_query || '%' OR
            search_query = ANY(rd.tags)
        )
        ORDER BY rd.created_at DESC
        LIMIT limit_results;
    END IF;
END;
$$;

COMMIT; 