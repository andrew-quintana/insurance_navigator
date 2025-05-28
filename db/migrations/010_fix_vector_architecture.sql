-- Migration: Fix Vector Table Architecture
-- Description: Remove user_id denormalization and add encryption support
-- Addresses: Multi-user policies, security consistency, proper normalization

BEGIN;

-- =====================================================================
-- STEP 1: ADD ENCRYPTION SUPPORT TO VECTOR TABLES
-- =====================================================================

-- Add encryption columns to policy_content_vectors
ALTER TABLE policy_content_vectors 
ADD COLUMN encrypted_content_text TEXT,
ADD COLUMN encrypted_policy_metadata TEXT,
ADD COLUMN encrypted_document_metadata TEXT,
ADD COLUMN encryption_key_id UUID REFERENCES encryption_keys(id);

-- Add encryption columns to user_document_vectors  
ALTER TABLE user_document_vectors
ADD COLUMN encrypted_chunk_text TEXT,
ADD COLUMN encrypted_chunk_metadata TEXT,
ADD COLUMN encryption_key_id UUID REFERENCES encryption_keys(id);

-- =====================================================================
-- STEP 2: REMOVE user_id DENORMALIZATION
-- =====================================================================

-- Remove user_id constraint and column from policy_content_vectors
-- (Keep for data migration, will be dropped after encryption migration)
ALTER TABLE policy_content_vectors ALTER COLUMN user_id DROP NOT NULL;

-- =====================================================================
-- STEP 3: CREATE POLICY ACCESS THROUGH user_policy_links
-- =====================================================================

-- Update RLS policies to use proper user_policy_links relationship
DROP POLICY IF EXISTS policy_content_vectors_user_access ON policy_content_vectors;

CREATE POLICY "policy_content_vectors_proper_access" ON policy_content_vectors
    FOR ALL USING (
        -- Access via user_policy_links (proper many-to-many)
        EXISTS (
            SELECT 1 FROM user_policy_links upl 
            WHERE upl.policy_id = policy_content_vectors.policy_id 
            AND upl.user_id = auth.uid() 
            AND upl.relationship_verified = true
        ) OR 
        -- Admin access
        EXISTS (
            SELECT 1 FROM user_roles ur JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid() AND r.name = 'admin'
        )
    );

-- Update user_document_vectors RLS policy for consistency  
DROP POLICY IF EXISTS user_document_vectors_user_access ON user_document_vectors;

CREATE POLICY "user_document_vectors_proper_access" ON user_document_vectors
    FOR ALL USING (
        -- Direct user access to their documents
        user_id = auth.uid() OR 
        -- Admin access
        EXISTS (
            SELECT 1 FROM user_roles ur JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid() AND r.name = 'admin'
        )
    );

-- =====================================================================
-- STEP 4: ADD ENCRYPTION INDEXES
-- =====================================================================

CREATE INDEX idx_policy_content_vectors_encryption_key 
    ON policy_content_vectors(encryption_key_id);
    
CREATE INDEX idx_user_document_vectors_encryption_key 
    ON user_document_vectors(encryption_key_id);

-- =====================================================================
-- STEP 5: ADD DATA INTEGRITY CONSTRAINTS
-- =====================================================================

-- Ensure either plaintext OR encrypted content exists (not both)
ALTER TABLE policy_content_vectors 
ADD CONSTRAINT chk_content_encryption CHECK (
    (content_text IS NOT NULL AND encrypted_content_text IS NULL) OR
    (content_text IS NULL AND encrypted_content_text IS NOT NULL)
);

ALTER TABLE policy_content_vectors 
ADD CONSTRAINT chk_metadata_encryption CHECK (
    (policy_metadata IS NOT NULL AND encrypted_policy_metadata IS NULL) OR
    (policy_metadata IS NULL AND encrypted_policy_metadata IS NOT NULL)
);

ALTER TABLE user_document_vectors
ADD CONSTRAINT chk_chunk_encryption CHECK (
    (chunk_text IS NOT NULL AND encrypted_chunk_text IS NULL) OR  
    (chunk_text IS NULL AND encrypted_chunk_text IS NOT NULL)
);

ALTER TABLE user_document_vectors
ADD CONSTRAINT chk_chunk_metadata_encryption CHECK (
    (chunk_metadata IS NOT NULL AND encrypted_chunk_metadata IS NULL) OR
    (chunk_metadata IS NULL AND encrypted_chunk_metadata IS NOT NULL)
);

-- =====================================================================
-- STEP 6: UPDATE VECTOR TABLE COMMENTS
-- =====================================================================

COMMENT ON TABLE policy_content_vectors IS 'Vector storage for policy content with encryption support. User access controlled via user_policy_links table.';
COMMENT ON COLUMN policy_content_vectors.user_id IS 'DEPRECATED: Will be removed after encryption migration. Use user_policy_links for access control.';
COMMENT ON COLUMN policy_content_vectors.encryption_key_id IS 'Reference to encryption key used for encrypting sensitive content and metadata.';

COMMENT ON TABLE user_document_vectors IS 'Vector storage for user-uploaded documents with encryption support.';
COMMENT ON COLUMN user_document_vectors.encryption_key_id IS 'Reference to encryption key used for encrypting sensitive content and metadata.';

COMMIT; 