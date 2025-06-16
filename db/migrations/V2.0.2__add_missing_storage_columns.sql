-- ================================================
-- V2.0.2 - Add Missing Storage Columns
-- Add storage_backend, bucket_name and other columns that the app expects
-- ================================================

-- Add storage-related columns to documents table
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS storage_backend VARCHAR(50) DEFAULT 'supabase',
ADD COLUMN IF NOT EXISTS bucket_name VARCHAR(100) DEFAULT 'raw_documents',
ADD COLUMN IF NOT EXISTS storage_path TEXT;

-- Add columns that the application code references
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS content_type VARCHAR(255),
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS progress_percentage INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_chunks INTEGER,
ADD COLUMN IF NOT EXISTS processed_chunks INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS failed_chunks INTEGER DEFAULT 0;

-- Update storage_path to match file_path for existing records where storage_path is null
UPDATE documents 
SET storage_path = file_path 
WHERE storage_path IS NULL AND file_path IS NOT NULL;

-- Add indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_documents_storage_backend 
ON documents (storage_backend);

CREATE INDEX IF NOT EXISTS idx_documents_bucket_name 
ON documents (bucket_name);

CREATE INDEX IF NOT EXISTS idx_documents_file_hash 
ON documents (file_hash);

CREATE INDEX IF NOT EXISTS idx_documents_progress 
ON documents (progress_percentage, status);

-- Log successful migration
INSERT INTO audit_logs (action, created_at)
VALUES ('SCHEMA_MIGRATION_V2.0.2_STORAGE_COLUMNS', NOW()); 