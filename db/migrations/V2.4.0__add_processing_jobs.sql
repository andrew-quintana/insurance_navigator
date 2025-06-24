-- Add processing jobs table for background task management
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Add indexes for common queries
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT valid_job_type CHECK (job_type IN ('llamaparse', 'vector_generation', 'chunking'))
);

CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs (status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_type ON processing_jobs (job_type);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_created ON processing_jobs (created_at DESC);

-- Add document vectors table for storing embeddings
CREATE TABLE IF NOT EXISTS document_vectors (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_embedding vector(1536) NOT NULL,
    chunk_metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Add indexes for vector similarity search
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_document_vectors_document ON document_vectors (document_id);
CREATE INDEX IF NOT EXISTS idx_document_vectors_user ON document_vectors (user_id);

-- Add vector similarity search index
CREATE INDEX IF NOT EXISTS idx_document_vectors_embedding ON document_vectors 
USING ivfflat (chunk_embedding vector_cosine_ops)
WITH (lists = 100); 