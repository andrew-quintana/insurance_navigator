-- Update processing_jobs table
ALTER TABLE processing_jobs
  ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS max_retries INTEGER NOT NULL DEFAULT 3,
  ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}';

-- Update job_type enum
ALTER TABLE processing_jobs
  DROP CONSTRAINT IF EXISTS valid_job_type;

ALTER TABLE processing_jobs
  ADD CONSTRAINT valid_job_type 
  CHECK (job_type IN ('parse', 'chunk', 'embed', 'complete', 'notify'));

-- Add document_chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id);

-- Add notifications table
CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}',
  read BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);

-- Add function to create initial parse job
CREATE OR REPLACE FUNCTION create_initial_parse_job()
RETURNS TRIGGER AS $$
BEGIN
  -- Create parse job for new document
  INSERT INTO processing_jobs (
    document_id,
    job_type,
    status,
    priority,
    payload,
    scheduled_at
  ) VALUES (
    NEW.id,
    'parse',
    'pending',
    1,
    jsonb_build_object(
      'documentId', NEW.id,
      'storagePath', NEW.storage_path,
      'contentType', NEW.content_type,
      'metadata', NEW.metadata
    ),
    NOW()
  );
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger for new documents
DROP TRIGGER IF EXISTS trigger_create_parse_job ON documents;
CREATE TRIGGER trigger_create_parse_job
  AFTER INSERT ON documents
  FOR EACH ROW
  EXECUTE FUNCTION create_initial_parse_job();

-- Add function to update document status
CREATE OR REPLACE FUNCTION update_document_status()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
    -- Update document status
    UPDATE documents
    SET 
      status = 'completed',
      updated_at = NOW(),
      metadata = jsonb_set(
        metadata,
        '{processing_completed}',
        to_jsonb(NOW())
      )
    WHERE id = NEW.document_id;
  ELSIF NEW.status = 'failed' AND OLD.status != 'failed' THEN
    -- Update document status
    UPDATE documents
    SET 
      status = 'failed',
      updated_at = NOW(),
      error_message = NEW.error,
      metadata = jsonb_set(
        metadata,
        '{processing_failed}',
        to_jsonb(NOW())
      )
    WHERE id = NEW.document_id;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger for job status changes
DROP TRIGGER IF EXISTS trigger_update_document_status ON processing_jobs;
CREATE TRIGGER trigger_update_document_status
  AFTER UPDATE ON processing_jobs
  FOR EACH ROW
  WHEN (NEW.status IN ('completed', 'failed'))
  EXECUTE FUNCTION update_document_status();

-- Add function to clean up old jobs
CREATE OR REPLACE FUNCTION cleanup_old_jobs()
RETURNS void AS $$
BEGIN
  -- Delete completed jobs older than 30 days
  DELETE FROM processing_jobs
  WHERE status = 'completed'
    AND completed_at < NOW() - INTERVAL '30 days';
    
  -- Delete failed jobs older than 7 days
  DELETE FROM processing_jobs
  WHERE status = 'failed'
    AND completed_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Add cron job for cleanup
SELECT cron.schedule(
  'cleanup-old-jobs',
  '0 0 * * *', -- Run at midnight every day
  $$SELECT cleanup_old_jobs();$$
); 