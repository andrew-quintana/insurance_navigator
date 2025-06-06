-- =============================================================================
-- Migration: Add V2 Features to Existing Schema
-- Version: 011
-- Description: Add V2 document tracking, feature flags, and monitoring to existing system
-- =============================================================================

BEGIN;

-- =============================================================================
-- V2 DOCUMENT MANAGEMENT SYSTEM
-- =============================================================================

-- Documents table - V2 central document tracking
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- File Information
    original_filename TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    content_type TEXT NOT NULL,
    file_hash TEXT UNIQUE NOT NULL, -- SHA256 hash to prevent duplicates
    storage_path TEXT, -- Supabase Storage path
    
    -- Processing Status (V2 Feature)
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'uploading', 'processing', 'chunking', 
        'embedding', 'completed', 'failed', 'cancelled'
    )),
    
    -- Progress Tracking (V2 Feature)
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    total_chunks INTEGER,
    processed_chunks INTEGER DEFAULT 0,
    failed_chunks INTEGER DEFAULT 0,
    
    -- LlamaParse Integration (V2 Feature)
    llama_parse_job_id TEXT,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    error_message TEXT,
    error_details JSONB,
    
    -- Document Metadata
    extracted_text_length INTEGER,
    document_type TEXT, -- 'policy', 'medical_record', 'claim', etc.
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Encryption
    encryption_key_id UUID REFERENCES encryption_keys(id),
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- V2 Constraints
    CONSTRAINT chk_progress_consistency CHECK (
        (status = 'completed' AND progress_percentage = 100) OR (status != 'completed')
    ),
    CONSTRAINT chk_chunk_consistency CHECK (
        (total_chunks IS NULL) OR (processed_chunks + failed_chunks <= total_chunks)
    ),
    CONSTRAINT chk_file_size_limit CHECK (file_size <= 52428800) -- 50MB limit
);

-- Document indexes
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_file_hash ON documents(file_hash);
CREATE INDEX idx_documents_llama_parse_job ON documents(llama_parse_job_id) WHERE llama_parse_job_id IS NOT NULL;
CREATE INDEX idx_documents_processing_status ON documents(status, processing_started_at) WHERE status IN ('processing', 'chunking', 'embedding');
CREATE INDEX idx_documents_user_status ON documents(user_id, status, created_at DESC);

-- Add foreign key to user_document_vectors for proper relationship
ALTER TABLE user_document_vectors 
ADD COLUMN document_record_id UUID REFERENCES documents(id) ON DELETE CASCADE;

CREATE INDEX idx_user_document_vectors_document_record ON user_document_vectors(document_record_id);

-- =============================================================================
-- V2 FEATURE FLAGS SYSTEM
-- =============================================================================

CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_enabled BOOLEAN DEFAULT false,
    rollout_percentage INTEGER DEFAULT 0 CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100),
    enabled_user_ids UUID[] DEFAULT '{}',
    enabled_user_emails TEXT[] DEFAULT '{}',
    disabled_user_ids UUID[] DEFAULT '{}',
    environment_restrictions TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_feature_flags_name ON feature_flags(flag_name);
CREATE INDEX idx_feature_flags_enabled ON feature_flags(is_enabled);

CREATE TABLE feature_flag_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_name TEXT NOT NULL,
    user_id UUID,
    user_email TEXT,
    evaluation_result BOOLEAN NOT NULL,
    evaluation_reason TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feature_flag_evaluations_flag ON feature_flag_evaluations(flag_name);
CREATE INDEX idx_feature_flag_evaluations_user ON feature_flag_evaluations(user_id);
CREATE INDEX idx_feature_flag_evaluations_time ON feature_flag_evaluations(evaluated_at);

-- =============================================================================
-- V2 MONITORING VIEWS
-- =============================================================================

-- Document processing analytics
CREATE VIEW document_processing_stats AS
SELECT 
    status,
    COUNT(*) as count,
    AVG(progress_percentage) as avg_progress,
    AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) as avg_processing_time_seconds,
    COUNT(*) FILTER (WHERE error_message IS NOT NULL) as error_count
FROM documents 
GROUP BY status;

-- Failed documents requiring attention
CREATE VIEW failed_documents AS
SELECT 
    d.id, d.user_id, u.email as user_email, d.original_filename,
    d.file_size, d.status, d.error_message, d.error_details,
    d.created_at, d.updated_at,
    EXTRACT(EPOCH FROM (NOW() - d.created_at)) as age_seconds
FROM documents d
JOIN users u ON u.id = d.user_id
WHERE d.status = 'failed'
ORDER BY d.created_at DESC;

-- Documents stuck in processing
CREATE VIEW stuck_documents AS  
SELECT 
    d.id, d.user_id, u.email as user_email, d.original_filename,
    d.status, d.progress_percentage, d.processing_started_at,
    EXTRACT(EPOCH FROM (NOW() - d.processing_started_at)) as stuck_duration_seconds
FROM documents d
JOIN users u ON u.id = d.user_id
WHERE d.status IN ('processing', 'chunking', 'embedding')
  AND d.processing_started_at < NOW() - INTERVAL '30 minutes'
ORDER BY d.processing_started_at ASC;

-- User upload statistics
CREATE VIEW user_upload_stats AS
SELECT 
    u.id as user_id, u.email,
    COUNT(d.id) as total_uploads,
    COUNT(*) FILTER (WHERE d.status = 'completed') as successful_uploads,
    COUNT(*) FILTER (WHERE d.status = 'failed') as failed_uploads,
    SUM(d.file_size) as total_bytes_uploaded,
    MAX(d.created_at) as last_upload_at,
    AVG(d.progress_percentage) as avg_progress
FROM users u
LEFT JOIN documents d ON d.user_id = u.id
GROUP BY u.id, u.email;

-- =============================================================================
-- V2 HELPER FUNCTIONS
-- =============================================================================

-- Update document progress (V2 function)
CREATE OR REPLACE FUNCTION update_document_progress(
    doc_id UUID,
    new_status TEXT DEFAULT NULL,
    progress_pct INTEGER DEFAULT NULL,
    chunks_processed INTEGER DEFAULT NULL,
    chunks_failed INTEGER DEFAULT NULL,
    error_msg TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE documents 
    SET 
        status = COALESCE(new_status, status),
        progress_percentage = COALESCE(progress_pct, progress_percentage),
        processed_chunks = COALESCE(chunks_processed, processed_chunks),
        failed_chunks = COALESCE(chunks_failed, failed_chunks),
        error_message = COALESCE(error_msg, error_message),
        updated_at = NOW(),
        processing_completed_at = CASE 
            WHEN new_status = 'completed' THEN NOW()
            ELSE processing_completed_at
        END
    WHERE id = doc_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Evaluate feature flags (V2 function)
CREATE OR REPLACE FUNCTION evaluate_feature_flag(
    flag_name_param TEXT,
    user_id_param UUID DEFAULT NULL,
    user_email_param TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    flag_record feature_flags%ROWTYPE;
    user_hash INTEGER;
    evaluation_result BOOLEAN := false;
    reason TEXT := 'disabled';
BEGIN
    SELECT * INTO flag_record FROM feature_flags WHERE flag_name = flag_name_param;
    
    IF NOT FOUND OR NOT flag_record.is_enabled THEN
        reason := 'disabled';
        evaluation_result := false;
    ELSE
        IF user_id_param = ANY(flag_record.enabled_user_ids) OR 
           user_email_param = ANY(flag_record.enabled_user_emails) THEN
            reason := 'user_enabled';
            evaluation_result := true;
        ELSIF user_id_param = ANY(flag_record.disabled_user_ids) THEN
            reason := 'user_disabled';  
            evaluation_result := false;
        ELSE
            user_hash := hashtext(COALESCE(user_id_param::text, user_email_param, ''));
            IF (user_hash % 100) < flag_record.rollout_percentage THEN
                reason := 'percentage_enabled';
                evaluation_result := true;
            ELSE
                reason := 'percentage_disabled';
                evaluation_result := false;
            END IF;
        END IF;
    END IF;
    
    INSERT INTO feature_flag_evaluations (
        flag_name, user_id, user_email, evaluation_result, evaluation_reason
    ) VALUES (
        flag_name_param, user_id_param, user_email_param, evaluation_result, reason
    );
    
    RETURN evaluation_result;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- V2 TRIGGERS
-- =============================================================================

-- Apply timestamp triggers to new tables
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feature_flags_updated_at
    BEFORE UPDATE ON feature_flags
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- V2 ROW LEVEL SECURITY
-- =============================================================================

-- Enable RLS on new tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flag_evaluations ENABLE ROW LEVEL SECURITY;

-- Documents RLS Policies
CREATE POLICY "documents_user_access" ON documents
    FOR ALL USING (
        user_id = get_current_user_id() OR 
        user_id = auth.uid() OR
        is_admin()
    );

-- Feature Flags RLS Policies  
CREATE POLICY "feature_flags_admin_only" ON feature_flags
    FOR ALL USING (is_admin());

-- Feature flag evaluations - users can see their own, admins see all
CREATE POLICY "feature_flag_evaluations_access" ON feature_flag_evaluations
    FOR ALL USING (
        user_id = get_current_user_id() OR 
        user_id = auth.uid() OR 
        is_admin()
    );

-- =============================================================================
-- V2 SEED DATA
-- =============================================================================

-- Insert initial feature flags for V2 system
INSERT INTO feature_flags (flag_name, description, is_enabled, rollout_percentage) VALUES
('supabase_v2_upload', 'Enable Supabase V2 upload system with Edge Functions', false, 0),
('realtime_progress', 'Enable real-time progress updates via Supabase Realtime', false, 0),
('llama_parse_integration', 'Enable LlamaParse for advanced document processing', false, 0),
('enhanced_error_handling', 'Enable enhanced error handling and retry logic', true, 100),
('vector_encryption', 'Enable encryption for vector storage', true, 100);

-- =============================================================================
-- MIGRATION COMPLETION
-- =============================================================================

-- Record this migration in system metadata
INSERT INTO system_metadata (key, value) VALUES (
    'v2_features_added',
    jsonb_build_object(
        'migration_version', '011',
        'completed_at', NOW(),
        'description', 'Added V2 document tracking, feature flags, and monitoring to existing schema',
        'tables_added', ARRAY['documents', 'feature_flags', 'feature_flag_evaluations'],
        'views_added', ARRAY['document_processing_stats', 'failed_documents', 'stuck_documents', 'user_upload_stats'],
        'functions_added', ARRAY['update_document_progress', 'evaluate_feature_flag'],
        'rls_policies_added', 3
    )
) ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = NOW();

COMMIT;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

/*
Verify V2 features added successfully:

-- 1. Check new tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN ('documents', 'feature_flags', 'feature_flag_evaluations');

-- 2. Verify views created
SELECT viewname FROM pg_views 
WHERE viewname IN ('document_processing_stats', 'failed_documents', 'stuck_documents', 'user_upload_stats');

-- 3. Test feature flag evaluation
SELECT evaluate_feature_flag('enhanced_error_handling', null, 'test@example.com') as should_be_true;

-- 4. Check initial feature flags
SELECT flag_name, is_enabled, rollout_percentage FROM feature_flags ORDER BY flag_name;

-- 5. Verify document_record_id column added
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'user_document_vectors' AND column_name = 'document_record_id';
*/ 