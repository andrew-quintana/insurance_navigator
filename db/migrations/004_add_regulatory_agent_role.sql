-- Add Regulatory Agent Role Migration
-- Version: 004
-- Description: Add regulatory agent role and permissions

-- Add regulatory_agent role if it doesn't exist
INSERT INTO roles (name, description)
VALUES (
    'regulatory_agent',
    'Role for accessing and managing regulatory documents'
) ON CONFLICT (name) DO NOTHING;

-- Grant role to admin users
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
CROSS JOIN roles r
WHERE r.name = 'regulatory_agent'
AND EXISTS (
    SELECT 1 FROM user_roles ur
    JOIN roles admin_r ON admin_r.id = ur.role_id
    WHERE ur.user_id = u.id
    AND admin_r.name = 'admin'
)
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Add metadata about the migration
INSERT INTO system_metadata (key, value)
VALUES (
    'regulatory_agent_role',
    jsonb_build_object(
        'added_at', NOW(),
        'version', '1.0',
        'permissions', jsonb_build_array(
            'read_regulatory_docs',
            'write_regulatory_docs',
            'manage_regulatory_docs'
        )
    )
) ON CONFLICT (key) DO UPDATE
SET value = EXCLUDED.value,
    updated_at = NOW(); 