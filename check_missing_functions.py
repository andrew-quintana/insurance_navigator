#!/usr/bin/env python3
"""
Check Missing Database Functions
Verifies which functions the Edge Functions need but are missing from database
"""

import asyncio
import asyncpg

async def check_missing_functions():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🔍 Checking Database Functions")
        print("=" * 50)
        
        # Functions that Edge Functions are trying to call
        required_functions = [
            'get_pending_jobs',
            'start_processing_job', 
            'complete_processing_job',
            'fail_processing_job',
            'schedule_next_job_safely'
        ]
        
        # Check what functions exist
        existing_functions = await conn.fetch("""
            SELECT routine_name, routine_type, specific_name
            FROM information_schema.routines 
            WHERE routine_schema = 'public' 
            AND routine_type = 'FUNCTION'
            ORDER BY routine_name
        """)
        
        existing_names = {func['routine_name'] for func in existing_functions}
        
        print(f"📋 Required Functions: {len(required_functions)}")
        print(f"📊 Existing Functions: {len(existing_functions)}")
        
        print(f"\n🔍 Function Status:")
        missing_functions = []
        
        for func_name in required_functions:
            if func_name in existing_names:
                print(f"   ✅ {func_name} - EXISTS")
            else:
                print(f"   ❌ {func_name} - MISSING")
                missing_functions.append(func_name)
        
        if missing_functions:
            print(f"\n🚨 CRITICAL: {len(missing_functions)} required functions are missing!")
            print(f"📋 Missing functions: {', '.join(missing_functions)}")
            
            print(f"\n💡 This explains the 'structure of query does not match function result type' error")
            print(f"🔧 The Edge Functions are calling functions that don't exist in the database")
            
            print(f"\n📍 Solution: Run database migration to create missing functions")
            print(f"   Migration file: db/migrations/013_add_job_queue_system.sql")
            
        else:
            print(f"\n✅ All required functions exist!")
        
        # Show some existing functions for reference
        print(f"\n📋 Sample existing functions:")
        for func in existing_functions[:10]:
            print(f"   - {func['routine_name']} ({func['routine_type']})")
        
        if len(existing_functions) > 10:
            print(f"   ... and {len(existing_functions) - 10} more")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(check_missing_functions()) 
"""
Check Missing Database Functions
Verifies which functions the Edge Functions need but are missing from database
"""

import asyncio
import asyncpg

async def check_missing_functions():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🔍 Checking Database Functions")
        print("=" * 50)
        
        # Functions that Edge Functions are trying to call
        required_functions = [
            'get_pending_jobs',
            'start_processing_job', 
            'complete_processing_job',
            'fail_processing_job',
            'schedule_next_job_safely'
        ]
        
        # Check what functions exist
        existing_functions = await conn.fetch("""
            SELECT routine_name, routine_type, specific_name
            FROM information_schema.routines 
            WHERE routine_schema = 'public' 
            AND routine_type = 'FUNCTION'
            ORDER BY routine_name
        """)
        
        existing_names = {func['routine_name'] for func in existing_functions}
        
        print(f"📋 Required Functions: {len(required_functions)}")
        print(f"📊 Existing Functions: {len(existing_functions)}")
        
        print(f"\n🔍 Function Status:")
        missing_functions = []
        
        for func_name in required_functions:
            if func_name in existing_names:
                print(f"   ✅ {func_name} - EXISTS")
            else:
                print(f"   ❌ {func_name} - MISSING")
                missing_functions.append(func_name)
        
        if missing_functions:
            print(f"\n🚨 CRITICAL: {len(missing_functions)} required functions are missing!")
            print(f"📋 Missing functions: {', '.join(missing_functions)}")
            
            print(f"\n💡 This explains the 'structure of query does not match function result type' error")
            print(f"🔧 The Edge Functions are calling functions that don't exist in the database")
            
            print(f"\n📍 Solution: Run database migration to create missing functions")
            print(f"   Migration file: db/migrations/013_add_job_queue_system.sql")
            
        else:
            print(f"\n✅ All required functions exist!")
        
        # Show some existing functions for reference
        print(f"\n📋 Sample existing functions:")
        for func in existing_functions[:10]:
            print(f"   - {func['routine_name']} ({func['routine_type']})")
        
        if len(existing_functions) > 10:
            print(f"   ... and {len(existing_functions) - 10} more")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(check_missing_functions()) 