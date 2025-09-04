-- Enable vector extension for embeddings
-- This must be run before any vector operations

-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify the extension is enabled
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'Vector extension could not be enabled. Please contact support.';
    ELSE
        RAISE NOTICE 'Vector extension enabled successfully';
    END IF;
END $$;
