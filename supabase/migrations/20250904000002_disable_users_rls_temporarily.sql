-- Temporarily disable RLS on users table for debugging
-- This is a temporary fix to allow user registration to work

begin;

-- Disable RLS on users table temporarily
alter table public.users disable row level security;

commit;

