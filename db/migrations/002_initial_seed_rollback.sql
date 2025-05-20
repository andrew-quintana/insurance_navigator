-- Rollback Initial Seed Data
-- Version: 002_rollback
-- Description: Removes seeded data while preserving schema

-- Remove system metadata
DROP TABLE IF EXISTS system_metadata;

-- Remove admin user role link
DELETE FROM user_roles
WHERE role_id IN (SELECT id FROM roles WHERE name = 'admin');

-- Remove initial encryption key
DELETE FROM encryption_keys
WHERE key_version = 1 AND key_status = 'active';

-- Remove core roles
DELETE FROM roles
WHERE name IN ('admin', 'agent', 'user');

-- Note: Storage bucket needs to be removed manually via Supabase Dashboard
-- Bucket name: documents 