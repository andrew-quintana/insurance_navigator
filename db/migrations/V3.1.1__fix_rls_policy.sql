-- =============================================================================
-- FIX RLS POLICY V3.1.1
-- Description: Fix RLS policy on document_vectors table
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- Drop existing policy
DROP POLICY IF EXISTS service_role_access_policy ON document_vectors;

-- Create new policy with correct function reference
CREATE POLICY service_role_access_policy ON document_vectors
    FOR ALL
    TO authenticated
    USING (
        is_service_role() OR
        (user_id = uid() AND document_source_type = 'user_document') OR
        document_source_type = 'regulatory_document'
    );

-- Record migration completion
INSERT INTO schema_migrations (version) VALUES ('V3.1.1') ON CONFLICT (version) DO NOTHING;

COMMIT; 