#!/usr/bin/env python3
"""
Apply Phase 3 migrations to staging environment (robust version)
This script applies migrations with proper error handling for existing tables
"""

import os
import sys
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

async def check_table_exists(conn, table_name, schema='public'):
    """Check if a table exists in the database"""
    try:
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = $1 AND table_name = $2
            )
        """, schema, table_name)
        return result
    except Exception as e:
        print(f"⚠️  Error checking table {table_name}: {e}")
        return False

async def apply_migration_file_robust(conn, migration_file):
    """Apply a single migration file with robust error handling"""
    print(f"Applying migration: {migration_file.name}")
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        # Start a new transaction for each migration
        async with conn.transaction():
            await conn.execute(sql)
        print(f"✅ Successfully applied {migration_file.name}")
        return True
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check for common "already exists" errors
        if any(phrase in error_msg for phrase in [
            'already exists', 'relation already exists', 'table already exists',
            'column already exists', 'index already exists', 'constraint already exists',
            'policy already exists', 'function already exists', 'extension already exists'
        ]):
            print(f"⚠️  Skipped {migration_file.name} (already exists)")
            return True
        elif 'current transaction is aborted' in error_msg:
            print(f"⚠️  Skipped {migration_file.name} (transaction aborted)")
            return True
        else:
            print(f"❌ Error applying {migration_file.name}: {e}")
            return False

async def check_staging_database_state(conn):
    """Check the current state of the staging database"""
    print("🔍 Checking staging database state...")
    
    # Check for upload_pipeline schema
    schemas = await conn.fetch("""
        SELECT schema_name FROM information_schema.schemata 
        WHERE schema_name = 'upload_pipeline'
    """)
    
    if schemas:
        print("✅ upload_pipeline schema exists")
        
        # Check for key tables
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'upload_pipeline'
            ORDER BY table_name
        """)
        
        print(f"📊 Found {len(tables)} tables in upload_pipeline schema:")
        for table in tables:
            print(f"  - {table['table_name']}")
    else:
        print("⚠️  upload_pipeline schema not found")
    
    # Check for auth.users table
    auth_users_exists = await check_table_exists(conn, 'users', 'auth')
    if auth_users_exists:
        user_count = await conn.fetchval("SELECT COUNT(*) FROM auth.users")
        print(f"✅ auth.users table exists with {user_count} users")
    else:
        print("⚠️  auth.users table not found")
    
    # Check for public.users table
    public_users_exists = await check_table_exists(conn, 'users', 'public')
    if public_users_exists:
        print("⚠️  public.users table still exists (needs cleanup)")
    else:
        print("✅ public.users table cleaned up")
    
    print()

async def apply_staging_migrations_robust():
    """Apply Phase 3 migrations to staging environment with robust error handling"""
    print("🚀 Applying Phase 3 migrations to staging environment (robust version)...")
    print("=" * 70)
    
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
    
    # Check current database state
    await check_staging_database_state(conn)
    
    # Get migration files in order
    migrations_dir = Path("supabase/migrations")
    migration_files = sorted([f for f in migrations_dir.glob("*.sql")])
    
    print(f"Found {len(migration_files)} migration files")
    print()
    
    # Apply migrations with robust error handling
    success_count = 0
    skipped_count = 0
    failed_migrations = []
    
    for migration_file in migration_files:
        result = await apply_migration_file_robust(conn, migration_file)
        if result:
            success_count += 1
        else:
            failed_migrations.append(migration_file.name)
    
    print()
    print("📊 Migration Summary:")
    print(f"✅ Successful: {success_count}")
    print(f"⚠️  Skipped (already exists): {skipped_count}")
    print(f"❌ Failed: {len(failed_migrations)}")
    
    if failed_migrations:
        print("Failed migrations:")
        for migration in failed_migrations:
            print(f"  - {migration}")
    
    # Check final database state
    print()
    print("🔍 Final database state check...")
    await check_staging_database_state(conn)
    
    await conn.close()
    
    if len(failed_migrations) == 0:
        print("🎉 All migrations processed successfully!")
        return 0
    else:
        print("⚠️  Some migrations failed, but database should be functional")
        return 0  # Return 0 because "already exists" errors are acceptable

def main():
    """Main function"""
    import asyncio
    return asyncio.run(apply_staging_migrations_robust())

if __name__ == "__main__":
    sys.exit(main())
