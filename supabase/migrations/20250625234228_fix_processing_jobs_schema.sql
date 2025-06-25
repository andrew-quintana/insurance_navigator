-- =============================================================================
-- FIX PROCESSING JOBS SCHEMA
-- Description: Add document_id column and update constraints
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
-- STEP 1: ADD DOCUMENT_ID COLUMN
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
