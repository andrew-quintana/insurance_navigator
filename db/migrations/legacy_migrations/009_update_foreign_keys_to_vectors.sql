-- Migration: Remove Foreign Key References to Legacy Tables
-- Description: Removes foreign key constraints to allow deletion of legacy tables

BEGIN;

-- Drop existing foreign key constraints that reference policy_records
ALTER TABLE user_policy_links DROP CONSTRAINT IF EXISTS user_policy_links_policy_id_fkey;
ALTER TABLE policy_access_logs DROP CONSTRAINT IF EXISTS policy_access_logs_policy_id_fkey;
ALTER TABLE agent_policy_context DROP CONSTRAINT IF EXISTS agent_policy_context_policy_id_fkey;

-- Since we have multiple vector records per policy_id, we cannot create a unique constraint
-- and thus cannot add foreign key constraints to the vector table
-- For sample data, we'll proceed without these constraints and handle referential integrity in the application layer

COMMIT; 