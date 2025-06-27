-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Update documents table
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS extracted_text TEXT;

-- Rename jobs table to processing_jobs and update structure
ALTER TABLE jobs RENAME TO processing_jobs;

ALTER TABLE processing_jobs 
ADD COLUMN IF NOT EXISTS job_type TEXT NOT NULL DEFAULT 'document_processing',
ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3,
ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS payload JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS result JSONB DEFAULT '{}'::jsonb;

-- Update status constraint
ALTER TABLE processing_jobs 
DROP CONSTRAINT IF EXISTS valid_status,
ADD CONSTRAINT valid_status CHECK (
  status IN ('pending', 'processing', 'completed', 'failed', 'retrying')
);

-- Create or update indexes
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status_type ON processing_jobs(status, job_type);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_priority ON processing_jobs(priority DESC);

-- Update RLS policies for processing_jobs
DROP POLICY IF EXISTS "Users can view jobs for their documents" ON processing_jobs;
DROP POLICY IF EXISTS "Service role can do all operations on jobs" ON processing_jobs;

CREATE POLICY "Users can view their processing jobs"
  ON processing_jobs FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM documents
    WHERE documents.id = processing_jobs.document_id
    AND documents.user_id = auth.uid()
  ));

CREATE POLICY "Service role can manage processing jobs"
  ON processing_jobs FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

-- Create job management functions
CREATE OR REPLACE FUNCTION create_processing_job(
  p_document_id UUID,
  p_job_type TEXT,
  p_priority INTEGER DEFAULT 0,
  p_payload JSONB DEFAULT '{}'::jsonb
) RETURNS UUID AS $$
DECLARE
  v_job_id UUID;
BEGIN
  INSERT INTO processing_jobs (
    document_id,
    job_type,
    priority,
    status,
    payload
  ) VALUES (
    p_document_id,
    p_job_type,
    p_priority,
    'pending',
    p_payload
  ) RETURNING id INTO v_job_id;
  
  RETURN v_job_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create job status update function
CREATE OR REPLACE FUNCTION update_job_status(
  p_job_id UUID,
  p_status TEXT,
  p_error_message TEXT DEFAULT NULL,
  p_error_details JSONB DEFAULT NULL,
  p_result JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
  UPDATE processing_jobs
  SET 
    status = p_status,
    error_message = CASE 
      WHEN p_status = 'failed' THEN p_error_message 
      ELSE NULL 
    END,
    error_details = CASE 
      WHEN p_status = 'failed' THEN p_error_details 
      ELSE NULL 
    END,
    result = COALESCE(p_result, result),
    completed_at = CASE 
      WHEN p_status IN ('completed', 'failed') THEN NOW() 
      ELSE completed_at 
    END,
    retry_count = CASE 
      WHEN p_status = 'retrying' THEN retry_count + 1 
      ELSE retry_count 
    END
  WHERE id = p_job_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create document status sync trigger
CREATE OR REPLACE FUNCTION sync_document_status() RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status IN ('completed', 'failed') THEN
    UPDATE documents
    SET status = CASE 
      WHEN NEW.status = 'completed' THEN 'processed'
      ELSE 'failed'
    END
    WHERE id = NEW.document_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sync_document_status_trigger
  AFTER UPDATE OF status ON processing_jobs
  FOR EACH ROW
  EXECUTE FUNCTION sync_document_status();

-- Update document vectors table with additional metadata fields
ALTER TABLE document_vectors
ADD COLUMN IF NOT EXISTS chunk_type TEXT DEFAULT 'text',
ADD COLUMN IF NOT EXISTS confidence FLOAT DEFAULT 1.0,
ADD COLUMN IF NOT EXISTS processing_metadata JSONB DEFAULT '{}'::jsonb;

-- Create vector processing trigger
CREATE OR REPLACE FUNCTION trigger_vector_processing() RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'uploaded' AND OLD.status != 'uploaded' THEN
    PERFORM create_processing_job(
      NEW.id,
      'vector_processing',
      1,
      jsonb_build_object('document_id', NEW.id)
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER vector_processing_trigger
  AFTER UPDATE OF status ON documents
  FOR EACH ROW
  EXECUTE FUNCTION trigger_vector_processing();

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO anon, authenticated, service_role; 