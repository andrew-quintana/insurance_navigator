-- Phase 3: Upload Pipeline RLS Final Update
-- This migration focuses ONLY on upload_pipeline schema and ensures proper RLS integration
-- with Supabase's auth.users table. Removes any references to documents schema.

begin;

-- -------------------------------
-- UPDATE UPLOAD_PIPELINE RLS POLICIES
-- -------------------------------
-- The upload_pipeline schema already has correct RLS policies using auth.uid()
-- Let's ensure they are comprehensive and working properly

-- Documents table: users can only access their own documents
drop policy if exists doc_select_self on upload_pipeline.documents;
create policy doc_select_self on upload_pipeline.documents
    for select using (user_id = auth.uid());

drop policy if exists doc_insert_self on upload_pipeline.documents;
create policy doc_insert_self on upload_pipeline.documents
    for insert with check (user_id = auth.uid());

drop policy if exists doc_update_self on upload_pipeline.documents;
create policy doc_update_self on upload_pipeline.documents
    for update using (user_id = auth.uid())
    with check (user_id = auth.uid());

drop policy if exists doc_delete_self on upload_pipeline.documents;
create policy doc_delete_self on upload_pipeline.documents
    for delete using (user_id = auth.uid());

-- Service role policies for documents
drop policy if exists doc_service_all on upload_pipeline.documents;
create policy doc_service_all on upload_pipeline.documents
    for all to service_role using (true) with check (true);

-- Document chunks: users can only see chunks from their documents
drop policy if exists chunk_select_self on upload_pipeline.document_chunks;
create policy chunk_select_self on upload_pipeline.document_chunks
    for select using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.document_chunks.document_id
                  and d.user_id = auth.uid())
    );

drop policy if exists chunk_insert_self on upload_pipeline.document_chunks;
create policy chunk_insert_self on upload_pipeline.document_chunks
    for insert with check (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.document_chunks.document_id
                  and d.user_id = auth.uid())
    );

drop policy if exists chunk_update_self on upload_pipeline.document_chunks;
create policy chunk_update_self on upload_pipeline.document_chunks
    for update using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.document_chunks.document_id
                  and d.user_id = auth.uid())
    )
    with check (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.document_chunks.document_id
                  and d.user_id = auth.uid())
    );

drop policy if exists chunk_delete_self on upload_pipeline.document_chunks;
create policy chunk_delete_self on upload_pipeline.document_chunks
    for delete using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.document_chunks.document_id
                  and d.user_id = auth.uid())
    );

-- Service role policies for document chunks
drop policy if exists chunk_service_all on upload_pipeline.document_chunks;
create policy chunk_service_all on upload_pipeline.document_chunks
    for all to service_role using (true) with check (true);

-- Upload jobs: users can see jobs for their documents
drop policy if exists job_select_self on upload_pipeline.upload_jobs;
create policy job_select_self on upload_pipeline.upload_jobs
    for select using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.upload_jobs.document_id
                  and d.user_id = auth.uid())
    );

drop policy if exists job_insert_self on upload_pipeline.upload_jobs;
create policy job_insert_self on upload_pipeline.upload_jobs
    for insert with check (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.upload_jobs.document_id
                  and d.user_id = auth.uid())
    );

drop policy if exists job_update_self on upload_pipeline.upload_jobs;
create policy job_update_self on upload_pipeline.upload_jobs
    for update using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.upload_jobs.document_id
                  and d.user_id = auth.uid())
    )
    with check (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.upload_jobs.document_id
                  and d.user_id = auth.uid())
    );

drop policy if exists job_delete_self on upload_pipeline.upload_jobs;
create policy job_delete_self on upload_pipeline.upload_jobs
    for delete using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.upload_jobs.document_id
                  and d.user_id = auth.uid())
    );

-- Service role policies for upload jobs
drop policy if exists job_service_all on upload_pipeline.upload_jobs;
create policy job_service_all on upload_pipeline.upload_jobs
    for all to service_role using (true) with check (true);

-- Events: users can see events for their documents
drop policy if exists evt_select_self on upload_pipeline.events;
create policy evt_select_self on upload_pipeline.events
    for select using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.events.document_id
                  and d.user_id = auth.uid())
    );

drop policy if exists evt_insert_self on upload_pipeline.events;
create policy evt_insert_self on upload_pipeline.events
    for insert with check (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.events.document_id
                  and d.user_id = auth.uid())
    );

drop policy if exists evt_update_self on upload_pipeline.events;
create policy evt_update_self on upload_pipeline.events
    for update using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.events.document_id
                  and d.user_id = auth.uid())
    )
    with check (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.events.document_id
                  and d.user_id = auth.uid())
    );

drop policy if exists evt_delete_self on upload_pipeline.events;
create policy evt_delete_self on upload_pipeline.events
    for delete using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.events.document_id
                  and d.user_id = auth.uid())
    );

-- Service role policies for events
drop policy if exists evt_service_all on upload_pipeline.events;
create policy evt_service_all on upload_pipeline.events
    for all to service_role using (true) with check (true);

-- Note: Buffer tables are not used in this implementation
-- Only core tables: documents, document_chunks, upload_jobs, events, webhook_log

-- -------------------------------
-- REMOVE OLD USER CONTEXT FUNCTIONS
-- -------------------------------
-- Remove the old manual user context setting functions
drop function if exists upload_pipeline.set_user_context(uuid);
drop function if exists upload_pipeline.clear_user_context();

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

-- Create a function to check if user exists in auth.users
create or replace function public.user_exists(user_id uuid)
returns boolean as $$
begin
    return exists (select 1 from auth.users where id = user_id);
end;
$$ language plpgsql security definer;

-- Grant execute permissions on helper functions
grant execute on function public.get_user_email(uuid) to authenticated, service_role;
grant execute on function public.get_user_metadata(uuid) to authenticated, service_role;
grant execute on function public.user_exists(uuid) to authenticated, service_role;

-- -------------------------------
-- UPDATE USER_INFO VIEW
-- -------------------------------
-- Update the user_info view to include more useful information
create or replace view public.user_info as
select 
    id,
    email,
    coalesce(raw_user_meta_data->>'name', split_part(email, '@', 1)) as name,
    email_confirmed_at is not null as email_confirmed,
    created_at,
    updated_at,
    last_sign_in_at,
    raw_user_meta_data,
    case 
        when deleted_at is not null then false
        else true
    end as is_active
from auth.users
where deleted_at is null;

-- Grant permissions on the view
grant select on public.user_info to authenticated, service_role;

-- -------------------------------
-- CREATE RLS POLICY TESTING FUNCTIONS
-- -------------------------------
-- Create functions to test RLS policies
create or replace function public.test_upload_pipeline_rls_policies()
returns table (
    table_name text,
    policy_name text,
    policy_type text,
    policy_definition text
) as $$
begin
    return query
    select 
        schemaname||'.'||tablename as table_name,
        policyname as policy_name,
        permissive as policy_type,
        qual as policy_definition
    from pg_policies 
    where schemaname = 'upload_pipeline'
    order by tablename, policyname;
end;
$$ language plpgsql security definer;

-- Grant execute permissions on testing function
grant execute on function public.test_upload_pipeline_rls_policies() to authenticated, service_role;

-- -------------------------------
-- COMMIT TRANSACTION
-- -------------------------------
commit;

-- -------------------------------
-- VERIFICATION QUERIES
-- -------------------------------
-- These queries can be run to verify the migration was successful
-- 
-- -- Check RLS policies
-- select * from public.test_upload_pipeline_rls_policies();
-- 
-- -- Test user access (replace with actual user ID)
-- set local role authenticated;
-- set local "request.jwt.claims" = '{"sub": "user-uuid-here"}';
-- select * from upload_pipeline.documents limit 1;
-- 
-- -- Reset role
-- reset role;
