-- 20251001T133103_bucket_policies_only.sql
-- Add only the missing bucket RLS policies

BEGIN;

-- Add RLS policies for storage.buckets table (these are missing!)
CREATE POLICY "Allow service role to view buckets"
ON storage.buckets
FOR SELECT
TO service_role
USING (true);

CREATE POLICY "Allow service role to manage buckets"
ON storage.buckets
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

COMMIT;
