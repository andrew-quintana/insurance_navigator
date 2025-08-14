-- 20250814T000000_init_upload_pipeline.sql
-- Insurance Document Ingestion Pipeline Refactor
-- Implements RFC001 schema with job-queue-based processing

begin;

-- -------------------------------
-- CREATE new schema for upload pipeline
-- -------------------------------
create schema if not exists upload_pipeline;

-- -------------------------------
-- DOCUMENTS TABLE (new schema)
-- -------------------------------
create table upload_pipeline.documents (
    document_id uuid primary key,
    user_id uuid not null,
    filename text not null,
    mime text not null,
    bytes_len bigint not null,
    file_sha256 text not null,
    parsed_sha256 text,
    raw_path text not null,
    parsed_path text,
    processing_status text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- Indexes for documents table
create unique index if not exists uq_user_filehash
    on upload_pipeline.documents (user_id, file_sha256);
create index if not exists ix_documents_user 
    on upload_pipeline.documents (user_id);

-- -------------------------------
-- UPLOAD_JOBS TABLE (job queue)
-- -------------------------------
create table upload_pipeline.upload_jobs (
    job_id uuid primary key,
    document_id uuid not null references upload_pipeline.documents(document_id),
    stage text not null check (stage in ('job_validated','parsing','parsed','parse_validated','chunking','chunks_buffered','chunked','embedding','embeddings_buffered','embedded')),
    state text not null check (state in ('queued','working','retryable','done','deadletter')),
    retry_count int default 0,
    idempotency_key text,
    payload jsonb,
    last_error jsonb,
    claimed_by text,
    claimed_at timestamptz,
    started_at timestamptz,
    finished_at timestamptz,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- Indexes for upload_jobs table
create unique index if not exists uq_job_doc_stage_active
    on upload_pipeline.upload_jobs (document_id, stage)
    where state in ('queued','working','retryable');
create index if not exists ix_jobs_state 
    on upload_pipeline.upload_jobs (state, created_at);

-- -------------------------------
-- DOCUMENT_CHUNKS TABLE (chunks + embeddings)
-- -------------------------------
create table upload_pipeline.document_chunks (
    chunk_id uuid primary key,
    document_id uuid not null references upload_pipeline.documents(document_id),
    chunker_name text not null,
    chunker_version text not null,
    chunk_ord int not null,
    text text not null,
    chunk_sha text not null,
    embed_model text not null,
    embed_version text not null,
    vector_dim int not null check (vector_dim = 1536),
    embedding vector(1536) not null,
    embed_updated_at timestamptz default now(),
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    unique (document_id, chunker_name, chunker_version, chunk_ord)
);

-- HNSW index for vector similarity search
create index if not exists idx_hnsw_chunks_te3s_v1
    on upload_pipeline.document_chunks using hnsw (embedding)
    where embed_model='text-embedding-3-small' and embed_version='1';

-- Storage optimization
alter table upload_pipeline.document_chunks set (fillfactor=70);

-- -------------------------------
-- DOCUMENT_VECTOR_BUFFER TABLE (write-ahead buffer)
-- -------------------------------
create table upload_pipeline.document_vector_buffer (
    buffer_id uuid primary key default gen_random_uuid(),
    chunk_id uuid not null references upload_pipeline.document_chunks(chunk_id),
    embed_model text not null,
    embed_version text not null,
    vector_dim int not null check (vector_dim = 1536),
    embedding vector(1536) not null,
    created_at timestamptz default now()
);

-- -------------------------------
-- EVENTS TABLE (comprehensive logging)
-- -------------------------------
create table upload_pipeline.events (
    event_id uuid primary key default gen_random_uuid(),
    job_id uuid not null references upload_pipeline.upload_jobs(job_id),
    document_id uuid not null references upload_pipeline.documents(document_id),
    ts timestamptz default now(),
    type text not null check (type in ('stage_started','stage_done','retry','error','finalized')),
    severity text not null check (severity in ('info','warn','error')),
    code text not null,
    payload jsonb,
    correlation_id uuid
);

-- Indexes for events table
create index if not exists idx_events_job_ts 
    on upload_pipeline.events (job_id, ts desc);
create index if not exists idx_events_doc_ts 
    on upload_pipeline.events (document_id, ts desc);

-- -------------------------------
-- STORAGE BUCKETS (private buckets)
-- -------------------------------
-- Raw documents bucket
insert into storage.buckets (
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types
) values (
    'raw',
    'raw',
    false,
    26214400, -- 25MB limit per CONTEXT.md
    ARRAY['application/pdf']
) on conflict (id) do nothing;

-- Parsed documents bucket
insert into storage.buckets (
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types
) values (
    'parsed',
    'parsed',
    false,
    10485760, -- 10MB limit for parsed markdown
    ARRAY['text/markdown', 'text/plain']
) on conflict (id) do nothing;

-- -------------------------------
-- GRANT permissions
-- -------------------------------
grant usage on schema upload_pipeline to postgres, anon, authenticated, service_role;
grant all on all tables in schema upload_pipeline to postgres, service_role;
grant select on all tables in schema upload_pipeline to authenticated;

-- -------------------------------
-- ENABLE RLS
-- -------------------------------
alter table upload_pipeline.documents enable row level security;
alter table upload_pipeline.upload_jobs enable row level security;
alter table upload_pipeline.document_chunks enable row level security;
alter table upload_pipeline.document_vector_buffer enable row level security;
alter table upload_pipeline.events enable row level security;

-- -------------------------------
-- RLS POLICIES
-- -------------------------------
-- Documents: users can only see their own documents
create policy doc_select_self on upload_pipeline.documents
    for select using (user_id = auth.uid());

-- Chunks: users can only see chunks from their documents
create policy chunk_select_self on upload_pipeline.document_chunks
    for select using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.document_chunks.document_id
                  and d.user_id = auth.uid())
    );

-- Jobs: users can see jobs for their documents (optional visibility)
create policy job_select_self on upload_pipeline.upload_jobs
    for select using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.upload_jobs.document_id
                  and d.user_id = auth.uid())
    );

-- Events: users can see events for their documents
create policy evt_select_self on upload_pipeline.events
    for select using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.events.document_id
                  and d.user_id = auth.uid())
    );

-- Buffer: no client access (workers only)
create policy buffer_no_client on upload_pipeline.document_vector_buffer
    for all using (false);

-- -------------------------------
-- HELPER FUNCTIONS
-- -------------------------------
-- Function to update updated_at timestamp
create or replace function upload_pipeline.update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- Triggers for updated_at
create trigger update_documents_updated_at
    before update on upload_pipeline.documents
    for each row execute function upload_pipeline.update_updated_at_column();

create trigger update_upload_jobs_updated_at
    before update on upload_pipeline.upload_jobs
    for each row execute function upload_pipeline.update_updated_at_column();

create trigger update_document_chunks_updated_at
    before update on upload_pipeline.document_chunks
    for each row execute function upload_pipeline.update_updated_at_column();

-- Function to validate stage transitions
create or replace function upload_pipeline.validate_stage_transition(
    old_stage text,
    new_stage text
) returns boolean as $$
begin
    -- Define valid stage progression
    case old_stage
        when 'queued' then
            return new_stage = 'job_validated';
        when 'job_validated' then
            return new_stage = 'parsing';
        when 'parsing' then
            return new_stage = 'parsed';
        when 'parsed' then
            return new_stage = 'parse_validated';
        when 'parse_validated' then
            return new_stage = 'chunking';
        when 'chunking' then
            return new_stage = 'chunks_buffered';
        when 'chunks_buffered' then
            return new_stage = 'chunked';
        when 'chunked' then
            return new_stage = 'embedding';
        when 'embedding' then
            return new_stage = 'embeddings_buffered';
        when 'embeddings_buffered' then
            return new_stage = 'embedded';
        when 'embedded' then
            return new_stage = 'embedded'; -- Terminal stage
        else
            return false;
    end case;
end;
$$ language plpgsql;

-- Function to validate state transitions
create or replace function upload_pipeline.validate_state_transition(
    old_state text,
    new_state text
) returns boolean as $$
begin
    -- Define valid state transitions
    case old_state
        when 'queued' then
            return new_state in ('working', 'done');
        when 'working' then
            return new_state in ('done', 'retryable', 'deadletter');
        when 'retryable' then
            return new_state in ('queued', 'deadletter');
        when 'done' then
            return new_state = 'done'; -- Terminal state
        when 'deadletter' then
            return new_state = 'deadletter'; -- Terminal state
        else
            return false;
    end case;
end;
$$ language plpgsql;

commit;
