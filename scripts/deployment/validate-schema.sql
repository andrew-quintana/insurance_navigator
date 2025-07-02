-- Validate core tables exist
DO $$
BEGIN
    -- Check users table
    IF NOT EXISTS (
        SELECT FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename = 'users'
    ) THEN
        RAISE EXCEPTION 'users table does not exist';
    END IF;

    -- Check documents table
    IF NOT EXISTS (
        SELECT FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename = 'documents'
    ) THEN
        RAISE EXCEPTION 'documents table does not exist';
    END IF;
END
$$;

-- Validate RLS is enabled
DO $$
DECLARE
    tables text[] := ARRAY['users', 'documents'];
    table_name text;
BEGIN
    FOREACH table_name IN ARRAY tables
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM pg_tables t
            JOIN pg_policies p ON p.tablename = t.tablename
            WHERE t.schemaname = 'public' 
            AND t.tablename = table_name
        ) THEN
            RAISE EXCEPTION 'RLS policies not found for table %', table_name;
        END IF;
    END LOOP;
END
$$;

-- Validate required columns
DO $$
BEGIN
    -- Check users table columns
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name IN ('id', 'email', 'name', 'created_at', 'last_login', 'session_expires')
    ) THEN
        RAISE EXCEPTION 'Missing required columns in users table';
    END IF;

    -- Check documents table columns
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'documents'
        AND column_name IN ('id', 'user_id', 'filename', 'content_type', 'status', 'created_at', 'updated_at', 'storage_path', 'error_message')
    ) THEN
        RAISE EXCEPTION 'Missing required columns in documents table';
    END IF;
END
$$;

-- Validate foreign key constraints
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu 
        ON tc.constraint_name = ccu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name = 'documents'
        AND ccu.table_name = 'users'
    ) THEN
        RAISE EXCEPTION 'Foreign key constraint missing between documents and users tables';
    END IF;
END
$$;

-- Validate indexes
DO $$
BEGIN
    -- Check users indexes
    IF NOT EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = 'users'
        AND indexdef LIKE '%email%'
    ) THEN
        RAISE EXCEPTION 'Index on users.email not found';
    END IF;

    -- Check documents indexes
    IF NOT EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = 'documents'
        AND indexdef LIKE '%user_id%'
    ) THEN
        RAISE EXCEPTION 'Index on documents.user_id not found';
    END IF;
END
$$;

-- Validate audit logging is enabled
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_extension
        WHERE extname = 'pgaudit'
    ) THEN
        RAISE WARNING 'pgaudit extension is not installed';
    END IF;
END
$$; 