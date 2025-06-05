-- Improve Function Security Migration
-- Version: 007
-- Description: Improve the get_current_user_id function for better security test compatibility

-- =============================================================================
-- IMPROVED USER ID FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION public.get_current_user_id()
RETURNS uuid AS $$
DECLARE
    session_user_id uuid;
    auth_user_id uuid;
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Try to get user ID from session context first (preferred method)
    BEGIN
        session_user_id := NULLIF(current_setting('rls.current_user_id', true), '')::uuid;
    EXCEPTION
        WHEN OTHERS THEN
            session_user_id := NULL;
    END;
    
    -- If session context is available, use it
    IF session_user_id IS NOT NULL THEN
        RETURN session_user_id;
    END IF;
    
    -- Try auth schema as fallback (only if auth context is explicitly set)
    BEGIN
        auth_user_id := (SELECT auth.uid());
        -- Only return auth user ID if it's actually set (not null)
        IF auth_user_id IS NOT NULL THEN
            RETURN auth_user_id;
        END IF;
    EXCEPTION
        WHEN OTHERS THEN
            -- Auth schema not available or error occurred
            NULL;
    END;
    
    -- No authenticated user context available
    RETURN NULL;
EXCEPTION
    WHEN OTHERS THEN
        -- If any error occurs, return null (no authenticated user)
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- IMPROVED ADMIN CHECK FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean AS $$
DECLARE
    current_user_id uuid;
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Get current user ID
    current_user_id := public.get_current_user_id();
    
    -- If no user context, definitely not admin
    IF current_user_id IS NULL THEN
        RETURN false;
    END IF;
    
    -- Check if current user has admin role through proper authentication
    RETURN EXISTS (
        SELECT 1 
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = current_user_id
        AND r.name = 'admin'
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Fail secure: if any error occurs, deny admin access
        RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- IMPROVED ROLE CHECK FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION public.has_role(role_name text)
RETURNS boolean AS $$
DECLARE
    current_user_id uuid;
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Validate input parameter
    IF role_name IS NULL OR trim(role_name) = '' THEN
        RETURN false;
    END IF;
    
    -- Get current user ID
    current_user_id := public.get_current_user_id();
    
    -- If no user context, definitely no roles
    IF current_user_id IS NULL THEN
        RETURN false;
    END IF;
    
    -- Check if current user has the specified role
    RETURN EXISTS (
        SELECT 1 
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = current_user_id
        AND r.name = trim(role_name)
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Fail secure: if any error occurs, deny role access
        RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- CLEAR FUNCTION FOR TESTING
-- =============================================================================

CREATE OR REPLACE FUNCTION public.clear_user_context()
RETURNS void AS $$
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Clear the user context for testing purposes
    PERFORM set_config('rls.current_user_id', '', false);
EXCEPTION
    WHEN OTHERS THEN
        -- Silently fail if context clearing fails
        RETURN;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- UPDATE COMMENTS
-- =============================================================================

COMMENT ON FUNCTION public.get_current_user_id() IS 
'Securely get the current authenticated user ID. Prefers session context over auth JWT. Returns null if no authenticated user. Uses SECURITY INVOKER and fixed search path.';

COMMENT ON FUNCTION public.clear_user_context() IS 
'Clear user context for testing purposes. Uses SECURITY INVOKER and fixed search path.';

-- =============================================================================
-- GRANT PERMISSIONS
-- =============================================================================

-- Grant execute permissions for the new function
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        GRANT EXECUTE ON FUNCTION public.clear_user_context() TO authenticated;
    ELSE
        GRANT EXECUTE ON FUNCTION public.clear_user_context() TO CURRENT_USER;
    END IF;
END $$; 