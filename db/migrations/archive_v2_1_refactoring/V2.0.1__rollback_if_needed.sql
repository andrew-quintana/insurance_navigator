-- =============================================================================
-- MVP SCHEMA REFACTOR ROLLBACK - V2.0.1
-- Description: Rollback V2.0.0 schema refactoring if needed
-- WARNING: This will restore the complex schema but may lose policy_basics data
-- =============================================================================

BEGIN;

-- =============================================================================
-- CRITICAL WARNING
-- =============================================================================
-- This rollback script restores the previous complex schema
-- Data in policy_basics column will be preserved but may not be accessible
-- through the old API endpoints until they are updated

-- =============================================================================
-- PHASE 1: RESTORE PROCESSING JOBS TABLE
-- =============================================================================

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
    CONSTRAINT chk_retry_count CHECK (retry_count >= 0 AND retry_count <= max_retries),
    CONSTRAINT chk_priority CHECK (priority >= 0 AND priority <= 10)
);

-- Restore indexes
CREATE INDEX idx_processing_jobs_status_scheduled ON processing_jobs(status, scheduled_at) WHERE status IN ('pending', 'retrying');
CREATE INDEX idx_processing_jobs_document ON processing_jobs(document_id);
CREATE INDEX idx_processing_jobs_type_status ON processing_jobs(job_type, status);
CREATE INDEX idx_processing_jobs_running ON processing_jobs(status, started_at) WHERE status = 'running';
CREATE INDEX idx_processing_jobs_failed ON processing_jobs(status, retry_count, max_retries) WHERE status = 'failed';

-- =============================================================================
-- PHASE 2: RESTORE AGENT TRACKING TABLES
-- =============================================================================

CREATE TABLE agent_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    state_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    state_type TEXT NOT NULL DEFAULT 'unknown',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE workflow_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    workflow_type TEXT NOT NULL,
    current_step TEXT,
    state_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    is_completed BOOLEAN DEFAULT false
);

CREATE TABLE agent_policy_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    policy_id UUID,
    context_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- =============================================================================
-- PHASE 3: RESTORE POLICY MANAGEMENT TABLES
-- =============================================================================

CREATE TABLE policy_records (
    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_policy_path TEXT NOT NULL,
    summary JSONB NOT NULL,
    structured_metadata JSONB NOT NULL,
    encrypted_policy_data JSONB NOT NULL,
    encryption_key_id UUID REFERENCES encryption_keys(id),
    source_type TEXT NOT NULL CHECK (source_type IN ('uploaded', 'fetched', 'admin_override')),
    coverage_start_date DATE NOT NULL,
    coverage_end_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE user_policy_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    policy_id UUID NOT NULL REFERENCES policy_records(policy_id),
    role TEXT NOT NULL CHECK (role IN ('subscriber', 'dependent', 'spouse', 'employee', 'guardian', 'representative', 'self')),
    relationship_verified BOOLEAN DEFAULT false,
    linked_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =============================================================================
-- PHASE 4: RESTORE FEATURE FLAGS SYSTEM
-- =============================================================================

CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_enabled BOOLEAN DEFAULT false,
    config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    environment TEXT DEFAULT 'production'
);

CREATE TABLE feature_flag_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_name TEXT NOT NULL,
    user_id UUID REFERENCES users(id),
    result BOOLEAN NOT NULL,
    context JSONB DEFAULT '{}'::jsonb,
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- PHASE 5: RESTORE COMPLEX COLUMNS TO DOCUMENTS TABLE
-- =============================================================================

ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
ADD COLUMN IF NOT EXISTS total_chunks INTEGER,
ADD COLUMN IF NOT EXISTS processed_chunks INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS failed_chunks INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS llama_parse_job_id TEXT,
ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS error_message TEXT,
ADD COLUMN IF NOT EXISTS error_details JSONB;

-- Restore complex constraints
ALTER TABLE documents 
ADD CONSTRAINT chk_progress_consistency CHECK (
    (status = 'completed' AND progress_percentage = 100) OR (status != 'completed')
),
ADD CONSTRAINT chk_chunk_consistency CHECK (
    (total_chunks IS NULL) OR (processed_chunks + failed_chunks <= total_chunks)
);

-- Update status constraint to include more statuses
ALTER TABLE documents 
DROP CONSTRAINT IF EXISTS documents_status_check;

ALTER TABLE documents 
ADD CONSTRAINT documents_status_check 
CHECK (status IN (
    'pending', 'uploading', 'processing', 'chunking', 
    'embedding', 'completed', 'failed', 'cancelled'
));

-- =============================================================================
-- PHASE 6: RESTORE COMPLEX COLUMNS TO REGULATORY_DOCUMENTS
-- =============================================================================

ALTER TABLE regulatory_documents 
ADD COLUMN IF NOT EXISTS search_metadata JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS program TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS source_last_checked TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS checksum_validation JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS parsing_metadata JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS version_history JSONB DEFAULT '[]'::jsonb;

-- =============================================================================
-- PHASE 7: RENAME DOCUMENT_VECTORS BACK TO USER_DOCUMENT_VECTORS
-- =============================================================================

ALTER TABLE document_vectors 
RENAME TO user_document_vectors;

-- Restore original indexes
DROP INDEX IF EXISTS idx_document_vectors_user_id;
DROP INDEX IF EXISTS idx_document_vectors_document_id;
DROP INDEX IF EXISTS idx_document_vectors_document_record;
DROP INDEX IF EXISTS idx_document_vectors_active;
DROP INDEX IF EXISTS idx_document_vectors_embedding;
DROP INDEX IF EXISTS idx_document_vectors_encryption_key;

CREATE INDEX idx_user_document_vectors_user_id ON user_document_vectors(user_id);
CREATE INDEX idx_user_document_vectors_document_id ON user_document_vectors(document_id);
CREATE INDEX idx_user_document_vectors_document_record ON user_document_vectors(document_record_id);
CREATE INDEX idx_user_document_vectors_active ON user_document_vectors(is_active) WHERE is_active = true;
CREATE INDEX idx_user_document_vectors_embedding ON user_document_vectors USING ivfflat (content_embedding vector_cosine_ops);
CREATE INDEX idx_user_document_vectors_encryption_key ON user_document_vectors(encryption_key_id);

-- =============================================================================
-- PHASE 8: RESTORE COMPLEX FUNCTIONS
-- =============================================================================

-- Restore job queue functions
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
    schedule_time := NOW() + (schedule_delay_seconds || ' seconds')::INTERVAL;
    
    INSERT INTO processing_jobs (
        document_id, job_type, payload, priority, max_retries, scheduled_at
    ) VALUES (
        doc_id, job_type_param, job_payload, priority_param, max_retries_param, schedule_time
    ) RETURNING id INTO job_id;
    
    RETURN job_id;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Restore document progress function
CREATE OR REPLACE FUNCTION update_document_progress(
    doc_id UUID,
    progress_pct INTEGER,
    total_chunks_param INTEGER DEFAULT NULL,
    processed_chunks_param INTEGER DEFAULT NULL,
    error_msg TEXT DEFAULT NULL,
    error_details_param JSONB DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE documents 
    SET 
        progress_percentage = progress_pct,
        total_chunks = COALESCE(total_chunks_param, total_chunks),
        processed_chunks = COALESCE(processed_chunks_param, processed_chunks),
        error_message = error_msg,
        error_details = error_details_param,
        updated_at = NOW()
    WHERE id = doc_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- PHASE 9: RESTORE COMPLEX VIEWS
-- =============================================================================

CREATE VIEW document_processing_stats AS
SELECT 
    status,
    COUNT(*) as count,
    AVG(progress_percentage) as avg_progress,
    COUNT(*) FILTER (WHERE error_message IS NOT NULL) as error_count
FROM documents 
GROUP BY status;

CREATE VIEW failed_documents AS
SELECT 
    id, original_filename, status, error_message, 
    created_at, updated_at
FROM documents 
WHERE status = 'failed' OR error_message IS NOT NULL;

-- =============================================================================
-- PHASE 10: RESTORE TRIGGERS
-- =============================================================================

CREATE TRIGGER update_feature_flags_updated_at 
    BEFORE UPDATE ON feature_flags 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_policy_records_updated_at 
    BEFORE UPDATE ON policy_records 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- PHASE 11: RESTORE RLS POLICIES
-- =============================================================================

-- Enable RLS on restored tables
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flag_evaluations ENABLE ROW LEVEL SECURITY;

-- Restore RLS policies
CREATE POLICY "users_own_processing_jobs" ON processing_jobs
    FOR ALL USING (
        document_id IN (
            SELECT id FROM documents WHERE user_id = get_current_user_id()
        ) OR is_admin()
    );

-- Update vector table RLS policy
DROP POLICY IF EXISTS "users_own_document_vectors" ON user_document_vectors;
CREATE POLICY "users_own_document_vectors" ON user_document_vectors
    FOR ALL USING (user_id = get_current_user_id() OR is_admin());

-- =============================================================================
-- PHASE 12: CLEAN UP NEW FUNCTIONS (KEEP POLICY_BASICS FUNCTIONS)
-- =============================================================================

-- Note: We keep the new policy_basics functions as they may be useful
-- and the policy_basics column is preserved for potential future use

-- Remove audit logging function if desired
-- DROP FUNCTION IF EXISTS log_user_action(UUID, TEXT, TEXT, TEXT, JSONB, INET, TEXT);

-- =============================================================================
-- PHASE 13: RESTORE COMPLEX INDEXES
-- =============================================================================

-- Restore processing indexes
CREATE INDEX idx_documents_llama_parse_job ON documents(llama_parse_job_id) WHERE llama_parse_job_id IS NOT NULL;
CREATE INDEX idx_documents_processing_status ON documents(status, processing_started_at) WHERE status IN ('processing', 'chunking', 'embedding');

-- Restore regulatory document indexes
CREATE INDEX idx_regulatory_docs_program ON regulatory_documents USING gin(program);
CREATE INDEX idx_regulatory_docs_tags ON regulatory_documents USING gin(tags);
CREATE INDEX idx_regulatory_docs_source_last_checked ON regulatory_documents(source_last_checked);
CREATE INDEX idx_regulatory_docs_search_metadata ON regulatory_documents USING gin(search_metadata);

-- =============================================================================
-- WARNING AND FINAL NOTES
-- =============================================================================

-- Note: The policy_basics column and related indexes are preserved
-- This means you have access to both the old complex schema AND the new policy_basics functionality
-- You may want to drop the policy_basics column if you're fully reverting:
-- ALTER TABLE documents DROP COLUMN IF EXISTS policy_basics;
-- DROP INDEX IF EXISTS idx_documents_policy_basics_gin;
-- DROP INDEX IF EXISTS idx_documents_policy_deductible;
-- DROP INDEX IF EXISTS idx_documents_policy_copay;
-- DROP INDEX IF EXISTS idx_documents_policy_annual_max;

-- The audit_logs table is also preserved as it provides value for HIPAA compliance
-- You may want to keep this table even in the rollback scenario

COMMIT;

-- =============================================================================
-- POST-ROLLBACK VERIFICATION
-- =============================================================================

-- Verify table count is restored:
-- SELECT COUNT(*) as table_count FROM information_schema.tables 
-- WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- Should show ~22 tables again 