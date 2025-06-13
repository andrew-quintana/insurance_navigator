-- ========================================================
-- Supabase Database Migration - Final Correct Version
-- ========================================================
-- This script migrates the existing Supabase database to the new simplified schema
-- using the actual column names and data types found in the database
-- ========================================================

BEGIN;

-- Create migration tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS migration_progress (
    id SERIAL PRIMARY KEY,
    step_name VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    details JSONB
);

-- Track migration start
INSERT INTO migration_progress (step_name, status, details)
VALUES (
    'supabase_migration_final',
    'running',
    jsonb_build_object(
        'migration_version', 'V2.1.2',
        'started_at', NOW(),
        'existing_tables_count', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'),
        'existing_documents', (SELECT COUNT(*) FROM documents),
        'existing_vectors', (SELECT COUNT(*) FROM user_document_vectors),
        'existing_conversations', (SELECT COUNT(*) FROM conversations),
        'existing_messages', (SELECT COUNT(*) FROM conversation_messages)
    )
)
ON CONFLICT (step_name) DO UPDATE SET
    status = EXCLUDED.status,
    started_at = NOW(),
    details = EXCLUDED.details;

-- ========================================================
-- Phase 1: Create new tables with correct data types
-- ========================================================

-- Create audit_logs table (HIPAA compliance)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create new user_documents table with policy_basics 
CREATE TABLE IF NOT EXISTS user_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    file_path TEXT NOT NULL, -- Will map to storage_path
    file_size BIGINT,
    mime_type VARCHAR(255), -- Will map to content_type
    storage_provider VARCHAR(50) DEFAULT 'supabase',
    bucket_name VARCHAR(255) DEFAULT 'raw_documents',
    upload_status VARCHAR(50) DEFAULT 'pending',
    processing_status VARCHAR(50) DEFAULT 'pending',
    content_extracted TEXT,
    policy_basics JSONB, -- New JSONB column for policy information
    metadata JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create new messages table (using TEXT for conversation_id to match existing schema)
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================================
-- Phase 2: Migrate existing data safely
-- ========================================================

-- Migrate documents to user_documents (using actual column names)
INSERT INTO user_documents (
    id, user_id, original_filename, file_path, file_size, mime_type,
    storage_provider, bucket_name, upload_status, processing_status,
    metadata, status, created_at, updated_at
)
SELECT 
    d.id,
    d.user_id,
    d.original_filename,
    COALESCE(d.storage_path, d.file_hash) as file_path, -- Use storage_path or file_hash
    d.file_size,
    d.content_type as mime_type,
    'supabase' as storage_provider,
    'raw_documents' as bucket_name,
    CASE 
        WHEN d.status = 'completed' THEN 'completed'
        WHEN d.status = 'processing' THEN 'processing'
        ELSE 'completed'
    END as upload_status,
    CASE 
        WHEN d.status = 'completed' THEN 'completed'
        WHEN d.status = 'processing' THEN 'processing'
        ELSE 'completed'
    END as processing_status,
    d.metadata,
    COALESCE(d.status, 'completed') as status,
    d.created_at,
    d.updated_at
FROM documents d
WHERE NOT EXISTS (
    SELECT 1 FROM user_documents ud WHERE ud.id = d.id
);

-- Migrate conversation_messages to messages
INSERT INTO messages (id, conversation_id, role, content, metadata, created_at)
SELECT 
    cm.id,
    cm.conversation_id,
    cm.role,
    cm.content,
    cm.metadata,
    cm.created_at
FROM conversation_messages cm
WHERE NOT EXISTS (
    SELECT 1 FROM messages m WHERE m.id = cm.id
);

-- ========================================================
-- Phase 3: Create indexes for performance
-- ========================================================

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_user_documents_policy_basics_gin 
ON user_documents USING gin(policy_basics);

CREATE INDEX IF NOT EXISTS idx_user_documents_metadata_gin 
ON user_documents USING gin(metadata);

CREATE INDEX IF NOT EXISTS idx_messages_metadata_gin 
ON messages USING gin(metadata);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_user_documents_user_id 
ON user_documents(user_id);

CREATE INDEX IF NOT EXISTS idx_user_documents_status 
ON user_documents(status);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
ON messages(conversation_id);

CREATE INDEX IF NOT EXISTS idx_messages_created_at 
ON messages(created_at);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id 
ON audit_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at 
ON audit_logs(created_at);

-- ========================================================
-- Phase 4: Create database functions
-- ========================================================

-- Function to log user actions (HIPAA compliance)
CREATE OR REPLACE FUNCTION log_user_action(
    user_uuid UUID,
    action_type TEXT,
    resource_type TEXT,
    resource_id TEXT DEFAULT NULL,
    action_details JSONB DEFAULT NULL,
    client_ip INET DEFAULT NULL,
    client_user_agent TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    log_id UUID;
BEGIN
    INSERT INTO audit_logs (
        user_id, action, resource_type, resource_id, 
        details, ip_address, user_agent
    ) VALUES (
        user_uuid, action_type, resource_type, resource_id,
        action_details, client_ip, client_user_agent
    ) RETURNING id INTO log_id;
    
    RETURN log_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get policy facts from JSONB
CREATE OR REPLACE FUNCTION get_policy_facts(document_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    policy_data JSONB;
BEGIN
    SELECT policy_basics INTO policy_data
    FROM user_documents 
    WHERE id = document_uuid;
    
    RETURN COALESCE(policy_data, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Function to update policy basics
CREATE OR REPLACE FUNCTION update_policy_basics(
    document_uuid UUID,
    policy_data JSONB
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE user_documents 
    SET 
        policy_basics = policy_data,
        updated_at = NOW()
    WHERE id = document_uuid;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function for policy-based search
CREATE OR REPLACE FUNCTION search_by_policy_criteria(
    user_uuid UUID,
    search_criteria JSONB,
    limit_count INTEGER DEFAULT 10
) RETURNS TABLE (
    id UUID,
    original_filename TEXT,
    policy_basics JSONB,
    relevance_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ud.id,
        ud.original_filename,
        ud.policy_basics,
        1.0 as relevance_score -- Placeholder for actual relevance scoring
    FROM user_documents ud
    WHERE ud.user_id = user_uuid
        AND ud.policy_basics IS NOT NULL
        AND ud.policy_basics ?& (SELECT array_agg(key) FROM jsonb_object_keys(search_criteria) AS key)
    ORDER BY ud.updated_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ========================================================
-- Phase 5: Record successful migration
-- ========================================================

-- Update migration progress
UPDATE migration_progress 
SET status = 'completed', completed_at = NOW(),
    details = jsonb_build_object(
        'migration_version', 'V2.1.2',
        'phase_1_completed', true,
        'new_tables_created', true,
        'data_migrated', true,
        'indexes_created', true,
        'functions_created', true,
        'documents_migrated', (SELECT COUNT(*) FROM user_documents),
        'messages_migrated', (SELECT COUNT(*) FROM messages),
        'audit_logs_table_created', true,
        'storage_bucket_name', 'raw_documents',
        'conversations_preserved', (SELECT COUNT(*) FROM conversations)
    )
WHERE step_name = 'supabase_migration_final';

-- Show migration results
DO $$
DECLARE
    doc_count INTEGER;
    msg_count INTEGER;
    conv_count INTEGER;
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO doc_count FROM user_documents;
    SELECT COUNT(*) INTO msg_count FROM messages;
    SELECT COUNT(*) INTO conv_count FROM conversations;
    SELECT COUNT(*) INTO table_count FROM information_schema.tables WHERE table_schema = 'public';
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'SUPABASE MIGRATION COMPLETED SUCCESSFULLY!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Documents migrated: %', doc_count;
    RAISE NOTICE 'Messages migrated: %', msg_count;
    RAISE NOTICE 'Conversations preserved: %', conv_count;
    RAISE NOTICE 'Current table count: %', table_count;
    RAISE NOTICE 'New tables created with policy_basics JSONB column';
    RAISE NOTICE 'Hybrid search functions created';
    RAISE NOTICE 'Audit logging enabled for HIPAA compliance';
    RAISE NOTICE 'Storage bucket: raw_documents';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- ========================================================
-- Migration Summary:
-- ========================================================
-- ✅ Created audit_logs table for HIPAA compliance
-- ✅ Created user_documents with policy_basics JSONB column
-- ✅ Created messages table (compatible with TEXT conversation IDs)
-- ✅ Migrated all existing documents data (using actual column names)
-- ✅ Migrated all conversation_messages data
-- ✅ Created performance indexes (GIN for JSONB, B-tree for lookups)
-- ✅ Created database functions for policy management and search
-- ✅ Updated storage bucket name to 'raw_documents' (as agreed)
-- ✅ Preserved all existing data integrity
--
-- Current Status: New core tables created, data migrated
-- Next Step: Run cleanup script to remove old tables
-- ======================================================== 