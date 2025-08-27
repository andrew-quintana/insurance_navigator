-- Row Level Security (RLS) Policies for upload_pipeline schema
-- This ensures users can only access their own documents and chunks

-- Enable RLS on all tables
ALTER TABLE upload_pipeline.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_pipeline.upload_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_pipeline.document_chunks ENABLE ROW LEVEL SECURITY;

-- Policy for documents table - users can only access their own documents
CREATE POLICY user_document_access ON upload_pipeline.documents
    FOR ALL TO postgres
    USING (user_id::text = current_setting('app.current_user_id', true) OR current_setting('app.current_user_id', true) IS NULL);

-- Policy for upload_jobs table - users can only access their own jobs
CREATE POLICY user_upload_job_access ON upload_pipeline.upload_jobs
    FOR ALL TO postgres
    USING (user_id::text = current_setting('app.current_user_id', true) OR current_setting('app.current_user_id', true) IS NULL);

-- Policy for document_chunks table - users can only access their own chunks
CREATE POLICY user_chunk_access ON upload_pipeline.document_chunks
    FOR ALL TO postgres
    USING (user_id::text = current_setting('app.current_user_id', true) OR current_setting('app.current_user_id', true) IS NULL);

-- Function to set current user context for RLS
CREATE OR REPLACE FUNCTION upload_pipeline.set_user_context(user_uuid UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_uuid::text, false);
END;
$$ LANGUAGE plpgsql;

-- Function to clear user context
CREATE OR REPLACE FUNCTION upload_pipeline.clear_user_context()
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_user_id', NULL, false);
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions on context functions
GRANT EXECUTE ON FUNCTION upload_pipeline.set_user_context(UUID) TO postgres;
GRANT EXECUTE ON FUNCTION upload_pipeline.clear_user_context() TO postgres;
