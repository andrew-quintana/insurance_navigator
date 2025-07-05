#!/bin/bash

# Script to apply migrations in the correct order
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Function to run SQL file with error handling
run_sql_file() {
    local file=$1
    echo "Applying migration: $file"
    PGPASSWORD=postgres psql -h localhost -p 54322 -U postgres -d postgres -f "$file" || {
        echo "❌ Failed to apply migration: $file"
        return 1
    }
}

# Function to check if a policy exists
check_policy_exists() {
    local table=$1
    local policy=$2
    PGPASSWORD=postgres psql -h localhost -p 54322 -U postgres -d postgres -t -c \
        "SELECT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = '$table' AND policyname = '$policy');"
}

# Function to drop a policy if it exists
drop_policy_if_exists() {
    local table=$1
    local policy=$2
    if [ "$(check_policy_exists "$table" "$policy")" = " t" ]; then
        echo "Dropping existing policy: $policy on $table"
        PGPASSWORD=postgres psql -h localhost -p 54322 -U postgres -d postgres -c \
            "DROP POLICY IF EXISTS \"$policy\" ON $table;"
    fi
}

cd "$PROJECT_ROOT/supabase"

# Drop existing policies that might conflict
drop_policy_if_exists "processing_logs" "Service role has full access to processing logs"
drop_policy_if_exists "processing_logs" "Users can read own document logs"

# Apply migrations in order
for migration in migrations/20240703000*.sql; do
    run_sql_file "$migration"
done

# Verify the migrations
echo "Verifying migrations..."
PGPASSWORD=postgres psql -h localhost -p 54322 -U postgres -d postgres -c \
    "SELECT version, name FROM supabase_migrations.schema_migrations ORDER BY version DESC LIMIT 5;"

echo "✅ Migrations applied successfully" 