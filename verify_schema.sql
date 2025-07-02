-- Verify users table
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users';

-- Verify documents table
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'documents';

-- Verify RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('users', 'documents');

-- Verify storage bucket
SELECT id, name, public, file_size_limit, allowed_mime_types
FROM storage.buckets
WHERE id = 'documents';

-- Verify RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('users', 'documents');
