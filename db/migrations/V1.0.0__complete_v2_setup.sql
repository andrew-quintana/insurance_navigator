-- =============================================================================
-- Migration: Complete Supabase V2 Upload System Setup
-- Version: V1.0.0
-- Description: Comprehensive migration for fresh V2 deployment
-- Author: System Agent
-- Date: Current
-- =============================================================================

BEGIN;

-- =============================================================================
-- SECTION 1: DOCUMENTS TABLE - Document Metadata & Processing Status
-- =============================================================================

-- Create documents table for tracking uploaded files and processing status
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- File Information
    original_filename TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    content_type TEXT NOT NULL,
    file_hash SHA256 UNIQUE NOT NULL, -- Prevent duplicate uploads
    storage_path TEXT, -- Supabase Storage path
    
    -- Processing Status
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending',     -- Initial upload state
        'uploading',   -- File being uploaded to storage
        'processing',  -- Being processed by LlamaParse
        'chunking',    -- Text extraction and chunking in progress
        'embedding',   -- Vector embedding generation
        'completed',   -- Successfully processed and stored
        'failed',      -- Processing failed
        'cancelled'    -- User or system cancelled
    )),
    
    -- Progress Tracking
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    total_chunks INTEGER,
    processed_chunks INTEGER DEFAULT 0,
    failed_chunks INTEGER DEFAULT 0,
    
    -- Processing Metadata
    llama_parse_job_id TEXT, -- LlamaParse job tracking
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
    
    -- Constraints
    CONSTRAINT chk_progress_consistency CHECK (
        (status = 'completed' AND progress_percentage = 100) OR
        (status != 'completed')
    ),
    CONSTRAINT chk_chunk_consistency CHECK (
        (total_chunks IS NULL) OR 
        (processed_chunks + failed_chunks <= total_chunks)
    )
);

-- Create indexes for documents table
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_file_hash ON documents(file_hash);
CREATE INDEX idx_documents_llama_parse_job ON documents(llama_parse_job_id) WHERE llama_parse_job_id IS NOT NULL;

-- Add foreign key to user_document_vectors for proper relationship
ALTER TABLE user_document_vectors 
ADD COLUMN document_record_id UUID REFERENCES documents(id) ON DELETE CASCADE;

CREATE INDEX idx_user_document_vectors_document_record ON user_document_vectors(document_record_id);

-- =============================================================================
-- SECTION 2: FEATURE FLAGS SYSTEM - Progressive Rollout Control
-- =============================================================================

-- Feature flags table for managing V2 rollout
CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_name TEXT NOT NULL UNIQUE,
    description TEXT,
    
    -- Control Settings
    is_enabled BOOLEAN DEFAULT false,
    rollout_percentage INTEGER DEFAULT 0 CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100),
    
    -- Targeting
    enabled_user_ids UUID[] DEFAULT '{}', -- Specific users
    enabled_user_emails TEXT[] DEFAULT '{}', -- Specific emails
    disabled_user_ids UUID[] DEFAULT '{}', -- Excluded users
    
    -- Environment Controls
    environment_restrictions TEXT[] DEFAULT '{}', -- 'development', 'staging', 'production'
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Create indexes for feature flags
CREATE INDEX idx_feature_flags_name ON feature_flags(flag_name);
CREATE INDEX idx_feature_flags_enabled ON feature_flags(is_enabled);

-- Feature flag evaluations log (for monitoring)
CREATE TABLE feature_flag_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_name TEXT NOT NULL,
    user_id UUID,
    user_email TEXT,
    evaluation_result BOOLEAN NOT NULL,
    evaluation_reason TEXT, -- 'percentage', 'user_list', 'disabled', etc.
    metadata JSONB DEFAULT '{}'::jsonb,
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feature_flag_evaluations_flag ON feature_flag_evaluations(flag_name);
CREATE INDEX idx_feature_flag_evaluations_user ON feature_flag_evaluations(user_id);
CREATE INDEX idx_feature_flag_evaluations_time ON feature_flag_evaluations(evaluated_at);

-- =============================================================================
-- SECTION 3: PROCESSING STATUS VIEWS - Monitoring & Analytics
-- =============================================================================

-- View for document processing analytics
CREATE VIEW document_processing_stats AS
SELECT 
    status,
    COUNT(*) as count,
    AVG(progress_percentage) as avg_progress,
    AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) as avg_processing_time_seconds,
    COUNT(*) FILTER (WHERE error_message IS NOT NULL) as error_count
FROM documents 
GROUP BY status;

-- View for failed documents requiring attention  
CREATE VIEW failed_documents AS
SELECT 
    d.id,
    d.user_id,
    u.email as user_email,
    d.original_filename,
    d.file_size,
    d.status,
    d.error_message,
    d.error_details,
    d.created_at,
    d.updated_at,
    EXTRACT(EPOCH FROM (NOW() - d.created_at)) as age_seconds
FROM documents d
JOIN users u ON u.id = d.user_id
WHERE d.status = 'failed'
ORDER BY d.created_at DESC;

-- View for documents stuck in processing
CREATE VIEW stuck_documents AS  
SELECT 
    d.id,
    d.user_id,
    u.email as user_email,
    d.original_filename,
    d.status,
    d.progress_percentage,
    d.processing_started_at,
    EXTRACT(EPOCH FROM (NOW() - d.processing_started_at)) as stuck_duration_seconds
FROM documents d
JOIN users u ON u.id = d.user_id
WHERE d.status IN ('processing', 'chunking', 'embedding')
  AND d.processing_started_at < NOW() - INTERVAL '30 minutes'
ORDER BY d.processing_started_at ASC;

-- View for user upload statistics
CREATE VIEW user_upload_stats AS
SELECT 
    u.id as user_id,
    u.email,
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
-- SECTION 4: RLS POLICIES - Complete Security Layer
-- =============================================================================

-- Enable RLS on new tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flag_evaluations ENABLE ROW LEVEL SECURITY;

-- Documents RLS Policies
CREATE POLICY "documents_user_access" ON documents
    FOR ALL USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM user_roles ur JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid() AND r.name = 'admin'
        )
    );

-- Feature Flags RLS Policies  
CREATE POLICY "feature_flags_admin_only" ON feature_flags
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid() AND r.name = 'admin'
        )
    );

-- Feature flag evaluations - users can see their own, admins see all
CREATE POLICY "feature_flag_evaluations_access" ON feature_flag_evaluations
    FOR ALL USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM user_roles ur JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid() AND r.name = 'admin'
        )
    );

-- =============================================================================
-- SECTION 5: STORAGE BUCKET SETUP - File Storage Configuration  
-- =============================================================================

-- Note: Storage buckets are managed via Supabase Dashboard or API
-- This section documents the required bucket configuration

/*
Required Storage Bucket: 'documents'
Configuration:
- Public: false (private bucket)
- File size limit: 50MB
- Allowed file types: PDF, DOC, DOCX, TXT
- RLS Policies:
  - Users can upload to their own folder: {user_id}/*
  - Users can read their own files
  - Admins have full access

Bucket RLS Policies (to be created via Supabase Dashboard):

1. Upload Policy:
   CREATE POLICY "Users can upload own files" ON storage.objects
   FOR INSERT WITH CHECK (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);

2. Select Policy: 
   CREATE POLICY "Users can view own files" ON storage.objects
   FOR SELECT USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);

3. Update Policy:
   CREATE POLICY "Users can update own files" ON storage.objects  
   FOR UPDATE USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);

4. Delete Policy:
   CREATE POLICY "Users can delete own files" ON storage.objects
   FOR DELETE USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);
*/

-- =============================================================================
-- SECTION 6: HELPER FUNCTIONS - V2 System Utilities
-- =============================================================================

-- Function to update document progress
CREATE OR REPLACE FUNCTION update_document_progress(
    doc_id UUID,
    new_status TEXT DEFAULT NULL,
    progress_pct INTEGER DEFAULT NULL,
    chunks_processed INTEGER DEFAULT NULL,
    chunks_failed INTEGER DEFAULT NULL,
    error_msg TEXT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
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
$$;

-- Function to evaluate feature flags for a user
CREATE OR REPLACE FUNCTION evaluate_feature_flag(
    flag_name_param TEXT,
    user_id_param UUID DEFAULT NULL,
    user_email_param TEXT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    flag_record feature_flags%ROWTYPE;
    user_hash INTEGER;
    evaluation_result BOOLEAN := false;
    reason TEXT := 'disabled';
BEGIN
    -- Get flag configuration
    SELECT * INTO flag_record FROM feature_flags WHERE flag_name = flag_name_param;
    
    -- If flag doesn't exist or is disabled, return false
    IF NOT FOUND OR NOT flag_record.is_enabled THEN
        reason := 'disabled';
        evaluation_result := false;
    ELSE
        -- Check if user is specifically enabled
        IF user_id_param = ANY(flag_record.enabled_user_ids) OR 
           user_email_param = ANY(flag_record.enabled_user_emails) THEN
            reason := 'user_enabled';
            evaluation_result := true;
        -- Check if user is specifically disabled
        ELSIF user_id_param = ANY(flag_record.disabled_user_ids) THEN
            reason := 'user_disabled';  
            evaluation_result := false;
        -- Check percentage rollout
        ELSE
            -- Use deterministic hash of user_id for consistent percentage evaluation
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
    
    -- Log the evaluation for monitoring
    INSERT INTO feature_flag_evaluations (
        flag_name, user_id, user_email, evaluation_result, evaluation_reason
    ) VALUES (
        flag_name_param, user_id_param, user_email_param, evaluation_result, reason
    );
    
    RETURN evaluation_result;
END;
$$;

-- =============================================================================
-- SECTION 7: SEED DATA - Initial Feature Flags & Configuration
-- =============================================================================

-- Insert initial feature flags for V2 system
INSERT INTO feature_flags (flag_name, description, is_enabled, rollout_percentage) VALUES
('supabase_v2_upload', 'Enable Supabase V2 upload system with Edge Functions', false, 0),
('realtime_progress', 'Enable real-time progress updates via Supabase Realtime', false, 0),
('llama_parse_integration', 'Enable LlamaParse for advanced document processing', false, 0),
('enhanced_error_handling', 'Enable enhanced error handling and retry logic', true, 100),
('vector_encryption', 'Enable encryption for vector storage', true, 100);

-- =============================================================================
-- SECTION 8: CONSTRAINTS & OPTIMIZATIONS - Performance & Data Integrity
-- =============================================================================

-- Add check constraint for file size (50MB limit)
ALTER TABLE documents 
ADD CONSTRAINT chk_file_size_limit 
CHECK (file_size <= 52428800); -- 50MB in bytes

-- Add partial index for active processing documents
CREATE INDEX idx_documents_processing_status 
ON documents(status, processing_started_at) 
WHERE status IN ('processing', 'chunking', 'embedding');

-- Add index for user document lookups
CREATE INDEX idx_documents_user_status 
ON documents(user_id, status, created_at DESC);

-- =============================================================================
-- SECTION 9: TRIGGERS - Automated Updates & Consistency
-- =============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to documents table
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to feature_flags table  
CREATE TRIGGER update_feature_flags_updated_at
    BEFORE UPDATE ON feature_flags
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- SECTION 10: COMMENTS & DOCUMENTATION - Schema Documentation
-- =============================================================================

-- Table comments
COMMENT ON TABLE documents IS 'Central table for tracking uploaded documents and their processing status in the V2 upload system';
COMMENT ON TABLE feature_flags IS 'Feature flag system for controlling V2 feature rollout and A/B testing';
COMMENT ON TABLE feature_flag_evaluations IS 'Audit log of feature flag evaluations for monitoring and analytics';

-- Column comments for documents table
COMMENT ON COLUMN documents.file_hash IS 'SHA256 hash of file content to prevent duplicate uploads';
COMMENT ON COLUMN documents.storage_path IS 'Path to file in Supabase Storage bucket';
COMMENT ON COLUMN documents.llama_parse_job_id IS 'Job ID from LlamaParse API for tracking processing status';
COMMENT ON COLUMN documents.progress_percentage IS 'Processing progress from 0-100%';

-- View comments
COMMENT ON VIEW document_processing_stats IS 'Real-time analytics for document processing performance';
COMMENT ON VIEW failed_documents IS 'Documents that failed processing and need attention';
COMMENT ON VIEW stuck_documents IS 'Documents stuck in processing state beyond normal timeframes';
COMMENT ON VIEW user_upload_stats IS 'Per-user upload statistics and success rates';

-- Function comments
COMMENT ON FUNCTION update_document_progress IS 'Helper function to safely update document processing progress';
COMMENT ON FUNCTION evaluate_feature_flag IS 'Evaluate if a feature flag is enabled for a specific user';

-- =============================================================================
-- MIGRATION COMPLETION LOG
-- =============================================================================

-- Record this migration in system metadata
INSERT INTO system_metadata (key, value, metadata) VALUES (
    'v2_migration_completed',
    'true',
    jsonb_build_object(
        'migration_version', 'V1.0.0',
        'completed_at', NOW(),
        'description', 'Complete Supabase V2 Upload System Setup',
        'tables_created', ARRAY['documents', 'feature_flags', 'feature_flag_evaluations'],
        'views_created', ARRAY['document_processing_stats', 'failed_documents', 'stuck_documents', 'user_upload_stats'],
        'functions_created', ARRAY['update_document_progress', 'evaluate_feature_flag'],
        'rls_policies_added', 3,
        'indexes_added', 12,
        'triggers_added', 2
    )
);

COMMIT;

-- =============================================================================
-- POST-MIGRATION VERIFICATION QUERIES
-- =============================================================================

/*
Run these queries after migration to verify successful deployment:

-- 1. Verify all tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN ('documents', 'feature_flags', 'feature_flag_evaluations');

-- 2. Verify RLS is enabled  
SELECT tablename, rowsecurity FROM pg_tables 
WHERE tablename IN ('documents', 'feature_flags', 'feature_flag_evaluations');

-- 3. Verify views are created
SELECT viewname FROM pg_views 
WHERE viewname IN ('document_processing_stats', 'failed_documents', 'stuck_documents', 'user_upload_stats');

-- 4. Verify functions exist
SELECT proname FROM pg_proc 
WHERE proname IN ('update_document_progress', 'evaluate_feature_flag');

-- 5. Test feature flag evaluation
SELECT evaluate_feature_flag('supabase_v2_upload', auth.uid(), 'test@example.com');

-- 6. Check initial feature flags
SELECT flag_name, is_enabled, rollout_percentage FROM feature_flags;
*/ 