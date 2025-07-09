-- -------------------------------
-- STORAGE BUCKET: 'files'
-- -------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM storage.buckets WHERE id = 'files') THEN
    INSERT INTO storage.buckets (
      id,
      name,
      public,
      file_size_limit,
      allowed_mime_types
    )
    VALUES (
      'files',
      'files',
      false,
      52428800,
      ARRAY[
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain',
        'text/csv',
        'text/markdown',
        'application/json',
        'application/xml',
        'text/xml',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'application/x-www-form-urlencoded',
        'multipart/form-data'
      ]
    );
  ELSE
    -- Update existing bucket configuration
    UPDATE storage.buckets
    SET 
      public = false,
      file_size_limit = 52428800,
      allowed_mime_types = ARRAY[
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain',
        'text/csv',
        'text/markdown',
        'application/json',
        'application/xml',
        'text/xml',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'application/x-www-form-urlencoded',
        'multipart/form-data'
      ]
    WHERE id = 'files';
  END IF;
END $$;

-- Add basic policies
CREATE POLICY "Allow service role to upload files"
ON storage.objects
FOR INSERT
TO service_role
WITH CHECK (bucket_id = 'files');

COMMIT;