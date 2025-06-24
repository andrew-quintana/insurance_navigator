-- =============================================================================
-- CLEANUP DOCUMENT SCHEMA
-- Description: Remove remaining unused columns and tables
-- Production deployment
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
-- STEP 1: REMOVE UNUSED COLUMNS FROM DOCUMENTS
-- =============================================================================

ALTER TABLE documents
DROP COLUMN IF EXISTS bucket_name,
DROP COLUMN IF EXISTS upload_status,
DROP COLUMN IF EXISTS processing_status,
DROP COLUMN IF EXISTS content_summary,
DROP COLUMN IF EXISTS progress_percentage,
DROP COLUMN IF EXISTS total_chunks,
DROP COLUMN IF EXISTS processed_chunks,
DROP COLUMN IF EXISTS failed_chunks,
DROP COLUMN IF EXISTS storage_backend,
DROP COLUMN IF EXISTS processing_progress,
DROP COLUMN IF EXISTS processing_stage;

-- =============================================================================
-- STEP 2: CLEANUP DOCUMENT VECTORS TABLE
-- =============================================================================

-- Remove old document source type constraint
ALTER TABLE document_vectors
DROP CONSTRAINT IF EXISTS document_vectors_document_source_type_check,
DROP CONSTRAINT IF EXISTS user_or_regulatory_document_check;

-- Remove unused columns
ALTER TABLE document_vectors
DROP COLUMN IF EXISTS document_id,
DROP COLUMN IF EXISTS regulatory_document_id,
DROP COLUMN IF EXISTS document_source_type;

-- Add new constraint
ALTER TABLE document_vectors
ADD CONSTRAINT document_vectors_document_record_id_fkey 
FOREIGN KEY (document_record_id) REFERENCES documents(id) ON DELETE CASCADE;

-- =============================================================================
-- STEP 3: CLEANUP FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Drop unused functions
DROP FUNCTION IF EXISTS public.auto_create_processing_job() CASCADE;
DROP FUNCTION IF EXISTS public.backfill_stuck_documents() CASCADE;
DROP FUNCTION IF EXISTS public.check_job_processing_health() CASCADE;
DROP FUNCTION IF EXISTS public.check_queue_health() CASCADE;
DROP FUNCTION IF EXISTS public.cleanup_old_jobs() CASCADE;
DROP FUNCTION IF EXISTS public.cleanup_realtime_progress_updates() CASCADE;
DROP FUNCTION IF EXISTS public.complete_processing_job() CASCADE;
DROP FUNCTION IF EXISTS public.create_processing_job() CASCADE;
DROP FUNCTION IF EXISTS public.fail_processing_job() CASCADE;
DROP FUNCTION IF EXISTS public.get_pending_jobs() CASCADE;
DROP FUNCTION IF EXISTS public.handle_job_completion() CASCADE;
DROP FUNCTION IF EXISTS public.monitor_processing_queue() CASCADE;
DROP FUNCTION IF EXISTS public.schedule_next_job_safely() CASCADE;
DROP FUNCTION IF EXISTS public.start_processing_job() CASCADE;
DROP FUNCTION IF EXISTS public.trigger_document_processing() CASCADE;
DROP FUNCTION IF EXISTS public.update_document_progress() CASCADE;
DROP FUNCTION IF EXISTS public.validate_job_completion() CASCADE;

COMMIT; 