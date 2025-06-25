-- =============================================================================
-- COMPREHENSIVE STORAGE AND DATABASE SETUP
-- Description: Align storage buckets, policies, and database tables
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
-- STEP 1: ENSURE STORAGE EXTENSION AND BUCKETS
-- =============================================================================

-- Enable storage extension if not enabled
CREATE EXTENSION IF NOT EXISTS "storage";

-- Create documents bucket if it doesn't exist
INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', false)
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
WHERE id = 'documents';

-- =============================================================================
-- STEP 2: ENSURE DOCUMENT TABLES EXIST WITH CORRECT SCHEMA
-- =============================================================================

-- Create or update documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    original_filename TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    content_type TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    document_type TEXT NOT NULL DEFAULT 'user_uploaded',
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    jurisdiction TEXT,
    program TEXT[],
    effective_date DATE,
    expiration_date DATE,
    source_url TEXT,
    tags TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add document type constraint
ALTER TABLE documents
DROP CONSTRAINT IF EXISTS valid_document_type;

ALTER TABLE documents
ADD CONSTRAINT valid_document_type 
CHECK (document_type IN ('user_uploaded', 'regulatory', 'policy', 'medical_record', 'claim'));

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_jurisdiction ON documents(jurisdiction) WHERE jurisdiction IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_documents_dates ON documents(effective_date, expiration_date) 
WHERE effective_date IS NOT NULL OR expiration_date IS NOT NULL;

-- Create or update processing_jobs table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
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

-- Add indexes for job processing
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_document ON processing_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_priority ON processing_jobs(priority) WHERE status = 'pending';

-- Create or update document_vectors table
CREATE TABLE IF NOT EXISTS document_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_record_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(document_record_id, chunk_index)
);

-- Add index for vector search
CREATE INDEX IF NOT EXISTS idx_document_vectors_embedding ON document_vectors USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- =============================================================================
-- STEP 3: UPDATE STORAGE POLICIES
-- =============================================================================

-- Remove any existing policies
DROP POLICY IF EXISTS "Allow authenticated users to upload files" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated users to read their own files" ON storage.objects;
DROP POLICY IF EXISTS "Allow service role full access" ON storage.objects;

-- Add storage policies for authenticated users
CREATE POLICY "Allow authenticated users to upload files"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Allow authenticated users to read their own files"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Add storage policy for service role (used by Edge Functions)
CREATE POLICY "Allow service role full access"
ON storage.objects
TO service_role
USING (bucket_id = 'documents')
WITH CHECK (bucket_id = 'documents');

-- =============================================================================
-- STEP 4: UPDATE DOCUMENT TABLES RLS POLICIES
-- =============================================================================

-- Documents table policies
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own documents" ON documents;
DROP POLICY IF EXISTS "Users can insert their own documents" ON documents;
DROP POLICY IF EXISTS "Users can update their own documents" ON documents;
DROP POLICY IF EXISTS "Service role full access to documents" ON documents;

CREATE POLICY "Users can view their own documents"
ON documents FOR SELECT
TO authenticated
USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own documents"
ON documents FOR INSERT
TO authenticated
WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own documents"
ON documents FOR UPDATE
TO authenticated
USING (user_id = auth.uid());

CREATE POLICY "Service role full access to documents"
ON documents
TO service_role
USING (true)
WITH CHECK (true);

-- Processing jobs policies
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role full access to processing jobs" ON processing_jobs;

CREATE POLICY "Service role full access to processing jobs"
ON processing_jobs
TO service_role
USING (true)
WITH CHECK (true);

-- Document vectors policies
ALTER TABLE document_vectors ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view vectors of their documents" ON document_vectors;
DROP POLICY IF EXISTS "Service role full access to vectors" ON document_vectors;

CREATE POLICY "Users can view vectors of their documents"
ON document_vectors FOR SELECT
TO authenticated
USING (EXISTS (
    SELECT 1 FROM documents
    WHERE documents.id = document_vectors.document_record_id
    AND documents.user_id = auth.uid()
));

CREATE POLICY "Service role full access to vectors"
ON document_vectors
TO service_role
USING (true)
WITH CHECK (true);

-- =============================================================================
-- FIX PROCESSING JOBS SCHEMA
-- Description: Add document_id column and update constraints
-- =============================================================================

-- Add document_id column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'processing_jobs' 
        AND column_name = 'document_id'
    ) THEN
        ALTER TABLE processing_jobs 
        ADD COLUMN document_id UUID REFERENCES documents(id) ON DELETE CASCADE;
    END IF;
EXCEPTION
    WHEN undefined_table THEN
        RAISE NOTICE 'Table processing_jobs does not exist';
END $$;

-- =============================================================================
-- STEP 2: UPDATE INDEXES
-- =============================================================================

-- Add index for document_id if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'processing_jobs' 
        AND indexname = 'idx_processing_jobs_document_id'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_processing_jobs_document_id 
        ON processing_jobs(document_id);
    END IF;
EXCEPTION
    WHEN undefined_table THEN
        RAISE NOTICE 'Table processing_jobs does not exist';
END $$;

-- =============================================================================
-- STEP 3: UPDATE RLS POLICIES
-- =============================================================================

-- Drop and recreate policies to use document_id
DO $$
BEGIN
    -- Drop existing policies
    DROP POLICY IF EXISTS "Users can view jobs for their documents" ON processing_jobs;
    DROP POLICY IF EXISTS "Service role can manage all jobs" ON processing_jobs;

    -- Recreate policies
    CREATE POLICY "Users can view jobs for their documents"
        ON processing_jobs FOR SELECT
        USING (EXISTS (
            SELECT 1 FROM documents
            WHERE documents.id = processing_jobs.document_id
            AND documents.user_id = auth.uid()
        ));

    CREATE POLICY "Service role can manage all jobs"
        ON processing_jobs
        TO service_role
        USING (true)
        WITH CHECK (true);
EXCEPTION
    WHEN undefined_table THEN
        RAISE NOTICE 'Table processing_jobs does not exist';
    WHEN undefined_object THEN
        RAISE NOTICE 'Policy does not exist';
END $$;

COMMIT; 