-- Fix Function Security Migration (Version 2)
-- Version: 006 V2
-- Description: Fix security vulnerabilities in public schema functions with proper dependency handling

-- =============================================================================
-- SECURITY FIXES FOR PUBLIC SCHEMA FUNCTIONS
-- =============================================================================

-- First, update policies that depend on is_admin_user to use is_admin instead
-- This allows us to safely drop the vulnerable function

-- Update system_metadata policy to use is_admin instead of is_admin_user
DROP POLICY IF EXISTS "system_metadata_admin_only" ON public.system_metadata;

-- Drop existing vulnerable functions (cascade to handle any remaining dependencies)
DROP FUNCTION IF EXISTS public.is_admin() CASCADE;
DROP FUNCTION IF EXISTS public.is_admin_user() CASCADE;
DROP FUNCTION IF EXISTS public.get_current_user_id() CASCADE;

-- =============================================================================
-- SECURE ADMIN CHECK FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean AS $$
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Check if current user has admin role through proper authentication
    -- This uses session context rather than JWT parsing to avoid injection
    RETURN EXISTS (
        SELECT 1 
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = COALESCE(
            -- Try to get user ID from session context first
            NULLIF(current_setting('rls.current_user_id', true), '')::uuid,
            -- Fallback to auth schema if available
            (SELECT auth.uid())
        )
        AND r.name = 'admin'
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Fail secure: if any error occurs, deny admin access
        RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- SECURE USER ID FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION public.get_current_user_id()
RETURNS uuid AS $$
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Get user ID from session context or auth system
    RETURN COALESCE(
        -- Primary: session context (set by application)
        NULLIF(current_setting('rls.current_user_id', true), '')::uuid,
        -- Secondary: auth schema if available
        (SELECT auth.uid()),
        -- Fallback: null (no authenticated user)
        NULL
    );
EXCEPTION
    WHEN OTHERS THEN
        -- If any error occurs, return null (no authenticated user)
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- SECURE ROLE CHECK FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION public.has_role(role_name text)
RETURNS boolean AS $$
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Validate input parameter
    IF role_name IS NULL OR trim(role_name) = '' THEN
        RETURN false;
    END IF;
    
    -- Check if current user has the specified role
    RETURN EXISTS (
        SELECT 1 
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = public.get_current_user_id()
        AND r.name = trim(role_name)
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Fail secure: if any error occurs, deny role access
        RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- SECURE POLICY ACCESS FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION public.can_access_policy(policy_uuid uuid)
RETURNS boolean AS $$
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Validate input parameter
    IF policy_uuid IS NULL THEN
        RETURN false;
    END IF;
    
    -- Admin users can access all policies
    IF public.is_admin() THEN
        RETURN true;
    END IF;
    
    -- Regular users can access policies they are linked to with verified relationships
    RETURN EXISTS (
        SELECT 1 
        FROM user_policy_links
        WHERE policy_id = policy_uuid
        AND user_id = public.get_current_user_id()
        AND relationship_verified = true
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Fail secure: if any error occurs, deny policy access
        RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- SECURE SESSION MANAGEMENT FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION public.set_current_user_context(user_uuid uuid)
RETURNS void AS $$
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Validate input parameter
    IF user_uuid IS NULL THEN
        RAISE EXCEPTION 'User UUID cannot be null';
    END IF;
    
    -- Verify the user exists before setting context
    IF NOT EXISTS (SELECT 1 FROM users WHERE id = user_uuid) THEN
        RAISE EXCEPTION 'User does not exist';
    END IF;
    
    -- Set the user context for RLS policies
    PERFORM set_config('rls.current_user_id', user_uuid::text, false);
EXCEPTION
    WHEN OTHERS THEN
        -- Don't expose internal errors
        RAISE EXCEPTION 'Failed to set user context';
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- AUDIT LOG FUNCTION (SECURE)
-- =============================================================================

CREATE OR REPLACE FUNCTION public.log_policy_access(
    policy_uuid uuid,
    access_type text,
    success boolean DEFAULT true,
    details jsonb DEFAULT '{}'::jsonb
)
RETURNS void AS $$
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Validate required parameters
    IF policy_uuid IS NULL OR access_type IS NULL THEN
        RETURN; -- Silently fail for audit logs to not break application flow
    END IF;
    
    -- Insert audit log entry
    INSERT INTO policy_access_logs (
        user_id,
        policy_id,
        access_type,
        success,
        access_details,
        timestamp
    ) VALUES (
        public.get_current_user_id(),
        policy_uuid,
        trim(access_type),
        success,
        details,
        CURRENT_TIMESTAMP
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Silently fail for audit logs to not break application flow
        RETURN;
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

-- =============================================================================
-- RECREATE SYSTEM METADATA POLICY WITH SECURE FUNCTION
-- =============================================================================

-- Recreate the policy using the secure is_admin function
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'system_metadata' AND table_schema = 'public') THEN
        EXECUTE 'CREATE POLICY "system_metadata_admin_only" ON public.system_metadata FOR ALL USING (public.is_admin())';
    END IF;
END
$$;

-- =============================================================================
-- UPDATE ALL POLICIES TO USE SECURE FUNCTIONS
-- =============================================================================

-- Update policies that were using is_admin_user to use the secure is_admin function
-- This ensures all policies use the new secure authentication

-- Update users policies
DROP POLICY IF EXISTS "users_admin_access" ON public.users;
CREATE POLICY "users_admin_access" ON public.users
    FOR ALL USING (public.is_admin());

-- Update policy_records policies
DROP POLICY IF EXISTS "policy_records_admin_access" ON public.policy_records;
CREATE POLICY "policy_records_admin_access" ON public.policy_records
    FOR ALL USING (public.is_admin());

-- Update user_policy_links policies
DROP POLICY IF EXISTS "user_policy_links_admin_access" ON public.user_policy_links;
CREATE POLICY "user_policy_links_admin_access" ON public.user_policy_links
    FOR ALL USING (public.is_admin());

-- Update policy_access_logs policies
DROP POLICY IF EXISTS "policy_access_logs_admin_access" ON public.policy_access_logs;
CREATE POLICY "policy_access_logs_admin_access" ON public.policy_access_logs
    FOR ALL USING (public.is_admin());

-- Update agent_policy_context policies
DROP POLICY IF EXISTS "agent_policy_context_admin_access" ON public.agent_policy_context;
CREATE POLICY "agent_policy_context_admin_access" ON public.agent_policy_context
    FOR ALL USING (public.is_admin());

-- Update roles policies
DROP POLICY IF EXISTS "roles_admin_access" ON public.roles;
CREATE POLICY "roles_admin_access" ON public.roles
    FOR ALL USING (public.is_admin());

-- Update user_roles policies
DROP POLICY IF EXISTS "user_roles_admin_access" ON public.user_roles;
CREATE POLICY "user_roles_admin_access" ON public.user_roles
    FOR ALL USING (public.is_admin());

-- Update encryption_keys policies
DROP POLICY IF EXISTS "encryption_keys_admin_only" ON public.encryption_keys;
CREATE POLICY "encryption_keys_admin_only" ON public.encryption_keys
    FOR ALL USING (public.is_admin());

-- Update policy_access_policies policies
DROP POLICY IF EXISTS "policy_access_policies_admin_only" ON public.policy_access_policies;
CREATE POLICY "policy_access_policies_admin_only" ON public.policy_access_policies
    FOR ALL USING (public.is_admin());

-- Update user access policies to use secure get_current_user_id
DROP POLICY IF EXISTS "users_self_select" ON public.users;
CREATE POLICY "users_self_select" ON public.users
    FOR SELECT USING (id = public.get_current_user_id());

DROP POLICY IF EXISTS "users_self_update" ON public.users;
CREATE POLICY "users_self_update" ON public.users
    FOR UPDATE USING (id = public.get_current_user_id());

-- Update user_policy_links user policies
DROP POLICY IF EXISTS "user_policy_links_user_access" ON public.user_policy_links;
CREATE POLICY "user_policy_links_user_access" ON public.user_policy_links
    FOR SELECT USING (user_id = public.get_current_user_id());

DROP POLICY IF EXISTS "user_policy_links_user_insert" ON public.user_policy_links;
CREATE POLICY "user_policy_links_user_insert" ON public.user_policy_links
    FOR INSERT WITH CHECK (user_id = public.get_current_user_id());

DROP POLICY IF EXISTS "user_policy_links_user_update" ON public.user_policy_links;
CREATE POLICY "user_policy_links_user_update" ON public.user_policy_links
    FOR UPDATE USING (user_id = public.get_current_user_id());

-- Update policy_access_logs user policies
DROP POLICY IF EXISTS "policy_access_logs_user_access" ON public.policy_access_logs;
CREATE POLICY "policy_access_logs_user_access" ON public.policy_access_logs
    FOR SELECT USING (user_id = public.get_current_user_id());

-- Update agent_policy_context user policies
DROP POLICY IF EXISTS "agent_policy_context_user_access" ON public.agent_policy_context;
CREATE POLICY "agent_policy_context_user_access" ON public.agent_policy_context
    FOR SELECT USING (user_id = public.get_current_user_id());

-- Update user_roles self access policy
DROP POLICY IF EXISTS "user_roles_self_access" ON public.user_roles;
CREATE POLICY "user_roles_self_access" ON public.user_roles
    FOR SELECT USING (user_id = public.get_current_user_id());

-- Update policy_records user access policy to use secure functions
DROP POLICY IF EXISTS "policy_records_user_access" ON public.policy_records;
CREATE POLICY "policy_records_user_access" ON public.policy_records
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_policy_links
            WHERE user_policy_links.policy_id = policy_records.policy_id
            AND user_policy_links.user_id = public.get_current_user_id()
            AND user_policy_links.relationship_verified = true
        )
    );

-- =============================================================================
-- UPDATE GRANTS AND PERMISSIONS
-- =============================================================================

-- Grant execute permissions to authenticated users only (not PUBLIC)
REVOKE ALL ON FUNCTION public.is_admin() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_current_user_id() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.has_role(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.can_access_policy(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.set_current_user_context(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.log_policy_access(uuid, text, boolean, jsonb) FROM PUBLIC;

-- Grant to authenticated role (if it exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        GRANT EXECUTE ON FUNCTION public.is_admin() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.get_current_user_id() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.has_role(text) TO authenticated;
        GRANT EXECUTE ON FUNCTION public.can_access_policy(uuid) TO authenticated;
        GRANT EXECUTE ON FUNCTION public.set_current_user_context(uuid) TO authenticated;
        GRANT EXECUTE ON FUNCTION public.log_policy_access(uuid, text, boolean, jsonb) TO authenticated;
    ELSE
        -- Fallback: grant to current database user
        GRANT EXECUTE ON FUNCTION public.is_admin() TO CURRENT_USER;
        GRANT EXECUTE ON FUNCTION public.get_current_user_id() TO CURRENT_USER;
        GRANT EXECUTE ON FUNCTION public.has_role(text) TO CURRENT_USER;
        GRANT EXECUTE ON FUNCTION public.can_access_policy(uuid) TO CURRENT_USER;
        GRANT EXECUTE ON FUNCTION public.set_current_user_context(uuid) TO CURRENT_USER;
        GRANT EXECUTE ON FUNCTION public.log_policy_access(uuid, text, boolean, jsonb) TO CURRENT_USER;
    END IF;
END $$;

-- =============================================================================
-- SECURITY COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON FUNCTION public.is_admin() IS 
'Securely check if the current authenticated user has admin role. Uses SECURITY INVOKER and fixed search path.';

COMMENT ON FUNCTION public.get_current_user_id() IS 
'Securely get the current authenticated user ID from session context or auth system. Uses SECURITY INVOKER and fixed search path.';

COMMENT ON FUNCTION public.has_role(text) IS 
'Securely check if the current authenticated user has a specific role. Uses SECURITY INVOKER and fixed search path.';

COMMENT ON FUNCTION public.can_access_policy(uuid) IS 
'Securely check if the current user can access a specific policy record. Uses SECURITY INVOKER and fixed search path.';

COMMENT ON FUNCTION public.set_current_user_context(uuid) IS 
'Securely set user context for RLS policies. Validates user existence. Uses SECURITY INVOKER and fixed search path.';

COMMENT ON FUNCTION public.log_policy_access(uuid, text, boolean, jsonb) IS 
'Securely log policy access attempts for audit trail. Uses SECURITY INVOKER and fixed search path.';

-- =============================================================================
-- VERIFY SECURITY CONFIGURATION
-- =============================================================================

-- Verify all functions use SECURITY INVOKER
DO $$
DECLARE
    func_record RECORD;
    security_definer_count INTEGER := 0;
BEGIN
    FOR func_record IN 
        SELECT proname, prosecdef 
        FROM pg_proc 
        WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        AND proname IN ('is_admin', 'get_current_user_id', 'has_role', 'can_access_policy', 'set_current_user_context', 'log_policy_access')
    LOOP
        IF func_record.prosecdef THEN
            security_definer_count := security_definer_count + 1;
            RAISE WARNING 'Function % still uses SECURITY DEFINER', func_record.proname;
        END IF;
    END LOOP;
    
    IF security_definer_count = 0 THEN
        RAISE NOTICE 'SUCCESS: All security functions now use SECURITY INVOKER';
    ELSE
        RAISE WARNING 'WARNING: % functions still use SECURITY DEFINER', security_definer_count;
    END IF;
END $$; 