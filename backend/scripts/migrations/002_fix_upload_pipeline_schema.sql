-- 002_fix_upload_pipeline_schema.sql
-- Fix upload_pipeline schema to match CONTEXT001.md specifications

BEGIN;

-- Drop existing incorrect tables
DROP TABLE IF EXISTS upload_pipeline.document_vector_buffer CASCADE;
DROP TABLE IF EXISTS upload_pipeline.document_chunk_buffer CASCADE;
DROP TABLE IF EXISTS upload_pipeline.events CASCADE;
DROP TABLE IF EXISTS upload_pipeline.upload_jobs CASCADE;

-- Create documents table (was missing)
CREATE TABLE IF NOT EXISTS upload_pipeline.documents (
    document_id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    filename text NOT NULL,
    mime text NOT NULL,
    bytes_len bigint NOT NULL,
    file_sha256 text NOT NULL,
    parsed_sha256 text,
    raw_path text NOT NULL,
    parsed_path text,
    processing_status text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Indexes for documents table
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_filehash
    ON upload_pipeline.documents (user_id, file_sha256);
CREATE INDEX IF NOT EXISTS ix_documents_user 
    ON upload_pipeline.documents (user_id);

-- Create upload_jobs table with correct schema
CREATE TABLE IF NOT EXISTS upload_pipeline.upload_jobs (
    job_id uuid PRIMARY KEY,
    document_id uuid NOT NULL REFERENCES upload_pipeline.documents(document_id),
    stage text NOT NULL CHECK (stage IN ('queued','job_validated','parsing','parsed','parse_validated','chunking','chunks_buffered','chunked','embedding','embeddings_buffered','embedded')),
    state text NOT NULL CHECK (state IN ('queued','working','retryable','done','deadletter')),
    retry_count int DEFAULT 0,
    idempotency_key text,
    payload jsonb,
    last_error jsonb,
    claimed_by text,
    claimed_at timestamptz,
    started_at timestamptz,
    finished_at timestamptz,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Indexes for upload_jobs table
CREATE UNIQUE INDEX IF NOT EXISTS uq_job_doc_stage_active
    ON upload_pipeline.upload_jobs (document_id, stage)
    WHERE state IN ('queued','working','retryable');
CREATE INDEX IF NOT EXISTS ix_jobs_state 
    ON upload_pipeline.upload_jobs (state, created_at);

-- Create document_chunks table with co-located embeddings
CREATE TABLE IF NOT EXISTS upload_pipeline.document_chunks (
    chunk_id uuid PRIMARY KEY,
    document_id uuid NOT NULL REFERENCES upload_pipeline.documents(document_id),
    chunker_name text NOT NULL,
    chunker_version text NOT NULL,
    chunk_ord int NOT NULL,
    text text NOT NULL,
    chunk_sha text NOT NULL,
    embed_model text NOT NULL,
    embed_version text NOT NULL,
    vector_dim int NOT NULL CHECK (vector_dim = 1536),
    embedding vector(1536) NOT NULL,
    embed_updated_at timestamptz DEFAULT now(),
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    UNIQUE (document_id, chunker_name, chunker_version, chunk_ord)
);

-- Note: HNSW index will be created separately after vector extension is properly configured
-- CREATE INDEX IF NOT EXISTS idx_hnsw_chunks_te3s_v1
--     ON upload_pipeline.document_chunks USING hnsw (embedding)
--     WHERE embed_model='text-embedding-3-small' AND embed_version='1';

-- Storage optimization
ALTER TABLE upload_pipeline.document_chunks SET (fillfactor=70);

-- Create document_vector_buffer table for write-ahead buffer
CREATE TABLE IF NOT EXISTS upload_pipeline.document_vector_buffer (
    buffer_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id uuid NOT NULL REFERENCES upload_pipeline.document_chunks(chunk_id),
    embed_model text NOT NULL,
    embed_version text NOT NULL,
    vector_dim int NOT NULL CHECK (vector_dim = 1536),
    embedding vector(1536) NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- Create events table for comprehensive logging
CREATE TABLE IF NOT EXISTS upload_pipeline.events (
    event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL REFERENCES upload_pipeline.upload_jobs(job_id),
    document_id uuid NOT NULL REFERENCES upload_pipeline.documents(document_id),
    ts timestamptz DEFAULT now(),
    type text NOT NULL CHECK (type IN ('stage_started','stage_done','retry','error','finalized')),
    severity text NOT NULL CHECK (severity IN ('info','warn','error')),
    code text NOT NULL,
    payload jsonb,
    correlation_id uuid
);

-- Indexes for events table
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
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON upload_pipeline.documents 
    FOR EACH ROW EXECUTE FUNCTION upload_pipeline.update_updated_at_column();

CREATE TRIGGER update_upload_jobs_updated_at 
    BEFORE UPDATE ON upload_pipeline.upload_jobs 
    FOR EACH ROW EXECUTE FUNCTION upload_pipeline.update_updated_at_column();

CREATE TRIGGER update_document_chunks_updated_at 
    BEFORE UPDATE ON upload_pipeline.document_chunks 
    FOR EACH ROW EXECUTE FUNCTION upload_pipeline.update_updated_at_column();

-- Insert sample data for testing
INSERT INTO upload_pipeline.documents (
    document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path
) VALUES (
    gen_random_uuid(),
    gen_random_uuid(),
    'test-document.pdf',
    'application/pdf',
    1024000,
    'test-sha256-hash-for-testing-purposes-only',
    'storage://raw/test-user/test-doc.pdf'
) ON CONFLICT DO NOTHING;

COMMIT;
