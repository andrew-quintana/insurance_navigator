-- =============================================================================
-- ENHANCE JOB PROCESSING SYSTEM V2.5.0
-- Description: Add better job tracking and rate limiting capabilities
-- =============================================================================

BEGIN;

-- =============================================================================
-- ENHANCE PROCESSING JOBS TABLE
-- =============================================================================

-- Add columns for better job tracking
ALTER TABLE processing_jobs
ADD COLUMN IF NOT EXISTS processing_stage TEXT,
ADD COLUMN IF NOT EXISTS rate_limit_key TEXT,
ADD COLUMN IF NOT EXISTS rate_limit_window INTERVAL,
ADD COLUMN IF NOT EXISTS rate_limit_count INTEGER,
ADD COLUMN IF NOT EXISTS parent_job_id UUID REFERENCES processing_jobs(id),
ADD COLUMN IF NOT EXISTS child_jobs_completed INTEGER DEFAULT 0;

-- Add index for rate limiting queries
CREATE INDEX IF NOT EXISTS idx_processing_jobs_rate_limit 
ON processing_jobs(rate_limit_key, created_at) 
WHERE status = 'completed';

-- Add index for parent-child relationship
CREATE INDEX IF NOT EXISTS idx_processing_jobs_parent 
ON processing_jobs(parent_job_id) 
WHERE parent_job_id IS NOT NULL;

-- =============================================================================
-- ENHANCE DOCUMENTS TABLE
-- =============================================================================

-- Add columns for more granular status tracking
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS processing_stage TEXT,
ADD COLUMN IF NOT EXISTS processing_progress INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_processing_steps INTEGER;

-- Add index for processing stage queries
CREATE INDEX IF NOT EXISTS idx_documents_processing_stage 
ON documents(processing_stage) 
WHERE status = 'processing';

-- =============================================================================
-- RECORD MIGRATION
-- =============================================================================

INSERT INTO schema_migrations (version) 
VALUES ('V2.5.0__enhance_job_processing')
ON CONFLICT (version) DO NOTHING;

COMMIT; 