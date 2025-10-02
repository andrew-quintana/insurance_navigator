-- 20250918T201725_add_storage_select_policy.sql
-- Add RLS policy to allow service role to download files from storage
-- This fixes the 400 Bad Request error when workers try to download files

begin;

-- Add RLS policy to allow service role to download files from storage
CREATE POLICY "Allow service role to download files"
ON storage.objects
FOR SELECT
TO service_role
USING (bucket_id = 'files');

commit;
