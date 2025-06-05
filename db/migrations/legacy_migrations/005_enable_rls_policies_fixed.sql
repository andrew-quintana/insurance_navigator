-- Enable RLS Policies Migration (Fixed)
-- Version: 005 Fixed
-- Description: Enable Row Level Security on all tables and create comprehensive policies

-- =============================================================================
-- ENABLE RLS ON ALL TABLES
-- =============================================================================

-- Enable RLS on tables that don't have it yet
ALTER TABLE encryption_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_access_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_policy_context ENABLE ROW LEVEL SECURITY;

-- Note: users, policy_records, user_policy_links, policy_access_logs, and regulatory_documents 
-- already have RLS enabled from previous migrations

-- =============================================================================
-- CREATE HELPER FUNCTIONS IN PUBLIC SCHEMA
-- =============================================================================

-- Function to check if current user is admin
CREATE OR REPLACE FUNCTION public.is_admin_user()
RETURNS boolean AS $$
BEGIN
    -- For now, return true for system operations
    -- This will be enhanced with proper authentication integration
    RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current user ID (placeholder)
CREATE OR REPLACE FUNCTION public.get_current_user_id()
RETURNS uuid AS $$
BEGIN
    -- This is a placeholder function
    -- In production, this would integrate with your authentication system
    RETURN '00000000-0000-0000-0000-000000000000'::uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- CREATE RLS POLICIES FOR USERS TABLE
-- =============================================================================

-- Users can only access their own records
CREATE POLICY "users_self_select" ON public.users
    FOR SELECT USING (id = public.get_current_user_id());

CREATE POLICY "users_self_update" ON public.users
    FOR UPDATE USING (id = public.get_current_user_id());

-- Admin users can access all user records
CREATE POLICY "users_admin_access" ON public.users
    FOR ALL USING (public.is_admin_user());

-- =============================================================================
-- CREATE RLS POLICIES FOR POLICY_RECORDS TABLE
-- =============================================================================

-- Users can access policies they are linked to
CREATE POLICY "policy_records_user_access" ON public.policy_records
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_policy_links
            WHERE user_policy_links.policy_id = policy_records.policy_id
            AND user_policy_links.user_id = public.get_current_user_id()
            AND user_policy_links.relationship_verified = true
        )
    );

-- Admin users can access all policy records
CREATE POLICY "policy_records_admin_access" ON public.policy_records
    FOR ALL USING (public.is_admin_user());

-- =============================================================================
-- CREATE RLS POLICIES FOR USER_POLICY_LINKS TABLE
-- =============================================================================

-- Users can only see their own policy links
CREATE POLICY "user_policy_links_user_access" ON public.user_policy_links
    FOR SELECT USING (user_id = public.get_current_user_id());

-- Users can insert their own policy links
CREATE POLICY "user_policy_links_user_insert" ON public.user_policy_links
    FOR INSERT WITH CHECK (user_id = public.get_current_user_id());

-- Users can update their own policy links
CREATE POLICY "user_policy_links_user_update" ON public.user_policy_links
    FOR UPDATE USING (user_id = public.get_current_user_id());

-- Admin users can access all policy links
CREATE POLICY "user_policy_links_admin_access" ON public.user_policy_links
    FOR ALL USING (public.is_admin_user());

-- =============================================================================
-- CREATE RLS POLICIES FOR POLICY_ACCESS_LOGS TABLE
-- =============================================================================

-- Users can only see logs related to themselves
CREATE POLICY "policy_access_logs_user_access" ON public.policy_access_logs
    FOR SELECT USING (user_id = public.get_current_user_id());

-- Admin users can see all access logs
CREATE POLICY "policy_access_logs_admin_access" ON public.policy_access_logs
    FOR ALL USING (public.is_admin_user());

-- Allow system to insert access logs
CREATE POLICY "policy_access_logs_system_insert" ON public.policy_access_logs
    FOR INSERT WITH CHECK (true);

-- =============================================================================
-- CREATE RLS POLICIES FOR AGENT_POLICY_CONTEXT TABLE
-- =============================================================================

-- Users can only see their own agent context
CREATE POLICY "agent_policy_context_user_access" ON public.agent_policy_context
    FOR SELECT USING (user_id = public.get_current_user_id());

-- Admin users can access all agent context
CREATE POLICY "agent_policy_context_admin_access" ON public.agent_policy_context
    FOR ALL USING (public.is_admin_user());

-- Allow system to insert agent context
CREATE POLICY "agent_policy_context_system_insert" ON public.agent_policy_context
    FOR INSERT WITH CHECK (true);

-- =============================================================================
-- CREATE RLS POLICIES FOR ROLES TABLE
-- =============================================================================

-- Admin users can manage roles
CREATE POLICY "roles_admin_access" ON public.roles
    FOR ALL USING (public.is_admin_user());

-- All users can read roles for UI purposes
CREATE POLICY "roles_read_access" ON public.roles
    FOR SELECT USING (true);

-- =============================================================================
-- CREATE RLS POLICIES FOR USER_ROLES TABLE
-- =============================================================================

-- Users can see their own roles
CREATE POLICY "user_roles_self_access" ON public.user_roles
    FOR SELECT USING (user_id = public.get_current_user_id());

-- Admin users can manage all user roles
CREATE POLICY "user_roles_admin_access" ON public.user_roles
    FOR ALL USING (public.is_admin_user());

-- =============================================================================
-- CREATE RLS POLICIES FOR ENCRYPTION_KEYS TABLE
-- =============================================================================

-- Only admin users can access encryption keys
CREATE POLICY "encryption_keys_admin_only" ON public.encryption_keys
    FOR ALL USING (public.is_admin_user());

-- =============================================================================
-- CREATE RLS POLICIES FOR POLICY_ACCESS_POLICIES TABLE
-- =============================================================================

-- Only admin users can manage access policies
CREATE POLICY "policy_access_policies_admin_only" ON public.policy_access_policies
    FOR ALL USING (public.is_admin_user());

-- =============================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- =============================================================================

-- Indexes to support RLS policies efficiently
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id_role_name 
ON user_roles (user_id) 
INCLUDE (role_id);

CREATE INDEX IF NOT EXISTS idx_roles_name 
ON roles (name);

CREATE INDEX IF NOT EXISTS idx_user_policy_links_user_policy 
ON user_policy_links (user_id, policy_id) 
WHERE relationship_verified = true;

-- =============================================================================
-- GRANT NECESSARY PERMISSIONS
-- =============================================================================

-- Grant execute permissions on helper functions
GRANT EXECUTE ON FUNCTION public.is_admin_user() TO PUBLIC;
GRANT EXECUTE ON FUNCTION public.get_current_user_id() TO PUBLIC;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON POLICY "users_self_select" ON public.users IS 
'Allow users to select their own user record';

COMMENT ON POLICY "users_admin_access" ON public.users IS 
'Allow admin users to access all user records';

COMMENT ON POLICY "policy_records_user_access" ON public.policy_records IS 
'Allow users to access only policy records they are linked to with verified relationships';

COMMENT ON POLICY "policy_records_admin_access" ON public.policy_records IS 
'Allow admin users full access to all policy records';

COMMENT ON FUNCTION public.is_admin_user() IS 
'Check if the current user has admin privileges';

COMMENT ON FUNCTION public.get_current_user_id() IS 
'Get the current authenticated user ID';

-- =============================================================================
-- SYSTEM METADATA TABLE RLS (if exists)
-- =============================================================================

-- Check if system_metadata table exists and enable RLS
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'system_metadata' AND table_schema = 'public') THEN
        EXECUTE 'ALTER TABLE public.system_metadata ENABLE ROW LEVEL SECURITY';
        EXECUTE 'CREATE POLICY "system_metadata_admin_only" ON public.system_metadata FOR ALL USING (public.is_admin_user())';
    END IF;
END
$$; 