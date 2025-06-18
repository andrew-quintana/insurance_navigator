-- Migration: Make user_id nullable for regulatory documents
-- File: 016_fix_user_id_nullable.sql

-- Make user_id nullable to allow regulatory documents without user_id
ALTER TABLE user_document_vectors ALTER COLUMN user_id DROP NOT NULL;

-- Add a check constraint to ensure that either user_id is not null OR document_source_type is 'regulatory_document'
ALTER TABLE user_document_vectors ADD CONSTRAINT user_id_or_regulatory_check 
CHECK (
    (user_id IS NOT NULL AND document_source_type = 'user_document') OR
    (user_id IS NULL AND document_source_type = 'regulatory_document')
);

-- Add comment to clarify the schema
COMMENT ON COLUMN user_document_vectors.user_id IS 'User ID for user documents, NULL for regulatory documents';
COMMENT ON CONSTRAINT user_id_or_regulatory_check ON user_document_vectors IS 'Ensures user_id is present for user documents but NULL for regulatory documents'; 