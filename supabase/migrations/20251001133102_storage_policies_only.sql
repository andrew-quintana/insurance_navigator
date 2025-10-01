-- 20251001T133102_storage_policies_only.sql
-- Apply only the storage RLS policies needed for FM-027
-- This bypasses the problematic user table migration

BEGIN;

-- Add RLS policies for storage.buckets table
CREATE POLICY "Allow service role to view buckets"
ON storage.buckets
FOR SELECT
TO service_role
USING (true);

CREATE POLICY "Allow service role to manage buckets"
ON storage.buckets
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Add missing RLS policies for storage.objects table
CREATE POLICY "Allow service role to update files"
ON storage.objects
FOR UPDATE
TO service_role
USING (bucket_id = 'files')
WITH CHECK (bucket_id = 'files');

CREATE POLICY "Allow service role to delete files"
ON storage.objects
FOR DELETE
TO service_role
USING (bucket_id = 'files');

CREATE POLICY "Allow service role to list files"
ON storage.objects
FOR SELECT
TO service_role
USING (bucket_id = 'files');

COMMIT;

