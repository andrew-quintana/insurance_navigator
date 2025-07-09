-- Safety check for read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

BEGIN;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can upload files to their own directory" ON storage.objects;
DROP POLICY IF EXISTS "Users can read their own files" ON storage.objects;

-- Create storage bucket if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM storage.buckets WHERE id = 'files') THEN
    INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
    VALUES ('files', 'files', false, 52428800, ARRAY['*/*']::text[]);
  END IF;
END $$;

-- Enable RLS on storage.objects (wrapped in exception handler)
DO $$
BEGIN
    ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;
EXCEPTION
    WHEN insufficient_privilege THEN
        -- Log the error but continue
        RAISE NOTICE 'Insufficient privilege to modify RLS on storage.objects';
END $$;

-- Create storage policies (wrapped in exception handler)
DO $$
BEGIN
    -- Create upload policy
    CREATE POLICY "Users can upload files to their own directory"
    ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (
      bucket_id = 'files' AND
      (storage.foldername(name))[1] = 'user' AND
      (storage.foldername(name))[2] = auth.uid()::text AND
      (storage.foldername(name))[3] = 'raw'
    );

    -- Create read policy
    CREATE POLICY "Users can read their own files"
    ON storage.objects
    FOR SELECT
    TO authenticated
    USING (
      bucket_id = 'files' AND
      (storage.foldername(name))[1] = 'user' AND
      (storage.foldername(name))[2] = auth.uid()::text
    );
EXCEPTION
    WHEN insufficient_privilege THEN
        RAISE NOTICE 'Insufficient privilege to create policies on storage.objects';
END $$;

COMMIT;