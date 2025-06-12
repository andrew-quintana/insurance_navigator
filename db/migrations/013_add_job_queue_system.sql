-- =============================================================================
-- Migration: Add Job Queue System for Reliable Processing
-- Version: 013
-- Description: Add job queue table and functions for webhook-driven processing
-- =============================================================================

BEGIN;

-- =============================================================================
-- JOB QUEUE SYSTEM
-- =============================================================================

-- Processing jobs table for reliable background processing
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    job_type TEXT NOT NULL CHECK (job_type IN ('parse', 'chunk', 'embed', 'complete', 'notify')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'retrying')),
    priority INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    error_details JSONB,
    payload JSONB DEFAULT '{}'::jsonb,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_retry_count CHECK (retry_count >= 0 AND retry_count <= max_retries),
    CONSTRAINT chk_priority CHECK (priority >= 0 AND priority <= 10)
);

-- Indexes for efficient job processing
CREATE INDEX idx_processing_jobs_status_scheduled ON processing_jobs(status, scheduled_at) WHERE status IN ('pending', 'retrying');
CREATE INDEX idx_processing_jobs_document ON processing_jobs(document_id);
CREATE INDEX idx_processing_jobs_type_status ON processing_jobs(job_type, status);
CREATE INDEX idx_processing_jobs_running ON processing_jobs(status, started_at) WHERE status = 'running';
CREATE INDEX idx_processing_jobs_failed ON processing_jobs(status, retry_count, max_retries) WHERE status = 'failed';

-- Enable RLS
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;

-- RLS Policy - users can see jobs for their documents
CREATE POLICY "users_own_processing_jobs" ON processing_jobs
    FOR ALL USING (
        document_id IN (
            SELECT id FROM documents WHERE user_id = get_current_user_id()
        ) OR is_admin()
    );

-- =============================================================================
-- JOB MANAGEMENT FUNCTIONS
-- =============================================================================

-- Create a new processing job
CREATE OR REPLACE FUNCTION create_processing_job(
    doc_id UUID,
    job_type_param TEXT,
    job_payload JSONB DEFAULT '{}'::jsonb,
    priority_param INTEGER DEFAULT 0,
    max_retries_param INTEGER DEFAULT 3,
    schedule_delay_seconds INTEGER DEFAULT 0
)
RETURNS UUID AS $$
DECLARE
    job_id UUID;
    schedule_time TIMESTAMPTZ;
BEGIN
    -- Calculate scheduled time
    schedule_time := NOW() + (schedule_delay_seconds || ' seconds')::INTERVAL;
    
    -- Insert job
    INSERT INTO processing_jobs (
        document_id, job_type, payload, priority, max_retries, scheduled_at
    ) VALUES (
        doc_id, job_type_param, job_payload, priority_param, max_retries_param, schedule_time
    ) RETURNING id INTO job_id;
    
    RETURN job_id;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Mark job as running
CREATE OR REPLACE FUNCTION start_processing_job(job_id_param UUID)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE processing_jobs 
    SET 
        status = 'running',
        started_at = NOW(),
        updated_at = NOW()
    WHERE id = job_id_param AND status IN ('pending', 'retrying');
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Complete a job successfully
CREATE OR REPLACE FUNCTION complete_processing_job(
    job_id_param UUID,
    job_result JSONB DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE processing_jobs 
    SET 
        status = 'completed',
        completed_at = NOW(),
        updated_at = NOW(),
        result = job_result
    WHERE id = job_id_param AND status = 'running';
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Fail a job and handle retries
CREATE OR REPLACE FUNCTION fail_processing_job(
    job_id_param UUID,
    error_msg TEXT,
    error_details_param JSONB DEFAULT NULL
)
RETURNS TEXT AS $$
DECLARE
    job_record processing_jobs%ROWTYPE;
    next_retry_delay INTEGER;
BEGIN
    -- Get current job state
    SELECT * INTO job_record FROM processing_jobs WHERE id = job_id_param;
    
    IF NOT FOUND THEN
        RETURN 'job_not_found';
    END IF;
    
    -- Check if we can retry
    IF job_record.retry_count < job_record.max_retries THEN
        -- Calculate exponential backoff: 1min, 5min, 15min
        next_retry_delay := POWER(5, job_record.retry_count) * 60;
        
        UPDATE processing_jobs 
        SET 
            status = 'retrying',
            retry_count = retry_count + 1,
            error_message = error_msg,
            error_details = error_details_param,
            scheduled_at = NOW() + (next_retry_delay || ' seconds')::INTERVAL,
            updated_at = NOW()
        WHERE id = job_id_param;
        
        RETURN 'scheduled_retry';
    ELSE
        -- Max retries reached, mark as permanently failed
        UPDATE processing_jobs 
        SET 
            status = 'failed',
            error_message = error_msg,
            error_details = error_details_param,
            updated_at = NOW()
        WHERE id = job_id_param;
        
        RETURN 'permanently_failed';
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Get next pending jobs for processing
CREATE OR REPLACE FUNCTION get_pending_jobs(limit_param INTEGER DEFAULT 10)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    job_type TEXT,
    payload JSONB,
    retry_count INTEGER,
    priority INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pj.id,
        pj.document_id,
        pj.job_type,
        pj.payload,
        pj.retry_count,
        pj.priority
    FROM processing_jobs pj
    WHERE pj.status IN ('pending', 'retrying')
      AND pj.scheduled_at <= NOW()
    ORDER BY pj.priority DESC, pj.created_at ASC
    LIMIT limit_param;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Clean up old completed jobs (older than 7 days)
CREATE OR REPLACE FUNCTION cleanup_old_jobs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM processing_jobs 
    WHERE status IN ('completed', 'failed') 
      AND updated_at < NOW() - INTERVAL '7 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- MONITORING VIEWS
-- =============================================================================

-- Job queue status overview
CREATE VIEW job_queue_stats AS
SELECT 
    job_type,
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
    MAX(retry_count) as max_retries_used
FROM processing_jobs 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY job_type, status
ORDER BY job_type, status;

-- Failed jobs requiring attention
CREATE VIEW failed_jobs AS
SELECT 
    pj.id, pj.document_id, d.original_filename, pj.job_type,
    pj.retry_count, pj.max_retries, pj.error_message,
    pj.created_at, pj.updated_at,
    EXTRACT(EPOCH FROM (NOW() - pj.updated_at)) as age_seconds
FROM processing_jobs pj
JOIN documents d ON d.id = pj.document_id
WHERE pj.status = 'failed'
ORDER BY pj.updated_at DESC;

-- Stuck jobs (running too long)
CREATE VIEW stuck_jobs AS
SELECT 
    pj.id, pj.document_id, d.original_filename, pj.job_type,
    pj.started_at, 
    EXTRACT(EPOCH FROM (NOW() - pj.started_at)) as running_duration_seconds
FROM processing_jobs pj
JOIN documents d ON d.id = pj.document_id
WHERE pj.status = 'running'
  AND pj.started_at < NOW() - INTERVAL '30 minutes'
ORDER BY pj.started_at ASC;

COMMIT; 