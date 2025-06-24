-- =============================================================================
-- SETUP PREREQUISITES V3.0.0
-- Description: Set up required tables and extensions
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- Create schema_migrations table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create vector extension if it doesn't exist
CREATE EXTENSION IF NOT EXISTS vector;

-- Record migration completion
INSERT INTO schema_migrations (version) VALUES ('V3.0.0') ON CONFLICT (version) DO NOTHING;

COMMIT; 