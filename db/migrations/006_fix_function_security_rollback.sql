-- Rollback Function Security Fixes Migration
-- Version: 006 Rollback
-- Description: Rollback security fixes for public schema functions

-- =============================================================================
-- WARNING: THIS ROLLBACK RESTORES SECURITY VULNERABILITIES
-- Only use this script if you understand the security implications
-- =============================================================================

-- Drop the secure functions
DROP FUNCTION IF EXISTS public.is_admin();
DROP FUNCTION IF EXISTS public.get_current_user_id();
DROP FUNCTION IF EXISTS public.has_role(text);
DROP FUNCTION IF EXISTS public.can_access_policy(uuid);
DROP FUNCTION IF EXISTS public.set_current_user_context(uuid);
DROP FUNCTION IF EXISTS public.log_policy_access(uuid, text, boolean, jsonb);

-- =============================================================================
-- RESTORE ORIGINAL VULNERABLE FUNCTIONS (for rollback purposes only)
-- =============================================================================

-- Restore original is_admin function (vulnerable - no fixed search path)
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean AS $$
BEGIN
    RETURN auth.jwt() ->> 'role' = 'admin';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Restore original is_admin_user function (vulnerable - always returns true)
CREATE OR REPLACE FUNCTION public.is_admin_user()
RETURNS boolean AS $$
BEGIN
    -- For now, return true for system operations
    -- This will be enhanced with proper authentication integration
    RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Restore original get_current_user_id function (vulnerable - hardcoded UUID)
CREATE OR REPLACE FUNCTION public.get_current_user_id()
RETURNS uuid AS $$
BEGIN
    -- This is a placeholder function
    -- In production, this would integrate with your authentication system
    RETURN '00000000-0000-0000-0000-000000000000'::uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- RESTORE ORIGINAL PERMISSIONS
-- =============================================================================

-- Grant execute permissions on restored functions
GRANT EXECUTE ON FUNCTION public.is_admin() TO PUBLIC;
GRANT EXECUTE ON FUNCTION public.is_admin_user() TO PUBLIC;
GRANT EXECUTE ON FUNCTION public.get_current_user_id() TO PUBLIC;

-- =============================================================================
-- RESTORE ORIGINAL COMMENTS
-- =============================================================================

COMMENT ON FUNCTION public.is_admin() IS 
'Check if the current user has admin privileges (VULNERABLE VERSION - RESTORED)';

COMMENT ON FUNCTION public.is_admin_user() IS 
'Check if the current user has admin privileges (VULNERABLE VERSION - RESTORED)';

COMMENT ON FUNCTION public.get_current_user_id() IS 
'Get the current authenticated user ID (VULNERABLE VERSION - RESTORED)';

-- =============================================================================
-- WARNING MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE WARNING '==========================================';
    RAISE WARNING 'SECURITY WARNING: Vulnerable functions restored!';
    RAISE WARNING 'The following security vulnerabilities are now active:';
    RAISE WARNING '1. public.is_admin() has mutable search path';
    RAISE WARNING '2. public.is_admin_user() always returns true';
    RAISE WARNING '3. public.get_current_user_id() returns hardcoded UUID';
    RAISE WARNING 'Please apply security fixes as soon as possible!';
    RAISE WARNING '==========================================';
END $$; 