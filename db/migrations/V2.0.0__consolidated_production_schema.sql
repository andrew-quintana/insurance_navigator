-- =============================================================================
-- CONSOLIDATED PRODUCTION SCHEMA V2.0.0 - SUPERSEDED
-- Description: Complete database schema for Insurance Navigator
-- STATUS: SUPERSEDED BY V2.1.0 - This migration did not match actual Supabase setup
-- ISSUE: Missing vector extension and several tables were not deployed
-- USE: V2.1.0__fix_schema_to_match_current_supabase.sql instead
-- =============================================================================

-- =============================================================================
-- CONSOLIDATED PRODUCTION SCHEMA V2.0.0
-- Description: Complete database schema for Insurance Navigator
-- Replaces: All previous migrations - fresh production deployment
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
CREATE TABLE IF NOT EXISTS users (
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

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Roles table for authorization
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User-role assignments (many-to-many)
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID NOT NULL REFERENCES users(id),
    role_id UUID NOT NULL REFERENCES roles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);

-- =============================================================================
-- ENCRYPTION MANAGEMENT
-- =============================================================================

CREATE TABLE IF NOT EXISTS encryption_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_version INTEGER NOT NULL DEFAULT 1,
    key_status TEXT NOT NULL CHECK (key_status IN ('active', 'rotated', 'retired')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rotated_at TIMESTAMPTZ,
    retired_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =============================================================================
-- DOCUMENT MANAGEMENT SYSTEM
-- =============================================================================

-- Documents table - Central document tracking
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- File Information
    original_filename TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    content_type TEXT NOT NULL,
    file_hash TEXT UNIQUE NOT NULL, -- SHA256 hash to prevent duplicates
    storage_path TEXT, -- Supabase Storage path
    
    -- Processing Status
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'uploading', 'processing', 'chunking', 
        'embedding', 'completed', 'failed', 'cancelled'
    )),
    
    -- Progress Tracking
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    total_chunks INTEGER,
    processed_chunks INTEGER DEFAULT 0,
    failed_chunks INTEGER DEFAULT 0,
    
    -- LlamaParse Integration
    llama_parse_job_id TEXT,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    error_message TEXT,
    error_details JSONB,
    
    -- Document Content
    structured_contents JSONB,
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
        (status = 'completed' AND progress_percentage = 100) OR (status != 'completed')
    ),
    CONSTRAINT chk_chunk_consistency CHECK (
        (total_chunks IS NULL) OR (processed_chunks + failed_chunks <= total_chunks)
    ),
    CONSTRAINT chk_file_size_limit CHECK (file_size <= 52428800) -- 50MB limit
);

-- Document indexes
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_llama_parse_job ON documents(llama_parse_job_id) WHERE llama_parse_job_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(status, processing_started_at) WHERE status IN ('processing', 'chunking', 'embedding');
CREATE INDEX IF NOT EXISTS idx_documents_user_status ON documents(user_id, status, created_at DESC);

-- =============================================================================
-- REGULATORY DOCUMENTS SYSTEM
-- =============================================================================

-- Regulatory documents table
CREATE TABLE regulatory_documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_document_path TEXT NOT NULL,
    title TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    program TEXT[] DEFAULT '{}',
    document_type TEXT NOT NULL,
    effective_date DATE,
    expiration_date DATE,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    structured_contents JSONB,
    source_url TEXT,
    source_last_checked TIMESTAMPTZ,
    content_hash TEXT UNIQUE,
    extraction_method TEXT,
    priority_score DECIMAL DEFAULT 1.0,
    search_metadata JSONB DEFAULT '{}'::jsonb,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
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
-- UNIFIED VECTOR STORAGE SYSTEM
-- =============================================================================

-- Unified document vectors table (supports both user and regulatory documents)
CREATE TABLE document_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    
    -- Document References (one of these will be populated)
    document_record_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    regulatory_document_id UUID REFERENCES regulatory_documents(document_id) ON DELETE CASCADE,
    
    -- Document source type
    document_source_type TEXT NOT NULL CHECK (document_source_type IN ('user_document', 'regulatory_document')),
    
    -- Vector data
    chunk_index INTEGER NOT NULL,
    content_embedding vector(1536) NOT NULL,
    
    -- Encrypted content
    encrypted_chunk_text TEXT,
    encrypted_chunk_metadata TEXT,
    encryption_key_id UUID REFERENCES encryption_keys(id),
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    -- Constraints
    CONSTRAINT chk_document_reference CHECK (
        (document_source_type = 'user_document' AND document_record_id IS NOT NULL AND regulatory_document_id IS NULL AND user_id IS NOT NULL) OR
        (document_source_type = 'regulatory_document' AND regulatory_document_id IS NOT NULL AND document_record_id IS NULL)
    ),
    CONSTRAINT chk_encryption_consistency CHECK (
        (encrypted_chunk_text IS NOT NULL AND encrypted_chunk_metadata IS NOT NULL AND encryption_key_id IS NOT NULL) OR
        (encrypted_chunk_text IS NULL AND encrypted_chunk_metadata IS NULL AND encryption_key_id IS NULL)
    )
);

-- Vector indexes
CREATE INDEX idx_document_vectors_user_id ON document_vectors(user_id);
CREATE INDEX idx_document_vectors_document_record ON document_vectors(document_record_id);
CREATE INDEX idx_document_vectors_regulatory_doc ON document_vectors(regulatory_document_id);
CREATE INDEX idx_document_vectors_source_type ON document_vectors(document_source_type);
CREATE INDEX idx_document_vectors_active ON document_vectors(is_active) WHERE is_active = true;
CREATE INDEX idx_document_vectors_embedding ON document_vectors USING ivfflat (content_embedding vector_cosine_ops);
CREATE INDEX idx_document_vectors_encryption_key ON document_vectors(encryption_key_id);
CREATE INDEX idx_document_vectors_regulatory_search ON document_vectors(regulatory_document_id, document_source_type, is_active) WHERE document_source_type = 'regulatory_document';

-- =============================================================================
-- CONVERSATION & AGENT SYSTEM
-- =============================================================================

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversation messages
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent states
CREATE TABLE IF NOT EXISTS agent_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    agent_type TEXT NOT NULL,
    state_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- JOB QUEUE SYSTEM
-- =============================================================================

-- Processing jobs table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'retrying')),
    priority INTEGER DEFAULT 0,
    payload JSONB NOT NULL,
    result JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_scheduled ON processing_jobs(scheduled_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_processing_jobs_type ON processing_jobs(job_type);

-- Realtime progress tracking
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
-- SYSTEM UTILITIES
-- =============================================================================

-- Schema migrations tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

-- System metadata
CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- USEFUL VIEWS
-- =============================================================================

-- Document processing statistics
CREATE VIEW document_processing_stats AS
SELECT 
    status,
    COUNT(*) as count,
    AVG(progress_percentage) as avg_progress,
    AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) as avg_processing_time_seconds
FROM documents 
WHERE processing_started_at IS NOT NULL
GROUP BY status;

-- Failed documents view
CREATE VIEW failed_documents AS
SELECT 
    id,
    user_id,
    original_filename,
    status,
    error_message,
    created_at,
    processing_started_at
FROM documents 
WHERE status = 'failed';

-- Regulatory documents searchable view
CREATE VIEW regulatory_documents_searchable AS
SELECT 
    rd.document_id,
    rd.title,
    rd.jurisdiction,
    rd.document_type,
    rd.source_url,
    rd.tags,
    rd.created_at,
    COUNT(dv.id) as vector_count,
    MAX(dv.created_at) as last_vectorized
FROM regulatory_documents rd
LEFT JOIN document_vectors dv ON rd.document_id = dv.regulatory_document_id
GROUP BY rd.document_id, rd.title, rd.jurisdiction, rd.document_type, rd.source_url, rd.tags, rd.created_at;

-- =============================================================================
-- CORE FUNCTIONS
-- =============================================================================

-- Function to search regulatory documents
CREATE OR REPLACE FUNCTION search_regulatory_documents(
    search_embedding vector(1536),
    similarity_threshold FLOAT DEFAULT 0.8,
    limit_results INTEGER DEFAULT 10
) RETURNS TABLE (
    document_id UUID,
    title TEXT,
    jurisdiction TEXT,
    source_url TEXT,
    document_type TEXT,
    similarity_score FLOAT,
    chunk_content TEXT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rd.document_id,
        rd.title,
        rd.jurisdiction,
        rd.source_url,
        rd.document_type,
        (1 - (dv.content_embedding <=> search_embedding))::FLOAT as similarity_score,
        dv.encrypted_chunk_text as chunk_content
    FROM document_vectors dv
    JOIN regulatory_documents rd ON dv.regulatory_document_id = rd.document_id
    WHERE dv.document_source_type = 'regulatory_document'
    AND dv.is_active = true
    AND (1 - (dv.content_embedding <=> search_embedding)) >= similarity_threshold
    ORDER BY dv.content_embedding <=> search_embedding
    LIMIT limit_results;
END;
$$;

-- Function to update progress
CREATE OR REPLACE FUNCTION update_document_progress(
    doc_id UUID,
    new_status TEXT DEFAULT NULL,
    new_progress INTEGER DEFAULT NULL,
    chunks_processed INTEGER DEFAULT NULL,
    chunks_failed INTEGER DEFAULT NULL,
    error_msg TEXT DEFAULT NULL
) RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE documents SET
        status = COALESCE(new_status, status),
        progress_percentage = COALESCE(new_progress, progress_percentage),
        processed_chunks = COALESCE(chunks_processed, processed_chunks),
        failed_chunks = COALESCE(chunks_failed, failed_chunks),
        error_message = COALESCE(error_msg, error_message),
        processing_completed_at = CASE 
            WHEN new_status = 'completed' THEN NOW() 
            ELSE processing_completed_at 
        END,
        updated_at = NOW()
    WHERE id = doc_id;
    
    RETURN FOUND;
END;
$$;

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Create triggers if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_documents_updated_at') THEN
        CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_regulatory_documents_updated_at') THEN
        CREATE TRIGGER update_regulatory_documents_updated_at BEFORE UPDATE ON regulatory_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_users_updated_at') THEN
        CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_conversations_updated_at') THEN
        CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert default roles
INSERT INTO roles (name, description) VALUES 
('admin', 'System administrator with full access'),
('user', 'Regular user with standard access'),
('agent', 'AI agent with system access')
ON CONFLICT (name) DO NOTHING;

-- Insert initial system metadata
INSERT INTO system_metadata (key, value) VALUES 
('schema_version', '"V2.0.0"'),
('deployment_date', to_jsonb(NOW())),
('vector_dimensions', '1536'),
('max_file_size_mb', '50')
ON CONFLICT (key) DO UPDATE SET 
    value = EXCLUDED.value,
    updated_at = NOW();

-- Record this migration
INSERT INTO schema_migrations (version) VALUES ('V2.0.0__consolidated_production_schema')
ON CONFLICT (version) DO NOTHING;

COMMIT; 