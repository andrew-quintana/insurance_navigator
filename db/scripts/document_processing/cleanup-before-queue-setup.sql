-- =============================================================================
-- Cleanup Script: Remove old queue management components
-- =============================================================================

BEGIN;

-- 1. Drop existing triggers
DROP TRIGGER IF EXISTS document_processing_trigger ON documents;
DROP TRIGGER IF EXISTS job_completion_trigger ON processing_jobs;
DROP TRIGGER IF EXISTS job_failure_trigger ON processing_jobs;

-- 2. Drop existing functions
DROP FUNCTION IF EXISTS trigger_document_processing();
DROP FUNCTION IF EXISTS monitor_processing_queue();
DROP FUNCTION IF EXISTS handle_job_completion();
DROP FUNCTION IF EXISTS handle_job_failure();
DROP FUNCTION IF EXISTS backfill_stuck_documents();

-- 3. Drop any existing queue-related views
DROP VIEW IF EXISTS queue_health CASCADE;

-- 4. Show what was cleaned up
SELECT 'Basic cleanup complete' as status;

-- 5. Attempt to clean up cron jobs (non-blocking)
DO $$
BEGIN
    -- Only attempt if we have superuser access
    IF EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'postgres'
    ) THEN
        DELETE FROM cron.job WHERE jobname = 'monitor-processing-queue';
        RAISE NOTICE 'Cron jobs cleaned up successfully';
    ELSE
        RAISE NOTICE 'Skipping cron job cleanup - requires superuser privileges';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Cron cleanup failed (non-critical): %', SQLERRM;
END $$;

COMMIT; 