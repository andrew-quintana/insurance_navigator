-- Create document_vectors table if it doesn't exist
CREATE TABLE IF NOT EXISTS document_vectors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  chunk_text TEXT NOT NULL,
  content_embedding VECTOR(1536),
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(document_id, chunk_index)
);

-- Enable RLS
ALTER TABLE document_vectors ENABLE ROW LEVEL SECURITY;

-- Create policies if they don't exist
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'document_vectors' AND policyname = 'Users can view vectors for their documents'
  ) THEN
    CREATE POLICY "Users can view vectors for their documents"
      ON document_vectors FOR SELECT
      USING (EXISTS (
        SELECT 1 FROM documents
        WHERE documents.id = document_vectors.document_id
        AND documents.user_id = auth.uid()
      ));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'document_vectors' AND policyname = 'Service role can do all operations'
  ) THEN
    CREATE POLICY "Service role can do all operations"
      ON document_vectors FOR ALL
      USING (auth.jwt() ->> 'role' = 'service_role');
  END IF;
END $$;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_document_vectors_document_id ON document_vectors(document_id);
CREATE INDEX IF NOT EXISTS idx_document_vectors_embedding ON document_vectors USING ivfflat (content_embedding vector_cosine_ops);

-- Create trigger if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger 
    WHERE tgname = 'update_document_vectors_updated_at'
  ) THEN
    CREATE TRIGGER update_document_vectors_updated_at
      BEFORE UPDATE ON document_vectors
      FOR EACH ROW
      EXECUTE FUNCTION update_updated_at_column();
  END IF;
END $$; 