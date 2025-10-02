-- 20250708T000000_documents_setup.sql

begin;

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
-- STORAGE BUCKET: 'files'
-- -------------------------------
insert into storage.buckets (
  id,
  name,
  file_size_limit,
  allowed_mime_types
)
VALUES (
  'files',
  'files',
  52428800,
  ARRAY[
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
    'text/csv',
    'text/markdown',
    'application/json',
    'application/xml',
    'text/xml',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'application/x-www-form-urlencoded',
    'multipart/form-data'
  ]
) ON CONFLICT (id) DO NOTHING;

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

commit;