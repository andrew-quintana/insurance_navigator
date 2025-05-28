-- Rollback RLS Policies Migration
-- Version: 005 Rollback
-- Description: Remove RLS policies and disable RLS on tables (if needed for debugging)

-- =============================================================================
-- WARNING: THIS ROLLBACK SCRIPT DISABLES SECURITY FEATURES
-- Only use this script if you understand the security implications
-- =============================================================================

-- Drop helper functions
DROP FUNCTION IF EXISTS auth.is_admin();
DROP FUNCTION IF EXISTS auth.has_role(text);
DROP FUNCTION IF EXISTS auth.can_access_policy(uuid);

-- =============================================================================
-- DROP RLS POLICIES FOR USERS TABLE
-- =============================================================================

DROP POLICY IF EXISTS "users_self_select" ON public.users;
DROP POLICY IF EXISTS "users_self_update" ON public.users;
DROP POLICY IF EXISTS "users_admin_access" ON public.users;

-- =============================================================================
-- DROP RLS POLICIES FOR POLICY_RECORDS TABLE
-- =============================================================================

DROP POLICY IF EXISTS "policy_records_user_access" ON public.policy_records;
DROP POLICY IF EXISTS "policy_records_admin_access" ON public.policy_records;
DROP POLICY IF EXISTS "policy_records_user_insert" ON public.policy_records;

-- =============================================================================
-- DROP RLS POLICIES FOR USER_POLICY_LINKS TABLE
-- =============================================================================

DROP POLICY IF EXISTS "user_policy_links_user_access" ON public.user_policy_links;
DROP POLICY IF EXISTS "user_policy_links_user_insert" ON public.user_policy_links;
DROP POLICY IF EXISTS "user_policy_links_user_update" ON public.user_policy_links;
DROP POLICY IF EXISTS "user_policy_links_admin_access" ON public.user_policy_links;

-- =============================================================================
-- DROP RLS POLICIES FOR POLICY_ACCESS_LOGS TABLE
-- =============================================================================

DROP POLICY IF EXISTS "policy_access_logs_user_access" ON public.policy_access_logs;
DROP POLICY IF EXISTS "policy_access_logs_admin_access" ON public.policy_access_logs;
DROP POLICY IF EXISTS "policy_access_logs_system_insert" ON public.policy_access_logs;

-- =============================================================================
-- DROP RLS POLICIES FOR AGENT_POLICY_CONTEXT TABLE
-- =============================================================================

DROP POLICY IF EXISTS "agent_policy_context_user_access" ON public.agent_policy_context;
DROP POLICY IF EXISTS "agent_policy_context_admin_access" ON public.agent_policy_context;
DROP POLICY IF EXISTS "agent_policy_context_system_insert" ON public.agent_policy_context;

-- =============================================================================
-- DROP RLS POLICIES FOR ROLES TABLE
-- =============================================================================

DROP POLICY IF EXISTS "roles_admin_access" ON public.roles;
DROP POLICY IF EXISTS "roles_read_access" ON public.roles;

-- =============================================================================
-- DROP RLS POLICIES FOR USER_ROLES TABLE
-- =============================================================================

DROP POLICY IF EXISTS "user_roles_self_access" ON public.user_roles;
DROP POLICY IF EXISTS "user_roles_admin_access" ON public.user_roles;

-- =============================================================================
-- DROP RLS POLICIES FOR ENCRYPTION_KEYS TABLE
-- =============================================================================

DROP POLICY IF EXISTS "encryption_keys_admin_only" ON public.encryption_keys;

-- =============================================================================
-- DROP RLS POLICIES FOR POLICY_ACCESS_POLICIES TABLE
-- =============================================================================

DROP POLICY IF EXISTS "policy_access_policies_admin_only" ON public.policy_access_policies;

-- =============================================================================
-- DISABLE RLS ON TABLES (OPTIONAL - UNCOMMENT IF NEEDED FOR DEBUGGING)
-- =============================================================================

-- WARNING: Uncommenting these lines will disable security features
-- Only do this if you understand the security implications

-- ALTER TABLE encryption_keys DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE roles DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_roles DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE policy_access_policies DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE agent_policy_context DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE users DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE policy_records DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_policy_links DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE policy_access_logs DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE regulatory_documents DISABLE ROW LEVEL SECURITY;

-- =============================================================================
-- DROP PERFORMANCE INDEXES
-- =============================================================================

DROP INDEX IF EXISTS idx_user_roles_user_id_role_name;
DROP INDEX IF EXISTS idx_roles_name;
DROP INDEX IF EXISTS idx_user_policy_links_user_policy; 