-- Restore Complete Database Schema for Insurance Navigator
-- This script restores all necessary tables and configurations

-- =============================================================================
-- 1. CREATE USERS TABLE
-- =============================================================================

-- Create users table for user registration and authentication
create table if not exists public.users (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null unique,
    name text not null,
    consent_version text not null default '1.0',
    consent_timestamp timestamptz not null default now(),
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Create indexes for users table
create unique index if not exists idx_users_email on public.users (email);
create index if not exists idx_users_active on public.users (is_active);
create index if not exists idx_users_created_at on public.users (created_at);

-- Enable RLS on users table
alter table public.users enable row level security;

-- Create RLS policies for users table
drop policy if exists "Users can view own profile" on public.users;
create policy "Users can view own profile" on public.users
    for select using (auth.uid() = id);

drop policy if exists "Users can update own profile" on public.users;
create policy "Users can update own profile" on public.users
    for update using (auth.uid() = id);

drop policy if exists "Service role can insert users" on public.users;
create policy "Service role can insert users" on public.users
    for insert with check (auth.role() = 'service_role');

drop policy if exists "Service role can select all users" on public.users;
create policy "Service role can select all users" on public.users
    for select using (auth.role() = 'service_role');

-- Grant permissions
grant usage on schema public to postgres, anon, authenticated, service_role;
grant all on public.users to postgres, service_role;
grant select, update on public.users to authenticated;

-- =============================================================================
-- 2. CREATE UPLOAD PIPELINE SCHEMA
-- =============================================================================

-- Create schema for upload pipeline
create schema if not exists upload_pipeline;

-- Documents table
create table if not exists upload_pipeline.documents (
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

-- Upload jobs table
create table if not exists upload_pipeline.upload_jobs (
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

-- Document chunks table
create table if not exists upload_pipeline.document_chunks (
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

-- Events table
create table if not exists upload_pipeline.events (
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

-- =============================================================================
-- 3. CREATE STORAGE BUCKETS
-- =============================================================================

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
    26214400, -- 25MB limit
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

-- =============================================================================
-- 4. GRANT PERMISSIONS
-- =============================================================================

-- Grant permissions for upload_pipeline schema
grant usage on schema upload_pipeline to postgres, anon, authenticated, service_role;
grant all on all tables in schema upload_pipeline to postgres, service_role;
grant select on all tables in schema upload_pipeline to authenticated;

-- =============================================================================
-- 5. ENABLE RLS
-- =============================================================================

-- Enable RLS on all tables
alter table upload_pipeline.documents enable row level security;
alter table upload_pipeline.upload_jobs enable row level security;
alter table upload_pipeline.document_chunks enable row level security;
alter table upload_pipeline.events enable row level security;

-- =============================================================================
-- 6. CREATE RLS POLICIES
-- =============================================================================

-- Documents: users can only see their own documents
drop policy if exists doc_select_self on upload_pipeline.documents;
create policy doc_select_self on upload_pipeline.documents
    for select using (user_id = auth.uid());

-- Chunks: users can only see chunks from their documents
drop policy if exists chunk_select_self on upload_pipeline.document_chunks;
create policy chunk_select_self on upload_pipeline.document_chunks
    for select using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.document_chunks.document_id
                  and d.user_id = auth.uid())
    );

-- Jobs: users can see jobs for their documents
drop policy if exists job_select_self on upload_pipeline.upload_jobs;
create policy job_select_self on upload_pipeline.upload_jobs
    for select using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.upload_jobs.document_id
                  and d.user_id = auth.uid())
    );

-- Events: users can see events for their documents
drop policy if exists evt_select_self on upload_pipeline.events;
create policy evt_select_self on upload_pipeline.events
    for select using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.events.document_id
                  and d.user_id = auth.uid())
    );

-- =============================================================================
-- 7. CREATE HELPER FUNCTIONS
-- =============================================================================

-- Function to update updated_at timestamp
create or replace function public.handle_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- Function to handle new user creation
create or replace function public.handle_new_user()
returns trigger as $$
begin
    insert into public.users (id, email, name, consent_version, consent_timestamp)
    values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data->>'name', split_part(new.email, '@', 1)),
        '1.0',
        now()
    );
    return new;
end;
$$ language plpgsql security definer;

-- =============================================================================
-- 8. CREATE TRIGGERS
-- =============================================================================

-- Trigger for updated_at on users table
drop trigger if exists update_users_updated_at on public.users;
create trigger update_users_updated_at
    before update on public.users
    for each row execute function public.handle_updated_at();

-- Trigger to automatically create user profile
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

-- Triggers for upload_pipeline tables
drop trigger if exists update_documents_updated_at on upload_pipeline.documents;
create trigger update_documents_updated_at
    before update on upload_pipeline.documents
    for each row execute function public.handle_updated_at();

drop trigger if exists update_upload_jobs_updated_at on upload_pipeline.upload_jobs;
create trigger update_upload_jobs_updated_at
    before update on upload_pipeline.upload_jobs
    for each row execute function public.handle_updated_at();

drop trigger if exists update_document_chunks_updated_at on upload_pipeline.document_chunks;
create trigger update_document_chunks_updated_at
    before update on upload_pipeline.document_chunks
    for each row execute function public.handle_updated_at();

-- =============================================================================
-- 9. VERIFY SETUP
-- =============================================================================

-- Test that all tables exist
do $$
begin
    -- Check users table
    if not exists (select 1 from information_schema.tables where table_name = 'users' and table_schema = 'public') then
        raise exception 'Users table not created';
    end if;
    
    -- Check upload_pipeline tables
    if not exists (select 1 from information_schema.tables where table_name = 'documents' and table_schema = 'upload_pipeline') then
        raise exception 'Documents table not created';
    end if;
    
    if not exists (select 1 from information_schema.tables where table_name = 'upload_jobs' and table_schema = 'upload_pipeline') then
        raise exception 'Upload jobs table not created';
    end if;
    
    if not exists (select 1 from information_schema.tables where table_name = 'document_chunks' and table_schema = 'upload_pipeline') then
        raise exception 'Document chunks table not created';
    end if;
    
    if not exists (select 1 from information_schema.tables where table_name = 'events' and table_schema = 'upload_pipeline') then
        raise exception 'Events table not created';
    end if;
    
    raise notice 'All tables created successfully!';
end $$;
