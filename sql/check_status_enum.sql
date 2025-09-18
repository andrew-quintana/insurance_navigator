-- Query to show possible status enumeration fields for upload_jobs table
-- Run this in your Supabase SQL editor

-- 1. Get the constraint definition for the status column
SELECT 
    conname as constraint_name,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint 
WHERE conrelid = 'upload_pipeline.upload_jobs'::regclass 
AND conname LIKE '%status%';

-- 2. Get all distinct status values currently in the table
SELECT DISTINCT status, COUNT(*) as count
FROM upload_pipeline.upload_jobs 
WHERE status IS NOT NULL
ORDER BY status;

-- 3. Get table structure information
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'upload_pipeline' 
AND table_name = 'upload_jobs'
AND column_name = 'status';

-- 4. Alternative way to get constraint values using pg_get_constraintdef
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    pg_get_constraintdef(tc.oid) as constraint_definition
FROM information_schema.table_constraints tc
JOIN pg_constraint pc ON tc.constraint_name = pc.conname
WHERE tc.table_schema = 'upload_pipeline'
AND tc.table_name = 'upload_jobs'
AND tc.constraint_type = 'CHECK';

