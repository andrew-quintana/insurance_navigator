-- 20250925T035142_fix_staging_storage_policy.sql
-- Fix staging storage policy for FRACAS FM-012
-- This migration ensures the storage policy exists in staging environment

begin;

-- Check if the policy already exists
DO $$
BEGIN
    -- Only create the policy if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' 
        AND schemaname = 'storage'
        AND policyname = 'Allow service role to download files'
    ) THEN
        -- Create the RLS policy to allow service role to download files
        CREATE POLICY "Allow service role to download files"
        ON storage.objects
        FOR SELECT
        TO service_role
        USING (bucket_id = 'files');
        
        RAISE NOTICE 'Storage policy "Allow service role to download files" created successfully';
    ELSE
        RAISE NOTICE 'Storage policy "Allow service role to download files" already exists';
    END IF;
END $$;

-- Verify the policy exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' 
        AND schemaname = 'storage'
        AND policyname = 'Allow service role to download files'
    ) THEN
        RAISE EXCEPTION 'Storage policy verification failed - policy does not exist';
    END IF;
    
    RAISE NOTICE 'Storage policy verification successful';
END $$;

commit;
