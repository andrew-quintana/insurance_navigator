-- ================================================
-- V2.0.1 - Fix Documents Table Compatibility
-- Rename user_documents to documents and apply V2.0.0 changes
-- ================================================

-- First, rename user_documents to documents
ALTER TABLE user_documents RENAME TO documents;

-- Add the policy_basics JSONB column that the app expects
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS policy_basics JSONB DEFAULT '{}';

-- Create GIN index for fast JSONB queries
CREATE INDEX IF NOT EXISTS idx_documents_policy_basics_gin 
ON documents USING GIN (policy_basics);

-- Create specialized indexes for common policy lookups
CREATE INDEX IF NOT EXISTS idx_documents_policy_type 
ON documents ((policy_basics->>'policy_type'));

CREATE INDEX IF NOT EXISTS idx_documents_coverage_amount 
ON documents ((policy_basics->>'coverage_amount'));

CREATE INDEX IF NOT EXISTS idx_documents_effective_date 
ON documents ((policy_basics->>'effective_date'));

-- Rename user_document_vectors to document_vectors (as migration expects)
ALTER TABLE user_document_vectors RENAME TO document_vectors;

-- Ensure document_vectors has proper indexes
CREATE INDEX IF NOT EXISTS idx_document_vectors_document_id 
ON document_vectors (document_id);

CREATE INDEX IF NOT EXISTS idx_document_vectors_user_id 
ON document_vectors (user_id);

-- Add missing columns that the app might expect
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS document_type VARCHAR(50) DEFAULT 'policy',
ADD COLUMN IF NOT EXISTS content_summary TEXT,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Add missing columns that conversation system expects
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS conversation_type VARCHAR(50) DEFAULT 'general',
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Add missing columns for users
ALTER TABLE users
ADD COLUMN IF NOT EXISTS user_role VARCHAR(50) DEFAULT 'patient',
ADD COLUMN IF NOT EXISTS access_level INTEGER DEFAULT 1;

-- Fix audit_logs table to match what the migration expects
ALTER TABLE audit_logs
ADD COLUMN IF NOT EXISTS table_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS record_id TEXT,
ADD COLUMN IF NOT EXISTS old_values JSONB,
ADD COLUMN IF NOT EXISTS new_values JSONB,
ADD COLUMN IF NOT EXISTS ip_address INET,
ADD COLUMN IF NOT EXISTS user_agent TEXT;

-- Create helper functions for policy operations
CREATE OR REPLACE FUNCTION update_policy_basics(
    doc_id UUID,
    policy_data JSONB,
    user_id_param UUID DEFAULT NULL
) RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    old_data JSONB;
BEGIN
    -- Get old data for audit
    SELECT policy_basics INTO old_data 
    FROM documents WHERE id = doc_id;
    
    -- Update policy basics
    UPDATE documents 
    SET policy_basics = policy_data,
        updated_at = NOW()
    WHERE id = doc_id;
    
    -- Log the change for HIPAA compliance (only if audit_logs has the right columns)
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'table_name') THEN
        INSERT INTO audit_logs (user_id, action, table_name, record_id, old_values, new_values)
        VALUES (user_id_param, 'UPDATE_POLICY_BASICS', 'documents', doc_id::TEXT, 
                old_data, policy_data);
    END IF;
    
    RETURN FOUND;
END;
$$;

-- Function to get policy facts (fast JSONB lookup)
CREATE OR REPLACE FUNCTION get_policy_facts(
    doc_id UUID
) RETURNS JSONB
LANGUAGE sql
STABLE
AS $$
    SELECT policy_basics 
    FROM documents 
    WHERE id = doc_id;
$$;

-- Function to search by policy criteria (hybrid approach)
CREATE OR REPLACE FUNCTION search_by_policy_criteria(
    criteria JSONB,
    user_id_param UUID DEFAULT NULL,
    limit_param INTEGER DEFAULT 10
) RETURNS TABLE (
    document_id UUID,
    policy_basics JSONB,
    relevance_score FLOAT
) 
LANGUAGE sql
STABLE
AS $$
    SELECT 
        d.id as document_id,
        d.policy_basics,
        -- Simple relevance scoring based on matching criteria
        (CASE 
            WHEN d.policy_basics @> criteria THEN 1.0
            WHEN d.policy_basics ? ANY(SELECT jsonb_object_keys(criteria)) THEN 0.7
            ELSE 0.3
        END) as relevance_score
    FROM documents d
    WHERE d.user_id = COALESCE(user_id_param, d.user_id)
        AND d.policy_basics IS NOT NULL
        AND (d.policy_basics @> criteria 
             OR d.policy_basics ?| ARRAY(SELECT jsonb_object_keys(criteria)))
    ORDER BY relevance_score DESC, d.updated_at DESC
    LIMIT limit_param;
$$;

-- Core performance indexes for MVP operations
CREATE INDEX IF NOT EXISTS idx_documents_user_type_active 
ON documents (user_id, document_type, is_active);

CREATE INDEX IF NOT EXISTS idx_conversations_user_active 
ON conversations (user_id, is_active, updated_at DESC);

-- Partial indexes for common queries
CREATE INDEX IF NOT EXISTS idx_documents_active_recent 
ON documents (updated_at DESC) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_conversations_recent_active 
ON conversations (created_at DESC) WHERE is_active = true;

-- Log successful migration
INSERT INTO audit_logs (action, created_at)
VALUES ('SCHEMA_MIGRATION_V2.0.1_COMPATIBILITY', NOW()); 