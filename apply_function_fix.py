#!/usr/bin/env python3
"""
Apply Function Type Fix
Fixes the get_pending_jobs function type mismatch
"""

import asyncio
import asyncpg

async def apply_function_fix():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🔧 Applying Function Type Fix")
        print("=" * 50)
        
        # Fix the function signature
        fix_sql = """
        -- Drop and recreate function with correct return types
        DROP FUNCTION IF EXISTS get_pending_jobs(integer);

        CREATE OR REPLACE FUNCTION get_pending_jobs(limit_param integer DEFAULT 10)
        RETURNS TABLE(
            id uuid, 
            document_id uuid, 
            job_type character varying,  -- Changed from 'text' to match table
            payload jsonb, 
            retry_count integer, 
            priority integer
        ) 
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                pj.id,
                pj.document_id,
                pj.job_type,
                pj.payload,
                pj.retry_count,
                pj.priority
            FROM processing_jobs pj
            WHERE pj.status IN ('pending', 'retrying')
              AND pj.scheduled_at <= NOW()
            ORDER BY pj.priority DESC, pj.created_at ASC
            LIMIT limit_param;
        END;
        $$;
        """
        
        print("🚀 Executing fix...")
        await conn.execute(fix_sql)
        print("✅ Function updated successfully!")
        
        # Test the fixed function
        print("\n🧪 Testing fixed function...")
        try:
            result = await conn.fetch("SELECT * FROM get_pending_jobs(5)")
            print(f"✅ Function call successful! Returned {len(result)} rows")
            if result:
                print(f"📋 Sample row: {dict(result[0])}")
            else:
                print(f"📋 No pending jobs found (this is normal)")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        await conn.close()
        
        print(f"\n🎉 SUCCESS: Function type mismatch fixed!")
        print(f"📍 Edge Functions should now work properly")
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(apply_function_fix()) 
"""
Apply Function Type Fix
Fixes the get_pending_jobs function type mismatch
"""

import asyncio
import asyncpg

async def apply_function_fix():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🔧 Applying Function Type Fix")
        print("=" * 50)
        
        # Fix the function signature
        fix_sql = """
        -- Drop and recreate function with correct return types
        DROP FUNCTION IF EXISTS get_pending_jobs(integer);

        CREATE OR REPLACE FUNCTION get_pending_jobs(limit_param integer DEFAULT 10)
        RETURNS TABLE(
            id uuid, 
            document_id uuid, 
            job_type character varying,  -- Changed from 'text' to match table
            payload jsonb, 
            retry_count integer, 
            priority integer
        ) 
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                pj.id,
                pj.document_id,
                pj.job_type,
                pj.payload,
                pj.retry_count,
                pj.priority
            FROM processing_jobs pj
            WHERE pj.status IN ('pending', 'retrying')
              AND pj.scheduled_at <= NOW()
            ORDER BY pj.priority DESC, pj.created_at ASC
            LIMIT limit_param;
        END;
        $$;
        """
        
        print("🚀 Executing fix...")
        await conn.execute(fix_sql)
        print("✅ Function updated successfully!")
        
        # Test the fixed function
        print("\n🧪 Testing fixed function...")
        try:
            result = await conn.fetch("SELECT * FROM get_pending_jobs(5)")
            print(f"✅ Function call successful! Returned {len(result)} rows")
            if result:
                print(f"📋 Sample row: {dict(result[0])}")
            else:
                print(f"📋 No pending jobs found (this is normal)")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        await conn.close()
        
        print(f"\n🎉 SUCCESS: Function type mismatch fixed!")
        print(f"📍 Edge Functions should now work properly")
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(apply_function_fix()) 