-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Create upload_pipeline schema
CREATE SCHEMA IF NOT EXISTS upload_pipeline;

-- Create upload_jobs table with enhanced monitoring
CREATE TABLE IF NOT EXISTS upload_pipeline.upload_jobs (
    job_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    document_id UUID NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'uploaded', 'parse_queued', 'parsed', 'parse_validated', 
        'chunking', 'chunks_stored', 'embedding_queued', 
        'embedding_in_progress', 'embeddings_stored', 'complete',
        'failed_parse', 'failed_chunking', 'failed_embedding'
    )),
    raw_path TEXT NOT NULL,
    parsed_path TEXT,
    parsed_sha256 TEXT,
    chunks_version TEXT NOT NULL DEFAULT 'markdown-simple@1',
    embed_model TEXT DEFAULT 'text-embedding-3-small',
    embed_version TEXT DEFAULT '1',
    progress JSONB DEFAULT '{}',
    retry_count INT DEFAULT 0,
    last_error JSONB,
    webhook_secret TEXT,
    -- Enhanced monitoring fields
    correlation_id UUID DEFAULT gen_random_uuid(),
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create document_chunk_buffer table for chunk staging
CREATE TABLE IF NOT EXISTS upload_pipeline.document_chunk_buffer (
    chunk_id UUID NOT NULL PRIMARY KEY,
    document_id UUID NOT NULL,
    chunk_ord INT NOT NULL,
    chunker_name TEXT NOT NULL,
    chunker_version TEXT NOT NULL,
    chunk_sha TEXT NOT NULL,
    text TEXT NOT NULL,
    meta JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (chunk_id)
);

-- Create document_vector_buffer table for embedding staging
CREATE TABLE IF NOT EXISTS upload_pipeline.document_vector_buffer (
    document_id UUID NOT NULL,
    chunk_id UUID NOT NULL,
    embed_model TEXT NOT NULL,
    embed_version TEXT NOT NULL,
    vector VECTOR(1536) NOT NULL,
    vector_sha TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (chunk_id, embed_model, embed_version),
    FOREIGN KEY (chunk_id) REFERENCES upload_pipeline.document_chunk_buffer(chunk_id)
);

-- Create events table for comprehensive logging
CREATE TABLE IF NOT EXISTS upload_pipeline.events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES upload_pipeline.upload_jobs(job_id),
    document_id UUID NOT NULL,
    ts TIMESTAMPTZ DEFAULT now(),
    type TEXT NOT NULL CHECK (type IN ('stage_started','stage_done','retry','error','finalized')),
    severity TEXT NOT NULL CHECK (severity IN ('info','warn','error')),
    code TEXT NOT NULL,
    payload JSONB,
    correlation_id UUID
);

-- Create indexes for efficient worker polling and monitoring
CREATE INDEX IF NOT EXISTS idx_upload_jobs_status ON upload_pipeline.upload_jobs (status, created_at);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_document ON upload_pipeline.upload_jobs (document_id);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_correlation ON upload_pipeline.upload_jobs (correlation_id);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_processing_time ON upload_pipeline.upload_jobs (processing_started_at, processing_completed_at);

CREATE INDEX IF NOT EXISTS idx_chunk_buffer_document ON upload_pipeline.document_chunk_buffer (document_id);
CREATE INDEX IF NOT EXISTS idx_vector_buffer_document ON upload_pipeline.document_vector_buffer (document_id);
CREATE INDEX IF NOT EXISTS idx_vector_buffer_embedding_progress ON upload_pipeline.document_vector_buffer (document_id, embed_model, embed_version);

CREATE INDEX IF NOT EXISTS idx_events_job_ts ON upload_pipeline.events (job_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_doc_ts ON upload_pipeline.events (document_id, ts DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION upload_pipeline.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_upload_jobs_updated_at 
    BEFORE UPDATE ON upload_pipeline.upload_jobs 
    FOR EACH ROW EXECUTE FUNCTION upload_pipeline.update_updated_at_column();

-- Create function to generate deterministic chunk IDs
CREATE OR REPLACE FUNCTION upload_pipeline.generate_chunk_id(
    document_id UUID,
    chunker_name TEXT,
    chunker_version TEXT,
    chunk_ord INT
) RETURNS UUID AS $$
BEGIN
    -- Use UUIDv5 with namespace 6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42
    RETURN gen_random_uuid(); -- Placeholder - will be implemented in Python
END;
$$ LANGUAGE plpgsql;

-- Insert sample data for testing
INSERT INTO upload_pipeline.upload_jobs (
    job_id, user_id, document_id, status, raw_path, chunks_version, embed_model, embed_version
) VALUES (
    gen_random_uuid(),
    gen_random_uuid(),
    gen_random_uuid(),
    'uploaded',
    'storage://raw/test-user/test-doc.pdf',
    'markdown-simple@1',
    'text-embedding-3-small',
    '1'
) ON CONFLICT DO NOTHING;
