-- =============================================================================
-- SCHEMA CORRECTION MIGRATION V2.1.0
-- Description: Fix database schema to match current Supabase setup
-- Adds missing tables and vector extension for document processing
-- =============================================================================

BEGIN;

-- =============================================================================
-- ADD MISSING EXTENSIONS
-- =============================================================================

-- Critical: Add vector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- ADD MISSING CORE TABLES FOR DOCUMENT PROCESSING
-- =============================================================================

-- Documents table - Central document tracking (MISSING FROM CURRENT DB)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- File Information
    original_filename TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    content_type TEXT NOT NULL,
    file_hash TEXT UNIQUE NOT NULL,
    storage_path TEXT,
    
    -- Processing Status
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'uploading', 'processing', 'chunking', 
        'embedding', 'completed', 'failed', 'cancelled'
    )),
    
    -- Progress Tracking
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    processing_progress INTEGER DEFAULT 0,
    processing_stage TEXT DEFAULT 'pending',
    total_chunks INTEGER,
    processed_chunks INTEGER DEFAULT 0,
    failed_chunks INTEGER DEFAULT 0,
    
    -- Processing Integration
    llama_parse_job_id TEXT,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    error_message TEXT,
    error_details JSONB,
    
    -- Document Content
    structured_contents JSONB,
    extracted_text_length INTEGER,
    document_type TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Encryption
    encryption_key_id UUID REFERENCES encryption_keys(id),
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document indexes
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);

-- =============================================================================
-- UNIFIED VECTOR STORAGE SYSTEM
-- =============================================================================

-- Document vectors table for embeddings
CREATE TABLE IF NOT EXISTS document_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    
    -- Document References
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
    is_active BOOLEAN DEFAULT true
);

-- Vector indexes
CREATE INDEX IF NOT EXISTS idx_document_vectors_user_id ON document_vectors(user_id);
CREATE INDEX IF NOT EXISTS idx_document_vectors_document_record ON document_vectors(document_record_id);
CREATE INDEX IF NOT EXISTS idx_document_vectors_regulatory_doc ON document_vectors(regulatory_document_id);
CREATE INDEX IF NOT EXISTS idx_document_vectors_source_type ON document_vectors(document_source_type);
CREATE INDEX IF NOT EXISTS idx_document_vectors_embedding ON document_vectors USING ivfflat (content_embedding vector_cosine_ops);

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
-- UPDATE REGULATORY DOCUMENTS TABLE
-- =============================================================================

-- Add missing columns to regulatory_documents
ALTER TABLE regulatory_documents 
ADD COLUMN IF NOT EXISTS last_updated TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS content_hash TEXT,
ADD COLUMN IF NOT EXISTS source_last_checked TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS priority_score DECIMAL DEFAULT 1.0,
ADD COLUMN IF NOT EXISTS search_metadata JSONB DEFAULT '{}'::jsonb;

-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_content_hash ON regulatory_documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_source_last_checked ON regulatory_documents(source_last_checked);
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_search_metadata ON regulatory_documents USING gin(search_metadata);

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

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Add update triggers for tables with updated_at columns
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_users_updated_at') THEN
        CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_regulatory_documents_updated_at') THEN
        CREATE TRIGGER update_regulatory_documents_updated_at BEFORE UPDATE ON regulatory_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Record migration completion
INSERT INTO schema_migrations (version) VALUES ('V2.1.0') ON CONFLICT (version) DO NOTHING;

COMMIT; 