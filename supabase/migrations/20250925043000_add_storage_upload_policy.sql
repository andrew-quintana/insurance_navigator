-- 20250925043000_add_storage_upload_policy.sql
-- Add RLS policy to allow service role to upload files to storage
-- This fixes the 400 Bad Request error when API tries to upload files

begin;

-- Add RLS policy to allow service role to upload files to storage
DROP POLICY IF EXISTS "Allow service role to upload files" ON storage.objects;
CREATE POLICY "Allow service role to upload files"
ON storage.objects
FOR INSERT
TO service_role
WITH CHECK (bucket_id = 'files');

-- Add RLS policy to allow service role to update files in storage
DROP POLICY IF EXISTS "Allow service role to update files" ON storage.objects;
CREATE POLICY "Allow service role to update files"
ON storage.objects
FOR UPDATE
TO service_role
USING (bucket_id = 'files')
WITH CHECK (bucket_id = 'files');

-- Add RLS policy to allow service role to delete files from storage
DROP POLICY IF EXISTS "Allow service role to delete files" ON storage.objects;
CREATE POLICY "Allow service role to delete files"
ON storage.objects
FOR DELETE
TO service_role
USING (bucket_id = 'files');

-- Verify the policies were created
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'objects'
        AND schemaname = 'storage'
        AND policyname = 'Allow service role to upload files'
    ) THEN
        RAISE EXCEPTION 'Storage upload policy was not created successfully';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'objects'
        AND schemaname = 'storage'
        AND policyname = 'Allow service role to update files'
    ) THEN
        RAISE EXCEPTION 'Storage update policy was not created successfully';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'objects'
        AND schemaname = 'storage'
        AND policyname = 'Allow service role to delete files'
    ) THEN
        RAISE EXCEPTION 'Storage delete policy was not created successfully';
    END IF;
END $$;

commit;
