#!/bin/bash

# Script to set up production environment
# Usage: ./setup-production-env.sh [PROJECT_ID]

set -e

if [ -z "$1" ]; then
    echo "Error: Project ID is required"
    echo "Usage: ./setup-production-env.sh [PROJECT_ID]"
    exit 1
fi

PROJECT_ID=$1
ENV_FILE=".env.production"
TEMPLATE_FILE="config/environment/env.production.template"

# Check if template exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Template file not found at $TEMPLATE_FILE"
    exit 1
fi

# Generate secure keys and escape special characters
JWT_SECRET=$(openssl rand -base64 32 | sed 's/[\/&]/\\&/g')
ENCRYPTION_KEY=$(openssl rand -base64 32 | sed 's/[\/&]/\\&/g')

# Create production environment file
cp "$TEMPLATE_FILE" "$ENV_FILE"

# Create a temporary file for substitutions
TMP_FILE=$(mktemp)

# Perform substitutions using a temporary file
cat "$ENV_FILE" | \
    sed "s/\[YOUR_PROJECT_ID\]/$PROJECT_ID/g" | \
    sed "s/\[GENERATE_SECURE_SECRET\]/$JWT_SECRET/g" | \
    sed "s/\[GENERATE_SECURE_KEY\]/$ENCRYPTION_KEY/g" > "$TMP_FILE"

# Move the temporary file back to the original
mv "$TMP_FILE" "$ENV_FILE"

echo "Production environment file created at $ENV_FILE"
echo "Please update the following values manually:"
echo "- NEXT_PUBLIC_SUPABASE_ANON_KEY"
echo "- SUPABASE_SERVICE_ROLE_KEY"
echo "- SUPABASE_DB_PASSWORD"
echo "- LLAMAPARSE_API_KEY"
echo "- OPENAI_API_KEY"
echo "- SENTRY_DSN"

# Verify database schema
echo "Verifying database schema..."
cat << 'EOF' > verify_schema.sql
-- Verify users table
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users';

-- Verify documents table
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'documents';

-- Verify RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('users', 'documents');

-- Verify storage bucket
SELECT id, name, public, file_size_limit, allowed_mime_types
FROM storage.buckets
WHERE id = 'documents';

-- Verify RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('users', 'documents');
EOF

echo "Created verification SQL script at verify_schema.sql"

# Create monitoring setup script
cat << 'EOF' > setup_monitoring.sql
-- Create monitoring view
CREATE VIEW IF NOT EXISTS vw_table_stats AS
SELECT
    schemaname,
    relname,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname = 'public';

-- Create performance logging table
CREATE TABLE IF NOT EXISTS performance_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    query_id TEXT,
    execution_time INTERVAL,
    rows_affected INTEGER,
    query_plan JSONB
);

-- Create alert function for long-running queries
CREATE OR REPLACE FUNCTION alert_long_running_queries()
RETURNS trigger AS $$
BEGIN
    IF NEW.execution_time > interval '30 seconds' THEN
        INSERT INTO alert_logs (alert_type, message)
        VALUES ('long_query', format('Query %s took %s', NEW.query_id, NEW.execution_time));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS tr_alert_long_queries ON performance_logs;
CREATE TRIGGER tr_alert_long_queries
AFTER INSERT ON performance_logs
FOR EACH ROW
EXECUTE FUNCTION alert_long_running_queries();
EOF

echo "Created monitoring setup SQL script at setup_monitoring.sql"

# Create backup script
cat << 'EOF' > backup_schema.sql
-- Create backup tables
CREATE TABLE IF NOT EXISTS users_backup AS SELECT * FROM users;
CREATE TABLE IF NOT EXISTS documents_backup AS SELECT * FROM documents;

-- Create backup function
CREATE OR REPLACE FUNCTION create_table_backup(table_name text)
RETURNS void AS $$
DECLARE
    backup_table text;
    timestamp_str text;
BEGIN
    timestamp_str := to_char(now(), 'YYYYMMDD_HH24MISS');
    backup_table := table_name || '_backup_' || timestamp_str;
    
    EXECUTE format('CREATE TABLE %I AS SELECT * FROM %I', backup_table, table_name);
    
    RAISE NOTICE 'Created backup table: %', backup_table;
END;
$$ LANGUAGE plpgsql;
EOF

echo "Created backup SQL script at backup_schema.sql"

echo "Production environment setup complete!"
echo "Next steps:"
echo "1. Review and update the environment file"
echo "2. Run verify_schema.sql to verify database setup"
echo "3. Run setup_monitoring.sql to set up monitoring"
echo "4. Keep backup_schema.sql for backup procedures" 