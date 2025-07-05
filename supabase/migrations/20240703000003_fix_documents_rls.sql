-- =============================================================================
-- FIX DOCUMENTS RLS POLICIES
-- Description: Enable RLS and add policies for documents table
-- Version: 20240703_3
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

DROP POLICY IF EXISTS "Users can read own documents" ON documents;
DROP POLICY IF EXISTS "Users can insert own documents" ON documents;
DROP POLICY IF EXISTS "Users can update own documents" ON documents;
DROP POLICY IF EXISTS "Users can delete own documents" ON documents;
DROP POLICY IF EXISTS "Service role has full access to documents" ON documents;

-- =============================================================================
-- STEP 2: CREATE COMPREHENSIVE POLICIES
-- =============================================================================

-- Allow users to read their own documents
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'documents' 
        AND policyname = 'Users can read own documents'
    ) THEN
        EXECUTE 'CREATE POLICY "Users can read own documents" ON documents
            FOR SELECT
            TO authenticated
            USING (user_id = auth.uid())';
    END IF;
END $$;

-- Allow users to insert their own documents
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'documents' 
        AND policyname = 'Users can insert own documents'
    ) THEN
        EXECUTE 'CREATE POLICY "Users can insert own documents" ON documents
            FOR INSERT
            TO authenticated
            WITH CHECK (user_id = auth.uid())';
    END IF;
END $$;

-- Allow users to update their own documents
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'documents' 
        AND policyname = 'Users can update own documents'
    ) THEN
        EXECUTE 'CREATE POLICY "Users can update own documents" ON documents
            FOR UPDATE
            TO authenticated
            USING (user_id = auth.uid())';
    END IF;
END $$;

-- Allow users to delete their own documents
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'documents' 
        AND policyname = 'Users can delete own documents'
    ) THEN
        EXECUTE 'CREATE POLICY "Users can delete own documents" ON documents
            FOR DELETE
            TO authenticated
            USING (user_id = auth.uid())';
    END IF;
END $$;

-- Service role has full access to documents
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'documents' 
        AND policyname = 'Service role has full access to documents'
    ) THEN
        EXECUTE 'CREATE POLICY "Service role has full access to documents" ON documents
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true)';
    END IF;
END $$;

-- =============================================================================
-- STEP 3: VERIFY RLS IS ENABLED
-- =============================================================================

-- Ensure RLS is enabled
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Check documents table constraints
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'documents'::regclass;

COMMIT; 