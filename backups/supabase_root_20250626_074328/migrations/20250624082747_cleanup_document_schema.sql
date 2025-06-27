-- =============================================================================
-- CLEANUP DOCUMENT SCHEMA
-- Description: Fix schema cache issues and ensure proper table setup
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
-- STEP 1: REFRESH SCHEMA CACHE
-- =============================================================================

-- Recreate processing_jobs table to ensure schema cache is updated
DROP TABLE IF EXISTS processing_jobs CASCADE;

CREATE TABLE processing_jobs (
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

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_processing_jobs_document_id ON processing_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_scheduled ON processing_jobs(scheduled_at) 
WHERE status = 'pending';

-- =============================================================================
-- STEP 2: ENSURE STORAGE BUCKETS
-- =============================================================================

-- Create raw_documents bucket if it doesn't exist
INSERT INTO storage.buckets (id, name, public)
VALUES ('raw_documents', 'raw_documents', false)
ON CONFLICT (id) DO UPDATE
SET public = false;

-- Set raw_documents bucket configuration
UPDATE storage.buckets
SET file_size_limit = 52428800, -- 50MB
    allowed_mime_types = ARRAY[
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ]
WHERE id = 'raw_documents';

-- Ensure documents bucket configuration
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
-- STEP 3: ENSURE RLS POLICIES
-- =============================================================================

-- Drop existing policies to avoid conflicts
DO $$
BEGIN
    -- Drop documents policies
    DROP POLICY IF EXISTS "Users can view their own documents" ON documents;
    DROP POLICY IF EXISTS "Users can insert their own documents" ON documents;
    DROP POLICY IF EXISTS "Users can update their own documents" ON documents;
    
    -- Drop processing_jobs policies
    DROP POLICY IF EXISTS "Users can view jobs for their documents" ON processing_jobs;
    DROP POLICY IF EXISTS "Service role can manage all jobs" ON processing_jobs;
EXCEPTION
    WHEN undefined_table THEN
        RAISE NOTICE 'Table does not exist, skipping policy drops';
    WHEN undefined_object THEN
        RAISE NOTICE 'Policy does not exist, skipping drop';
END $$;

-- Enable RLS on tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;

-- Recreate policies safely
DO $$
BEGIN
    -- Documents table policies
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'documents' 
        AND policyname = 'Users can view their own documents'
    ) THEN
        CREATE POLICY "Users can view their own documents"
            ON documents FOR SELECT
            USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'documents' 
        AND policyname = 'Users can insert their own documents'
    ) THEN
        CREATE POLICY "Users can insert their own documents"
            ON documents FOR INSERT
            WITH CHECK (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'documents' 
        AND policyname = 'Users can update their own documents'
    ) THEN
        CREATE POLICY "Users can update their own documents"
            ON documents FOR UPDATE
            USING (auth.uid() = user_id);
    END IF;

    -- Processing jobs table policies
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'processing_jobs' 
        AND policyname = 'Users can view jobs for their documents'
    ) THEN
        CREATE POLICY "Users can view jobs for their documents"
            ON processing_jobs FOR SELECT
            USING (EXISTS (
                SELECT 1 FROM documents
                WHERE documents.id = processing_jobs.document_id
                AND documents.user_id = auth.uid()
            ));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'processing_jobs' 
        AND policyname = 'Service role can manage all jobs'
    ) THEN
        CREATE POLICY "Service role can manage all jobs"
            ON processing_jobs
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

COMMIT; 