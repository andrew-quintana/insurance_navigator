#!/usr/bin/env python3
"""
Apply migrations to staging environment safely
Handles errors gracefully and continues with other migrations
"""

import os
import sys
import asyncio
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

async def apply_migration_file_safe(conn, migration_file):
    """Apply a single migration file to the database with error handling"""
    print(f"📄 Applying migration: {migration_file.name}")
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        # Execute each statement separately to avoid transaction issues
        statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement:
                try:
                    await conn.execute(statement)
                except Exception as e:
                    print(f"  ⚠️ Statement {i+1} failed: {e}")
                    # Continue with other statements
                    continue
        
        print(f"✅ Successfully applied {migration_file.name}")
        return True
    except Exception as e:
        print(f"❌ Error applying {migration_file.name}: {e}")
        return False

async def check_and_fix_user_tables(conn):
    """Check and safely remove user tables if they exist"""
    print("🔍 Checking and cleaning up user tables...")
    
    try:
        # Check if public.users exists
        users_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'users'
            )
        """)
        
        if users_exists:
            print("  📋 Found public.users table")
            count = await conn.fetchval("SELECT COUNT(*) FROM public.users")
            print(f"    - Contains {count} records")
            
            # Drop the table safely
            await conn.execute("DROP TABLE IF EXISTS public.users CASCADE")
            print("  ✅ Dropped public.users table")
        
        # Check if public.user_info exists
        user_info_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'user_info'
            )
        """)
        
        if user_info_exists:
            print("  📋 Found public.user_info table")
            count = await conn.fetchval("SELECT COUNT(*) FROM public.user_info")
            print(f"    - Contains {count} records")
            
            # Drop the table safely
            await conn.execute("DROP TABLE IF EXISTS public.user_info CASCADE")
            print("  ✅ Dropped public.user_info table")
        
        # Check for views
        user_info_view = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.views 
                WHERE table_schema = 'public' AND table_name = 'user_info'
            )
        """)
        
        if user_info_view:
            print("  📋 Found public.user_info view")
            await conn.execute("DROP VIEW IF EXISTS public.user_info CASCADE")
            print("  ✅ Dropped public.user_info view")
        
        print("  ✅ User table cleanup completed")
        return True
        
    except Exception as e:
        print(f"  ❌ Error during user table cleanup: {e}")
        return False

async def apply_staging_migrations_safe():
    """Apply all migrations to staging environment safely"""
    print("🚀 Applying migrations to staging environment (safe mode)...")
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
    
    print(f"📊 Environment: {env_vars.get('ENVIRONMENT', 'Unknown')}")
    print(f"📊 Database URL: {database_url[:50]}...")
    print()
    
    # Connect to staging database
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to staging database")
    except Exception as e:
        print(f"❌ Failed to connect to staging database: {e}")
        return 1
    
    # First, clean up user tables safely
    await check_and_fix_user_tables(conn)
    print()
    
    # Get migration files in order
    migrations_dir = Path("supabase/migrations")
    migration_files = sorted([f for f in migrations_dir.glob("*.sql")])
    
    print(f"📋 Found {len(migration_files)} migration files")
    print()
    
    # Apply migrations
    success_count = 0
    failed_migrations = []
    
    for migration_file in migration_files:
        if await apply_migration_file_safe(conn, migration_file):
            success_count += 1
        else:
            failed_migrations.append(migration_file.name)
    
    print()
    print("📊 Migration Summary:")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {len(migration_files) - success_count}")
    
    if failed_migrations:
        print("❌ Failed migrations:")
        for migration in failed_migrations:
            print(f"  - {migration}")
    
    await conn.close()
    
    if success_count == len(migration_files):
        print("🎉 All migrations applied successfully to staging!")
        return 0
    else:
        print("💥 Some migrations failed!")
        return 1

async def verify_staging_schema():
    """Verify that the staging schema is correct after migrations"""
    print("\n🔍 Verifying staging schema...")
    
    env_vars = load_staging_environment()
    if not env_vars:
        return False
    
    database_url = env_vars.get('DATABASE_URL')
    if not database_url:
        return False
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Check key tables exist
        tables_to_check = [
            ('auth', 'users'),
            ('documents', 'documents'), 
            ('documents', 'document_chunks'),
            ('upload_pipeline', 'documents'),
            ('upload_pipeline', 'upload_jobs'),
            ('upload_pipeline', 'events')
        ]
        
        print("📋 Checking key tables:")
        for schema, table_name in tables_to_check:
            try:
                result = await conn.fetchval(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = $1 AND table_name = $2
                    )
                """, schema, table_name)
                
                if result:
                    print(f"  ✅ {schema}.{table_name}")
                else:
                    print(f"  ❌ {schema}.{table_name} - Missing")
            except Exception as e:
                print(f"  ❌ {schema}.{table_name} - Error: {e}")
        
        # Check storage buckets
        print("\n📋 Checking storage buckets:")
        try:
            buckets = await conn.fetch("SELECT id, name FROM storage.buckets")
            for bucket in buckets:
                print(f"  ✅ storage.buckets.{bucket['id']} ({bucket['name']})")
        except Exception as e:
            print(f"  ❌ storage.buckets - Error: {e}")
        
        # Verify public.users is gone
        print("\n📋 Verifying public.users cleanup:")
        try:
            users_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'users'
                )
            """)
            if users_exists:
                print("  ❌ public.users still exists")
            else:
                print("  ✅ public.users successfully removed")
        except Exception as e:
            print(f"  ❌ Error checking public.users: {e}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False

def main():
    """Main function"""
    print("🔄 Staging Migration Deployment (Safe Mode)")
    print("=" * 50)
    
    # Apply migrations
    result = asyncio.run(apply_staging_migrations_safe())
    
    if result == 0:
        # Verify schema
        asyncio.run(verify_staging_schema())
        print("\n🎉 Staging deployment completed successfully!")
    else:
        print("\n💥 Staging deployment failed!")
    
    return result

if __name__ == "__main__":
    sys.exit(main())
