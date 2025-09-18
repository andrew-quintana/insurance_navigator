-- Migration: Stage rename from 'chunks_buffered' to 'chunked'
-- This migration handles any existing database records with the old stage name

-- Update any existing jobs with the old stage name
UPDATE upload_pipeline.upload_jobs 
SET stage = 'chunked' 
WHERE stage = 'chunks_buffered';

-- Verify the migration
SELECT 
    stage, 
    COUNT(*) as job_count 
FROM upload_pipeline.upload_jobs 
GROUP BY stage 
ORDER BY stage;