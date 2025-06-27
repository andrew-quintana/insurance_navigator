-- =============================================================================
-- CONSOLIDATE AUTHENTICATION SCHEMA
-- Description: Simplify auth schema by consolidating tables and adding role to user profile
-- =============================================================================

BEGIN;

-- =============================================================================
-- BACKUP EXISTING DATA
-- =============================================================================

-- Create temporary table to store user data
CREATE TEMP TABLE temp_user_data AS
SELECT 
    u.id,
    u.email,
    u.encrypted_password,
    u.email_confirmed_at,
    u.confirmed_at,
    p.full_name,
    p.metadata,
    p.last_login,
    r.name as role_name
FROM auth.users u
LEFT JOIN public.user_profiles p ON p.user_id = u.id
LEFT JOIN public.user_roles ur ON ur.user_id = u.id
LEFT JOIN public.roles r ON r.id = ur.role_id;

-- =============================================================================
-- DROP OLD SCHEMA
-- =============================================================================

-- Drop old tables and related objects
DROP TABLE IF EXISTS public.user_roles;
DROP TABLE IF EXISTS public.roles;
ALTER TABLE IF EXISTS public.user_profiles 
    DROP CONSTRAINT IF EXISTS user_profiles_user_id_fkey;
DROP TABLE IF EXISTS public.user_profiles;

-- =============================================================================
-- CREATE NEW SCHEMA
-- =============================================================================

-- Create consolidated user_profiles table
CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- Create index for user lookups
CREATE INDEX idx_user_profiles_user_id ON public.user_profiles(user_id);
CREATE INDEX idx_user_profiles_role ON public.user_profiles(role);

-- =============================================================================
-- RESTORE DATA
-- =============================================================================

-- Restore user data to new schema
INSERT INTO public.user_profiles (
    user_id,
    full_name,
    role,
    metadata,
    last_login
)
SELECT 
    id,
    full_name,
    COALESCE(role_name, 'user'),
    COALESCE(metadata, '{}'::jsonb),
    last_login
FROM temp_user_data;

-- =============================================================================
-- CREATE FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to create user profile on auth.users insert
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (
        user_id,
        full_name,
        role,
        metadata
    )
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'Anonymous User'),
        COALESCE(NEW.raw_user_meta_data->>'role', 'user'),
        COALESCE(NEW.raw_user_meta_data, '{}'::jsonb)
    );
    RETURN NEW;
END;
$$ language 'plpgsql' SECURITY DEFINER;

-- Function to update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop existing triggers
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON public.user_profiles;

-- Create triggers
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- =============================================================================
-- RLS POLICIES
-- =============================================================================

-- Enable RLS
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view their own profile" ON public.user_profiles;
DROP POLICY IF EXISTS "Users can update their own profile" ON public.user_profiles;
DROP POLICY IF EXISTS "Service role has full access to profiles" ON public.user_profiles;

-- Create policies
CREATE POLICY "Users can view their own profile"
    ON public.user_profiles FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own profile"
    ON public.user_profiles FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id AND NEW.role = OLD.role); -- Prevent role self-update

CREATE POLICY "Service role has full access to profiles"
    ON public.user_profiles FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- =============================================================================
-- GRANTS
-- =============================================================================

-- Grant access to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT, UPDATE (full_name, metadata) ON public.user_profiles TO authenticated;

-- Grant access to service role
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO service_role;

COMMIT; 