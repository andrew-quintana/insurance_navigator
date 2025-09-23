-- Create Upload Pipeline Schema and Tables
-- This script creates the missing database schema and tables for the enhanced base worker

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS upload_pipeline;

-- Grant permissions
GRANT USAGE ON SCHEMA upload_pipeline TO postgres;
GRANT CREATE ON SCHEMA upload_pipeline TO postgres;

-- Create upload_jobs table
CREATE TABLE IF NOT EXISTS upload_pipeline.upload_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    document_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    correlation_id UUID,
    request_id UUID
);

-- Create documents table
CREATE TABLE IF NOT EXISTS upload_pipeline.documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    file_path TEXT,
    storage_bucket VARCHAR(100),
    storage_key VARCHAR(500)
);

-- Create document_chunks table
CREATE TABLE IF NOT EXISTS upload_pipeline.document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES upload_pipeline.documents(document_id) ON DELETE CASCADE,
    chunk_ord INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    tokens INTEGER,
    page_number INTEGER,
    section_title VARCHAR(500)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_upload_jobs_user_id ON upload_pipeline.upload_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_status ON upload_pipeline.upload_jobs(status);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_created_at ON upload_pipeline.upload_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_correlation_id ON upload_pipeline.upload_jobs(correlation_id);

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON upload_pipeline.documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON upload_pipeline.documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON upload_pipeline.documents(created_at);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON upload_pipeline.document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_ord ON upload_pipeline.document_chunks(document_id, chunk_ord);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON upload_pipeline.document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION upload_pipeline.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
DROP TRIGGER IF EXISTS update_upload_jobs_updated_at ON upload_pipeline.upload_jobs;
CREATE TRIGGER update_upload_jobs_updated_at
    BEFORE UPDATE ON upload_pipeline.upload_jobs
    FOR EACH ROW
    EXECUTE FUNCTION upload_pipeline.update_updated_at_column();

DROP TRIGGER IF EXISTS update_documents_updated_at ON upload_pipeline.documents;
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON upload_pipeline.documents
    FOR EACH ROW
    EXECUTE FUNCTION upload_pipeline.update_updated_at_column();

-- Grant permissions to postgres user
GRANT ALL PRIVILEGES ON SCHEMA upload_pipeline TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA upload_pipeline TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA upload_pipeline TO postgres;

-- Verify schema creation
DO $$
BEGIN
    -- Check if schema exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'upload_pipeline') THEN
        RAISE EXCEPTION 'upload_pipeline schema was not created';
    END IF;
    
    -- Check if tables exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'upload_pipeline' AND table_name = 'upload_jobs') THEN
        RAISE EXCEPTION 'upload_jobs table was not created';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'upload_pipeline' AND table_name = 'documents') THEN
        RAISE EXCEPTION 'documents table was not created';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'upload_pipeline' AND table_name = 'document_chunks') THEN
        RAISE EXCEPTION 'document_chunks table was not created';
    END IF;
    
    RAISE NOTICE 'upload_pipeline schema and tables created successfully';
END $$;