-- =============================================================================
-- CREATE BASE TABLES V3.0.0.0
-- Description: Create the base tables for the application
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    original_filename TEXT NOT NULL,
    document_type TEXT NOT NULL DEFAULT 'user_uploaded',
    content_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    jurisdiction TEXT,
    program TEXT[],
    effective_date DATE,
    expiration_date DATE,
    source_url TEXT,
    tags TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create encryption_keys table
CREATE TABLE IF NOT EXISTS encryption_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    key_data BYTEA NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Record migration completion
INSERT INTO schema_migrations (version) VALUES ('V3.0.0.0') ON CONFLICT (version) DO NOTHING;

COMMIT; 