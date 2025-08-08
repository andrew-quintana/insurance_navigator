-- Short-Term Chat Memory MVP — Phase 1
-- Migration: Add chat_metadata and chat_context_queue tables
-- Date: 2025-08-07

begin;

-- =========================================
-- Table: chat_metadata
-- =========================================
-- Note: FK targets existing chat table used by the system.
-- The platform uses `conversations(id)` (TEXT) for chat identifiers.
-- We align to that to ensure compatibility.
-- RFC specified UUID and `chats(id)`, but repo uses `conversations`.

create table if not exists public.chat_metadata (
    chat_id text primary key references public.conversations(id) on delete cascade,
    user_confirmed jsonb default '{}'::jsonb not null,
    llm_inferred jsonb default '{}'::jsonb not null,
    general_summary text default '' not null,
    token_count integer default 0 not null,
    last_updated timestamptz default now() not null,
    created_at timestamptz default now() not null
);

create index if not exists idx_chat_metadata_chat_id on public.chat_metadata(chat_id);
create index if not exists idx_chat_metadata_updated on public.chat_metadata(last_updated);

-- =========================================
-- Table: chat_context_queue
-- =========================================

create table if not exists public.chat_context_queue (
    id uuid primary key default gen_random_uuid(),
    chat_id text not null references public.conversations(id) on delete cascade,
    new_context_snippet text not null,
    status varchar(50) not null default 'pending_summarization',
    created_at timestamptz default now() not null,
    processed_at timestamptz,
    retry_count integer default 0 not null,
    error_message text
);

create index if not exists idx_chat_context_queue_status on public.chat_context_queue(status, created_at);
create index if not exists idx_chat_context_queue_chat_id on public.chat_context_queue(chat_id);

commit;

