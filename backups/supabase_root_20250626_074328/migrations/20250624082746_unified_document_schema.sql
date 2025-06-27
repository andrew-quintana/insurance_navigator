-- =============================================================================
-- UNIFIED DOCUMENT SCHEMA
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
-- STEP 1: ADD REGULATORY DOCUMENT FIELDS
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

-- =============================================================================
-- STEP 2: ADD CONSTRAINTS AND INDEXES
-- =============================================================================

-- Add document type constraint
ALTER TABLE documents
DROP CONSTRAINT IF EXISTS valid_document_type;

ALTER TABLE documents
ADD CONSTRAINT valid_document_type 
CHECK (document_type IN ('user_uploaded', 'regulatory', 'policy', 'medical_record', 'claim'));

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_jurisdiction ON documents(jurisdiction) WHERE jurisdiction IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_documents_dates ON documents(effective_date, expiration_date) 
WHERE effective_date IS NOT NULL OR expiration_date IS NOT NULL;

COMMIT; 