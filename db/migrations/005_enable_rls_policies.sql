-- Enable RLS Policies Migration
-- Version: 005
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
-- CREATE RLS POLICIES FOR USERS TABLE
-- =============================================================================

-- Users can only access their own records
CREATE POLICY "users_self_select" ON public.users
    FOR SELECT USING (id = auth.uid());

CREATE POLICY "users_self_update" ON public.users
    FOR UPDATE USING (id = auth.uid());

-- Admin users can access all user records
CREATE POLICY "users_admin_access" ON public.users
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid()
            AND r.name = 'admin'
        )
    );

-- =============================================================================
-- CREATE RLS POLICIES FOR POLICY_RECORDS TABLE
-- =============================================================================

-- Enable the previously commented out policy with improvements
CREATE POLICY "policy_records_user_access" ON public.policy_records
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_policy_links
            WHERE user_policy_links.policy_id = policy_records.policy_id
            AND user_policy_links.user_id = auth.uid()
            AND user_policy_links.relationship_verified = true
        )
    );

-- Admin users can access all policy records
CREATE POLICY "policy_records_admin_access" ON public.policy_records
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid()
            AND r.name = 'admin'
        )
    );

-- Allow users to insert their own policy records
CREATE POLICY "policy_records_user_insert" ON public.policy_records
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_policy_links
            WHERE user_policy_links.policy_id = policy_records.policy_id
            AND user_policy_links.user_id = auth.uid()
            AND user_policy_links.role IN ('subscriber', 'self')
        )
    );

-- =============================================================================
-- CREATE RLS POLICIES FOR USER_POLICY_LINKS TABLE
-- =============================================================================

-- Users can only see their own policy links
CREATE POLICY "user_policy_links_user_access" ON public.user_policy_links
    FOR SELECT USING (user_id = auth.uid());

-- Users can insert their own policy links
CREATE POLICY "user_policy_links_user_insert" ON public.user_policy_links
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- Users can update their own policy links
CREATE POLICY "user_policy_links_user_update" ON public.user_policy_links
    FOR UPDATE USING (user_id = auth.uid());

-- Admin users can access all policy links
CREATE POLICY "user_policy_links_admin_access" ON public.user_policy_links
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid()
            AND r.name = 'admin'
        )
    );

-- =============================================================================
-- CREATE RLS POLICIES FOR POLICY_ACCESS_LOGS TABLE
-- =============================================================================

-- Users can only see logs related to themselves
CREATE POLICY "policy_access_logs_user_access" ON public.policy_access_logs
    FOR SELECT USING (user_id = auth.uid());

-- Admin users can see all access logs
CREATE POLICY "policy_access_logs_admin_access" ON public.policy_access_logs
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid()
            AND r.name = 'admin'
        )
    );

-- Allow system to insert access logs
CREATE POLICY "policy_access_logs_system_insert" ON public.policy_access_logs
    FOR INSERT WITH CHECK (true);

-- =============================================================================
-- CREATE RLS POLICIES FOR AGENT_POLICY_CONTEXT TABLE
-- =============================================================================

-- Users can only see their own agent context
CREATE POLICY "agent_policy_context_user_access" ON public.agent_policy_context
    FOR SELECT USING (user_id = auth.uid());

-- Admin users can access all agent context
CREATE POLICY "agent_policy_context_admin_access" ON public.agent_policy_context
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid()
            AND r.name = 'admin'
        )
    );

-- Allow system to insert agent context
CREATE POLICY "agent_policy_context_system_insert" ON public.agent_policy_context
    FOR INSERT WITH CHECK (true);

-- =============================================================================
-- CREATE RLS POLICIES FOR ROLES TABLE
-- =============================================================================

-- Admin users can manage roles
CREATE POLICY "roles_admin_access" ON public.roles
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid()
            AND r.name = 'admin'
        )
    );

-- All authenticated users can read roles for UI purposes
CREATE POLICY "roles_read_access" ON public.roles
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- =============================================================================
-- CREATE RLS POLICIES FOR USER_ROLES TABLE
-- =============================================================================

-- Users can see their own roles
CREATE POLICY "user_roles_self_access" ON public.user_roles
    FOR SELECT USING (user_id = auth.uid());

-- Admin users can manage all user roles
CREATE POLICY "user_roles_admin_access" ON public.user_roles
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid()
            AND r.name = 'admin'
        )
    );

-- =============================================================================
-- CREATE RLS POLICIES FOR ENCRYPTION_KEYS TABLE
-- =============================================================================

-- Only admin users can access encryption keys
CREATE POLICY "encryption_keys_admin_only" ON public.encryption_keys
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid()
            AND r.name = 'admin'
        )
    );

-- =============================================================================
-- CREATE RLS POLICIES FOR POLICY_ACCESS_POLICIES TABLE
-- =============================================================================

-- Only admin users can manage access policies
CREATE POLICY "policy_access_policies_admin_only" ON public.policy_access_policies
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid()
            AND r.name = 'admin'
        )
    );

-- =============================================================================
-- CREATE HELPER FUNCTIONS FOR RLS
-- =============================================================================

-- Function to check if current user is admin
CREATE OR REPLACE FUNCTION auth.is_admin()
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid()
        AND r.name = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if current user has specific role
CREATE OR REPLACE FUNCTION auth.has_role(role_name text)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid()
        AND r.name = role_name
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user has access to specific policy
CREATE OR REPLACE FUNCTION auth.can_access_policy(policy_uuid uuid)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_policy_links
        WHERE policy_id = policy_uuid
        AND user_id = auth.uid()
        AND relationship_verified = true
    ) OR auth.is_admin();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

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
GRANT EXECUTE ON FUNCTION auth.is_admin() TO authenticated;
GRANT EXECUTE ON FUNCTION auth.has_role(text) TO authenticated;
GRANT EXECUTE ON FUNCTION auth.can_access_policy(uuid) TO authenticated;

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

COMMENT ON FUNCTION auth.is_admin() IS 
'Check if the current authenticated user has admin role';

COMMENT ON FUNCTION auth.has_role(text) IS 
'Check if the current authenticated user has a specific role';

COMMENT ON FUNCTION auth.can_access_policy(uuid) IS 
'Check if the current user can access a specific policy record'; 