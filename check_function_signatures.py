#!/usr/bin/env python3
"""
Check Function Signatures
Verifies the exact signatures and return types of database functions
"""

import asyncio
import asyncpg

async def check_function_signatures():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🔍 Checking Function Signatures")
        print("=" * 50)
        
        # Check the specific function that's failing
        print("🎯 Checking get_pending_jobs function...")
        
        # Get detailed function information
        func_info = await conn.fetchrow("""
            SELECT 
                p.proname as function_name,
                pg_catalog.pg_get_function_result(p.oid) as return_type,
                pg_catalog.pg_get_function_arguments(p.oid) as arguments,
                pg_catalog.pg_get_functiondef(p.oid) as definition
            FROM pg_catalog.pg_proc p
            JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
            WHERE p.proname = 'get_pending_jobs'
            AND n.nspname = 'public'
        """)
        
        if func_info:
            print(f"📋 Function: {func_info['function_name']}")
            print(f"📥 Arguments: {func_info['arguments']}")
            print(f"📤 Return Type: {func_info['return_type']}")
            print(f"\n📝 Function Definition:")
            print("-" * 30)
            print(func_info['definition'])
            
            # Test calling the function to see the exact error
            print(f"\n🧪 Testing function call...")
            try:
                result = await conn.fetch("SELECT * FROM get_pending_jobs(5)")
                print(f"✅ Function call successful! Returned {len(result)} rows")
                if result:
                    print(f"📋 Sample row structure: {dict(result[0])}")
                else:
                    print(f"📋 No rows returned (no pending jobs)")
                    
            except Exception as e:
                print(f"❌ Function call failed: {e}")
                print(f"🔍 Error details: {type(e).__name__}: {str(e)}")
        else:
            print("❌ Function get_pending_jobs not found!")
        
        # Also check processing_jobs table structure
        print(f"\n📊 Checking processing_jobs table structure...")
        try:
            table_info = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'processing_jobs'
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            if table_info:
                print(f"📋 processing_jobs table columns:")
                for col in table_info:
                    print(f"   - {col['column_name']}: {col['data_type']} {'(nullable)' if col['is_nullable'] == 'YES' else '(not null)'}")
            else:
                print("❌ processing_jobs table not found!")
                
        except Exception as e:
            print(f"❌ Error checking table: {e}")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(check_function_signatures()) 
"""
Check Function Signatures
Verifies the exact signatures and return types of database functions
"""

import asyncio
import asyncpg

async def check_function_signatures():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🔍 Checking Function Signatures")
        print("=" * 50)
        
        # Check the specific function that's failing
        print("🎯 Checking get_pending_jobs function...")
        
        # Get detailed function information
        func_info = await conn.fetchrow("""
            SELECT 
                p.proname as function_name,
                pg_catalog.pg_get_function_result(p.oid) as return_type,
                pg_catalog.pg_get_function_arguments(p.oid) as arguments,
                pg_catalog.pg_get_functiondef(p.oid) as definition
            FROM pg_catalog.pg_proc p
            JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
            WHERE p.proname = 'get_pending_jobs'
            AND n.nspname = 'public'
        """)
        
        if func_info:
            print(f"📋 Function: {func_info['function_name']}")
            print(f"📥 Arguments: {func_info['arguments']}")
            print(f"📤 Return Type: {func_info['return_type']}")
            print(f"\n📝 Function Definition:")
            print("-" * 30)
            print(func_info['definition'])
            
            # Test calling the function to see the exact error
            print(f"\n🧪 Testing function call...")
            try:
                result = await conn.fetch("SELECT * FROM get_pending_jobs(5)")
                print(f"✅ Function call successful! Returned {len(result)} rows")
                if result:
                    print(f"📋 Sample row structure: {dict(result[0])}")
                else:
                    print(f"📋 No rows returned (no pending jobs)")
                    
            except Exception as e:
                print(f"❌ Function call failed: {e}")
                print(f"🔍 Error details: {type(e).__name__}: {str(e)}")
        else:
            print("❌ Function get_pending_jobs not found!")
        
        # Also check processing_jobs table structure
        print(f"\n📊 Checking processing_jobs table structure...")
        try:
            table_info = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'processing_jobs'
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            if table_info:
                print(f"📋 processing_jobs table columns:")
                for col in table_info:
                    print(f"   - {col['column_name']}: {col['data_type']} {'(nullable)' if col['is_nullable'] == 'YES' else '(not null)'}")
            else:
                print("❌ processing_jobs table not found!")
                
        except Exception as e:
            print(f"❌ Error checking table: {e}")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(check_function_signatures()) 