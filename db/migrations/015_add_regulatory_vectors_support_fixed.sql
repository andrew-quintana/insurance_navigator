-- =============================================================================
-- Migration: Add Regulatory Document Vector Support (Fixed)
-- Version: 015 Fixed
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
ADD COLUMN IF NOT EXISTS regulatory_document_id UUID;

-- Add the foreign key constraint separately
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

-- Add document source type to distinguish vector sources
ALTER TABLE document_vectors 
ADD COLUMN IF NOT EXISTS document_source_type TEXT DEFAULT 'user_document';

-- Update existing records based on their data
UPDATE document_vectors 
SET document_source_type = CASE 
    WHEN document_record_id IS NOT NULL THEN 'user_document'
    ELSE 'regulatory_document'
END
WHERE document_source_type = 'user_document' OR document_source_type IS NULL;

-- Make document_source_type NOT NULL after setting values
ALTER TABLE document_vectors 
ALTER COLUMN document_source_type SET NOT NULL;

-- Add check constraint for document_source_type values
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

COMMIT; 