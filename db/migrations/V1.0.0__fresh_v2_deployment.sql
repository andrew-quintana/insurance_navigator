-- =============================================================================
-- FRESH V2 DEPLOYMENT - COMPLETE SCHEMA SETUP
-- Version: V1.0.0
-- Description: Complete database schema for fresh Supabase V2 Upload System
-- Consolidates: All previous migrations + V2 features
-- =============================================================================

BEGIN;

-- =============================================================================
-- EXTENSIONS & CORE SETUP
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- CORE AUTHENTICATION & USER MANAGEMENT
-- =============================================================================

-- Users table with complete authentication support
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_users_email ON users(email);

-- Roles table for authorization
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User-role assignments (many-to-many)
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id),
    role_id UUID NOT NULL REFERENCES roles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);

-- =============================================================================
-- ENCRYPTION MANAGEMENT
-- =============================================================================

CREATE TABLE encryption_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_version INTEGER NOT NULL DEFAULT 1,
    key_status TEXT NOT NULL CHECK (key_status IN ('active', 'rotated', 'retired')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rotated_at TIMESTAMPTZ,
    retired_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =============================================================================
-- DOCUMENT MANAGEMENT (V2 Core)
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

-- =============================================================================
-- VECTOR STORAGE SYSTEM
-- =============================================================================

-- User document vectors with encryption support
CREATE TABLE user_document_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    document_id UUID NOT NULL, -- Legacy: references documents.id conceptually
    document_record_id UUID REFERENCES documents(id) ON DELETE CASCADE, -- V2: proper FK
    chunk_index INTEGER NOT NULL,
    content_embedding vector(1536) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    -- Encryption columns (from migration 010)
    encrypted_chunk_text TEXT,
    encrypted_chunk_metadata TEXT,
    encryption_key_id UUID REFERENCES encryption_keys(id),
    
    -- V2 Constraints: require encryption
    CONSTRAINT chk_chunk_encryption CHECK (
        (encrypted_chunk_text IS NOT NULL AND encrypted_chunk_metadata IS NOT NULL AND encryption_key_id IS NOT NULL)
    )
);

-- Vector indexes
CREATE INDEX idx_user_document_vectors_user_id ON user_document_vectors(user_id);
CREATE INDEX idx_user_document_vectors_document_id ON user_document_vectors(document_id);
CREATE INDEX idx_user_document_vectors_document_record ON user_document_vectors(document_record_id);
CREATE INDEX idx_user_document_vectors_active ON user_document_vectors(is_active) WHERE is_active = true;
CREATE INDEX idx_user_document_vectors_embedding ON user_document_vectors USING ivfflat (content_embedding vector_cosine_ops);
CREATE INDEX idx_user_document_vectors_encryption_key ON user_document_vectors(encryption_key_id);

-- =============================================================================
-- POLICY MANAGEMENT (Legacy Support)
-- =============================================================================

-- Policy records table (maintained for existing functionality)
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

-- User-policy relationships
CREATE TABLE user_policy_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    policy_id UUID NOT NULL REFERENCES policy_records(policy_id),
    role TEXT NOT NULL CHECK (role IN ('subscriber', 'dependent', 'spouse', 'employee', 'guardian', 'representative', 'self')),
    relationship_verified BOOLEAN DEFAULT false,
    linked_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_user_policy_links_user ON user_policy_links(user_id);
CREATE INDEX idx_user_policy_links_policy ON user_policy_links(policy_id);

-- Policy content vectors (for policy documents)
CREATE TABLE policy_content_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES policy_records(policy_id),
    user_id UUID, -- Legacy: will be removed after migration
    chunk_index INTEGER NOT NULL,
    content_embedding vector(1536) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    -- Encryption columns
    encrypted_content_text TEXT,
    encrypted_policy_metadata TEXT,
    encrypted_document_metadata TEXT,
    encryption_key_id UUID REFERENCES encryption_keys(id)
);

CREATE INDEX idx_policy_content_vectors_policy ON policy_content_vectors(policy_id);
CREATE INDEX idx_policy_content_vectors_user ON policy_content_vectors(user_id);
CREATE INDEX idx_policy_content_vectors_embedding ON policy_content_vectors USING ivfflat (content_embedding vector_cosine_ops);

-- =============================================================================
-- ACCESS CONTROL & AUDIT
-- =============================================================================

CREATE TABLE policy_access_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID REFERENCES roles(id),
    policy_type TEXT NOT NULL,
    action TEXT NOT NULL,
    conditions JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE policy_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID, -- Flexible reference (no FK due to multiple table sources)
    user_id UUID NOT NULL,
    action TEXT NOT NULL,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('user', 'agent')),
    actor_id UUID NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    purpose TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_policy_access_logs_policy ON policy_access_logs(policy_id);
CREATE INDEX idx_policy_access_logs_user ON policy_access_logs(user_id);

CREATE TABLE agent_policy_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id TEXT NOT NULL,
    session_id UUID NOT NULL,
    policy_id UUID, -- Flexible reference
    user_id UUID NOT NULL,
    context_type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    encrypted_context JSONB NOT NULL,
    encryption_key_id UUID REFERENCES encryption_keys(id),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_agent_policy_context_session ON agent_policy_context(session_id);

-- =============================================================================
-- CONVERSATION SYSTEM
-- =============================================================================

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE agent_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    state_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE workflow_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    workflow_name TEXT NOT NULL,
    current_step TEXT NOT NULL,
    state_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- REGULATORY DOCUMENTS SYSTEM
-- =============================================================================

CREATE TABLE regulatory_documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_document_path TEXT NOT NULL,
    title TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    program TEXT[] NOT NULL,
    document_type TEXT NOT NULL,
    effective_date DATE,
    expiration_date DATE,
    structured_contents JSONB,
    summary JSONB,
    source_url TEXT,
    encrypted_restrictions JSONB,
    encryption_key_id UUID REFERENCES encryption_keys(id),
    tags TEXT[],
    
    -- Enhanced search fields (from migration 004)
    source_last_checked TIMESTAMPTZ,
    content_hash TEXT,
    extraction_method TEXT DEFAULT 'manual',
    priority_score FLOAT,
    search_metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    version INT DEFAULT 1
);

-- Regulatory document indexes
CREATE INDEX idx_regulatory_docs_document_type ON regulatory_documents(document_type);
CREATE INDEX idx_regulatory_docs_effective_date ON regulatory_documents(effective_date);
CREATE INDEX idx_regulatory_docs_expiration_date ON regulatory_documents(expiration_date);
CREATE INDEX idx_regulatory_docs_jurisdiction ON regulatory_documents(jurisdiction);
CREATE INDEX idx_regulatory_docs_program ON regulatory_documents USING gin(program);
CREATE INDEX idx_regulatory_docs_tags ON regulatory_documents USING gin(tags);
CREATE INDEX idx_regulatory_docs_content_hash ON regulatory_documents(content_hash);
CREATE INDEX idx_regulatory_docs_source_last_checked ON regulatory_documents(source_last_checked);
CREATE INDEX idx_regulatory_docs_search_metadata ON regulatory_documents USING gin(search_metadata);

-- =============================================================================
-- FEATURE FLAGS SYSTEM (V2)
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
-- SYSTEM METADATA & MIGRATION TRACKING
-- =============================================================================

CREATE TABLE schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE system_metadata (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

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

-- Regulatory documents searchable view
CREATE VIEW regulatory_documents_searchable AS
SELECT 
    document_id, title, jurisdiction, program, document_type,
    source_url, tags, priority_score, content_hash, extraction_method,
    created_at, updated_at, source_last_checked,
    CASE 
        WHEN source_last_checked IS NULL THEN 'never_checked'
        WHEN source_last_checked < NOW() - INTERVAL '7 days' THEN 'needs_update'
        ELSE 'current'
    END as freshness_status
FROM regulatory_documents
WHERE source_url IS NOT NULL;

-- =============================================================================
-- SECURE HELPER FUNCTIONS
-- =============================================================================

-- Get current user ID securely
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS uuid AS $$
DECLARE
    session_user_id uuid;
    auth_user_id uuid;
BEGIN
    SET search_path = public, pg_catalog;
    
    BEGIN
        session_user_id := NULLIF(current_setting('rls.current_user_id', true), '')::uuid;
    EXCEPTION WHEN OTHERS THEN
        session_user_id := NULL;
    END;
    
    IF session_user_id IS NOT NULL THEN
        RETURN session_user_id;
    END IF;
    
    BEGIN
        auth_user_id := (SELECT auth.uid());
        IF auth_user_id IS NOT NULL THEN
            RETURN auth_user_id;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        NULL;
    END;
    
    RETURN NULL;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Check if current user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS boolean AS $$
DECLARE
    current_user_id uuid;
BEGIN
    SET search_path = public, pg_catalog;
    
    current_user_id := get_current_user_id();
    
    IF current_user_id IS NULL THEN
        RETURN false;
    END IF;
    
    RETURN EXISTS (
        SELECT 1 FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = current_user_id AND r.name = 'admin'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Check if user has specific role
CREATE OR REPLACE FUNCTION has_role(role_name text)
RETURNS boolean AS $$
DECLARE
    current_user_id uuid;
BEGIN
    SET search_path = public, pg_catalog;
    
    IF role_name IS NULL OR trim(role_name) = '' THEN
        RETURN false;
    END IF;
    
    current_user_id := get_current_user_id();
    
    IF current_user_id IS NULL THEN
        RETURN false;
    END IF;
    
    RETURN EXISTS (
        SELECT 1 FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = current_user_id AND r.name = trim(role_name)
    );
EXCEPTION WHEN OTHERS THEN
    RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Set user context for RLS
CREATE OR REPLACE FUNCTION set_current_user_context(user_uuid uuid)
RETURNS void AS $$
BEGIN
    SET search_path = public, pg_catalog;
    
    IF user_uuid IS NULL THEN
        RAISE EXCEPTION 'User UUID cannot be null';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM users WHERE id = user_uuid) THEN
        RAISE EXCEPTION 'User does not exist';
    END IF;
    
    PERFORM set_config('rls.current_user_id', user_uuid::text, false);
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Failed to set user context';
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

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
    SET search_path = public, pg_catalog;
    
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
    SET search_path = public, pg_catalog;
    
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

-- Regulatory document helper functions
CREATE OR REPLACE FUNCTION mark_document_for_refresh(doc_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    SET search_path = public, pg_catalog;
    
    UPDATE regulatory_documents 
    SET source_last_checked = NULL,
        search_metadata = search_metadata || '{"needs_refresh": true}'::jsonb
    WHERE document_id = doc_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

CREATE OR REPLACE FUNCTION get_stale_documents(check_interval INTERVAL DEFAULT '7 days')
RETURNS TABLE(
    document_id UUID,
    title TEXT,
    source_url TEXT,
    last_checked TIMESTAMPTZ
) AS $$
BEGIN
    SET search_path = public, pg_catalog;
    
    RETURN QUERY
    SELECT 
        rd.document_id,
        rd.title,
        rd.source_url,
        rd.source_last_checked
    FROM regulatory_documents rd
    WHERE rd.source_url IS NOT NULL
    AND (rd.source_last_checked IS NULL OR rd.source_last_checked < NOW() - check_interval)
    ORDER BY rd.source_last_checked ASC NULLS FIRST;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- Clear user context (for testing)
CREATE OR REPLACE FUNCTION clear_user_context()
RETURNS void AS $$
BEGIN
    SET search_path = public, pg_catalog;
    PERFORM set_config('rls.current_user_id', '', false);
EXCEPTION WHEN OTHERS THEN
    RETURN;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =============================================================================

-- Update timestamps automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to relevant tables
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_feature_flags_updated_at BEFORE UPDATE ON feature_flags FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_policy_records_updated_at BEFORE UPDATE ON policy_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_regulatory_documents_updated_at BEFORE UPDATE ON regulatory_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ROW LEVEL SECURITY SETUP
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE encryption_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_document_vectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_policy_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_content_vectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_access_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_access_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_policy_context ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flag_evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE schema_migrations ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "user_is_self" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "users_self_select" ON users FOR SELECT USING (id = get_current_user_id());
CREATE POLICY "users_self_update" ON users FOR UPDATE USING (id = get_current_user_id());
CREATE POLICY "users_admin_access" ON users FOR ALL USING (is_admin());
CREATE POLICY "users_insert_registration" ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "users_delete_admin_only" ON users FOR DELETE USING ((auth.jwt() ->> 'role'::text) = 'admin'::text);

-- Documents policies (V2)
CREATE POLICY "documents_user_access" ON documents FOR ALL USING (
    user_id = auth.uid() OR user_id = get_current_user_id() OR is_admin()
);

-- Vector policies
CREATE POLICY "user_document_vectors_proper_access" ON user_document_vectors FOR ALL USING (
    user_id = auth.uid() OR user_id = get_current_user_id() OR is_admin()
);

CREATE POLICY "policy_content_vectors_proper_access" ON policy_content_vectors FOR ALL USING (
    EXISTS (
        SELECT 1 FROM user_policy_links upl 
        WHERE upl.policy_id = policy_content_vectors.policy_id 
        AND (upl.user_id = auth.uid() OR upl.user_id = get_current_user_id())
        AND upl.relationship_verified = true
    ) OR is_admin()
);

-- Policy management
CREATE POLICY "policy_records_user_access" ON policy_records FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM user_policy_links
        WHERE user_policy_links.policy_id = policy_records.policy_id
        AND (user_policy_links.user_id = auth.uid() OR user_policy_links.user_id = get_current_user_id())
        AND user_policy_links.relationship_verified = true
    )
);
CREATE POLICY "policy_records_admin_access" ON policy_records FOR ALL USING (is_admin());

CREATE POLICY "user_policy_links_user_access" ON user_policy_links FOR ALL USING (
    user_id = auth.uid() OR user_id = get_current_user_id()
);
CREATE POLICY "user_policy_links_admin_access" ON user_policy_links FOR ALL USING (is_admin());
CREATE POLICY "user_policy_links_user_insert" ON user_policy_links FOR INSERT WITH CHECK (true);
CREATE POLICY "user_policy_links_user_update" ON user_policy_links FOR UPDATE USING (
    user_id = auth.uid() OR user_id = get_current_user_id()
);

-- Access control and audit
CREATE POLICY "policy_access_policies_admin_only" ON policy_access_policies FOR ALL USING (is_admin());

CREATE POLICY "policy_access_logs_user_access" ON policy_access_logs FOR SELECT USING (
    user_id = auth.uid() OR user_id = get_current_user_id()
);
CREATE POLICY "policy_access_logs_admin_access" ON policy_access_logs FOR ALL USING (is_admin());
CREATE POLICY "policy_access_logs_system_insert" ON policy_access_logs FOR INSERT WITH CHECK (true);

CREATE POLICY "agent_policy_context_user_access" ON agent_policy_context FOR SELECT USING (
    user_id = auth.uid() OR user_id = get_current_user_id()
);
CREATE POLICY "agent_policy_context_admin_access" ON agent_policy_context FOR ALL USING (is_admin());
CREATE POLICY "agent_policy_context_system_insert" ON agent_policy_context FOR INSERT WITH CHECK (true);

-- Conversation system
CREATE POLICY "conversations_user_access" ON conversations FOR ALL USING (
    user_id = auth.uid() OR user_id = get_current_user_id() OR is_admin()
);

CREATE POLICY "messages_user_access" ON conversation_messages FOR ALL USING (
    EXISTS (
        SELECT 1 FROM conversations c 
        WHERE c.id = conversation_messages.conversation_id 
        AND (c.user_id = auth.uid() OR c.user_id = get_current_user_id())
    ) OR is_admin()
);
CREATE POLICY "messages_admin_modify" ON conversation_messages FOR UPDATE USING ((auth.jwt() ->> 'role'::text) = 'admin'::text);
CREATE POLICY "messages_admin_delete" ON conversation_messages FOR DELETE USING ((auth.jwt() ->> 'role'::text) = 'admin'::text);

-- Role and permission policies
CREATE POLICY "roles_admin_access" ON roles FOR ALL USING (is_admin());
CREATE POLICY "roles_read_access" ON roles FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY "user_roles_self_access" ON user_roles FOR SELECT USING (
    user_id = auth.uid() OR user_id = get_current_user_id()
);
CREATE POLICY "user_roles_admin_access" ON user_roles FOR ALL USING (is_admin());

-- System tables
CREATE POLICY "encryption_keys_admin_only" ON encryption_keys FOR ALL USING (is_admin());
CREATE POLICY "system_metadata_admin_only" ON system_metadata FOR ALL USING (is_admin());
CREATE POLICY "select_schema_migrations" ON schema_migrations FOR SELECT USING (auth.uid() IS NOT NULL);

-- Regulatory documents
CREATE POLICY "regulatory_docs_read" ON regulatory_documents FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE (ur.user_id = (CURRENT_USER)::uuid OR ur.user_id = auth.uid() OR ur.user_id = get_current_user_id())
        AND (r.name = 'admin'::text OR r.name = 'regulatory_agent'::text)
    )
);
CREATE POLICY "regulatory_docs_write" ON regulatory_documents FOR INSERT WITH CHECK (true);
CREATE POLICY "regulatory_docs_update" ON regulatory_documents FOR UPDATE USING (
    EXISTS (
        SELECT 1 FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE (ur.user_id = (CURRENT_USER)::uuid OR ur.user_id = auth.uid() OR ur.user_id = get_current_user_id())
        AND r.name = 'admin'::text
    )
);

-- Feature flags (V2)
CREATE POLICY "feature_flags_admin_only" ON feature_flags FOR ALL USING (is_admin());

CREATE POLICY "feature_flag_evaluations_access" ON feature_flag_evaluations FOR ALL USING (
    user_id = auth.uid() OR user_id = get_current_user_id() OR is_admin()
);

-- =============================================================================
-- INITIAL SEED DATA
-- =============================================================================

-- Core roles
INSERT INTO roles (name, description) VALUES
    ('admin', 'System admin with full access'),
    ('agent', 'AI agent or assistant role'),
    ('user', 'Basic end-user role'),
    ('regulatory_agent', 'Role for accessing and managing regulatory documents')
ON CONFLICT (name) DO NOTHING;

-- Admin user
INSERT INTO users (
    id, email, hashed_password, full_name, is_active, metadata
) VALUES (
    '9d3a637a-58a4-4be0-bf0d-1d00260666d2',
    'admin@insurance-navigator.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyBAQ/fzJ8ZzuC',
    'System Administrator',
    true,
    jsonb_build_object('created_by', 'system', 'is_system_admin', true)
) ON CONFLICT (email) DO NOTHING;

-- Admin user roles
INSERT INTO user_roles (user_id, role_id)
SELECT '9d3a637a-58a4-4be0-bf0d-1d00260666d2', id 
FROM roles 
WHERE name IN ('admin', 'regulatory_agent')
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Initial encryption key
INSERT INTO encryption_keys (key_version, key_status, metadata)
VALUES (
    1, 'active',
    jsonb_build_object('created_by', 'system', 'purpose', 'initial_key', 'rotation_interval', '30d')
) ON CONFLICT DO NOTHING;

-- V2 Feature flags
INSERT INTO feature_flags (flag_name, description, is_enabled, rollout_percentage) VALUES
('supabase_v2_upload', 'Enable Supabase V2 upload system with Edge Functions', false, 0),
('realtime_progress', 'Enable real-time progress updates via Supabase Realtime', false, 0),
('llama_parse_integration', 'Enable LlamaParse for advanced document processing', false, 0),
('enhanced_error_handling', 'Enable enhanced error handling and retry logic', true, 100),
('vector_encryption', 'Enable encryption for vector storage', true, 100)
ON CONFLICT (flag_name) DO NOTHING;

-- System metadata
INSERT INTO system_metadata (key, value, metadata) VALUES (
    'fresh_v2_deployment_completed',
    'true'::jsonb,
    jsonb_build_object(
        'migration_version', 'V1.0.0',
        'deployment_type', 'fresh_v2',
        'completed_at', NOW(),
        'description', 'Complete fresh deployment with consolidated schema and V2 features',
        'features', ARRAY[
            'consolidated_schema', 'v2_document_tracking', 'feature_flags',
            'processing_status', 'monitoring_views', 'encryption_support',
            'vector_storage', 'llama_parse_integration', 'rls_security'
        ]
    )
) ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- Record migration as applied
INSERT INTO schema_migrations (version) VALUES ('V1.0.0') ON CONFLICT (version) DO NOTHING;

COMMIT;

-- =============================================================================
-- POST-DEPLOYMENT VERIFICATION QUERIES
-- =============================================================================

/*
Verify deployment with these queries:

-- 1. Check all tables exist
SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';

-- 2. Verify V2 features
SELECT flag_name, is_enabled FROM feature_flags ORDER BY flag_name;
SELECT COUNT(*) as documents_table_exists FROM information_schema.tables WHERE table_name = 'documents';

-- 3. Check RLS policies
SELECT COUNT(*) as policy_count FROM pg_policies WHERE schemaname = 'public';

-- 4. Verify functions
SELECT proname FROM pg_proc WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public') 
AND proname IN ('evaluate_feature_flag', 'update_document_progress', 'get_current_user_id', 'is_admin');

-- 5. Test feature flag evaluation
SELECT evaluate_feature_flag('enhanced_error_handling', null, 'test@example.com') as should_be_true;

-- 6. Check admin user exists
SELECT email, full_name FROM users WHERE email = 'admin@insurance-navigator.local';
*/ 