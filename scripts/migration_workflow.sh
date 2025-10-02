#!/bin/bash
# Future-Proof Migration Workflow
# Use this script for all future database changes

set -e

echo "🚀 Starting migration workflow..."

# Step 1: Check if Supabase is running
if ! supabase status > /dev/null 2>&1; then
    echo "❌ Supabase is not running. Start it with: supabase start"
    exit 1
fi

# Step 2: Create new migration
echo "📝 Creating new migration..."
read -p "Enter migration name: " migration_name
timestamp=$(date +"%Y%m%d%H%M%S")
migration_file="supabase/migrations/${timestamp}_${migration_name}.sql"

# Create migration file
touch "$migration_file"
echo "-- Migration: $migration_name" > "$migration_file"
echo "-- Created: $(date)" >> "$migration_file"
echo "" >> "$migration_file"

echo "✅ Created migration file: $migration_file"

# Step 3: Edit migration
echo "📝 Edit your migration file: $migration_file"
read -p "Press Enter when you're done editing..."

# Step 4: Test migration locally
echo "🧪 Testing migration locally..."
supabase db reset

# Step 5: Commit changes
echo "💾 Committing changes..."
git add "$migration_file"
git commit -m "Add migration: $migration_name"

echo "✅ Migration workflow completed!"
echo "📋 Next steps:"
echo "   1. Test your changes thoroughly"
echo "   2. Push to remote: git push"
echo "   3. Deploy to production: supabase db push"
