-- =============================================================================
-- UNIFIED DOCUMENT SCHEMA V3.0.0
-- Description: Consolidate document tables and remove redundant fields
-- Production deployment - NO LOCAL DEVELOPMENT
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- =============================================================================
-- STEP 1: MIGRATE REGULATORY DOCUMENTS TO DOCUMENTS TABLE
-- =============================================================================

-- Add new fields to documents table
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS document_type TEXT NOT NULL DEFAULT 'user_uploaded',
ADD COLUMN IF NOT EXISTS jurisdiction TEXT,
ADD COLUMN IF NOT EXISTS program TEXT[],
ADD COLUMN IF NOT EXISTS effective_date DATE,
ADD COLUMN IF NOT EXISTS expiration_date DATE,
ADD COLUMN IF NOT EXISTS source_url TEXT,
ADD COLUMN IF NOT EXISTS tags TEXT[];

-- Migrate data from regulatory_documents to documents
INSERT INTO documents (
    id,
    original_filename,
    file_size,
    content_type,
    file_hash,
    storage_path,
    document_type,
    jurisdiction,
    program,
    effective_date,
    expiration_date,
    source_url,
    created_at,
    updated_at
)
SELECT
    document_id,
    raw_document_path,
    0, -- file_size not available
    'application/pdf', -- assuming PDF
    '', -- file_hash not available
    raw_document_path,
    'regulatory',
    jurisdiction,
    program,
    effective_date,
    expiration_date,
    source_url,
    created_at,
    last_updated
FROM regulatory_documents
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- STEP 2: CLEANUP UNUSED TABLES AND COLUMNS
-- =============================================================================

-- Drop unused tables
DROP TABLE IF EXISTS regulatory_documents CASCADE;
DROP TABLE IF EXISTS realtime_progress_updates CASCADE;
DROP TABLE IF EXISTS processing_jobs CASCADE;

-- Remove unused columns from documents
ALTER TABLE documents
DROP COLUMN IF EXISTS mime_type,
DROP COLUMN IF EXISTS storage_provider,
DROP COLUMN IF EXISTS content_extracted,
DROP COLUMN IF EXISTS policy_basics,
DROP COLUMN IF EXISTS file_path;

-- =============================================================================
-- STEP 3: ADD CONSTRAINTS AND INDEXES
-- =============================================================================

-- Add document type constraint
ALTER TABLE documents
ADD CONSTRAINT valid_document_type 
CHECK (document_type IN ('user_uploaded', 'regulatory', 'policy', 'medical_record', 'claim'));

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_jurisdiction ON documents(jurisdiction) WHERE jurisdiction IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_documents_dates ON documents(effective_date, expiration_date) 
WHERE effective_date IS NOT NULL OR expiration_date IS NOT NULL;

COMMIT; 