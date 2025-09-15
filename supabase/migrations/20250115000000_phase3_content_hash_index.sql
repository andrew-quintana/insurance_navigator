-- Phase 3: Multi-User Data Integrity - Content Hash Index
-- Adds index for cross-user duplicate detection based on content hash

begin;

-- Add index for content hash-based duplicate detection across all users
-- This enables efficient lookup of existing documents by content regardless of user
create index if not exists idx_documents_content_hash 
    on upload_pipeline.documents (file_sha256);

-- Add index for parsed content hash as well (for processed content deduplication)
create index if not exists idx_documents_parsed_hash 
    on upload_pipeline.documents (parsed_sha256) 
    where parsed_sha256 is not null;

-- Add composite index for user + content hash for user-scoped queries
-- This maintains existing user isolation while enabling cross-user lookups
create index if not exists idx_documents_user_content_hash 
    on upload_pipeline.documents (user_id, file_sha256);

commit;

