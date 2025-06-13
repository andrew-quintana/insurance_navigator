-- ========================================================
-- Restore Cron Jobs and Processing Infrastructure
-- ========================================================
-- This script restores the cron job and trigger functionality
-- that was accidentally removed, updated to work with the new schema
-- ========================================================

BEGIN;

-- Track restoration start
INSERT INTO migration_progress (step_name, status, details)
VALUES (
    'restore_cron_triggers',
    'running',
    jsonb_build_object(
        'migration_version', 'V2.1.4',
        'started_at', NOW(),
        'restoring_tables', ARRAY['cron_job_logs', 'processing_jobs'],
        'updating_triggers', true,
        'updating_cron_jobs', true
    )
)
ON CONFLICT (step_name) DO UPDATE SET
    status = EXCLUDED.status,
    started_at = NOW(),
    details = EXCLUDED.details;

-- ========================================================
-- Phase 1: Restore Essential Tables for Cron Jobs
-- ========================================================

-- Table for cron job execution logs
CREATE TABLE IF NOT EXISTS cron_job_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name TEXT NOT NULL,
    execution_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    http_status INTEGER,
    response_content TEXT,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_cron_job_logs_job_name ON cron_job_logs(job_name);
CREATE INDEX IF NOT EXISTS idx_cron_job_logs_execution_time ON cron_job_logs(execution_time);

-- Processing jobs table (updated for new schema)
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES user_documents(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL CHECK (job_type IN ('parse', 'vector', 'extract_policy')),
    payload JSONB,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    priority INTEGER DEFAULT 1,
    max_retries INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for processing jobs
CREATE INDEX IF NOT EXISTS idx_processing_jobs_document_id ON processing_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_scheduled_for ON processing_jobs(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_job_type ON processing_jobs(job_type);

-- ========================================================
-- Phase 2: Update Trigger Function for New Schema
-- ========================================================

-- Updated trigger function to work with user_documents table
CREATE OR REPLACE FUNCTION trigger_document_processing()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    -- Only create a job if the document is newly uploaded or status changed to uploaded
    IF (TG_OP = 'INSERT' AND NEW.status IN ('pending', 'uploaded')) OR 
       (TG_OP = 'UPDATE' AND OLD.status != NEW.status AND NEW.status IN ('pending', 'uploaded')) THEN
        
        -- Create a parse job for the document
        INSERT INTO processing_jobs (
            id,
            document_id,
            job_type,
            payload,
            status,
            priority,
            max_retries,
            retry_count,
            created_at,
            scheduled_for
        ) VALUES (
            gen_random_uuid(),
            NEW.id,
            'parse',
            jsonb_build_object(
                'filename', NEW.original_filename,
                'file_path', NEW.file_path,
                'user_id', NEW.user_id,
                'storage_provider', NEW.storage_provider,
                'bucket_name', NEW.bucket_name
            ),
            'pending',
            1, -- priority
            3, -- max_retries
            0, -- retry_count
            NOW(),
            NOW() + INTERVAL '5 seconds' -- process in 5 seconds
        );
        
        -- Log the job creation
        RAISE LOG 'Created processing job for document %: %', NEW.id, NEW.original_filename;
        
        -- Update document status to processing
        UPDATE user_documents 
        SET 
            processing_status = 'processing',
            updated_at = NOW()
        WHERE id = NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$;

-- ========================================================
-- Phase 3: Create Updated Trigger
-- ========================================================

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS document_processing_trigger ON user_documents;

-- Create trigger that fires on INSERT and UPDATE on user_documents
CREATE TRIGGER document_processing_trigger
    AFTER INSERT OR UPDATE ON user_documents
    FOR EACH ROW
    EXECUTE FUNCTION trigger_document_processing();

-- ========================================================
-- Phase 4: Update Cron Jobs for New Schema
-- ========================================================

-- Update the cleanup cron job to clean cron_job_logs
SELECT cron.unschedule('cleanup-old-logs');
SELECT cron.schedule(
    'cleanup-old-logs',
    '0 2 * * *',
    $$
    DELETE FROM cron_job_logs WHERE execution_time < NOW() - INTERVAL '7 days';
    DELETE FROM processing_jobs WHERE status = 'completed' AND completed_at < NOW() - INTERVAL '30 days';
    $$
);

-- Update the health monitoring job
SELECT cron.unschedule('monitor-job-health');
SELECT cron.schedule(
    'monitor-job-health',
    '*/5 * * * *',
    $$
    INSERT INTO cron_job_logs (job_name, execution_time, success, response_content)
    VALUES ('health-check', NOW(), TRUE, 
        jsonb_build_object(
            'pending_jobs', (SELECT COUNT(*) FROM processing_jobs WHERE status = 'pending'),
            'user_documents', (SELECT COUNT(*) FROM user_documents),
            'recent_uploads', (SELECT COUNT(*) FROM user_documents WHERE created_at > NOW() - INTERVAL '1 hour')
        )::text
    );
    $$
);

-- The document processing job should remain the same as it calls edge functions

-- ========================================================
-- Phase 5: Backfill Function for New Schema
-- ========================================================

CREATE OR REPLACE FUNCTION backfill_stuck_documents()
RETURNS TABLE (
    document_id UUID,
    filename TEXT,
    jobs_created INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    doc_record RECORD;
    job_count INTEGER;
BEGIN
    -- Find documents that are stuck (uploaded but no processing jobs)
    FOR doc_record IN 
        SELECT d.id, d.original_filename, d.file_path, d.user_id, d.status, d.processing_status
        FROM user_documents d
        LEFT JOIN processing_jobs pj ON d.id = pj.document_id
        WHERE d.status IN ('pending', 'uploaded') 
          AND d.processing_status IN ('pending', 'uploaded')
          AND pj.id IS NULL -- No existing jobs
          AND d.created_at > NOW() - INTERVAL '7 days' -- Only recent documents
    LOOP
        -- Create a parse job for this stuck document
        INSERT INTO processing_jobs (
            id,
            document_id,
            job_type,
            payload,
            status,
            priority,
            max_retries,
            retry_count,
            created_at,
            scheduled_for
        ) VALUES (
            gen_random_uuid(),
            doc_record.id,
            'parse',
            jsonb_build_object(
                'filename', doc_record.original_filename,
                'file_path', doc_record.file_path,
                'user_id', doc_record.user_id
            ),
            'pending',
            1, -- priority
            3, -- max_retries
            0, -- retry_count
            NOW(),
            NOW() + INTERVAL '10 seconds' -- process in 10 seconds
        );
        
        job_count := 1;
        
        -- Update document status
        UPDATE user_documents 
        SET 
            processing_status = 'processing',
            updated_at = NOW()
        WHERE id = doc_record.id;
        
        -- Return info about processed document
        document_id := doc_record.id;
        filename := doc_record.original_filename;
        jobs_created := job_count;
        
        RETURN NEXT;
        
        RAISE LOG 'Backfilled processing job for stuck document %: %', doc_record.id, doc_record.original_filename;
    END LOOP;
    
    RETURN;
END;
$$;

-- ========================================================
-- Phase 6: Execute Backfill and Validation
-- ========================================================

-- Process any existing documents that need jobs
SELECT * FROM backfill_stuck_documents();

-- Update migration progress
UPDATE migration_progress 
SET status = 'completed', completed_at = NOW(),
    details = jsonb_build_object(
        'migration_version', 'V2.1.4',
        'tables_restored', ARRAY['cron_job_logs', 'processing_jobs'],
        'triggers_updated', true,
        'cron_jobs_updated', true,
        'backfill_completed', true,
        'final_table_count', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'),
        'processing_jobs_created', (SELECT COUNT(*) FROM processing_jobs),
        'documents_ready_for_processing', (SELECT COUNT(*) FROM user_documents WHERE processing_status = 'pending')
    )
WHERE step_name = 'restore_cron_triggers';

-- Show restoration results
DO $$
DECLARE
    job_count INTEGER;
    doc_count INTEGER;
    trigger_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO job_count FROM processing_jobs;
    SELECT COUNT(*) INTO doc_count FROM user_documents;
    SELECT COUNT(*) INTO trigger_count FROM information_schema.triggers WHERE trigger_name = 'document_processing_trigger';
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'CRON & TRIGGER RESTORATION COMPLETED!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables restored: cron_job_logs, processing_jobs';
    RAISE NOTICE 'Processing jobs: %', job_count;
    RAISE NOTICE 'User documents: %', doc_count;
    RAISE NOTICE 'Document trigger: % (% = working)', trigger_count, CASE WHEN trigger_count > 0 THEN '✅' ELSE '❌' END;
    RAISE NOTICE '';
    RAISE NOTICE 'Cron jobs updated to work with new schema:';
    RAISE NOTICE '- process-document-jobs: calls edge functions';
    RAISE NOTICE '- monitor-job-health: logs to cron_job_logs';
    RAISE NOTICE '- cleanup-old-logs: cleans both tables';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- ========================================================
-- Restoration Summary:
-- ========================================================
-- ✅ Restored cron_job_logs table for monitoring
-- ✅ Restored processing_jobs table (updated for user_documents)
-- ✅ Updated document_processing_trigger for new schema
-- ✅ Updated cron jobs to work with new table structure
-- ✅ Created backfill function for stuck documents
-- ✅ Maintained all existing cron job schedules
--
-- Final Table Count: 13 (11 core + 2 processing infrastructure)
-- All cron jobs and triggers now work with the simplified schema
-- ======================================================== 