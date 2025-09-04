-- 20250904T000000_create_users_table.sql
-- Create users table for user registration and authentication
-- This table stores user profile information and HIPAA compliance data

begin;

-- -------------------------------
-- CREATE users table
-- -------------------------------
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

-- -------------------------------
-- CREATE indexes for users table
-- -------------------------------
create unique index if not exists idx_users_email on public.users (email);
create index if not exists idx_users_active on public.users (is_active);
create index if not exists idx_users_created_at on public.users (created_at);

-- -------------------------------
-- ENABLE RLS on users table
-- -------------------------------
alter table public.users enable row level security;

-- -------------------------------
-- CREATE RLS policies for users table
-- -------------------------------
-- Users can only see their own profile
create policy "Users can view own profile" on public.users
    for select using (auth.uid() = id);

-- Users can update their own profile
create policy "Users can update own profile" on public.users
    for update using (auth.uid() = id);

-- Service role can insert users (for registration)
create policy "Service role can insert users" on public.users
    for insert with check (auth.role() = 'service_role');

-- Service role can select all users (for admin operations)
create policy "Service role can select all users" on public.users
    for select using (auth.role() = 'service_role');

-- -------------------------------
-- GRANT permissions
-- -------------------------------
grant usage on schema public to postgres, anon, authenticated, service_role;
grant all on public.users to postgres, service_role;
grant select, update on public.users to authenticated;

-- -------------------------------
-- CREATE handle_updated_at function if it doesn't exist
-- -------------------------------
create or replace function public.handle_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- -------------------------------
-- CREATE trigger for updated_at
-- -------------------------------
create trigger update_users_updated_at
    before update on public.users
    for each row execute function public.handle_updated_at();

-- -------------------------------
-- CREATE function to handle new user creation
-- -------------------------------
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

-- -------------------------------
-- CREATE trigger to automatically create user profile
-- -------------------------------
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

commit;
