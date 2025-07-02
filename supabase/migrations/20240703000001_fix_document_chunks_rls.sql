-- =============================================================================
-- FIX DOCUMENT CHUNKS RLS POLICIES
-- Description: Add missing RLS policies for document chunks table
-- Version: 20240703_1
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

DROP POLICY IF EXISTS "Users can read own document chunks" ON document_chunks;
DROP POLICY IF EXISTS "Service role has full access to document chunks" ON document_chunks;

-- =============================================================================
-- STEP 2: CREATE COMPREHENSIVE POLICIES
-- =============================================================================

-- Allow users to read their own document chunks
CREATE POLICY "Users can read own document chunks" ON document_chunks
    FOR SELECT
    TO authenticated
    USING (EXISTS (
        SELECT 1 FROM documents
        WHERE documents.id = document_chunks.document_id
        AND documents.user_id = auth.uid()
    ));

-- Allow users to insert chunks for their own documents
CREATE POLICY "Users can insert own document chunks" ON document_chunks
    FOR INSERT
    TO authenticated
    WITH CHECK (EXISTS (
        SELECT 1 FROM documents
        WHERE documents.id = document_chunks.document_id
        AND documents.user_id = auth.uid()
    ));

-- Allow users to update chunks for their own documents
CREATE POLICY "Users can update own document chunks" ON document_chunks
    FOR UPDATE
    TO authenticated
    USING (EXISTS (
        SELECT 1 FROM documents
        WHERE documents.id = document_chunks.document_id
        AND documents.user_id = auth.uid()
    ));

-- Allow users to delete chunks for their own documents
CREATE POLICY "Users can delete own document chunks" ON document_chunks
    FOR DELETE
    TO authenticated
    USING (EXISTS (
        SELECT 1 FROM documents
        WHERE documents.id = document_chunks.document_id
        AND documents.user_id = auth.uid()
    ));

-- Service role has full access to document chunks
CREATE POLICY "Service role has full access to document chunks" ON document_chunks
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- =============================================================================
-- STEP 3: VERIFY RLS IS ENABLED
-- =============================================================================

-- Ensure RLS is enabled
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

COMMIT; 