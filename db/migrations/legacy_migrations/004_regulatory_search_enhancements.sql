-- Regulatory Search Enhancements Migration
-- Version: 004
-- Description: Add fields for web search and caching functionality

-- Add new columns to regulatory_documents table
ALTER TABLE regulatory_documents 
ADD COLUMN IF NOT EXISTS source_last_checked TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS content_hash TEXT,
ADD COLUMN IF NOT EXISTS extraction_method TEXT DEFAULT 'manual',
ADD COLUMN IF NOT EXISTS priority_score FLOAT,
ADD COLUMN IF NOT EXISTS search_metadata JSONB DEFAULT '{}';

-- Create indexes for new fields
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_content_hash ON regulatory_documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_source_last_checked ON regulatory_documents(source_last_checked);
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_extraction_method ON regulatory_documents(extraction_method);
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_search_metadata ON regulatory_documents USING gin(search_metadata);

-- Add comments for new fields
COMMENT ON COLUMN regulatory_documents.source_last_checked IS 'Last time the source URL was checked for updates';
COMMENT ON COLUMN regulatory_documents.content_hash IS 'MD5 hash of document content for duplicate detection';
COMMENT ON COLUMN regulatory_documents.extraction_method IS 'Method used to extract content (manual, web_search_automated, scheduled_crawl)';
COMMENT ON COLUMN regulatory_documents.priority_score IS 'Search ranking priority score (0.0-1.0)';
COMMENT ON COLUMN regulatory_documents.search_metadata IS 'Additional metadata from search and extraction process';

-- Create a view for search-ready documents
CREATE OR REPLACE VIEW regulatory_documents_searchable AS
SELECT 
    document_id,
    title,
    jurisdiction,
    program,
    document_type,
    source_url,
    tags,
    priority_score,
    content_hash,
    extraction_method,
    created_at,
    updated_at,
    source_last_checked,
    CASE 
        WHEN source_last_checked IS NULL THEN 'never_checked'
        WHEN source_last_checked < NOW() - INTERVAL '7 days' THEN 'needs_update'
        ELSE 'current'
    END as freshness_status
FROM regulatory_documents
WHERE source_url IS NOT NULL;

-- Create a function to mark documents for refresh
CREATE OR REPLACE FUNCTION mark_document_for_refresh(doc_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE regulatory_documents 
    SET source_last_checked = NULL,
        search_metadata = search_metadata || '{"needs_refresh": true}'::jsonb
    WHERE document_id = doc_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get stale documents
CREATE OR REPLACE FUNCTION get_stale_documents(check_interval INTERVAL DEFAULT '7 days')
RETURNS TABLE(
    document_id UUID,
    title TEXT,
    source_url TEXT,
    last_checked TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rd.document_id,
        rd.title,
        rd.source_url,
        rd.source_last_checked
    FROM regulatory_documents rd
    WHERE rd.source_url IS NOT NULL
    AND (
        rd.source_last_checked IS NULL 
        OR rd.source_last_checked < NOW() - check_interval
    )
    ORDER BY rd.source_last_checked ASC NULLS FIRST;
END;
$$ LANGUAGE plpgsql;

-- Update existing documents to set default extraction method
UPDATE regulatory_documents 
SET extraction_method = 'manual'
WHERE extraction_method IS NULL;

-- Grant permissions for the new functions
GRANT EXECUTE ON FUNCTION mark_document_for_refresh(UUID) TO regulatory_agent;
GRANT EXECUTE ON FUNCTION get_stale_documents(INTERVAL) TO regulatory_agent;
GRANT SELECT ON regulatory_documents_searchable TO regulatory_agent; 