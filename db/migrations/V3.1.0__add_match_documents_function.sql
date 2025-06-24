-- =============================================================================
-- ADD MATCH_DOCUMENTS FUNCTION V3.1.0
-- Description: Add vector similarity search function
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- Create the match_documents function
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float,
    match_count int
)
RETURNS TABLE (
    encrypted_chunk_text text,
    similarity float,
    document_record_id uuid,
    regulatory_document_id uuid,
    document_source_type text
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dv.encrypted_chunk_text,
        1 - (dv.content_embedding <=> query_embedding) as similarity,
        dv.document_record_id,
        dv.regulatory_document_id,
        dv.document_source_type
    FROM document_vectors dv
    WHERE 1 - (dv.content_embedding <=> query_embedding) > match_threshold
        AND dv.is_active = true
    ORDER BY dv.content_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION match_documents(vector(1536), float, int) TO authenticated;

-- Create RLS policy to allow service role to access document_vectors
ALTER TABLE document_vectors ENABLE ROW LEVEL SECURITY;

CREATE POLICY service_role_access_policy ON document_vectors
    FOR ALL
    TO authenticated
    USING (
        -- Allow service role to access all records
        (SELECT is_service_role() FROM auth.jwt())
        OR
        -- Allow users to access their own records
        (user_id = auth.uid() AND document_source_type = 'user_document')
        OR
        -- Allow access to regulatory documents
        (document_source_type = 'regulatory_document')
    );

-- Record migration completion
INSERT INTO schema_migrations (version) VALUES ('V3.1.0') ON CONFLICT (version) DO NOTHING;

COMMIT;
 