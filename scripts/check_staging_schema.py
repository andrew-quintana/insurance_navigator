#!/usr/bin/env python3
"""
Check staging database schema
"""

import os
import sys
import asyncio
import asyncpg
from pathlib import Path

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

async def check_staging_schema():
    """Check what's currently in the staging database"""
    print("🔍 Checking staging database schema...")
    
    env_vars = load_staging_environment()
    if not env_vars:
        return
    
    database_url = env_vars.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to staging database")
        
        # Check all schemas
        print("\n📋 Available schemas:")
        schemas = await conn.fetch("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
        for schema in schemas:
            print(f"  - {schema['schema_name']}")
        
        # Check tables in each schema
        print("\n📋 Tables by schema:")
        for schema in schemas:
            schema_name = schema['schema_name']
            if schema_name in ['information_schema', 'pg_catalog', 'pg_toast']:
                continue
                
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = $1 
                ORDER BY table_name
            """, schema_name)
            
            if tables:
                print(f"\n  {schema_name}:")
                for table in tables:
                    print(f"    - {table['table_name']}")
        
        # Check storage buckets
        print("\n📋 Storage buckets:")
        try:
            buckets = await conn.fetch("SELECT id, name FROM storage.buckets")
            for bucket in buckets:
                print(f"  - {bucket['id']} ({bucket['name']})")
        except Exception as e:
            print(f"  ❌ Error checking storage buckets: {e}")
        
        # Check if public.users exists
        print("\n📋 Checking for public.users table:")
        try:
            users_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'users'
                )
            """)
            if users_exists:
                print("  ✅ public.users table exists")
                # Check if it has data
                count = await conn.fetchval("SELECT COUNT(*) FROM public.users")
                print(f"    - Contains {count} records")
            else:
                print("  ❌ public.users table does not exist")
        except Exception as e:
            print(f"  ❌ Error checking public.users: {e}")
        
        # Check if public.user_info exists
        print("\n📋 Checking for public.user_info table:")
        try:
            user_info_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'user_info'
                )
            """)
            if user_info_exists:
                print("  ✅ public.user_info table exists")
                count = await conn.fetchval("SELECT COUNT(*) FROM public.user_info")
                print(f"    - Contains {count} records")
            else:
                print("  ❌ public.user_info table does not exist")
        except Exception as e:
            print(f"  ❌ Error checking public.user_info: {e}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Failed to connect to staging database: {e}")

def main():
    asyncio.run(check_staging_schema())

if __name__ == "__main__":
    main()
