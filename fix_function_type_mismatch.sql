-- Fix Function Type Mismatch
-- Updates get_pending_jobs function to match actual table schema

-- TODO: IMPROVE QUEUE PROCESSING - Include stale 'running' jobs in get_pending_jobs()
-- Current function only looks for 'pending' and 'retrying' jobs, but jobs can get stuck in 'running' status
-- Should add logic to include jobs that have been 'running' for > 5 minutes to auto-recovery stale jobs
-- For MVP: Use fix_stuck_queue.py to manually reset stuck jobs

-- Drop and recreate function with correct return types
DROP FUNCTION IF EXISTS get_pending_jobs(integer);

CREATE OR REPLACE FUNCTION get_pending_jobs(limit_param integer DEFAULT 10)
RETURNS TABLE(
    id uuid, 
    document_id uuid, 
    job_type character varying,  -- Changed from 'text' to match table
    payload jsonb, 
    retry_count integer, 
    priority integer
) 
LANGUAGE plpgsql
AS $$
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
$$; 
-- Updates get_pending_jobs function to match actual table schema

-- TODO: IMPROVE QUEUE PROCESSING - Include stale 'running' jobs in get_pending_jobs()
-- Current function only looks for 'pending' and 'retrying' jobs, but jobs can get stuck in 'running' status
-- Should add logic to include jobs that have been 'running' for > 5 minutes to auto-recovery stale jobs
-- For MVP: Use fix_stuck_queue.py to manually reset stuck jobs

-- Drop and recreate function with correct return types
DROP FUNCTION IF EXISTS get_pending_jobs(integer);

CREATE OR REPLACE FUNCTION get_pending_jobs(limit_param integer DEFAULT 10)
RETURNS TABLE(
    id uuid, 
    document_id uuid, 
    job_type character varying,  -- Changed from 'text' to match table
    payload jsonb, 
    retry_count integer, 
    priority integer
) 
LANGUAGE plpgsql
AS $$
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
$$; 