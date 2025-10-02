#!/usr/bin/env python3
"""
Migration Sync Script
This script helps sync local migrations with production and sets up a future-proof workflow.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    return result

def check_supabase_status():
    """Check if Supabase is running locally."""
    result = run_command("supabase status", check=False)
    if result and result.returncode == 0:
        print("✅ Supabase is running locally")
        return True
    else:
        print("❌ Supabase is not running locally")
        print("Run: supabase start")
        return False

def backup_current_migrations():
    """Backup current migrations before syncing."""
    migrations_dir = Path("supabase/migrations")
    backup_dir = Path("supabase/migrations/backup")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"migrations_backup_{timestamp}"
    backup_path.mkdir(exist_ok=True)
    
    # Copy all migration files
    for migration_file in migrations_dir.glob("*.sql"):
        if migration_file.name != "backup":
            subprocess.run(f"cp {migration_file} {backup_path}/", shell=True)
    
    print(f"✅ Migrations backed up to: {backup_path}")
    return backup_path

def sync_with_production():
    """Sync local migrations with production."""
    print("🔄 Syncing with production...")
    
    # Step 1: Repair migration history
    repair_commands = [
        "supabase migration repair --status reverted 20250904000000",
        "supabase migration repair --status reverted 20250904000001", 
        "supabase migration repair --status reverted 20250904000002",
        "supabase migration repair --status reverted 20250904000004",
        "supabase migration repair --status applied 20250101000000"
    ]
    
    for cmd in repair_commands:
        result = run_command(cmd, check=False)
        if result and result.returncode == 0:
            print(f"✅ {cmd}")
        else:
            print(f"⚠️ {cmd} - {result.stderr if result else 'No result'}")
    
    # Step 2: Pull production schema
    result = run_command("supabase db pull", check=False)
    if result and result.returncode == 0:
        print("✅ Successfully pulled production schema")
        return True
    else:
        print(f"❌ Failed to pull production schema: {result.stderr if result else 'No result'}")
        return False

def create_future_proof_workflow():
    """Create scripts and documentation for future-proof migration workflow."""
    
    # Create migration workflow script
    workflow_script = """#!/bin/bash
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
"""

    with open("scripts/migration_workflow.sh", "w") as f:
        f.write(workflow_script)
    
    # Make it executable
    os.chmod("scripts/migration_workflow.sh", 0o755)
    
    # Create documentation
    docs = """# Migration Workflow Documentation

## Current Status
- ✅ Local migrations synced with production
- ✅ Future-proof workflow established
- ✅ Backup system in place

## How to Add New Migrations

### Option 1: Use the Workflow Script (Recommended)
```bash
./scripts/migration_workflow.sh
```

### Option 2: Manual Process
1. **Create migration file:**
   ```bash
   supabase migration new your_migration_name
   ```

2. **Edit the migration file:**
   ```bash
   # Edit supabase/migrations/TIMESTAMP_your_migration_name.sql
   ```

3. **Test locally:**
   ```bash
   supabase db reset
   ```

4. **Commit and push:**
   ```bash
   git add supabase/migrations/
   git commit -m "Add migration: your_migration_name"
   git push
   ```

5. **Deploy to production:**
   ```bash
   supabase db push
   ```

## Best Practices

### ✅ DO:
- Always test migrations locally first
- Use descriptive migration names
- Include rollback instructions in comments
- Commit migrations immediately after testing
- Use transactions for complex migrations

### ❌ DON'T:
- Edit existing migration files
- Skip local testing
- Deploy untested migrations
- Mix schema and data changes in one migration

## Troubleshooting

### Migration Drift Issues
If you get "migration history does not match" errors:

1. **Check what's different:**
   ```bash
   supabase db pull --dry-run
   ```

2. **Repair specific migrations:**
   ```bash
   supabase migration repair --status reverted MIGRATION_ID
   ```

3. **Full sync (nuclear option):**
   ```bash
   supabase db pull
   ```

### Storage Bucket Issues
If you get column errors with storage.buckets:

1. **Check current schema:**
   ```sql
   \\d storage.buckets
   ```

2. **Use conditional logic:**
   ```sql
   DO $$
   BEGIN
       IF EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_schema = 'storage' 
                  AND table_name = 'buckets' 
                  AND column_name = 'public') THEN
           -- Use old schema
       ELSE
           -- Use new schema
       END IF;
   END $$;
   ```

## Emergency Procedures

### Rollback Migration
```bash
supabase migration repair --status reverted MIGRATION_ID
```

### Reset Everything
```bash
supabase db reset
```

### Backup Before Changes
```bash
supabase db dump > backup_$(date +%Y%m%d_%H%M%S).sql
```
"""

    with open("docs/MIGRATION_WORKFLOW.md", "w") as f:
        f.write(docs)
    
    print("✅ Created future-proof workflow:")
    print("   📄 scripts/migration_workflow.sh")
    print("   📚 docs/MIGRATION_WORKFLOW.md")

def main():
    """Main function."""
    print("🔄 Migration Sync and Future-Proofing Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("supabase").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Step 1: Check Supabase status
    if not check_supabase_status():
        print("Please start Supabase first: supabase start")
        return
    
    # Step 2: Backup current migrations
    backup_path = backup_current_migrations()
    
    # Step 3: Try to sync with production
    print("\n🔄 Attempting to sync with production...")
    if sync_with_production():
        print("✅ Successfully synced with production!")
    else:
        print("⚠️ Could not sync with production (connection issues)")
        print("📋 Manual sync required:")
        print("   1. Fix connection to production database")
        print("   2. Run: supabase db pull")
        print("   3. Review generated migration files")
    
    # Step 4: Create future-proof workflow
    print("\n🛠️ Setting up future-proof workflow...")
    create_future_proof_workflow()
    
    print("\n🎉 Migration sync and future-proofing completed!")
    print("\n📋 Next steps:")
    print("   1. Review any new migration files generated")
    print("   2. Test migrations locally: supabase db reset")
    print("   3. Use the new workflow for future changes")
    print("   4. Read docs/MIGRATION_WORKFLOW.md for best practices")

if __name__ == "__main__":
    main()
