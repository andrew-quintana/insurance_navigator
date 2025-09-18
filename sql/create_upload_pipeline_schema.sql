-- Create upload pipeline schema and tables for production Supabase
BEGIN;

-- Create upload_pipeline schema
CREATE SCHEMA IF NOT EXISTS upload_pipeline;

-- Create documents table for upload pipeline
CREATE TABLE IF NOT EXISTS upload_pipeline.documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create upload_jobs table for processing queue
CREATE TABLE IF NOT EXISTS upload_pipeline.upload_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES upload_pipeline.documents(document_id) ON DELETE CASCADE,
    stage TEXT NOT NULL DEFAULT 'job_created',
    state TEXT NOT NULL DEFAULT 'pending',
    payload JSONB,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Create document_chunks table for processed chunks
CREATE TABLE IF NOT EXISTS upload_pipeline.document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES upload_pipeline.documents(document_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    tokens INTEGER,
    vector JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_upload_jobs_stage_state ON upload_pipeline.upload_jobs(stage, state);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_document_id ON upload_pipeline.upload_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON upload_pipeline.documents(user_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON upload_pipeline.document_chunks(document_id);

-- Grant permissions
GRANT USAGE ON SCHEMA upload_pipeline TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA upload_pipeline TO postgres, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA upload_pipeline TO authenticated;

-- Enable RLS
ALTER TABLE upload_pipeline.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_pipeline.upload_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_pipeline.document_chunks ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view their own documents" ON upload_pipeline.documents
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own documents" ON upload_pipeline.documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own documents" ON upload_pipeline.documents
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view jobs for their documents" ON upload_pipeline.upload_jobs
    FOR SELECT USING (
        document_id IN (
            SELECT document_id FROM upload_pipeline.documents WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view chunks for their documents" ON upload_pipeline.document_chunks
    FOR SELECT USING (
        document_id IN (
            SELECT document_id FROM upload_pipeline.documents WHERE user_id = auth.uid()
        )
    );

COMMIT;
