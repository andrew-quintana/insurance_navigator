-- -------------------------------
-- STORAGE BUCKET: 'files'
-- -------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM storage.buckets WHERE id = 'files') THEN
    -- Insert bucket with basic schema (compatible with all Supabase versions)
    INSERT INTO storage.buckets (id, name)
    VALUES ('files', 'files');
  END IF;
END $$;

-- Add basic policies
CREATE POLICY "Allow service role to upload files"
ON storage.objects
FOR INSERT
TO service_role
WITH CHECK (bucket_id = 'files');

COMMIT;