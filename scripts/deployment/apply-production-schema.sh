#!/bin/bash
set -e

# Check if required environment variables are set
required_vars=(
  "SUPABASE_SERVICE_ROLE_KEY"
  "SUPABASE_DB_URL"
)

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "Error: Required environment variable $var is not set"
    exit 1
  fi
done

# Extract database password from SUPABASE_DB_URL
DB_PASSWORD=$(echo "$SUPABASE_DB_URL" | sed -n 's/.*:\/\/postgres:\([^@]*\)@.*/\1/p')
if [ -z "$DB_PASSWORD" ]; then
  echo "Error: Could not extract database password from SUPABASE_DB_URL"
  exit 1
fi

echo "🔍 Verifying database connection..."
if ! PGPASSWORD=$DB_PASSWORD psql "$SUPABASE_DB_URL" -c '\conninfo'; then
  echo "❌ Failed to connect to database"
  exit 1
fi

echo "📦 Applying initial schema migration..."
if ! PGPASSWORD=$DB_PASSWORD psql "$SUPABASE_DB_URL" -f supabase/migrations/20240321000000_initial_schema.sql; then
  echo "❌ Migration failed"
  exit 1
fi

echo "✅ Schema migration completed successfully"

echo "🔒 Verifying RLS policies..."
PGPASSWORD=$DB_PASSWORD psql "$SUPABASE_DB_URL" << 'EOF'
SELECT tablename, policyname, permissive, roles, cmd, qual, with_check 
FROM pg_policies 
WHERE schemaname = 'public' 
ORDER BY tablename, policyname;
EOF

echo "📊 Verifying table structures..."
PGPASSWORD=$DB_PASSWORD psql "$SUPABASE_DB_URL" << 'EOF'
\d+ public.users
\d+ public.documents
\d storage.buckets
EOF

echo "🗄️ Verifying storage bucket..."
PGPASSWORD=$DB_PASSWORD psql "$SUPABASE_DB_URL" -c "SELECT * FROM storage.buckets WHERE id = 'documents';"

# Disable pgaudit logging for MVP phase
echo "Disabling audit logging for MVP phase..."
PGPASSWORD=$DB_PASSWORD psql "$SUPABASE_DB_URL" -c "ALTER ROLE postgres RESET pgaudit.log;"
PGPASSWORD=$DB_PASSWORD psql "$SUPABASE_DB_URL" -c "ALTER ROLE authenticator RESET pgaudit.log;"

echo "✨ Database setup complete!" 