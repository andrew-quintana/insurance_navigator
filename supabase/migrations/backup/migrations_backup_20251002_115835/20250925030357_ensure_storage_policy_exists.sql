-- 20250925T030357_ensure_storage_policy_exists.sql
-- Ensure storage policy exists to allow service role to download files
-- This fixes the 400 Bad Request error when workers try to download files

begin;

-- Drop existing policy if it exists (to avoid conflicts)
DROP POLICY IF EXISTS "Allow service role to download files" ON storage.objects;

-- Add RLS policy to allow service role to download files from storage
CREATE POLICY "Allow service role to download files"
ON storage.objects
FOR SELECT
TO service_role
USING (bucket_id = 'files');

-- Verify the policy was created
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' 
        AND schemaname = 'storage'
        AND policyname = 'Allow service role to download files'
    ) THEN
        RAISE EXCEPTION 'Storage policy was not created successfully';
    END IF;
END $$;

commit;
