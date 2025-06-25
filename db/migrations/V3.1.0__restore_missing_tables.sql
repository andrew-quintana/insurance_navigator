-- =============================================================================
-- RESTORE MISSING TABLES V3.1.0
-- Description: Restore critical tables that were inadvertently dropped
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- =============================================================================
-- STEP 1: RESTORE SCHEMA MIGRATIONS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

-- Record all known applied migrations
INSERT INTO schema_migrations (version, applied_at) VALUES
    ('V2.0.0__consolidated_production_schema', NOW() - INTERVAL '4 days'),
    ('V2.1.0__fix_schema_to_match_current_supabase', NOW() - INTERVAL '3 days'),
    ('V2.3.0__add_document_processing_status', NOW() - INTERVAL '2 days'),
    ('V2.4.0__add_processing_jobs', NOW() - INTERVAL '1 day'),
    ('V2.5.0__enhance_job_processing', NOW() - INTERVAL '12 hours'),
    ('V3.0.0__unified_document_schema', NOW() - INTERVAL '6 hours'),
    ('V3.1.0__restore_missing_tables', NOW())
ON CONFLICT (version) DO NOTHING;

-- =============================================================================
-- STEP 2: RESTORE PROCESSING JOBS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS "public"."processing_jobs" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "document_id" uuid NOT NULL,
    "job_type" varchar(50) NOT NULL,
    "status" varchar(50) DEFAULT 'pending' NOT NULL,
    "priority" integer DEFAULT 0,
    "max_retries" integer DEFAULT 3,
    "retry_count" integer DEFAULT 0,
    "payload" jsonb DEFAULT '{}',
    "result" jsonb,
    "error_details" jsonb,
    "created_at" timestamptz DEFAULT now(),
    "started_at" timestamptz,
    "completed_at" timestamptz,
    "updated_at" timestamptz DEFAULT now(),
    "scheduled_at" timestamptz DEFAULT now(),
    CONSTRAINT "processing_jobs_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "processing_jobs_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."documents"("id") ON DELETE CASCADE,
    CONSTRAINT "valid_job_type" CHECK (job_type IN ('parse', 'vectorize', 'analyze', 'extract')),
    CONSTRAINT "valid_job_status" CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Add index for job querying
CREATE INDEX IF NOT EXISTS "idx_processing_jobs_status_priority" ON "public"."processing_jobs" ("status", "priority" DESC);
CREATE INDEX IF NOT EXISTS "idx_processing_jobs_document" ON "public"."processing_jobs" ("document_id");

-- Add trigger for updating updated_at
CREATE TRIGGER "set_processing_jobs_updated_at"
    BEFORE UPDATE ON "public"."processing_jobs"
    FOR EACH ROW
    EXECUTE FUNCTION "public"."update_updated_at_column"();

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE ON "public"."processing_jobs" TO "anon";
GRANT SELECT, INSERT, UPDATE ON "public"."processing_jobs" TO "authenticated";
GRANT SELECT, INSERT, UPDATE ON "public"."processing_jobs" TO "service_role";

-- =============================================================================
-- STEP 3: RESTORE DOCUMENT PROCESSING STATUS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS document_processing_status (
    document_id UUID PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    total_chunks INTEGER NOT NULL,
    processed_chunks INTEGER[] DEFAULT '{}',
    status TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    overlap INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Restore indexes
CREATE INDEX IF NOT EXISTS idx_doc_processing_status ON document_processing_status(status);

-- Restore trigger
CREATE OR REPLACE FUNCTION update_document_processing_status_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_doc_processing_status_timestamp
    BEFORE UPDATE ON document_processing_status
    FOR EACH ROW
    EXECUTE FUNCTION update_document_processing_status_updated_at();

-- =============================================================================
-- STEP 4: RESTORE REALTIME PROGRESS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS realtime_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    session_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    progress_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_realtime_progress_user_session ON realtime_progress(user_id, session_id);
CREATE INDEX IF NOT EXISTS idx_realtime_progress_created ON realtime_progress(created_at);

-- =============================================================================
-- STEP 5: MIGRATE EXISTING DOCUMENT STATUS
-- =============================================================================

-- Create processing jobs for any documents in 'processing' state
INSERT INTO processing_jobs (
    id,
    job_type,
    status,
    payload,
    created_at,
    updated_at
)
SELECT
    gen_random_uuid(),
    'document_processing',
    CASE 
        WHEN d.status = 'processing' THEN 'running'
        WHEN d.status = 'failed' THEN 'failed'
        ELSE 'pending'
    END,
    jsonb_build_object(
        'document_id', d.id,
        'user_id', d.user_id,
        'filename', d.original_filename
    ),
    d.created_at,
    d.updated_at
FROM documents d
WHERE d.status IN ('processing', 'failed', 'pending')
ON CONFLICT (id) DO NOTHING;

-- Create document processing status entries
INSERT INTO document_processing_status (
    document_id,
    total_chunks,
    status,
    chunk_size,
    overlap,
    storage_path,
    created_at,
    updated_at
)
SELECT
    d.id,
    1, -- Default to 1 chunk since we don't have total_chunks
    d.status,
    4000, -- default chunk size
    200,  -- default overlap
    COALESCE(d.storage_path, ''), -- Handle NULL storage paths
    d.created_at,
    d.updated_at
FROM documents d
WHERE d.status != 'completed'
ON CONFLICT (document_id) DO NOTHING;

-- Add cron job to process documents
SELECT cron.schedule(
    'process-documents',  -- job name
    '* * * * *',         -- every minute
    $$
    SELECT net.http_post(
        url := 'http://localhost:54321/functions/v1/job-processor',
        headers := '{"Content-Type": "application/json", "Authorization": "Bearer ' || current_setting('app.settings.service_role_key') || '"}'::jsonb,
        body := '{}'::jsonb
    ) AS request_id;
    $$
);

-- Function to get pending jobs
CREATE OR REPLACE FUNCTION get_pending_jobs(limit_param integer)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    job_type text,
    status text,
    priority integer,
    retry_count integer,
    payload jsonb
) AS $$
BEGIN
    RETURN QUERY
    SELECT j.id, j.document_id, j.job_type, j.status, j.priority, j.retry_count, j.payload
    FROM processing_jobs j
    WHERE j.status = 'pending'
    AND j.scheduled_at <= NOW()
    ORDER BY j.priority DESC, j.scheduled_at ASC
    LIMIT limit_param
    FOR UPDATE SKIP LOCKED;
END;
$$ LANGUAGE plpgsql;

-- Function to start a processing job
CREATE OR REPLACE FUNCTION start_processing_job(job_id_param uuid)
RETURNS void AS $$
BEGIN
    UPDATE processing_jobs
    SET status = 'running',
        started_at = NOW(),
        updated_at = NOW()
    WHERE id = job_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to complete a processing job
CREATE OR REPLACE FUNCTION complete_processing_job(job_id_param uuid, job_result jsonb)
RETURNS void AS $$
BEGIN
    UPDATE processing_jobs
    SET status = 'completed',
        result = job_result,
        completed_at = NOW(),
        updated_at = NOW()
    WHERE id = job_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to fail a processing job
CREATE OR REPLACE FUNCTION fail_processing_job(
    job_id_param uuid,
    error_msg text,
    error_details_param jsonb
)
RETURNS void AS $$
DECLARE
    current_retry_count integer;
    max_retries_count integer;
BEGIN
    -- Get current retry count and max retries
    SELECT retry_count, max_retries 
    INTO current_retry_count, max_retries_count
    FROM processing_jobs
    WHERE id = job_id_param;

    -- Update job status based on retry count
    UPDATE processing_jobs
    SET status = CASE 
            WHEN current_retry_count >= max_retries_count THEN 'failed'
            ELSE 'retrying'
        END,
        retry_count = retry_count + 1,
        error_message = error_msg,
        error_details = error_details_param,
        scheduled_at = CASE 
            WHEN current_retry_count < max_retries_count 
            THEN NOW() + (INTERVAL '1 minute' * (2 ^ retry_count)) -- Exponential backoff
            ELSE scheduled_at
        END,
        updated_at = NOW()
    WHERE id = job_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to create a new processing job
CREATE OR REPLACE FUNCTION create_processing_job(
    doc_id uuid,
    job_type_param text,
    job_payload jsonb,
    schedule_delay_seconds integer DEFAULT 0
)
RETURNS uuid AS $$
DECLARE
    new_job_id uuid;
BEGIN
    INSERT INTO processing_jobs (
        document_id,
        job_type,
        status,
        priority,
        payload,
        scheduled_at
    ) VALUES (
        doc_id,
        job_type_param,
        'pending',
        5, -- Default priority
        job_payload,
        NOW() + (schedule_delay_seconds * INTERVAL '1 second')
    )
    RETURNING id INTO new_job_id;

    RETURN new_job_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get job statistics
CREATE OR REPLACE FUNCTION get_job_stats()
RETURNS jsonb AS $$
DECLARE
    result jsonb;
BEGIN
    SELECT jsonb_build_object(
        'pending_count', (SELECT COUNT(*) FROM processing_jobs WHERE status = 'pending'),
        'running_count', (SELECT COUNT(*) FROM processing_jobs WHERE status = 'running'),
        'completed_count', (SELECT COUNT(*) FROM processing_jobs WHERE status = 'completed'),
        'failed_count', (SELECT COUNT(*) FROM processing_jobs WHERE status = 'failed'),
        'retrying_count', (SELECT COUNT(*) FROM processing_jobs WHERE status = 'retrying'),
        'recent_failures', (
            SELECT jsonb_agg(job)
            FROM (
                SELECT id, document_id, job_type, error_message, updated_at
                FROM processing_jobs
                WHERE status = 'failed'
                ORDER BY updated_at DESC
                LIMIT 10
            ) job
        ),
        'stuck_jobs', (
            SELECT jsonb_agg(job)
            FROM (
                SELECT id, document_id, job_type, started_at, updated_at
                FROM processing_jobs
                WHERE status = 'running'
                AND started_at < NOW() - INTERVAL '1 hour'
                ORDER BY started_at ASC
            ) job
        )
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMIT;