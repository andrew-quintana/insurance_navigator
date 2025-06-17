-- ================================================
-- V2.0.3 - Restore Processing Jobs Table
-- The documents table triggers expect this table to exist
-- ================================================

-- Create processing_jobs table (restored from previous schema)
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    payload JSONB DEFAULT '{}',
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_processing_jobs_document_id ON processing_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_scheduled_at ON processing_jobs(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_job_type ON processing_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_user_id ON processing_jobs(user_id);

-- Create indexes for job processing queries
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status_scheduled ON processing_jobs(status, scheduled_at) 
WHERE status IN ('pending', 'retrying');

CREATE INDEX IF NOT EXISTS idx_processing_jobs_running ON processing_jobs(status, started_at) 
WHERE status = 'running';

CREATE INDEX IF NOT EXISTS idx_processing_jobs_failed ON processing_jobs(status, retry_count, max_retries) 
WHERE status = 'failed';

-- Enable RLS (if needed)
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for user access
DROP POLICY IF EXISTS "users_own_processing_jobs" ON processing_jobs;
CREATE POLICY "users_own_processing_jobs" ON processing_jobs
    FOR ALL USING (user_id = auth.uid());

-- Log successful migration
DO $$ 
BEGIN
    -- Check if audit_logs has the required columns
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'audit_logs' AND column_name = 'action'
    ) THEN
        -- Try to insert with required fields
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'audit_logs' AND column_name = 'resource_type'
        ) THEN
            -- Has resource_type column
            INSERT INTO audit_logs (action, resource_type, created_at)
            VALUES ('SCHEMA_MIGRATION_V2.0.3_PROCESSING_JOBS_RESTORED', 'migration', NOW());
        ELSE
            -- No resource_type column, use basic insert
            INSERT INTO audit_logs (action, created_at)
            VALUES ('SCHEMA_MIGRATION_V2.0.3_PROCESSING_JOBS_RESTORED', NOW());
        END IF;
    END IF;
END $$; 