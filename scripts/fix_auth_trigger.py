#!/usr/bin/env python3
"""
Fix auth trigger that references removed public.users table
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

async def fix_auth_trigger():
    """Remove the problematic auth trigger and function"""
    print("🔧 Fixing auth trigger that references removed public.users table...")
    
    env_vars = load_staging_environment()
    if not env_vars:
        return False
    
    database_url = env_vars.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to staging database")
        
        # Drop the trigger first
        print("📋 Dropping on_auth_user_created trigger...")
        await conn.execute("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users")
        print("✅ Trigger dropped")
        
        # Drop the function
        print("📋 Dropping handle_new_user function...")
        await conn.execute("DROP FUNCTION IF EXISTS public.handle_new_user()")
        print("✅ Function dropped")
        
        # Verify the trigger is gone
        triggers = await conn.fetch("""
            SELECT trigger_name 
            FROM information_schema.triggers 
            WHERE event_object_table = 'users' AND event_object_schema = 'auth'
        """)
        
        if not triggers:
            print("✅ No triggers found on auth.users")
        else:
            print("⚠️ Remaining triggers on auth.users:")
            for trigger in triggers:
                print(f"  - {trigger['trigger_name']}")
        
        await conn.close()
        print("🎉 Auth trigger fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing auth trigger: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Auth Trigger Fix")
    print("=" * 30)
    
    success = asyncio.run(fix_auth_trigger())
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
