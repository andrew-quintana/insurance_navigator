-- Enable RLS on storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policy for uploads (INSERT)
CREATE POLICY "Authenticated users can upload files"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'policies' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy for reading own files (SELECT)
CREATE POLICY "Users can view own files"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'policies' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy for deleting own files (DELETE)
CREATE POLICY "Users can delete own files"
ON storage.objects
FOR DELETE
TO authenticated
USING (
  bucket_id = 'policies' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy for updating own files (UPDATE)
CREATE POLICY "Users can update own files"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
  bucket_id = 'policies' AND
  (storage.foldername(name))[1] = auth.uid()::text
)
WITH CHECK (
  bucket_id = 'policies' AND
  (storage.foldername(name))[1] = auth.uid()::text
); 