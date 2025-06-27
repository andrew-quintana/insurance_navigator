-- =============================================================================
-- ADD RAW DOCUMENTS STORAGE POLICIES
-- Description: Add storage policies for raw_documents bucket
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
-- STEP 1: ADD STORAGE POLICIES FOR RAW_DOCUMENTS
-- =============================================================================

-- Drop existing policies if any
DROP POLICY IF EXISTS "Allow service role raw documents access" ON storage.objects;
DROP POLICY IF EXISTS "Allow service role documents access" ON storage.objects;

-- Create comprehensive policies for raw_documents bucket
CREATE POLICY "service_role_raw_documents_all"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'raw_documents')
WITH CHECK (bucket_id = 'raw_documents');

-- Create comprehensive policies for documents bucket
CREATE POLICY "service_role_documents_all"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'documents')
WITH CHECK (bucket_id = 'documents');

-- Ensure buckets exist and are private
INSERT INTO storage.buckets (id, name, public)
VALUES 
    ('raw_documents', 'raw_documents', false),
    ('documents', 'documents', false)
ON CONFLICT (id) DO UPDATE
SET public = false;

-- Update bucket configuration
UPDATE storage.buckets
SET file_size_limit = 52428800, -- 50MB
    allowed_mime_types = ARRAY[
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ]
WHERE id = 'raw_documents';

COMMIT; 