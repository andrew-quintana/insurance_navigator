-- Check if all required tables exist
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('users', 'documents', 'document_chunks', 'document_vectors')
ORDER BY table_name;

-- Check if required extensions are enabled
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('uuid-ossp', 'vector', 'pgvector', 'pg_stat_statements');

-- Check if RLS is enabled on all tables
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('users', 'documents', 'document_chunks', 'document_vectors');

-- Check indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('users', 'documents', 'document_chunks', 'document_vectors')
ORDER BY tablename, indexname;

-- Check documents table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'documents'
ORDER BY ordinal_position;

-- Check users table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'users'
ORDER BY ordinal_position; 