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

COMMIT;