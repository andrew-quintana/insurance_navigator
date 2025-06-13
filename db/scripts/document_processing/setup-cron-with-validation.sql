-- Setup Supabase Cron Jobs with Proper Validation and State Management
-- This ensures that jobs only move between states when truly complete

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;

-- ============================================================================
-- Enhanced Job State Validation Functions
-- ============================================================================

-- Function to validate a job is truly complete before scheduling next step
CREATE OR REPLACE FUNCTION validate_job_completion(
    job_id_param UUID,
    required_data_keys TEXT[] DEFAULT ARRAY[]::TEXT[]
)
RETURNS BOOLEAN AS $$
DECLARE
    job_record processing_jobs%ROWTYPE;
    result_data JSONB;
    key TEXT;
BEGIN
    -- Get job record
    SELECT * INTO job_record FROM processing_jobs WHERE id = job_id_param;
    
    IF NOT FOUND THEN
        RAISE WARNING 'Job % not found for validation', job_id_param;
        RETURN FALSE;
    END IF;
    
    -- Check if job is in completed status
    IF job_record.status != 'completed' THEN
        RAISE WARNING 'Job % not in completed status: %', job_id_param, job_record.status;
        RETURN FALSE;
    END IF;
    
    -- Check if result data contains required keys
    result_data := job_record.result;
    IF result_data IS NULL THEN
        RAISE WARNING 'Job % has no result data', job_id_param;
        RETURN FALSE;
    END IF;
    
    -- Validate required data keys exist
    FOREACH key IN ARRAY required_data_keys
    LOOP
        IF NOT (result_data ? key) THEN
            RAISE WARNING 'Job % missing required result key: %', job_id_param, key;
            RETURN FALSE;
        END IF;
    END LOOP;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Function to safely schedule next job only if previous is truly complete
CREATE OR REPLACE FUNCTION schedule_next_job_safely(
    prev_job_id UUID,
    doc_id UUID,
    next_job_type TEXT,
    next_payload JSONB DEFAULT '{}'::jsonb,
    required_data_keys TEXT[] DEFAULT ARRAY[]::TEXT[]
)
RETURNS UUID AS $$
DECLARE
    next_job_id UUID;
BEGIN
    -- Validate previous job completion
    IF NOT validate_job_completion(prev_job_id, required_data_keys) THEN
        RAISE EXCEPTION 'Previous job % not properly completed, cannot schedule next job', prev_job_id;
    END IF;
    
    -- Create next job
    next_job_id := create_processing_job(
        doc_id, 
        next_job_type, 
        next_payload, 
        1, -- priority
        3, -- max_retries
        5  -- 5 second delay for processing
    );
    
    -- Log the transition
    INSERT INTO job_transitions (
        from_job_id, to_job_id, document_id, 
        transition_type, created_at
    ) VALUES (
        prev_job_id, next_job_id, doc_id,
        prev_job_id::text || '->' || next_job_type,
        NOW()
    );
    
    RETURN next_job_id;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Create job transitions tracking table
CREATE TABLE IF NOT EXISTS job_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_job_id UUID REFERENCES processing_jobs(id),
    to_job_id UUID REFERENCES processing_jobs(id),
    document_id UUID REFERENCES documents(id),
    transition_type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_transitions_document ON job_transitions(document_id);
CREATE INDEX IF NOT EXISTS idx_job_transitions_created ON job_transitions(created_at);

-- ============================================================================
-- Enhanced Job Processing Monitoring
-- ============================================================================

-- Function to check job processing health
CREATE OR REPLACE FUNCTION check_job_processing_health()
RETURNS TABLE (
    status TEXT,
    stuck_jobs_count INTEGER,
    failed_jobs_count INTEGER,
    processing_time_avg NUMERIC,
    recommendation TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH job_stats AS (
        SELECT 
            COUNT(*) FILTER (WHERE status = 'pending' AND created_at < NOW() - INTERVAL '10 minutes') as stuck_pending,
            COUNT(*) FILTER (WHERE status = 'running' AND started_at < NOW() - INTERVAL '30 minutes') as stuck_running,
            COUNT(*) FILTER (WHERE status = 'failed' AND updated_at > NOW() - INTERVAL '1 hour') as recent_failed,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) FILTER (WHERE status = 'completed' AND completed_at > NOW() - INTERVAL '1 hour') as avg_processing_time
        FROM processing_jobs
    )
    SELECT 
        CASE 
            WHEN stuck_pending + stuck_running = 0 AND recent_failed <= 2 THEN 'healthy'
            WHEN stuck_pending + stuck_running <= 3 AND recent_failed <= 5 THEN 'warning'
            ELSE 'critical'
        END as status,
        (stuck_pending + stuck_running)::INTEGER as stuck_jobs_count,
        recent_failed::INTEGER as failed_jobs_count,
        COALESCE(avg_processing_time, 0)::NUMERIC as processing_time_avg,
        CASE 
            WHEN stuck_pending > 5 THEN 'Multiple jobs stuck in pending - check cron jobs'
            WHEN stuck_running > 3 THEN 'Multiple jobs stuck running - check edge functions'
            WHEN recent_failed > 10 THEN 'High failure rate - check error logs'
            WHEN avg_processing_time > 300 THEN 'Slow processing - optimize edge functions'
            ELSE 'System operating normally'
        END as recommendation
    FROM job_stats;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- ============================================================================
-- Cron Job Setup with Error Handling
-- ============================================================================

-- Note: Cron jobs must be created by a superuser in Supabase
-- This script will raise a notice if run without superuser privileges
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'postgres'
    ) THEN
        -- Cron job for processing document jobs (every minute)
        PERFORM cron.schedule(
            'process-document-jobs-enhanced',
            '* * * * *',
            $CRON$
            SELECT net.http_post(
                url := 'https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/job-processor',
                headers := jsonb_build_object(
                    'Content-Type', 'application/json',
                    'Authorization', 'Bearer ' || current_setting('app.supabase_service_role_key', true)
                ),
                body := jsonb_build_object(
                    'source', 'cron_enhanced',
                    'timestamp', now(),
                    'validation_enabled', true
                ),
                timeout_milliseconds := 45000
            );
            $CRON$
        );

        -- Cron job for health monitoring (every 5 minutes)
        PERFORM cron.schedule(
            'monitor-job-health',
            '*/5 * * * *',
            $CRON$
            INSERT INTO job_health_log (check_time, health_status, stuck_jobs, failed_jobs, avg_processing_time, recommendation)
            SELECT 
                NOW(),
                status,
                (details->>'stuck_jobs')::INTEGER,
                (details->>'failed_jobs')::INTEGER,
                (details->>'avg_completion_time_sec')::NUMERIC,
                CASE 
                    WHEN status = 'WARNING' THEN 'Stuck jobs detected - check processing queue'
                    WHEN status = 'DEGRADED' THEN 'High failure rate - check error logs'
                    WHEN status = 'IDLE' THEN 'Queue is idle - no active processing'
                    ELSE 'System operating normally'
                END
            FROM check_queue_health();
            $CRON$
        );

        -- Cron job for cleanup (daily at 2 AM)
        PERFORM cron.schedule(
            'cleanup-old-jobs-enhanced',
            '0 2 * * *',
            $CRON$
            -- Clean up old cron logs (keep 7 days)
            DELETE FROM cron_job_logs WHERE execution_time < NOW() - INTERVAL '7 days';
            
            -- Clean up old health logs (keep 30 days)
            DELETE FROM job_health_log WHERE check_time < NOW() - INTERVAL '30 days';
            $CRON$
        );
    ELSE
        RAISE NOTICE 'Skipping cron job creation - requires superuser privileges';
    END IF;
END $$;

-- ============================================================================
-- Monitoring Tables
-- ============================================================================

-- Table for cron job execution logs
CREATE TABLE IF NOT EXISTS cron_job_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name TEXT NOT NULL,
    execution_time TIMESTAMPTZ NOT NULL,
    http_status INTEGER,
    response_content TEXT,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cron_job_logs_job_name ON cron_job_logs(job_name);
CREATE INDEX IF NOT EXISTS idx_cron_job_logs_execution_time ON cron_job_logs(execution_time);

-- Table for health monitoring
CREATE TABLE IF NOT EXISTS job_health_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_time TIMESTAMPTZ NOT NULL,
    health_status TEXT NOT NULL,
    stuck_jobs INTEGER DEFAULT 0,
    failed_jobs INTEGER DEFAULT 0,
    avg_processing_time NUMERIC DEFAULT 0,
    recommendation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_health_log_check_time ON job_health_log(check_time);

-- ============================================================================
-- Views for Monitoring
-- ============================================================================

-- View for current job processing status
CREATE OR REPLACE VIEW current_job_status AS
SELECT 
    d.id as document_id,
    d.original_filename,
    d.status as document_status,
    d.progress_percentage,
    d.created_at as uploaded_at,
    COUNT(pj.id) as total_jobs,
    COUNT(CASE WHEN pj.status = 'completed' THEN 1 END) as completed_jobs,
    COUNT(CASE WHEN pj.status = 'pending' THEN 1 END) as pending_jobs,
    COUNT(CASE WHEN pj.status = 'running' THEN 1 END) as running_jobs,
    COUNT(CASE WHEN pj.status = 'failed' THEN 1 END) as failed_jobs,
    MAX(pj.updated_at) as last_job_update,
    ARRAY_AGG(pj.job_type ORDER BY pj.created_at) as job_sequence,
    ARRAY_AGG(pj.status ORDER BY pj.created_at) as status_sequence
FROM documents d
LEFT JOIN processing_jobs pj ON d.id = pj.document_id
WHERE d.created_at > NOW() - INTERVAL '24 hours'
GROUP BY d.id, d.original_filename, d.status, d.progress_percentage, d.created_at
ORDER BY d.created_at DESC;

-- View for cron job health
CREATE OR REPLACE VIEW cron_job_health AS
SELECT 
    job_name,
    COUNT(*) as total_executions,
    COUNT(*) FILTER (WHERE success = TRUE) as successful_executions,
    COUNT(*) FILTER (WHERE success = FALSE) as failed_executions,
    MAX(execution_time) as last_execution,
    AVG(CASE WHEN http_status = 200 THEN 1 ELSE 0 END) as success_rate
FROM cron_job_logs 
WHERE execution_time > NOW() - INTERVAL '24 hours'
GROUP BY job_name
ORDER BY job_name;

-- ============================================================================
-- View current cron jobs and their status
-- ============================================================================
SELECT 
    jobname as "Job Name",
    schedule as "Schedule", 
    active as "Active",
    CASE 
        WHEN active THEN '✅ Running'
        ELSE '❌ Stopped'
    END as "Status"
FROM cron.job 
WHERE jobname LIKE '%document%' OR jobname LIKE '%job%' OR jobname LIKE '%health%'
ORDER BY jobname;

-- Show recent cron execution results
SELECT 
    jr.jobid,
    j.jobname,
    jr.runid,
    jr.job_pid,
    jr.database,
    jr.username,
    jr.command,
    jr.status,
    jr.return_message,
    jr.start_time,
    jr.end_time
FROM cron.job_run_details jr
JOIN cron.job j ON jr.jobid = j.jobid
WHERE jr.start_time > NOW() - INTERVAL '1 hour'
ORDER BY jr.start_time DESC
LIMIT 10; 