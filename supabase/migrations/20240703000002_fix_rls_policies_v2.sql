-- =============================================================================
-- FIX RLS POLICIES FOR USERS TABLE V2
-- Description: Fix RLS policies to properly handle service role access
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- =============================================================================
-- STEP 1: DROP ALL EXISTING POLICIES
-- =============================================================================

DROP POLICY IF EXISTS "Users can view their own data" ON public.users;
DROP POLICY IF EXISTS "Users can update their own data" ON public.users;
DROP POLICY IF EXISTS "Service role has full access" ON public.users;
DROP POLICY IF EXISTS "Users can read their own data" ON public.users;
DROP POLICY IF EXISTS "Users can read own record" ON public.users;
DROP POLICY IF EXISTS "Users can update own record" ON public.users;
DROP POLICY IF EXISTS "Allow signup" ON public.users;
DROP POLICY IF EXISTS "Service role has full access to users" ON public.users;

-- =============================================================================
-- STEP 2: ENSURE RLS IS ENABLED
-- =============================================================================

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- STEP 3: CREATE NEW POLICIES
-- =============================================================================

-- Service role has full access (highest priority)
CREATE POLICY "service_role_full_access" ON public.users
    USING (true)
    WITH CHECK (true);

-- Users can read their own data
CREATE POLICY "user_read_own" ON public.users
    FOR SELECT
    TO authenticated
    USING (auth.uid() = id);

-- Users can update their own data
CREATE POLICY "user_update_own" ON public.users
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Allow signup
CREATE POLICY "allow_signup" ON public.users
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- =============================================================================
-- STEP 4: GRANT PERMISSIONS
-- =============================================================================

-- Grant access to authenticated users
GRANT SELECT, UPDATE ON public.users TO authenticated;

-- Grant full access to service role
GRANT ALL ON public.users TO service_role;

COMMIT; 