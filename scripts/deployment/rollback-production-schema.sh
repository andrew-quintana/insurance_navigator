#!/bin/bash
set -e

# Check if required environment variables are set
required_vars=(
  "SUPABASE_SERVICE_ROLE_KEY"
  "SUPABASE_DB_URL"
  "NEXT_PUBLIC_SUPABASE_URL"
)

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "Error: Required environment variable $var is not set"
    exit 1
  fi
done

echo "⚠️ WARNING: This will delete all data and schema. Are you sure? (y/N)"
read -r confirm
if [ "$confirm" != "y" ]; then
  echo "Rollback cancelled"
  exit 0
fi

echo "📝 Creating backup before rollback..."
timestamp=$(date +%Y%m%d_%H%M%S)
backup_file="backups/pre_rollback_${timestamp}.sql"
mkdir -p backups
PGPASSWORD=$SUPABASE_DB_PASSWORD pg_dump "$SUPABASE_DB_URL" > "$backup_file"

echo "🗑️ Rolling back schema changes..."
PGPASSWORD=$SUPABASE_DB_PASSWORD psql "$SUPABASE_DB_URL" << 'EOF'
-- Drop storage policies
DROP POLICY IF EXISTS "Users can upload to own directory" ON storage.objects;
DROP POLICY IF EXISTS "Users can read own files" ON storage.objects;
DROP POLICY IF EXISTS "Service role has full access to storage" ON storage.objects;

-- Delete storage bucket
DELETE FROM storage.buckets WHERE id = 'documents';

-- Drop tables (this will cascade to policies and triggers)
DROP TABLE IF EXISTS public.documents;
DROP TABLE IF EXISTS public.users;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column();
EOF

echo "✅ Rollback completed successfully"
echo "💾 Backup saved to: $backup_file" 