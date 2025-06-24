-- Enable required extensions
create extension if not exists vector;
create extension if not exists pgcrypto;

-- Create the documents table
create table if not exists documents (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null,
    original_filename text not null,
    file_size bigint,
    metadata jsonb,
    status text not null default 'pending',
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now(),
    document_type text not null default 'user_uploaded',
    is_active boolean default true,
    content_type text,
    file_hash text,
    storage_path text,
    jurisdiction text,
    program text[],
    effective_date date,
    expiration_date date,
    source_url text,
    tags text[],
    constraint valid_document_type check (document_type in ('user_uploaded', 'regulatory', 'policy', 'medical_record', 'claim'))
);

-- Create the document vectors table
create table if not exists document_vectors (
    id uuid primary key default gen_random_uuid(),
    user_id uuid,
    chunk_index integer not null,
    content_embedding vector(1536) not null,
    created_at timestamp with time zone default now(),
    is_active boolean default true,
    encrypted_chunk_text text,
    encrypted_chunk_metadata text,
    encryption_key_id uuid,
    document_record_id uuid,
    regulatory_document_id uuid,
    document_source_type text not null,
    constraint chk_document_reference_exclusive check (
        (document_source_type = 'user_document' AND document_record_id IS NOT NULL AND regulatory_document_id IS NULL) OR
        (document_source_type = 'regulatory_document' AND regulatory_document_id IS NOT NULL AND document_record_id IS NULL)
    ),
    constraint chk_user_document_requires_user_id check (
        (document_source_type = 'regulatory_document') OR 
        (document_source_type = 'user_document' AND user_id IS NOT NULL)
    ),
    constraint chk_encryption_consistency check (
        (encrypted_chunk_text IS NOT NULL AND encrypted_chunk_metadata IS NOT NULL AND encryption_key_id IS NOT NULL) OR
        (encrypted_chunk_text IS NULL AND encrypted_chunk_metadata IS NULL AND encryption_key_id IS NULL)
    )
);

-- Create indexes
create index if not exists idx_documents_type on documents(document_type);
create index if not exists idx_documents_jurisdiction on documents(jurisdiction) where jurisdiction is not null;
create index if not exists idx_documents_dates on documents(effective_date, expiration_date) 
where effective_date is not null or expiration_date is not null;

create unique index if not exists idx_document_vectors_user_doc_chunk_unique 
on document_vectors(document_record_id, chunk_index) 
where document_source_type = 'user_document' and is_active = true;

create unique index if not exists idx_document_vectors_regulatory_doc_chunk_unique 
on document_vectors(regulatory_document_id, chunk_index) 
where document_source_type = 'regulatory_document' and is_active = true;

create index if not exists document_vectors_embedding_idx on document_vectors 
using ivfflat (content_embedding vector_cosine_ops)
with (lists = 100);

-- Create the vector similarity search function
create or replace function match_documents(
    query_embedding vector(1536),
    match_threshold float,
    match_count int
)
returns table (
    encrypted_chunk_text text,
    similarity float,
    document_record_id uuid,
    regulatory_document_id uuid,
    document_source_type text
)
language plpgsql
as $$
begin
    return query
    select
        dv.encrypted_chunk_text,
        1 - (dv.content_embedding <=> query_embedding) as similarity,
        dv.document_record_id,
        dv.regulatory_document_id,
        dv.document_source_type
    from document_vectors dv
    where 1 - (dv.content_embedding <=> query_embedding) > match_threshold
        and dv.is_active = true
    order by dv.content_embedding <=> query_embedding
    limit match_count;
end;
$$; 