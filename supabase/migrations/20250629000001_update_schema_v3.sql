-- =============================================================================
-- SCHEMA UPDATE MIGRATION V3.0.0
-- Description: Update schema to match new requirements while preserving functionality
-- =============================================================================

BEGIN;

-- =============================================================================
-- EXTENSIONS
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- DOCUMENT MANAGEMENT SYSTEM
-- =============================================================================

-- Documents table - Core document storage
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    storage_path TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending',
    extracted_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Additional tracking fields
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    error_message TEXT,
    error_details JSONB,
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100)
);

-- Document vectors table
CREATE TABLE IF NOT EXISTS public.document_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    content_embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

-- Processing jobs table
CREATE TABLE IF NOT EXISTS public.processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    error_details JSONB,
    payload JSONB DEFAULT '{}'::jsonb,
    result JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON public.documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON public.documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_storage_path ON public.documents(storage_path);

-- Document vectors indexes
CREATE INDEX IF NOT EXISTS idx_document_vectors_document_id ON public.document_vectors(document_id);
CREATE INDEX IF NOT EXISTS idx_document_vectors_embedding ON public.document_vectors USING ivfflat (content_embedding vector_cosine_ops);

-- Processing jobs indexes
CREATE INDEX IF NOT EXISTS idx_processing_jobs_document_id ON public.processing_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON public.processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_type ON public.processing_jobs(job_type);

-- =============================================================================
-- RLS POLICIES
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_vectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.processing_jobs ENABLE ROW LEVEL SECURITY;

-- Documents policies
CREATE POLICY "Users can view their own documents"
    ON public.documents FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own documents"
    ON public.documents FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own documents"
    ON public.documents FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role has full access to documents"
    ON public.documents FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Document vectors policies
CREATE POLICY "Users can view vectors of their documents"
    ON public.document_vectors FOR SELECT
    TO authenticated
    USING (EXISTS (
        SELECT 1 FROM public.documents
        WHERE documents.id = document_vectors.document_id
        AND documents.user_id = auth.uid()
    ));

CREATE POLICY "Service role has full access to vectors"
    ON public.document_vectors FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Processing jobs policies
CREATE POLICY "Users can view jobs for their documents"
    ON public.processing_jobs FOR SELECT
    TO authenticated
    USING (EXISTS (
        SELECT 1 FROM public.documents
        WHERE documents.id = processing_jobs.document_id
        AND documents.user_id = auth.uid()
    ));

CREATE POLICY "Service role has full access to jobs"
    ON public.processing_jobs FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Document status update function
CREATE OR REPLACE FUNCTION public.update_document_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Update document status based on job status
    IF NEW.status = 'completed' THEN
        UPDATE public.documents
        SET status = 'completed',
            processing_completed_at = NOW(),
            progress_percentage = 100
        WHERE id = NEW.document_id;
    ELSIF NEW.status = 'failed' THEN
        UPDATE public.documents
        SET status = 'failed',
            error_message = NEW.error_message,
            error_details = NEW.error_details
        WHERE id = NEW.document_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update timestamps
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON public.documents
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_document_vectors_updated_at
    BEFORE UPDATE ON public.document_vectors
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_processing_jobs_updated_at
    BEFORE UPDATE ON public.processing_jobs
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Update document status on job completion
CREATE TRIGGER update_document_status_on_job_change
    AFTER UPDATE OF status ON public.processing_jobs
    FOR EACH ROW
    WHEN (NEW.status IN ('completed', 'failed'))
    EXECUTE FUNCTION public.update_document_status();

-- =============================================================================
-- GRANTS
-- =============================================================================

-- Grant access to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT, INSERT ON public.documents TO authenticated;
GRANT SELECT ON public.document_vectors TO authenticated;
GRANT SELECT ON public.processing_jobs TO authenticated;

-- Grant full access to service role
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO service_role;

COMMIT; 