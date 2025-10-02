-- Drop public.users and public.user_info tables
-- This migration removes unused public schema user tables since we're using auth.users exclusively

begin;

-- -------------------------------
-- CHECK AND DROP public.user_info TABLE
-- -------------------------------
do $$
begin
    if exists (select 1 from information_schema.tables where table_name = 'user_info' and table_schema = 'public') then
        -- Drop RLS policies first
        drop policy if exists "Users can view own user_info" on public.user_info;
        drop policy if exists "Users can update own user_info" on public.user_info;
        drop policy if exists "Service role can insert user_info" on public.user_info;
        drop policy if exists "Service role can select all user_info" on public.user_info;
        
        -- Drop triggers
        drop trigger if exists update_user_info_updated_at on public.user_info;
        
        -- Drop indexes
        drop index if exists idx_user_info_user_id;
        drop index if exists idx_user_info_created_at;
        
        -- Drop the table
        drop table public.user_info;
        
        raise notice '✅ Dropped public.user_info table';
    else
        raise notice 'ℹ️ public.user_info table does not exist';
    end if;
end $$;

-- -------------------------------
-- CHECK AND DROP public.users TABLE
-- -------------------------------
do $$
begin
    if exists (select 1 from information_schema.tables where table_name = 'users' and table_schema = 'public') then
        -- Drop RLS policies first
        drop policy if exists "Users can view own profile" on public.users;
        drop policy if exists "Users can update own profile" on public.users;
        drop policy if exists "Service role can insert users" on public.users;
        drop policy if exists "Anon can insert users during registration" on public.users;
        drop policy if exists "Service role can select all users" on public.users;
        
        -- Drop triggers
        drop trigger if exists on_auth_user_created on auth.users;
        drop trigger if exists update_users_updated_at on public.users;
        
        -- Drop functions
        drop function if exists public.handle_new_user();
        
        -- Drop indexes
        drop index if exists idx_users_email;
        drop index if exists idx_users_active;
        drop index if exists idx_users_created_at;
        drop index if exists idx_users_email_confirmed;
        drop index if exists idx_users_auth_method;
        
        -- Drop the table
        drop table public.users;
        
        raise notice '✅ Dropped public.users table';
    else
        raise notice 'ℹ️ public.users table does not exist';
    end if;
end $$;

-- -------------------------------
-- VERIFY CLEANUP
-- -------------------------------
do $$
declare
    user_tables_count integer;
begin
    select count(*) into user_tables_count
    from information_schema.tables 
    where table_schema = 'public' 
    and table_name in ('users', 'user_info');
    
    if user_tables_count = 0 then
        raise notice '✅ Successfully removed all public user tables';
        raise notice '🔐 System now uses auth.users exclusively';
    else
        raise notice '⚠️ Some user tables may still exist: %', user_tables_count;
    end if;
end $$;

commit;
