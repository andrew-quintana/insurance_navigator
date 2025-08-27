-- Integration Schema Setup for Upload Pipeline + Agent Integration
-- This file creates the upload_pipeline schema with all necessary tables and indexes

-- Create the upload_pipeline schema
CREATE SCHEMA IF NOT EXISTS upload_pipeline;

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Core upload processing tables
CREATE TABLE IF NOT EXISTS upload_pipeline.documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    filename TEXT NOT NULL,
    document_type TEXT DEFAULT 'policy',
    file_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS upload_pipeline.upload_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES upload_pipeline.documents(document_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'uploaded', 'parse_queued', 'parsed', 'parse_validated',
        'chunking', 'chunks_stored', 'embedding_queued', 
        'embedding_in_progress', 'embeddings_stored', 'complete',
        'failed_parse', 'failed_chunking', 'failed_embedding'
    )),
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Final vector storage (Agent RAG Target)
CREATE TABLE IF NOT EXISTS upload_pipeline.document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES upload_pipeline.documents(document_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_metadata JSONB DEFAULT '{}',
    embedding_vector vector(1536),
    chunk_index INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for RAG performance
CREATE INDEX IF NOT EXISTS idx_document_chunks_user_id ON upload_pipeline.document_chunks (user_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON upload_pipeline.document_chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON upload_pipeline.document_chunks USING ivfflat (embedding_vector vector_cosine_ops);

-- Create indexes for upload pipeline performance
CREATE INDEX IF NOT EXISTS idx_upload_jobs_user_id ON upload_pipeline.upload_jobs (user_id);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_status ON upload_pipeline.upload_jobs (status);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_document_id ON upload_pipeline.upload_jobs (document_id);

-- Create indexes for documents table
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON upload_pipeline.documents (user_id);
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON upload_pipeline.documents (document_type);

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

-- Create function to check document availability by type
CREATE OR REPLACE FUNCTION upload_pipeline.check_document_availability(user_uuid UUID)
RETURNS TABLE(document_type TEXT, document_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT d.document_type, COUNT(*) as document_count
    FROM upload_pipeline.documents d
    WHERE d.user_id = user_uuid
      AND d.document_id IN (
        SELECT document_id 
        FROM upload_pipeline.upload_jobs 
        WHERE status = 'complete'
      )
    GROUP BY d.document_type;
END;
$$ LANGUAGE plpgsql;

-- Create function to get RAG-ready documents
CREATE OR REPLACE FUNCTION upload_pipeline.get_rag_ready_documents(user_uuid UUID)
RETURNS TABLE(
    document_id UUID,
    filename TEXT,
    chunk_count BIGINT,
    avg_vector_norm FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.document_id,
        d.filename,
        COUNT(dc.chunk_id) as chunk_count,
        AVG(vector_norm(dc.embedding_vector)) as avg_vector_norm
    FROM upload_pipeline.documents d
    JOIN upload_pipeline.upload_jobs uj ON d.document_id = uj.document_id
    LEFT JOIN upload_pipeline.document_chunks dc ON d.document_id = dc.document_id
    WHERE uj.status = 'complete' AND d.user_id = user_uuid
    GROUP BY d.document_id, d.filename
    HAVING COUNT(dc.chunk_id) > 0;
END;
$$ LANGUAGE plpgsql;

-- Insert sample test data for integration testing
INSERT INTO upload_pipeline.documents (document_id, user_id, filename, document_type, file_path) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'sample_policy.pdf', 'policy', '/test/sample_policy.pdf'),
    ('550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'complex_policy.pdf', 'policy', '/test/complex_policy.pdf')
ON CONFLICT (document_id) DO NOTHING;

INSERT INTO upload_pipeline.upload_jobs (job_id, document_id, user_id, status, processing_completed_at) VALUES
    ('550e8400-e29b-41d4-a716-446655440011', '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'complete', now()),
    ('550e8400-e29b-41d4-a716-446655440012', '550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'complete', now())
ON CONFLICT (job_id) DO NOTHING;

-- Insert sample chunks with mock embeddings for testing (1536-dimensional vectors)
INSERT INTO upload_pipeline.document_chunks (chunk_id, document_id, user_id, chunk_text, chunk_metadata, embedding_vector, chunk_index) VALUES
    ('550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'This policy provides coverage for medical expenses up to $10,000 per year.', '{"section": "coverage", "page": 1}', array_fill(0.1, ARRAY[1536])::vector(1536), 1),
    ('550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'The deductible is $500 per individual or $1,000 per family.', '{"section": "deductible", "page": 2}', array_fill(0.2, ARRAY[1536])::vector(1536), 2),
    ('550e8400-e29b-41d4-a716-446655440023', '550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'This comprehensive policy includes dental and vision coverage.', '{"section": "benefits", "page": 1}', array_fill(0.3, ARRAY[1536])::vector(1536), 1)
ON CONFLICT (chunk_id) DO NOTHING;

-- Grant permissions
GRANT USAGE ON SCHEMA upload_pipeline TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA upload_pipeline TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA upload_pipeline TO postgres;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA upload_pipeline TO postgres;
