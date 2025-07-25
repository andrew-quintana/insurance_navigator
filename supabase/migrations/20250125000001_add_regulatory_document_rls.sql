-- 20250125000001_add_regulatory_document_rls.sql

BEGIN;

-- Policy: Users can read regulatory documents
CREATE POLICY "Users can read regulatory documents"
  ON documents.documents
  FOR SELECT
  TO authenticated
  USING (document_type = 'regulatory_document');

-- Policy: Admins can insert regulatory documents
CREATE POLICY "Admins can insert regulatory documents"
  ON documents.documents
  FOR INSERT
  TO authenticated
  WITH CHECK (
    (auth.jwt() -> 'user_metadata' ->> 'role' = 'admin' OR
     (auth.jwt() -> 'user_metadata' -> 'roles') ? 'admin')
    AND document_type = 'regulatory_document'
  );

-- Policy: Users can insert user documents (default)
CREATE POLICY "Users can insert user documents"
  ON documents.documents
  FOR INSERT
  TO authenticated
  WITH CHECK (
    document_type = 'user_document'
  );

-- Policy: Users can update their own user documents
CREATE POLICY "Users can update their own user documents"
  ON documents.documents
  FOR UPDATE
  TO authenticated
  USING (
    owner = auth.uid() AND document_type = 'user_document'
  )
  WITH CHECK (
    owner = auth.uid() AND document_type = 'user_document'
  );

COMMIT; 