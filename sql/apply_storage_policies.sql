-- Apply storage RLS policies directly
-- This bypasses the migration system

-- Add RLS policies for storage.buckets table
CREATE POLICY IF NOT EXISTS "Allow service role to view buckets"
ON storage.buckets
FOR SELECT
TO service_role
USING (true);

CREATE POLICY IF NOT EXISTS "Allow service role to manage buckets"
ON storage.buckets
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Add missing RLS policies for storage.objects table
CREATE POLICY IF NOT EXISTS "Allow service role to update files"
ON storage.objects
FOR UPDATE
TO service_role
USING (bucket_id = 'files')
WITH CHECK (bucket_id = 'files');

CREATE POLICY IF NOT EXISTS "Allow service role to delete files"
ON storage.objects
FOR DELETE
TO service_role
USING (bucket_id = 'files');

CREATE POLICY IF NOT EXISTS "Allow service role to list files"
ON storage.objects
FOR SELECT
TO service_role
USING (bucket_id = 'files');
