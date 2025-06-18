-- Migration: Add status columns to regulatory_documents table
-- This adds the status tracking columns that exist in documents table but are missing from regulatory_documents

-- Add status columns
ALTER TABLE regulatory_documents 
ADD COLUMN IF NOT EXISTS upload_status VARCHAR(50) DEFAULT 'completed',
ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS progress_percentage INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS error_message TEXT,
ADD COLUMN IF NOT EXISTS vectors_generated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS vector_count INTEGER DEFAULT 0;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_processing_status ON regulatory_documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_status ON regulatory_documents(status);
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_vectors_generated ON regulatory_documents(vectors_generated);
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_progress ON regulatory_documents(progress_percentage, status);

-- Update existing regulatory documents to have proper initial status
UPDATE regulatory_documents 
SET 
    upload_status = 'completed',
    processing_status = 'pending',
    status = 'pending',
    progress_percentage = 10, -- Documents are uploaded but vectors not processed
    vectors_generated = FALSE,
    vector_count = 0
WHERE upload_status IS NULL OR processing_status IS NULL;

-- Add a comment to document this change
COMMENT ON COLUMN regulatory_documents.upload_status IS 'Status of document upload: pending, processing, completed, failed';
COMMENT ON COLUMN regulatory_documents.processing_status IS 'Status of content processing: pending, processing, completed, failed';
COMMENT ON COLUMN regulatory_documents.status IS 'Overall document status: pending, processing, completed, failed';
COMMENT ON COLUMN regulatory_documents.progress_percentage IS 'Processing progress from 0-100%';
COMMENT ON COLUMN regulatory_documents.vectors_generated IS 'Whether vector embeddings have been generated';
COMMENT ON COLUMN regulatory_documents.vector_count IS 'Number of vector chunks generated for this document'; 