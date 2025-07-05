-- =============================================================================
-- ADD MONITORING SCHEMA
-- Description: Add monitoring tables and policies
-- Version: 20240703_4
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- =============================================================================
-- STEP 1: DROP EXISTING POLICIES
-- =============================================================================

DROP POLICY IF EXISTS "Service role has full access to processing logs" ON public.processing_logs;
DROP POLICY IF EXISTS "Users can read own document logs" ON public.processing_logs;

-- =============================================================================
-- STEP 2: CREATE OR UPDATE TABLES
-- =============================================================================

-- Create monitoring table in public schema
CREATE TABLE IF NOT EXISTS public.processing_logs (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    document_id uuid REFERENCES public.documents(id) ON DELETE CASCADE,
    stage text NOT NULL,
    status text NOT NULL,
    error_message text,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_processing_logs_document_id ON public.processing_logs(document_id);
CREATE INDEX IF NOT EXISTS idx_processing_logs_stage ON public.processing_logs(stage);
CREATE INDEX IF NOT EXISTS idx_processing_logs_status ON public.processing_logs(status);
CREATE INDEX IF NOT EXISTS idx_processing_logs_created_at ON public.processing_logs(created_at);

-- Add RLS policies
ALTER TABLE public.processing_logs ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role has full access to processing logs"
ON public.processing_logs
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Allow users to read their own document logs
CREATE POLICY "Users can read own document logs"
ON public.processing_logs
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.documents
        WHERE documents.id = processing_logs.document_id
        AND documents.user_id = auth.uid()
    )
);

-- Add trigger for updated_at
DROP TRIGGER IF EXISTS update_processing_logs_updated_at ON public.processing_logs;
CREATE TRIGGER update_processing_logs_updated_at
    BEFORE UPDATE ON public.processing_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create monitoring schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Create edge function logs table
CREATE TABLE IF NOT EXISTS monitoring.edge_function_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    function_name TEXT NOT NULL,
    request_id TEXT,
    execution_time_ms INTEGER,
    memory_usage_mb FLOAT,
    status TEXT,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Add index for faster querying
CREATE INDEX IF NOT EXISTS idx_edge_function_logs_function_name 
ON monitoring.edge_function_logs(function_name);

-- Add index for timestamp-based queries
CREATE INDEX IF NOT EXISTS idx_edge_function_logs_created_at 
ON monitoring.edge_function_logs(created_at);

-- Grant access to the monitoring schema
GRANT USAGE ON SCHEMA monitoring TO service_role;
GRANT ALL ON ALL TABLES IN SCHEMA monitoring TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA monitoring TO service_role;

-- Create helper function to log edge function execution
CREATE OR REPLACE FUNCTION monitoring.log_edge_function(
    p_function_name TEXT,
    p_request_id TEXT,
    p_execution_time_ms INTEGER,
    p_memory_usage_mb FLOAT,
    p_status TEXT,
    p_error_message TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO monitoring.edge_function_logs
        (function_name, request_id, execution_time_ms, memory_usage_mb, status, error_message, metadata)
    VALUES
        (p_function_name, p_request_id, p_execution_time_ms, p_memory_usage_mb, p_status, p_error_message, p_metadata)
    RETURNING id INTO v_log_id;
    
    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMIT; 