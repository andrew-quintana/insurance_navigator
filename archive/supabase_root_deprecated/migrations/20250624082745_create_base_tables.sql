-- =============================================================================
-- CREATE BASE TABLES
-- Description: Set up initial tables before schema unification
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
-- STEP 1: ENSURE EXTENSIONS
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- =============================================================================
-- STEP 2: CREATE BASE TABLES
-- =============================================================================

-- Documents table - Central document tracking
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    original_filename TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    content_type TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Processing jobs table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 1,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Document vectors table
DO $$
BEGIN
    -- Drop existing table if it exists
    DROP TABLE IF EXISTS document_vectors CASCADE;
    
    -- Create the table with the embedding column
    CREATE TABLE document_vectors (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_record_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        chunk_index INTEGER NOT NULL,
        chunk_text TEXT NOT NULL,
        embedding vector(1536),
        metadata JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE(document_record_id, chunk_index)
    );

    -- Add index for vector search
    CREATE INDEX IF NOT EXISTS idx_document_vectors_embedding 
    ON document_vectors 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error creating document_vectors table: %', SQLERRM;
END $$;

-- =============================================================================
-- STEP 3: ADD INITIAL STORAGE CONFIGURATION
-- =============================================================================

-- Create documents bucket if it doesn't exist
INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', false)
ON CONFLICT (id) DO UPDATE
SET public = false;

-- Create raw_documents bucket if it doesn't exist
INSERT INTO storage.buckets (id, name, public)
VALUES ('raw_documents', 'raw_documents', false)
ON CONFLICT (id) DO UPDATE
SET public = false;

-- Set bucket configuration
UPDATE storage.buckets
SET file_size_limit = 52428800, -- 50MB
    allowed_mime_types = ARRAY[
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ]
WHERE id IN ('documents', 'raw_documents');

-- =============================================================================
-- STEP 4: ENABLE RLS (POLICIES WILL BE ADDED LATER)
-- =============================================================================

-- Enable RLS on tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_vectors ENABLE ROW LEVEL SECURITY;

COMMIT; 