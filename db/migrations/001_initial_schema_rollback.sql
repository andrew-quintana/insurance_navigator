-- Rollback Migration for Initial Schema
-- Version: 001_rollback
-- Description: Removes all tables and extensions created in the initial migration

-- Drop RLS Policies
DROP POLICY IF EXISTS policy_records_access ON policy_records;
DROP POLICY IF EXISTS user_policy_links_access ON user_policy_links;
DROP POLICY IF EXISTS policy_access_logs_access ON policy_access_logs;

-- Disable RLS
ALTER TABLE policy_records DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_policy_links DISABLE ROW LEVEL SECURITY;
ALTER TABLE policy_access_logs DISABLE ROW LEVEL SECURITY;

-- Drop Indexes
DROP INDEX IF EXISTS idx_policy_access_logs_policy;
DROP INDEX IF EXISTS idx_policy_access_logs_user;
DROP INDEX IF EXISTS idx_user_policy_links_user;
DROP INDEX IF EXISTS idx_user_policy_links_policy;
DROP INDEX IF EXISTS idx_agent_policy_context_session;
DROP INDEX IF EXISTS idx_user_roles_user;
DROP INDEX IF EXISTS idx_user_roles_role;

-- Drop Tables
DROP TABLE IF EXISTS agent_policy_context;
DROP TABLE IF EXISTS policy_access_logs;
DROP TABLE IF EXISTS policy_access_policies;
DROP TABLE IF EXISTS user_policy_links;
DROP TABLE IF EXISTS policy_records;
DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS encryption_keys;

-- Drop Extensions
DROP EXTENSION IF EXISTS "uuid-ossp"; 