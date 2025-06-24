-- Create document processing status table
CREATE TABLE IF NOT EXISTS document_processing_status (
    document_id UUID PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    total_chunks INTEGER NOT NULL,
    processed_chunks INTEGER[] DEFAULT '{}',
    status TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    overlap INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index for status queries
CREATE INDEX IF NOT EXISTS idx_doc_processing_status ON document_processing_status(status);

-- Add trigger to update updated_at
CREATE OR REPLACE FUNCTION update_document_processing_status_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_doc_processing_status_timestamp
    BEFORE UPDATE ON document_processing_status
    FOR EACH ROW
    EXECUTE FUNCTION update_document_processing_status_updated_at(); 