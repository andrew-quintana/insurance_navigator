-- =============================================================================
-- Migration: Add Regulatory Document Vector Support (Targeted)
-- Version: 015 Targeted
-- Description: Add missing features for regulatory documents to existing document_vectors table
-- =============================================================================

BEGIN;

-- Add missing columns to regulatory_documents table if they don't exist
ALTER TABLE regulatory_documents 
ADD COLUMN IF NOT EXISTS content_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(100),
ADD COLUMN IF NOT EXISTS priority_score DECIMAL DEFAULT 1.0,
ADD COLUMN IF NOT EXISTS search_metadata JSONB DEFAULT '{}';

-- Add foreign key constraint for regulatory_document_id if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'document_vectors_regulatory_document_id_fkey'
    ) THEN
        ALTER TABLE document_vectors 
        ADD CONSTRAINT document_vectors_regulatory_document_id_fkey 
        FOREIGN KEY (regulatory_document_id) REFERENCES regulatory_documents(document_id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add check constraint for document_source_type values if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'document_vectors_document_source_type_check'
    ) THEN
        ALTER TABLE document_vectors 
        ADD CONSTRAINT document_vectors_document_source_type_check 
        CHECK (document_source_type IN ('user_document', 'regulatory_document'));
    END IF;
END $$;

-- Create indexes for regulatory document vectors
CREATE INDEX IF NOT EXISTS idx_document_vectors_regulatory_doc 
ON document_vectors(regulatory_document_id) 
WHERE regulatory_document_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_document_vectors_source_type 
ON document_vectors(document_source_type);

-- Composite index for efficient regulatory vector queries
CREATE INDEX IF NOT EXISTS idx_document_vectors_regulatory_search 
ON document_vectors(regulatory_document_id, document_source_type, is_active) 
WHERE document_source_type = 'regulatory_document';

-- Add indexes for regulatory_documents table
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_content_hash 
ON regulatory_documents(content_hash) 
WHERE content_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_regulatory_docs_extraction_method 
ON regulatory_documents(extraction_method);

CREATE INDEX IF NOT EXISTS idx_regulatory_docs_priority_score 
ON regulatory_documents(priority_score DESC);

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
            (dv.chunk_embedding <=> search_embedding)::FLOAT as similarity_score,
            COALESCE(dv.encrypted_chunk_text, dv.chunk_text) as chunk_content
        FROM document_vectors dv
        JOIN regulatory_documents rd ON dv.regulatory_document_id = rd.document_id
        WHERE dv.document_source_type = 'regulatory_document'
        AND dv.is_active = true
        ORDER BY dv.chunk_embedding <=> search_embedding
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