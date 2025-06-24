-- =============================================================================
-- ADD AUTH HELPER FUNCTIONS V3.0.0.2
-- Description: Add authentication helper functions for RLS policies
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- Create jwt() function to mock JWT claims
CREATE OR REPLACE FUNCTION jwt()
RETURNS TABLE (
    role text,
    iss text,
    sub text,
    email text
)
LANGUAGE sql
STABLE
AS $$
    SELECT 
        COALESCE(current_setting('request.jwt.claims', true)::json->>'role', 'anon')::text AS role,
        COALESCE(current_setting('request.jwt.claims', true)::json->>'iss', '')::text AS iss,
        COALESCE(current_setting('request.jwt.claims', true)::json->>'sub', '')::text AS sub,
        COALESCE(current_setting('request.jwt.claims', true)::json->>'email', '')::text AS email;
$$;

-- Create uid() function to get current user ID
CREATE OR REPLACE FUNCTION uid()
RETURNS uuid
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(
        (current_setting('request.jwt.claims', true)::json->>'sub')::uuid,
        '00000000-0000-0000-0000-000000000000'::uuid
    );
$$;

-- Create is_service_role() function
CREATE OR REPLACE FUNCTION is_service_role()
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(
        current_setting('request.jwt.claims', true)::json->>'role' = 'service_role',
        FALSE
    );
$$;

-- Record migration completion
INSERT INTO schema_migrations (version) VALUES ('V3.0.0.2') ON CONFLICT (version) DO NOTHING;

COMMIT; 