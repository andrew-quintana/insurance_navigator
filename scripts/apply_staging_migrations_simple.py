#!/usr/bin/env python3
"""
Apply migrations to staging environment
Simplified version using only asyncpg
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

async def apply_migration_file(conn, migration_file):
    """Apply a single migration file to the database"""
    print(f"📄 Applying migration: {migration_file.name}")
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        await conn.execute(sql)
        print(f"✅ Successfully applied {migration_file.name}")
        return True
    except Exception as e:
        print(f"❌ Error applying {migration_file.name}: {e}")
        return False

async def test_staging_connection():
    """Test connection to staging database"""
    print("🔍 Testing staging database connection...")
    
    # Load staging environment
    env_vars = load_staging_environment()
    if not env_vars:
        return False
    
    # Get database URL
    database_url = env_vars.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in staging environment")
        return False
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Successfully connected to staging database")
        
        # Test basic query
        result = await conn.fetchval("SELECT version()")
        print(f"📊 Database version: {result[:50]}...")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to connect to staging database: {e}")
        return False

async def apply_staging_migrations():
    """Apply all migrations to staging environment"""
    print("🚀 Applying migrations to staging environment...")
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
    
    # Get migration files in order
    migrations_dir = Path("supabase/migrations")
    migration_files = sorted([f for f in migrations_dir.glob("*.sql")])
    
    print(f"📋 Found {len(migration_files)} migration files")
    print()
    
    # Apply migrations
    success_count = 0
    failed_migrations = []
    
    for migration_file in migration_files:
        if await apply_migration_file(conn, migration_file):
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
            'auth.users',
            'documents.documents', 
            'documents.document_chunks',
            'upload_pipeline.documents',
            'upload_pipeline.upload_jobs',
            'upload_pipeline.events'
        ]
        
        print("📋 Checking key tables:")
        for table in tables_to_check:
            try:
                schema, table_name = table.split('.')
                result = await conn.fetchval(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = $1 AND table_name = $2
                    )
                """, schema, table_name)
                
                if result:
                    print(f"  ✅ {table}")
                else:
                    print(f"  ❌ {table} - Missing")
            except Exception as e:
                print(f"  ❌ {table} - Error: {e}")
        
        # Check storage buckets
        print("\n📋 Checking storage buckets:")
        try:
            buckets = await conn.fetch("SELECT id, name FROM storage.buckets")
            for bucket in buckets:
                print(f"  ✅ storage.buckets.{bucket['id']} ({bucket['name']})")
        except Exception as e:
            print(f"  ❌ storage.buckets - Error: {e}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False

def main():
    """Main function"""
    print("🔄 Staging Migration Deployment")
    print("=" * 50)
    
    # Test connection first
    if not asyncio.run(test_staging_connection()):
        print("❌ Cannot proceed without database connection")
        return 1
    
    # Apply migrations
    result = asyncio.run(apply_staging_migrations())
    
    if result == 0:
        # Verify schema
        asyncio.run(verify_staging_schema())
        print("\n🎉 Staging deployment completed successfully!")
    else:
        print("\n💥 Staging deployment failed!")
    
    return result

if __name__ == "__main__":
    sys.exit(main())
