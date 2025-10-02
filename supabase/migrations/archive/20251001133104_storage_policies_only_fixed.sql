-- 20251001T133104_storage_policies_only_fixed.sql
-- Apply only the storage RLS policies needed for FM-027
-- This handles existing policies gracefully

BEGIN;

-- Add RLS policies for storage.buckets table (if they don't exist)
DO $$
BEGIN
    -- Allow service role to view buckets
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'storage' 
        AND tablename = 'buckets' 
        AND policyname = 'Allow service role to view buckets'
    ) THEN
        CREATE POLICY "Allow service role to view buckets"
        ON storage.buckets
        FOR SELECT
        TO service_role
        USING (true);
    END IF;

    -- Allow service role to manage buckets
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'storage' 
        AND tablename = 'buckets' 
        AND policyname = 'Allow service role to manage buckets'
    ) THEN
        CREATE POLICY "Allow service role to manage buckets"
        ON storage.buckets
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
    END IF;
END $$;

-- Add missing RLS policies for storage.objects table (if they don't exist)
DO $$
BEGIN
    -- Allow service role to update files
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'storage' 
        AND tablename = 'objects' 
        AND policyname = 'Allow service role to update files'
    ) THEN
        CREATE POLICY "Allow service role to update files"
        ON storage.objects
        FOR UPDATE
        TO service_role
        USING (bucket_id = 'files')
        WITH CHECK (bucket_id = 'files');
    END IF;

    -- Allow service role to delete files
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'storage' 
        AND tablename = 'objects' 
        AND policyname = 'Allow service role to delete files'
    ) THEN
        CREATE POLICY "Allow service role to delete files"
        ON storage.objects
        FOR DELETE
        TO service_role
        USING (bucket_id = 'files');
    END IF;

    -- Allow service role to list files
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'storage' 
        AND tablename = 'objects' 
        AND policyname = 'Allow service role to list files'
    ) THEN
        CREATE POLICY "Allow service role to list files"
        ON storage.objects
        FOR SELECT
        TO service_role
        USING (bucket_id = 'files');
    END IF;
END $$;

COMMIT;
