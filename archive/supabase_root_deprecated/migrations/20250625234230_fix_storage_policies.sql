-- =============================================================================
-- FIX STORAGE POLICIES
-- Description: Add comprehensive storage policies for service role
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
-- STEP 1: DROP EXISTING POLICIES
-- =============================================================================

DROP POLICY IF EXISTS "Allow service role raw documents access" ON storage.objects;
DROP POLICY IF EXISTS "Allow service role documents access" ON storage.objects;

-- =============================================================================
-- STEP 2: CREATE COMPREHENSIVE POLICIES
-- =============================================================================

-- Service role policy for raw_documents bucket (full access)
CREATE POLICY "service_role_raw_documents_policy"
ON storage.objects
TO service_role
USING (bucket_id = 'raw_documents')
WITH CHECK (bucket_id = 'raw_documents');

-- Additional explicit permissions for service role
CREATE POLICY "service_role_raw_documents_select"
ON storage.objects FOR SELECT
TO service_role
USING (bucket_id = 'raw_documents');

CREATE POLICY "service_role_raw_documents_insert"
ON storage.objects FOR INSERT
TO service_role
WITH CHECK (bucket_id = 'raw_documents');

CREATE POLICY "service_role_raw_documents_update"
ON storage.objects FOR UPDATE
TO service_role
USING (bucket_id = 'raw_documents')
WITH CHECK (bucket_id = 'raw_documents');

CREATE POLICY "service_role_raw_documents_delete"
ON storage.objects FOR DELETE
TO service_role
USING (bucket_id = 'raw_documents');

-- Same policies for documents bucket
CREATE POLICY "service_role_documents_policy"
ON storage.objects
TO service_role
USING (bucket_id = 'documents')
WITH CHECK (bucket_id = 'documents');

CREATE POLICY "service_role_documents_select"
ON storage.objects FOR SELECT
TO service_role
USING (bucket_id = 'documents');

CREATE POLICY "service_role_documents_insert"
ON storage.objects FOR INSERT
TO service_role
WITH CHECK (bucket_id = 'documents');

CREATE POLICY "service_role_documents_update"
ON storage.objects FOR UPDATE
TO service_role
USING (bucket_id = 'documents')
WITH CHECK (bucket_id = 'documents');

CREATE POLICY "service_role_documents_delete"
ON storage.objects FOR DELETE
TO service_role
USING (bucket_id = 'documents');

-- =============================================================================
-- STEP 3: VERIFY BUCKET CONFIGURATION
-- =============================================================================

-- Ensure both buckets exist and are configured correctly
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
WHERE id IN ('raw_documents', 'documents');

COMMIT; 