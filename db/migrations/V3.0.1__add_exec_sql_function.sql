-- =============================================================================
-- ADD EXEC_SQL FUNCTION V3.0.1
-- Description: Add utility function for executing raw SQL commands
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- Create the exec_sql function
CREATE OR REPLACE FUNCTION exec_sql(sql_command text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Execute the SQL command
    EXECUTE sql_command;
EXCEPTION
    WHEN OTHERS THEN
        -- Log error details
        RAISE NOTICE 'Error executing SQL: %', SQLERRM;
        RAISE;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION exec_sql(text) TO authenticated;

-- Record migration completion
INSERT INTO schema_migrations (version) VALUES ('V3.0.1') ON CONFLICT (version) DO NOTHING;

COMMIT;
