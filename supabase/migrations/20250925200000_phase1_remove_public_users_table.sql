-- Phase 1: Remove public.users table and migrate to auth.users only
-- This migration eliminates the architectural conflict by removing the duplicate users table
-- and updating all references to use auth.users directly

begin;

-- -------------------------------
-- BACKUP EXISTING DATA (if needed)
-- -------------------------------
-- Create a backup table with user data before dropping
create table if not exists public.users_backup as 
select * from public.users;

-- -------------------------------
-- DROP TRIGGERS AND FUNCTIONS
-- -------------------------------
-- Drop the trigger that creates user records
drop trigger if exists on_auth_user_created on auth.users;

-- Drop the function that handles new user creation
drop function if exists public.handle_new_user();

-- Drop the updated_at trigger
drop trigger if exists update_users_updated_at on public.users;

-- -------------------------------
-- DROP RLS POLICIES
-- -------------------------------
-- Drop all RLS policies on users table
drop policy if exists "Users can view own profile" on public.users;
drop policy if exists "Users can update own profile" on public.users;
drop policy if exists "Service role can insert users" on public.users;
drop policy if exists "Anon can insert users during registration" on public.users;
drop policy if exists "Service role can select all users" on public.users;

-- -------------------------------
-- DROP INDEXES
-- -------------------------------
drop index if exists idx_users_email;
drop index if exists idx_users_active;
drop index if exists idx_users_created_at;
drop index if exists idx_users_email_confirmed;
drop index if exists idx_users_auth_method;

-- -------------------------------
-- DROP TABLE
-- -------------------------------
-- Drop the public.users table
drop table if exists public.users;

-- -------------------------------
-- UPDATE UPLOAD_PIPELINE RLS POLICIES
-- -------------------------------
-- Update RLS policies to use auth.uid() directly instead of referencing public.users
-- The upload_pipeline tables already use auth.uid() correctly, but let's ensure consistency

-- Documents policy (already correct)
drop policy if exists doc_select_self on upload_pipeline.documents;
create policy doc_select_self on upload_pipeline.documents
    for select using (user_id = auth.uid());

-- Chunks policy (already correct)
drop policy if exists chunk_select_self on upload_pipeline.document_chunks;
create policy chunk_select_self on upload_pipeline.document_chunks
    for select using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.document_chunks.document_id
                  and d.user_id = auth.uid())
    );

-- Jobs policy (already correct)
drop policy if exists job_select_self on upload_pipeline.upload_jobs;
create policy job_select_self on upload_pipeline.upload_jobs
    for select using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.upload_jobs.document_id
                  and d.user_id = auth.uid())
    );

-- Events policy (already correct)
drop policy if exists evt_select_self on upload_pipeline.events;
create policy evt_select_self on upload_pipeline.events
    for select using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.events.document_id
                  and d.user_id = auth.uid())
    );

-- -------------------------------
-- UPDATE DOCUMENTS SCHEMA RLS POLICIES
-- -------------------------------
-- Update documents schema policies to use auth.uid() directly
drop policy if exists "Users can update their own user documents" on documents.documents;
create policy "Users can update their own user documents" on documents.documents
    for update to authenticated
    using (owner = auth.uid() and document_type = 'user_document')
    with check (owner = auth.uid() and document_type = 'user_document');

-- -------------------------------
-- CREATE HELPER FUNCTIONS FOR AUTH.USERS
-- -------------------------------
-- Create a function to get user email from auth.users
create or replace function public.get_user_email(user_id uuid)
returns text as $$
begin
    return (select email from auth.users where id = user_id);
end;
$$ language plpgsql security definer;

-- Create a function to get user metadata from auth.users
create or replace function public.get_user_metadata(user_id uuid)
returns jsonb as $$
begin
    return (select raw_user_meta_data from auth.users where id = user_id);
end;
$$ language plpgsql security definer;

-- Grant execute permissions on helper functions
grant execute on function public.get_user_email(uuid) to authenticated, service_role;
grant execute on function public.get_user_metadata(uuid) to authenticated, service_role;

-- -------------------------------
-- CREATE VIEW FOR USER INFORMATION
-- -------------------------------
-- Create a view that provides user information from auth.users
-- This can be used by the application to get user details
create or replace view public.user_info as
select 
    id,
    email,
    coalesce(raw_user_meta_data->>'name', split_part(email, '@', 1)) as name,
    email_confirmed_at is not null as email_confirmed,
    created_at,
    updated_at,
    last_sign_in_at,
    raw_user_meta_data
from auth.users
where deleted_at is null;

-- Grant permissions on the view
grant select on public.user_info to authenticated, service_role;

-- -------------------------------
-- COMMIT TRANSACTION
-- -------------------------------
commit;

-- -------------------------------
-- VERIFICATION QUERIES
-- -------------------------------
-- These queries can be run to verify the migration was successful
-- 
-- -- Check that public.users table is gone
-- select count(*) from information_schema.tables where table_name = 'users' and table_schema = 'public';
-- 
-- -- Check that auth.users still exists
-- select count(*) from information_schema.tables where table_name = 'users' and table_schema = 'auth';
-- 
-- -- Check that user_info view works
-- select count(*) from public.user_info;
-- 
-- -- Check that RLS policies are working
-- select schemaname, tablename, policyname from pg_policies where tablename in ('documents', 'document_chunks', 'upload_jobs', 'events');
