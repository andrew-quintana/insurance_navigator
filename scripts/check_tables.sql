-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE';

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
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE';

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