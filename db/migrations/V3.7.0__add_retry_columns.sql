-- Add retry tracking columns to processing_jobs
BEGIN;

-- Add retry tracking columns
ALTER TABLE processing_jobs
ADD COLUMN IF NOT EXISTS last_retry_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS initial_created_at TIMESTAMPTZ DEFAULT NOW();

COMMIT; 