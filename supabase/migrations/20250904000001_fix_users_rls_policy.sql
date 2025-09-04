-- Fix RLS policy for users table to allow anon role to insert during registration
-- This is a temporary fix until service role is properly configured

begin;

-- Drop existing insert policies
drop policy if exists "Service role can insert users" on public.users;
drop policy if exists "Anon can insert users during registration" on public.users;

-- Create new policies that allow both service role and anon role to insert
create policy "Service role can insert users" on public.users
    for insert with check (auth.role() = 'service_role');

create policy "Anon can insert users during registration" on public.users
    for insert with check (auth.role() = 'anon');

commit;
