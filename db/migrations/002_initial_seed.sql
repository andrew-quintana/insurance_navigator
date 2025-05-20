-- Initial Seed Data
-- Version: 002
-- Description: Seeds core roles, admin user, and initial encryption key

-- 1. Create Core Roles
INSERT INTO roles (name, description) VALUES
    ('admin', 'System admin with full access'),
    ('agent', 'AI agent or assistant role'),
    ('user', 'Basic end-user role')
ON CONFLICT (name) DO NOTHING;

-- 2. Generate and Store Admin User UUID
DO $$
DECLARE
    admin_user_id UUID;
BEGIN
    -- Generate UUID for admin user
    admin_user_id := gen_random_uuid();
    
    -- Store the UUID in a temporary table for reference
    CREATE TEMP TABLE IF NOT EXISTS temp_admin_user (
        user_id UUID PRIMARY KEY
    );
    
    INSERT INTO temp_admin_user (user_id)
    VALUES (admin_user_id);
    
    -- 3. Link Admin User to Role
    INSERT INTO user_roles (user_id, role_id)
    SELECT admin_user_id, id 
    FROM roles 
    WHERE name = 'admin';
    
    -- Log the admin user ID for reference
    RAISE NOTICE 'Admin user ID: %', admin_user_id;
END $$;

-- 4. Seed Initial Encryption Key
INSERT INTO encryption_keys (key_version, key_status, metadata)
VALUES (
    1, 
    'active',
    jsonb_build_object(
        'created_by', 'system',
        'purpose', 'initial_key',
        'rotation_interval', '30d'
    )
)
ON CONFLICT DO NOTHING;

-- 5. Create Storage Bucket (Note: This needs to be done via Supabase Dashboard or API)
-- Bucket name: documents
-- Visibility: Private
-- Location: Supabase Dashboard → Storage → "New Bucket"

-- Add metadata to track initialization
CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO system_metadata (key, value)
VALUES (
    'initialization',
    jsonb_build_object(
        'completed_at', NOW(),
        'version', '1.0',
        'components', jsonb_build_array(
            'core_roles',
            'admin_user',
            'encryption_key',
            'storage_bucket'
        )
    )
)
ON CONFLICT (key) DO UPDATE
SET value = EXCLUDED.value,
    updated_at = NOW(); 