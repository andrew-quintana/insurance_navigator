-- Enhance job processing with better validation and monitoring
-- This migration adds job validation, retry tracking, and improved metadata

-- Add retry tracking columns to processing_jobs if they don't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'processing_jobs' 
                  AND column_name = 'retry_count') THEN
        ALTER TABLE processing_jobs 
        ADD COLUMN retry_count INTEGER DEFAULT 0,
        ADD COLUMN last_retry_at TIMESTAMPTZ,
        ADD COLUMN initial_created_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- Create enhanced job validation and creation function
CREATE OR REPLACE FUNCTION validate_and_create_document_job()
RETURNS TRIGGER AS $$
DECLARE
    existing_job_id UUID;
    max_retries INTEGER := 3;
    retry_count INTEGER := 0;
BEGIN
    -- Use advisory lock to prevent race conditions
    -- Lock using document ID as the key
    WHILE retry_count < max_retries LOOP
        -- Try to acquire advisory lock
        IF pg_try_advisory_xact_lock(hashtext(NEW.id::text)) THEN
            -- Check for recent jobs with proper locking
            SELECT id INTO existing_job_id 
            FROM processing_jobs 
            WHERE payload->>'document_id' = NEW.id::text 
            AND created_at > NOW() - INTERVAL '5 minutes'
            AND status NOT IN ('failed', 'cancelled')
            FOR UPDATE SKIP LOCKED;
            
            IF existing_job_id IS NULL THEN
                -- No recent active job found, create new one
                INSERT INTO processing_jobs (
                    job_type,
                    status,
                    priority,
                    payload,
                    retry_count,
                    last_retry_at,
                    initial_created_at
                ) VALUES (
                    'parse',
                    'pending',
                    1,
                    jsonb_build_object(
                        'document_id', NEW.id,
                        'storage_path', NEW.storage_path,
                        'content_type', NEW.content_type,
                        'file_hash', NEW.file_hash,
                        'original_filename', NEW.original_filename,
                        'created_from', TG_NAME,
                        'initial_status', NEW.status,
                        'trigger_timestamp', NOW(),
                        'attempt_count', retry_count + 1
                    ),
                    0,
                    NULL,
                    NOW()
                );
                
                -- Update document status
                UPDATE documents 
                SET status = 'processing',
                    processing_started_at = NOW()
                WHERE id = NEW.id;
                
                RETURN NEW;
            END IF;
            
            -- Job exists, no need to create new one
            RETURN NEW;
        END IF;
        
        -- Failed to acquire lock, wait and retry
        retry_count := retry_count + 1;
        IF retry_count < max_retries THEN
            -- Wait with exponential backoff
            PERFORM pg_sleep(power(2, retry_count)::INTEGER);
        END IF;
    END LOOP;
    
    -- If we get here, failed to acquire lock after retries
    RAISE WARNING 'Failed to acquire lock for document % after % retries', NEW.id, max_retries;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS trigger_document_processing ON documents;

-- Create new enhanced trigger
CREATE TRIGGER trigger_document_processing
    AFTER INSERT ON documents
    FOR EACH ROW
    EXECUTE FUNCTION validate_and_create_document_job();

-- Create function to track job retries
CREATE OR REPLACE FUNCTION update_job_retry_count()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'retry' AND OLD.status != 'retry' THEN
        NEW.retry_count = COALESCE(OLD.retry_count, 0) + 1;
        NEW.last_retry_at = NOW();
        
        -- Update document status
        UPDATE documents 
        SET status = 'retrying',
            error_message = format('Retrying job. Attempt %s', NEW.retry_count)
        WHERE id = (NEW.payload->>'document_id')::uuid;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for retry tracking
CREATE TRIGGER trigger_job_retry_tracking
    BEFORE UPDATE ON processing_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_job_retry_count();

-- Add index for faster job lookups
CREATE INDEX IF NOT EXISTS idx_processing_jobs_document_id_created_at 
ON processing_jobs ((payload->>'document_id')::uuid, created_at);

-- Add index for status monitoring
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status_created_at 
ON processing_jobs (status, created_at);

-- Add index for document status monitoring
CREATE INDEX IF NOT EXISTS idx_documents_status_processing 
ON documents (status, processing_started_at) 
WHERE status IN ('processing', 'retrying'); 