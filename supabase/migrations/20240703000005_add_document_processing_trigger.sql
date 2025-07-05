-- Enable the pg_net extension if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;

-- Create the trigger function
CREATE OR REPLACE FUNCTION process_document()
RETURNS trigger AS $$
BEGIN
    -- Call the Edge Function to process the document
    PERFORM
        extensions.http_post(
            'http://127.0.0.1:54321/functions/v1/upload-handler',
            headers := jsonb_build_object(
                'Authorization', 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.p2fuVDatv5iaDizrYVeg2Gx_U1utFdpwLHwkiZfsRxs',
                'Content-Type', 'application/json'
            ),
            body := jsonb_build_object(
                'document_id', NEW.id,
                'storage_path', NEW.storage_path,
                'content_type', NEW.content_type
            )
        );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
DROP TRIGGER IF EXISTS trigger_process_document ON documents;
CREATE TRIGGER trigger_process_document
    AFTER INSERT ON documents
    FOR EACH ROW
    WHEN (NEW.status = 'processing')
    EXECUTE FUNCTION process_document(); 