-- Regulatory Documents Migration
-- Version: 003
-- Description: Add regulatory documents table and related schemas

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create regulatory_documents table
CREATE TABLE regulatory_documents (
  document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_document_path TEXT NOT NULL,
  title TEXT NOT NULL,
  jurisdiction TEXT NOT NULL, -- e.g., 'federal', 'CA', 'San Mateo County'
  program TEXT[] NOT NULL, -- e.g., ['Medicaid', 'SNAP']
  document_type TEXT NOT NULL, -- e.g., 'manual', 'guidance', 'faq'
  effective_date DATE,
  expiration_date DATE,
  structured_contents JSONB, -- parsed, machine-readable rules
  summary JSONB, -- natural language summary
  source_url TEXT,
  encrypted_restrictions JSONB,
  encryption_key_id UUID REFERENCES encryption_keys(id),
  tags TEXT[], -- useful for search and filtering
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  version INT DEFAULT 1
);

-- Create indexes for efficient querying
CREATE INDEX idx_regulatory_docs_document_type ON regulatory_documents(document_type);
CREATE INDEX idx_regulatory_docs_effective_date ON regulatory_documents(effective_date);
CREATE INDEX idx_regulatory_docs_expiration_date ON regulatory_documents(expiration_date);
CREATE INDEX idx_regulatory_docs_jurisdiction ON regulatory_documents(jurisdiction);
CREATE INDEX idx_regulatory_docs_program ON regulatory_documents USING gin(program);
CREATE INDEX idx_regulatory_docs_tags ON regulatory_documents USING gin(tags);

-- Enable Row Level Security
ALTER TABLE regulatory_documents ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY "regulatory_docs_read" ON regulatory_documents
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN roles r ON r.id = ur.role_id
      WHERE ur.user_id = current_user::uuid
      AND (r.name = 'admin' OR r.name = 'regulatory_agent')
    )
  );

CREATE POLICY "regulatory_docs_write" ON regulatory_documents
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN roles r ON r.id = ur.role_id
      WHERE ur.user_id = current_user::uuid
      AND r.name = 'admin'
    )
  );

CREATE POLICY "regulatory_docs_update" ON regulatory_documents
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN roles r ON r.id = ur.role_id
      WHERE ur.user_id = current_user::uuid
      AND r.name = 'admin'
    )
  ); 