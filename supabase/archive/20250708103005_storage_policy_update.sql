-- 20250708T000000_documents_setup.sql

begin;

-- -------------------------------
-- DROP existing tables if present
-- -------------------------------
drop table if exists documents.document_chunks cascade;
drop table if exists documents.documents cascade;

-- Drop schema if empty (safe fallback)
drop schema if exists documents cascade;

-- -------------------------------
-- CREATE schema
-- -------------------------------
create schema if not exists documents;

-- -------------------------------
-- DOCUMENTS TABLE
-- -------------------------------
create table documents.documents (
  id uuid primary key default gen_random_uuid(),
  owner uuid not null,
  name text not null,
  source_path text not null,
  uploaded_at timestamptz not null default now()
);

-- -------------------------------
-- DOCUMENT CHUNKS TABLE
-- -------------------------------
create table documents.document_chunks (
  id uuid primary key default gen_random_uuid(),
  doc_id uuid references documents.documents(id) on delete cascade,
  chunk_index int not null,
  level_1 int,
  level_2 int,
  level_3 int,
  full_chunk_id text not null,
  text text not null,
  tokens int,
  vector jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- -------------------------------
-- GRANT permissions
-- -------------------------------
grant usage on schema documents to postgres, anon, authenticated, service_role;
grant all on all tables in schema documents to postgres, service_role;
grant select on all tables in schema documents to authenticated;

-- -------------------------------
-- ENABLE RLS
-- -------------------------------
alter table documents.documents enable row level security;
alter table documents.document_chunks enable row level security;

-- -------------------------------
-- RLS POLICIES: documents
-- -------------------------------
create policy "Service role can access all documents"
  on documents.documents
  for all
  to service_role
  using (true)
  with check (true);

create policy "Users can read their documents"
  on documents.documents
  for select
  to authenticated
  using (owner = auth.uid());

-- -------------------------------
-- RLS POLICIES: document_chunks
-- -------------------------------
create policy "Service role can access all chunks"
  on documents.document_chunks
  for all
  to service_role
  using (true)
  with check (true);

create policy "Users can read their document chunks"
  on documents.document_chunks
  for select
  to authenticated
  using (
    exists (
      select 1
      from documents.documents d
      where d.id = document_chunks.doc_id
      and d.owner = auth.uid()
    )
  );

-- -------------------------------
-- STORAGE BUCKET: 'files'
-- -------------------------------
-- Supabase Storage uses the `storage.buckets` table
-- Ensure it exists if resetting manually

insert into storage.buckets (id, name, public)
values ('files', 'files', false)
on conflict (id) do nothing;

commit;