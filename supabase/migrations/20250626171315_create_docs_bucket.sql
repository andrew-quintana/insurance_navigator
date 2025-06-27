-- Create the docs bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('docs', 'docs', false)
ON CONFLICT (id) DO NOTHING;

-- Set basic configuration
UPDATE storage.buckets
SET file_size_limit = 10485760, -- 10MB
    allowed_mime_types = ARRAY[
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ]
WHERE id = 'docs';

-- Create basic storage policy for authenticated users
CREATE POLICY "Allow authenticated uploads"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'docs');

CREATE POLICY "Allow authenticated reads"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'docs');
