-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  original_filename TEXT NOT NULL,
  content_type TEXT NOT NULL,
  file_size BIGINT NOT NULL,
  storage_path TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'::jsonb,
  UNIQUE(storage_path)
);

-- Create jobs table
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'STARTED',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  error_message TEXT,
  error_details JSONB,
  metadata JSONB DEFAULT '{}'::jsonb,
  CONSTRAINT valid_status CHECK (
    status IN ('STARTED', 'UPLOAD_FAILED', 'PARSE_FAILED', 'VECTORIZE_FAILED', 'COMPLETED')
  )
);

-- Create RLS policies
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Documents policies
CREATE POLICY "Users can view their own documents"
  ON documents FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own documents"
  ON documents FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role can do all operations"
  ON documents FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

-- Jobs policies
CREATE POLICY "Users can view jobs for their documents"
  ON jobs FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM documents
    WHERE documents.id = jobs.document_id
    AND documents.user_id = auth.uid()
  ));

CREATE POLICY "Service role can do all operations on jobs"
  ON jobs FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_document_id ON jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_documents_updated_at
  BEFORE UPDATE ON documents
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at
  BEFORE UPDATE ON jobs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();


-- Create RLS policies
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Documents policies
CREATE POLICY "Users can view their own documents"
  ON documents FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own documents"
  ON documents FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role can do all operations"
  ON documents FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

-- Jobs policies
CREATE POLICY "Users can view jobs for their documents"
  ON jobs FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM documents
    WHERE documents.id = jobs.document_id
    AND documents.user_id = auth.uid()
  ));

CREATE POLICY "Service role can do all operations on jobs"
  ON jobs FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_document_id ON jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_documents_updated_at
  BEFORE UPDATE ON documents
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at
  BEFORE UPDATE ON jobs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
