-- 20250815T000000_002_worker_refactor_buffer_tables.sql
-- 002 Worker Refactor: Buffer Tables and Enhanced Schema
-- Implements CONTEXT002.md buffer-driven pipeline architecture

begin;

-- -------------------------------
-- UPDATE upload_jobs table with new status values and progress tracking
-- -------------------------------
-- Drop existing constraints and indexes
drop index if exists upload_pipeline.uq_job_doc_stage_active;
drop index if exists upload_pipeline.ix_jobs_state;

-- Add new columns for enhanced state management
alter table upload_pipeline.upload_jobs 
add column if not exists status text,
add column if not exists progress jsonb default '{}',
add column if not exists webhook_secret text,
add column if not exists chunks_version text default 'markdown-simple@1',
add column if not exists embed_model text default 'text-embedding-3-small',
add column if not exists embed_version text default '1';

-- Update existing rows to set status based on stage
update upload_pipeline.upload_jobs 
set status = case 
    when stage = 'job_validated' then 'uploaded'
    when stage = 'parsing' then 'parse_queued'
    when stage = 'parsed' then 'parsed'
    when stage = 'parse_validated' then 'parse_validated'
    when stage = 'chunking' then 'chunking'
    when stage = 'chunks_buffered' then 'chunking'
    when stage = 'chunked' then 'chunks_stored'
    when stage = 'embedding' then 'embedding_queued'
    when stage = 'embeddings_buffered' then 'embedding_in_progress'
    when stage = 'embedded' then 'embeddings_stored'
    else 'uploaded'
end;

-- Drop old stage column and rename status to be the primary state field
alter table upload_pipeline.upload_jobs 
drop column if exists stage,
drop column if exists idempotency_key,
drop column if exists payload,
drop column if exists claimed_by,
drop column if exists claimed_at,
drop column if exists started_at,
drop column if exists finished_at;

-- Add status constraint with new values from CONTEXT002.md
alter table upload_pipeline.upload_jobs 
add constraint ck_upload_jobs_status check (status in (
    'uploaded', 'parse_queued', 'parsed', 'parse_validated',
    'chunking', 'chunks_stored', 'embedding_queued', 
    'embedding_in_progress', 'embeddings_stored', 'complete',
    'failed_parse', 'failed_chunking', 'failed_embedding'
));

-- Add new indexes for efficient worker polling
create index if not exists idx_upload_jobs_status_created 
    on upload_pipeline.upload_jobs (status, created_at) 
    where status not in ('complete', 'failed_parse', 'failed_chunking', 'failed_embedding');

create index if not exists idx_upload_jobs_document 
    on upload_pipeline.upload_jobs (document_id);

-- Note: user_id is accessed through document_id -> documents.user_id
-- No direct user_id column in upload_jobs table

-- -------------------------------
-- CREATE document_chunk_buffer table for chunk staging
-- -------------------------------
create table if not exists upload_pipeline.document_chunk_buffer (
    chunk_id uuid primary key,  -- UUIDv5 deterministic
    document_id uuid not null references upload_pipeline.documents(document_id),
    chunk_ord int not null,
    chunker_name text not null,
    chunker_version text not null,
    chunk_sha text not null,     -- Content integrity
    text text not null,
    meta jsonb,                  -- {page, section, headings, offsets}
    created_at timestamptz default now(),
    
    unique (document_id, chunker_name, chunker_version, chunk_ord)
);

-- Indexes for chunk buffer
create index if not exists idx_chunk_buffer_document 
    on upload_pipeline.document_chunk_buffer (document_id);

create index if not exists idx_chunk_buffer_for_embedding 
    on upload_pipeline.document_chunk_buffer (document_id, chunker_name, chunker_version);

-- -------------------------------
-- CREATE document_vector_buffer table for embedding staging
-- -------------------------------
create table if not exists upload_pipeline.document_vector_buffer (
    buffer_id uuid primary key default gen_random_uuid(),
    document_id uuid not null,
    chunk_id uuid not null references upload_pipeline.document_chunk_buffer(chunk_id),
    embed_model text not null,
    embed_version text not null,
    vector vector(1536) not null,
    vector_sha text not null,
    batch_id uuid,               -- Track micro-batch operations
    created_at timestamptz default now(),
    
    unique (chunk_id, embed_model, embed_version)
);

-- Indexes for vector buffer
-- Check if document_id column exists before creating indexes
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'document_vector_buffer' 
               AND table_schema = 'upload_pipeline' 
               AND column_name = 'document_id') THEN
        CREATE INDEX IF NOT EXISTS idx_vector_buffer_document 
            ON upload_pipeline.document_vector_buffer (document_id);
        
        CREATE INDEX IF NOT EXISTS idx_vector_buffer_pending 
            ON upload_pipeline.document_vector_buffer (document_id, embed_model, embed_version);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'document_vector_buffer' 
               AND table_schema = 'upload_pipeline' 
               AND column_name = 'batch_id') THEN
        CREATE INDEX IF NOT EXISTS idx_vector_buffer_batch 
            ON upload_pipeline.document_vector_buffer (batch_id);
    END IF;
END $$;

-- -------------------------------
-- CREATE webhook_log table for replay protection
-- -------------------------------
create table if not exists upload_pipeline.webhook_log (
    webhook_id text primary key,
    job_id uuid not null references upload_pipeline.upload_jobs(job_id),
    processed_at timestamptz default now(),
    ip_address inet,
    payload_hash text not null
);

-- Index for webhook log
create index if not exists idx_webhook_log_job 
    on upload_pipeline.webhook_log (job_id);

create index if not exists idx_webhook_log_processed 
    on upload_pipeline.webhook_log (processed_at);

-- -------------------------------
-- UPDATE RLS policies for new tables
-- -------------------------------
-- Enable RLS on new tables
alter table upload_pipeline.document_chunk_buffer enable row level security;
alter table upload_pipeline.document_vector_buffer enable row level security;
alter table upload_pipeline.webhook_log enable row level security;

-- Chunk buffer: no client access (workers only)
drop policy if exists chunk_buffer_no_client on upload_pipeline.document_chunk_buffer;
create policy chunk_buffer_no_client on upload_pipeline.document_chunk_buffer
    for all using (false);

-- Vector buffer: no client access (workers only)
drop policy if exists vector_buffer_no_client on upload_pipeline.document_vector_buffer;
create policy vector_buffer_no_client on upload_pipeline.document_vector_buffer
    for all using (false);

-- Webhook log: no client access (internal use only)
drop policy if exists webhook_log_no_client on upload_pipeline.webhook_log;
create policy webhook_log_no_client on upload_pipeline.webhook_log
    for all using (false);

-- -------------------------------
-- HELPER FUNCTIONS for buffer operations
-- -------------------------------
-- Function to generate deterministic chunk ID
create or replace function upload_pipeline.generate_chunk_id(
    document_id uuid,
    chunker_name text,
    chunker_version text,
    chunk_ord int
) returns uuid as $$
begin
    -- Use UUIDv5 with canonicalized string
    -- Format: "{document_id}:{chunker_name}:{chunker_version}:{chunk_ord}"
    return gen_random_uuid(); -- Placeholder - actual UUIDv5 implementation in Python
end;
$$ language plpgsql;

-- Function to validate status transitions for new state machine
create or replace function upload_pipeline.validate_status_transition(
    old_status text,
    new_status text
) returns boolean as $$
begin
    -- Define valid status progression from CONTEXT002.md
    case old_status
        when 'uploaded' then
            return new_status = 'parse_queued';
        when 'parse_queued' then
            return new_status = 'parsed';
        when 'parsed' then
            return new_status = 'parse_validated';
        when 'parse_validated' then
            return new_status = 'chunking';
        when 'chunking' then
            return new_status = 'chunks_stored';
        when 'chunks_stored' then
            return new_status = 'embedding_queued';
        when 'embedding_queued' then
            return new_status = 'embedding_in_progress';
        when 'embedding_in_progress' then
            return new_status = 'embeddings_stored';
        when 'embeddings_stored' then
            return new_status = 'complete';
        else
            return false;
    end case;
end;
$$ language plpgsql;

-- Function to update job progress atomically
create or replace function upload_pipeline.update_job_progress(
    p_job_id uuid,
    p_progress jsonb
) returns void as $$
begin
    update upload_pipeline.upload_jobs 
    set progress = p_progress,
        updated_at = now()
    where job_id = p_job_id;
end;
$$ language plpgsql;

-- Function to get buffer counts for progress calculation
create or replace function upload_pipeline.get_buffer_counts(
    p_document_id uuid
) returns table(chunks_total bigint, vectors_total bigint) as $$
begin
    return query
    select 
        coalesce(chunk_counts.total, 0) as chunks_total,
        coalesce(vector_counts.total, 0) as vectors_total
    from (
        select count(*) as total
        from upload_pipeline.document_chunk_buffer
        where document_id = p_document_id
    ) chunk_counts
    cross join (
        select count(*) as total
        from upload_pipeline.document_vector_buffer
        where document_id = p_document_id
    ) vector_counts;
end;
$$ language plpgsql;

-- -------------------------------
-- GRANT permissions for new tables
-- -------------------------------
grant all on all tables in schema upload_pipeline to postgres, service_role;
grant select on all tables in schema upload_pipeline to authenticated;

-- -------------------------------
-- CLEANUP old functions that are no longer needed
-- -------------------------------
drop function if exists upload_pipeline.validate_stage_transition(text, text);
drop function if exists upload_pipeline.validate_state_transition(text, text);

commit;
