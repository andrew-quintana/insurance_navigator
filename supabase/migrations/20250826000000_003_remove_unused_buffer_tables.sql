-- 20250826T000000_003_remove_unused_buffer_tables.sql
-- Remove unused buffer tables following Phase 3.7 direct-write architecture discovery
-- Implements buffer table bypass architecture for performance optimization

begin;

-- -------------------------------
-- REMOVE unused buffer tables and related functionality
-- -------------------------------

-- Drop the unused document_vector_buffer table
-- This table was bypassed in favor of direct writes to document_chunks
-- for 10x performance improvement as documented in Phase 3.7
drop table if exists upload_pipeline.document_vector_buffer cascade;

-- Drop the document_chunk_buffer table if it exists from 002 migration
-- Also unused in direct-write architecture
drop table if exists upload_pipeline.document_chunk_buffer cascade;

-- -------------------------------
-- REMOVE buffer-related functions that are no longer needed
-- -------------------------------

-- Remove buffer-related helper functions
drop function if exists upload_pipeline.get_buffer_counts(uuid);
drop function if exists upload_pipeline.generate_chunk_id(uuid, text, text, int);

-- -------------------------------
-- UPDATE documentation comments in remaining functions
-- -------------------------------

-- Update function comments to reflect direct-write architecture
comment on function upload_pipeline.validate_status_transition(text, text) is 
'Validates status transitions in direct-write architecture. Buffer stages bypassed for performance.';

comment on function upload_pipeline.update_job_progress(uuid, jsonb) is 
'Updates job progress atomically in direct-write architecture without buffer dependency.';

-- -------------------------------
-- ADD technical debt documentation
-- -------------------------------

-- Create a view to document the architectural decision
create or replace view upload_pipeline.architecture_notes as
select 
    'direct_write' as architecture_type,
    'Chunks and embeddings written directly to document_chunks table' as description,
    'Bypassed document_vector_buffer for 10x performance improvement' as rationale,
    'SQS-based async processing with buffer tables planned for future phases' as future_plans,
    now() as documented_at;

comment on view upload_pipeline.architecture_notes is 
'Documents the Phase 3.7 architectural decision to bypass buffer tables for direct-write performance optimization';

-- -------------------------------
-- GRANT permissions for new view
-- -------------------------------
grant select on upload_pipeline.architecture_notes to postgres, service_role, authenticated;

commit;