-- Drop existing function and trigger if they exist
DROP TRIGGER IF EXISTS create_document_job_trigger ON documents;
DROP FUNCTION IF EXISTS create_document_job();

-- Create the function
CREATE OR REPLACE FUNCTION create_document_job()
RETURNS TRIGGER AS $$
DECLARE
  job_id uuid;
BEGIN
  RAISE NOTICE 'create_document_job trigger started for document_id: %', NEW.id;

  BEGIN
    INSERT INTO jobs (document_id, status, metadata)
    VALUES (NEW.id, 'STARTED', jsonb_build_object(
      'document_id', NEW.id,
      'file_path', NEW.file_path,
      'file_type', NEW.file_type,
      'created_at', NEW.created_at
    ))
    RETURNING id INTO job_id;
    
    RAISE NOTICE 'Job created successfully with id: %', job_id;
  EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error creating job: % %', SQLERRM, SQLSTATE;
    RAISE;
  END;

  RETURN NEW;
END;
$$ language 'plpgsql' SECURITY DEFINER;

-- Create the trigger
CREATE TRIGGER create_document_job_trigger
  AFTER INSERT ON documents
  FOR EACH ROW
  EXECUTE FUNCTION create_document_job(); 