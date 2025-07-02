-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create document_chunks table
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

-- Create document_vectors table
CREATE TABLE document_vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE CASCADE,
    vector_data VECTOR(1536) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_vectors_chunk_id ON document_vectors(chunk_id);

-- Create trigger for document_chunks table
CREATE TRIGGER update_document_chunks_updated_at
    BEFORE UPDATE ON document_chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for document_vectors table
CREATE TRIGGER update_document_vectors_updated_at
    BEFORE UPDATE ON document_vectors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_vectors ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies for document_chunks table
CREATE POLICY "Users can read own document chunks" ON document_chunks
    FOR SELECT
    TO authenticated
    USING (EXISTS (
        SELECT 1 FROM documents
        WHERE documents.id = document_chunks.document_id
        AND documents.user_id = auth.uid()
    ));

CREATE POLICY "Service role has full access to document chunks" ON document_chunks
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Create RLS Policies for document_vectors table
CREATE POLICY "Users can read own document vectors" ON document_vectors
    FOR SELECT
    TO authenticated
    USING (EXISTS (
        SELECT 1 FROM document_chunks
        JOIN documents ON document_chunks.document_id = documents.id
        WHERE document_chunks.id = document_vectors.chunk_id
        AND documents.user_id = auth.uid()
    ));

CREATE POLICY "Service role has full access to document vectors" ON document_vectors
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Comments for future HIPAA compliance and scaling considerations
COMMENT ON TABLE document_chunks IS 'Document chunks for processing and vector storage';
COMMENT ON TABLE document_vectors IS 'Document vectors for semantic search';
COMMENT ON COLUMN document_chunks.chunk_index IS 'Order of chunks within a document';
COMMENT ON COLUMN document_vectors.vector_data IS 'Embedding vector for semantic search'; 