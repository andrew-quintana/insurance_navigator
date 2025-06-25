-- Add trigger for document processing
CREATE OR REPLACE FUNCTION create_document_processing_job()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO processing_jobs (
        document_id,
        job_type,
        status,
        priority,
        metadata
    ) VALUES (
        NEW.id,
        'parse',
        'pending',
        1,
        jsonb_build_object('document_type', NEW.document_type)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_document_processing
AFTER INSERT ON documents
FOR EACH ROW
EXECUTE FUNCTION create_document_processing_job();

-- Update vector column type
ALTER TABLE document_vectors
ALTER COLUMN content_embedding TYPE float[] USING content_embedding::float[]; 