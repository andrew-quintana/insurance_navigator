-- =============================================================================
-- ROLLBACK UNIFIED DOCUMENT SCHEMA V3.0.0
-- Description: Rollback the unified document schema changes
-- =============================================================================

BEGIN;

-- =============================================================================
-- STEP 1: RECREATE DROPPED TABLES
-- =============================================================================

-- Recreate regulatory_documents table
CREATE TABLE IF NOT EXISTS regulatory_documents (
    document_id UUID PRIMARY KEY,
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

-- Recreate processing_jobs table
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

-- Recreate document_processing_status table
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

-- Recreate realtime_progress_updates table
CREATE TABLE IF NOT EXISTS realtime_progress_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    status TEXT NOT NULL,
    progress INTEGER,
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- STEP 2: RESTORE DOCUMENT VECTORS TABLE
-- =============================================================================

-- Restore regulatory document reference
ALTER TABLE document_vectors
ADD COLUMN IF NOT EXISTS regulatory_document_id UUID REFERENCES regulatory_documents(document_id) ON DELETE CASCADE,
DROP CONSTRAINT IF EXISTS chk_document_reference,
ADD CONSTRAINT chk_document_reference_exclusive CHECK (
    (document_source_type = 'user_document' AND document_record_id IS NOT NULL AND regulatory_document_id IS NULL) OR
    (document_source_type = 'regulatory_document' AND regulatory_document_id IS NOT NULL AND document_record_id IS NULL)
);

-- =============================================================================
-- STEP 3: RESTORE DOCUMENTS TABLE
-- =============================================================================

-- Restore removed fields
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS mime_type TEXT,
ADD COLUMN IF NOT EXISTS storage_provider TEXT,
ADD COLUMN IF NOT EXISTS content_extracted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS policy_basics JSONB,
ADD COLUMN IF NOT EXISTS total_chunks INTEGER,
ADD COLUMN IF NOT EXISTS processed_chunks INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS failed_chunks INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS storage_backend TEXT,
ADD COLUMN IF NOT EXISTS progress_percentage INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS llama_parse_job_id TEXT,
ADD COLUMN IF NOT EXISTS processing_progress INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS processing_stage TEXT,
ADD COLUMN IF NOT EXISTS file_path TEXT;

-- Restore original status constraint
ALTER TABLE documents
DROP CONSTRAINT IF EXISTS documents_status_check,
ADD CONSTRAINT documents_status_check CHECK (
    status IN ('pending', 'uploading', 'processing', 'chunking', 'embedding', 'completed', 'failed', 'cancelled')
);

-- Remove regulatory-specific fields
ALTER TABLE documents
DROP COLUMN IF EXISTS jurisdiction,
DROP COLUMN IF EXISTS program,
DROP COLUMN IF EXISTS effective_date,
DROP COLUMN IF EXISTS expiration_date,
DROP COLUMN IF EXISTS source_url,
DROP COLUMN IF EXISTS source_last_checked,
DROP COLUMN IF EXISTS priority_score,
DROP COLUMN IF EXISTS tags;

-- =============================================================================
-- STEP 4: MIGRATE DATA BACK
-- =============================================================================

-- Move regulatory documents back
INSERT INTO regulatory_documents (
    document_id,
    raw_document_path,
    title,
    jurisdiction,
    program,
    document_type,
    effective_date,
    expiration_date,
    source_url,
    source_last_checked,
    content_hash,
    priority_score,
    search_metadata,
    tags,
    created_at,
    updated_at
)
SELECT
    id,
    storage_path,
    original_filename,
    jurisdiction,
    program,
    document_type,
    effective_date,
    expiration_date,
    source_url,
    source_last_checked,
    file_hash,
    priority_score,
    metadata,
    tags,
    created_at,
    updated_at
FROM documents
WHERE document_type = 'regulatory'
ON CONFLICT (document_id) DO NOTHING;

-- Update document vectors
UPDATE document_vectors
SET regulatory_document_id = document_record_id,
    document_source_type = 'regulatory_document'
WHERE document_source_type = 'document'
AND document_record_id IN (SELECT id FROM documents WHERE document_type = 'regulatory');

-- =============================================================================
-- STEP 5: RECREATE VIEWS
-- =============================================================================

-- Recreate document processing stats view
CREATE OR REPLACE VIEW document_processing_stats AS
SELECT 
    status,
    COUNT(*) as count,
    AVG(progress_percentage) as avg_progress,
    AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) as avg_processing_time_seconds
FROM documents 
WHERE processing_started_at IS NOT NULL
GROUP BY status;

-- Recreate failed documents view
CREATE OR REPLACE VIEW failed_documents AS
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

-- Recreate regulatory documents searchable view
CREATE OR REPLACE VIEW regulatory_documents_searchable AS
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
-- RECORD ROLLBACK
-- =============================================================================

DELETE FROM schema_migrations 
WHERE version = 'V3.0.0__unified_document_schema';

COMMIT; 