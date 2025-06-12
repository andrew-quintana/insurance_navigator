-- =============================================================================
-- Queue Management System Setup
-- =============================================================================

BEGIN;

-- 1. Create queue monitoring function
CREATE OR REPLACE FUNCTION monitor_processing_queue()
RETURNS void AS $$
DECLARE
    stuck_job RECORD;
    failed_job RECORD;
BEGIN
    -- Check for stuck jobs (running for too long)
    FOR stuck_job IN 
        SELECT 
            pj.id as job_id,
            pj.document_id,
            pj.job_type,
            pj.created_at,
            d.original_filename
        FROM processing_jobs pj
        JOIN documents d ON d.id = pj.document_id
        WHERE pj.status = 'running'
          AND pj.created_at < NOW() - INTERVAL '30 minutes'
    LOOP
        -- Mark stuck jobs as failed
        UPDATE processing_jobs 
        SET 
            status = 'failed',
            error_message = 'Job stuck in running state for over 30 minutes',
            updated_at = NOW()
        WHERE id = stuck_job.job_id;
        
        RAISE LOG 'Marked stuck job as failed: % for document %', stuck_job.job_id, stuck_job.original_filename;
    END LOOP;

    -- Retry failed jobs that haven't exceeded max retries
    FOR failed_job IN 
        SELECT 
            pj.id as job_id,
            pj.document_id,
            pj.job_type,
            pj.retry_count,
            pj.max_retries,
            d.original_filename
        FROM processing_jobs pj
        JOIN documents d ON d.id = pj.document_id
        WHERE pj.status = 'failed'
          AND pj.retry_count < pj.max_retries
          AND pj.created_at > NOW() - INTERVAL '24 hours'
    LOOP
        -- Reset failed job to pending
        UPDATE processing_jobs 
        SET 
            status = 'pending',
            retry_count = retry_count + 1,
            updated_at = NOW(),
            error_message = NULL
        WHERE id = failed_job.job_id;
        
        RAISE LOG 'Retrying failed job: % for document % (attempt %/%)', 
            failed_job.job_id, failed_job.original_filename, 
            failed_job.retry_count + 1, failed_job.max_retries;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 2. Create job completion trigger function
CREATE OR REPLACE FUNCTION handle_job_completion()
RETURNS TRIGGER AS $$
DECLARE
    doc_record documents%ROWTYPE;
BEGIN
    -- Only handle completed jobs
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        -- Get document info
        SELECT * INTO doc_record FROM documents WHERE id = NEW.document_id;
        
        -- Handle different job types
        CASE NEW.job_type
            WHEN 'parse' THEN
                -- Create embed job after successful parse
                INSERT INTO processing_jobs (
                    id, document_id, job_type, status, priority, 
                    max_retries, retry_count, created_at
                ) VALUES (
                    gen_random_uuid(), NEW.document_id, 'embed', 'pending',
                    1, 3, 0, NOW()
                );
                
                -- Update document progress
                UPDATE documents 
                SET progress_percentage = 50
                WHERE id = NEW.document_id;
                
            WHEN 'embed' THEN
                -- Mark document as completed after successful embed
                UPDATE documents 
                SET 
                    status = 'completed',
                    progress_percentage = 100,
                    updated_at = NOW()
                WHERE id = NEW.document_id;
        END CASE;
        
        RAISE LOG 'Processed job completion: % type % for document %', 
            NEW.id, NEW.job_type, doc_record.original_filename;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Create job failure trigger function
CREATE OR REPLACE FUNCTION handle_job_failure()
RETURNS TRIGGER AS $$
DECLARE
    doc_record documents%ROWTYPE;
BEGIN
    -- Only handle newly failed jobs
    IF NEW.status = 'failed' AND OLD.status != 'failed' THEN
        -- Get document info
        SELECT * INTO doc_record FROM documents WHERE id = NEW.document_id;
        
        -- If max retries exceeded, mark document as failed
        IF NEW.retry_count >= NEW.max_retries THEN
            UPDATE documents 
            SET 
                status = 'failed',
                error_message = NEW.error_message,
                updated_at = NOW()
            WHERE id = NEW.document_id;
            
            RAISE LOG 'Document % failed after % retries: %', 
                doc_record.original_filename, NEW.retry_count, NEW.error_message;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Create triggers for job status changes
DROP TRIGGER IF EXISTS job_completion_trigger ON processing_jobs;
CREATE TRIGGER job_completion_trigger
    AFTER UPDATE ON processing_jobs
    FOR EACH ROW
    WHEN (NEW.status = 'completed')
    EXECUTE FUNCTION handle_job_completion();

DROP TRIGGER IF EXISTS job_failure_trigger ON processing_jobs;
CREATE TRIGGER job_failure_trigger
    AFTER UPDATE ON processing_jobs
    FOR EACH ROW
    WHEN (NEW.status = 'failed')
    EXECUTE FUNCTION handle_job_failure();

-- 5. Create queue health monitoring view
CREATE OR REPLACE VIEW queue_health AS
WITH job_stats AS (
    SELECT
        COUNT(*) FILTER (WHERE status = 'pending') as pending_jobs,
        COUNT(*) FILTER (WHERE status = 'running') as running_jobs,
        COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs,
        COUNT(*) FILTER (WHERE status = 'completed') as completed_jobs,
        COUNT(*) FILTER (WHERE status = 'running' AND created_at < NOW() - INTERVAL '30 minutes') as stuck_jobs,
        AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) FILTER (WHERE status = 'completed') as avg_completion_time_sec
    FROM processing_jobs
    WHERE created_at > NOW() - INTERVAL '24 hours'
),
document_stats AS (
    SELECT
        COUNT(*) FILTER (WHERE status = 'uploading') as uploading_docs,
        COUNT(*) FILTER (WHERE status = 'processing') as processing_docs,
        COUNT(*) FILTER (WHERE status = 'completed') as completed_docs,
        COUNT(*) FILTER (WHERE status = 'failed') as failed_docs
    FROM documents
    WHERE created_at > NOW() - INTERVAL '24 hours'
)
SELECT 
    js.*,
    ds.*,
    NOW() as checked_at
FROM job_stats js, document_stats ds;

-- 6. Create function to check queue health
CREATE OR REPLACE FUNCTION check_queue_health()
RETURNS TABLE (
    status text,
    details jsonb
) AS $$
DECLARE
    health_record RECORD;
BEGIN
    SELECT * INTO health_record FROM queue_health;
    
    -- Return overall health status
    RETURN QUERY
    SELECT
        CASE 
            WHEN health_record.stuck_jobs > 0 THEN 'WARNING'
            WHEN health_record.failed_jobs > health_record.completed_jobs THEN 'DEGRADED'
            WHEN health_record.pending_jobs = 0 AND health_record.running_jobs = 0 THEN 'IDLE'
            ELSE 'HEALTHY'
        END,
        jsonb_build_object(
            'pending_jobs', health_record.pending_jobs,
            'running_jobs', health_record.running_jobs,
            'failed_jobs', health_record.failed_jobs,
            'completed_jobs', health_record.completed_jobs,
            'stuck_jobs', health_record.stuck_jobs,
            'avg_completion_time_sec', health_record.avg_completion_time_sec,
            'uploading_docs', health_record.uploading_docs,
            'processing_docs', health_record.processing_docs,
            'completed_docs', health_record.completed_docs,
            'failed_docs', health_record.failed_docs,
            'checked_at', health_record.checked_at
        );
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- Show initial queue health after setup
SELECT * FROM check_queue_health(); 