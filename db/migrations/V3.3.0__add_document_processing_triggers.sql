-- Add trigger for document processing
CREATE OR REPLACE FUNCTION create_document_processing_job()
RETURNS TRIGGER AS $$
BEGIN
    -- Create initial parsing job
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
            'document_id', NEW.id,
            'storage_path', NEW.storage_path,
            'content_type', NEW.content_type,
            'document_type', NEW.document_type,
            'created_at', NEW.created_at
        ),
        NOW()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on documents table
DROP TRIGGER IF EXISTS trigger_document_processing ON documents;
CREATE TRIGGER trigger_document_processing
    AFTER INSERT ON documents
    FOR EACH ROW
    EXECUTE FUNCTION create_document_processing_job();

-- Add trigger for job completion notifications
CREATE OR REPLACE FUNCTION notify_job_completion()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        -- Insert notification into realtime_progress table
        INSERT INTO realtime_progress (
            user_id,
            document_id,
            notification_type,
            payload,
            created_at
        ) VALUES (
            (SELECT user_id FROM documents WHERE id = NEW.document_id),
            NEW.document_id,
            'job_completion',
            jsonb_build_object(
                'job_type', NEW.job_type,
                'status', NEW.status,
                'completed_at', NEW.completed_at,
                'metadata', NEW.metadata
            ),
            NOW()
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on processing_jobs table
DROP TRIGGER IF EXISTS trigger_job_completion ON processing_jobs;
CREATE TRIGGER trigger_job_completion
    AFTER UPDATE ON processing_jobs
    FOR EACH ROW
    EXECUTE FUNCTION notify_job_completion(); 