-- 20250125000000_add_document_type_mvp.sql

BEGIN;

-- 1. Create the document_type enum
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_type') THEN
    CREATE TYPE document_type AS ENUM ('user_document', 'regulatory_document');
  END IF;
END$$;

-- 2. Add the document_type column to documents.documents
ALTER TABLE documents.documents
  ADD COLUMN IF NOT EXISTS document_type document_type NOT NULL DEFAULT 'user_document';

-- 3. Create an index on document_type
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents.documents(document_type);

-- 4. Backfill existing rows to user_document (if needed)
UPDATE documents.documents SET document_type = 'user_document' WHERE document_type IS NULL;

COMMIT; 