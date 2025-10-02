-- 20250907T000000_add_duplicate_status.sql
-- Add 'duplicate' status to upload_jobs table constraint
-- This allows the worker service to properly mark duplicate jobs

begin;

-- Update the status constraint to include 'duplicate'
alter table upload_pipeline.upload_jobs 
drop constraint if exists ck_upload_jobs_status;

alter table upload_pipeline.upload_jobs 
add constraint ck_upload_jobs_status check (status in (
    'uploaded', 'parse_queued', 'parsed', 'parse_validated',
    'chunking', 'chunks_stored', 'embedding_queued', 
    'embedding_in_progress', 'embeddings_stored', 'complete',
    'failed_parse', 'failed_chunking', 'failed_embedding',
    'duplicate'
));

commit;
