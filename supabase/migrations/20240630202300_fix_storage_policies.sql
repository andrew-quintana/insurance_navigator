-- =============================================================================
-- FIX STORAGE POLICIES
-- Description: Fix storage bucket policies for service role and test user
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

DROP POLICY IF EXISTS "Users can upload to own directory" ON storage.objects;
DROP POLICY IF EXISTS "Users can read own files" ON storage.objects;
DROP POLICY IF EXISTS "Service role has full access to storage" ON storage.objects;

-- =============================================================================
-- STEP 2: CREATE COMPREHENSIVE POLICIES
-- =============================================================================

-- Service role policy for documents bucket (full access)
CREATE POLICY "service_role_documents_policy"
ON storage.objects
TO service_role
USING (bucket_id = 'documents')
WITH CHECK (bucket_id = 'documents');

-- Authenticated user policy for documents bucket
CREATE POLICY "authenticated_user_documents_policy"
ON storage.objects
TO authenticated
USING (bucket_id = 'documents')
WITH CHECK (bucket_id = 'documents');

-- =============================================================================
-- STEP 3: VERIFY BUCKET CONFIGURATION
-- =============================================================================

-- Ensure bucket exists and is configured correctly
INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', false)
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
WHERE id = 'documents';

COMMIT; 