#!/usr/bin/env python3
"""
Apply Phase 3 migrations to staging environment
This script applies the upload_pipeline schema and RLS policies to staging
"""

import os
import sys
import psycopg2
import asyncpg
from pathlib import Path
from datetime import datetime

def load_staging_environment():
    """Load staging environment variables"""
    env_file = Path(".env.staging")
    if not env_file.exists():
        print("❌ Staging environment file (.env.staging) not found!")
        return None
    
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
    
    return env_vars

async def apply_migration_file_async(conn, migration_file):
    """Apply a single migration file to the database using asyncpg"""
    print(f"Applying migration: {migration_file.name}")
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        await conn.execute(sql)
        print(f"✅ Successfully applied {migration_file.name}")
        return True
    except Exception as e:
        print(f"❌ Error applying {migration_file.name}: {e}")
        return False

async def apply_staging_migrations():
    """Apply Phase 3 migrations to staging environment"""
    print("🚀 Applying Phase 3 migrations to staging environment...")
    print("=" * 60)
    
    # Load staging environment
    env_vars = load_staging_environment()
    if not env_vars:
        return 1
    
    # Get database URL
    database_url = env_vars.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in staging environment")
        return 1
    
    print(f"📊 Database: {env_vars.get('DB_HOST', 'Unknown')}")
    print(f"📊 Environment: {env_vars.get('ENVIRONMENT', 'Unknown')}")
    print()
    
    # Connect to staging database
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to staging database")
    except Exception as e:
        print(f"❌ Failed to connect to staging database: {e}")
        return 1
    
    # Get migration files in order
    migrations_dir = Path("supabase/migrations")
    migration_files = sorted([f for f in migrations_dir.glob("*.sql")])
    
    print(f"Found {len(migration_files)} migration files")
    print()
    
    # Apply migrations
    success_count = 0
    failed_migrations = []
    
    for migration_file in migration_files:
        if await apply_migration_file_async(conn, migration_file):
            success_count += 1
        else:
            failed_migrations.append(migration_file.name)
    
    print()
    print("📊 Migration Summary:")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {len(migration_files) - success_count}")
    
    if failed_migrations:
        print("Failed migrations:")
        for migration in failed_migrations:
            print(f"  - {migration}")
    
    await conn.close()
    
    if success_count == len(migration_files):
        print("🎉 All migrations applied successfully to staging!")
        return 0
    else:
        print("💥 Some migrations failed!")
        return 1

def main():
    """Main function"""
    import asyncio
    return asyncio.run(apply_staging_migrations())

if __name__ == "__main__":
    sys.exit(main())
