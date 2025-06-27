-- Enable RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Create policies for documents
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'documents' AND policyname = 'Users can view their own documents'
  ) THEN
    CREATE POLICY "Users can view their own documents"
    ON documents FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'documents' AND policyname = 'Users can insert their own documents'
  ) THEN
    CREATE POLICY "Users can insert their own documents"
    ON documents FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'jobs' AND policyname = 'Users can view their own jobs'
  ) THEN
    CREATE POLICY "Users can view their own jobs"
    ON jobs FOR SELECT
    TO authenticated
    USING (document_id IN (
        SELECT id FROM documents WHERE user_id = auth.uid()
    ));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'jobs' AND policyname = 'Users can insert their own jobs'
  ) THEN
    CREATE POLICY "Users can insert their own jobs"
    ON jobs FOR INSERT
    TO authenticated
    WITH CHECK (document_id IN (
        SELECT id FROM documents WHERE user_id = auth.uid()
    ));
  END IF;
END $$;

  ) THEN
    CREATE POLICY "Users can view their own jobs"
    ON jobs FOR SELECT
    TO authenticated
    USING (document_id IN (
        SELECT id FROM documents WHERE user_id = auth.uid()
    ));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'jobs' AND policyname = 'Users can insert their own jobs'
  ) THEN
    CREATE POLICY "Users can insert their own jobs"
    ON jobs FOR INSERT
    TO authenticated
    WITH CHECK (document_id IN (
        SELECT id FROM documents WHERE user_id = auth.uid()
    ));
  END IF;
END $$;
