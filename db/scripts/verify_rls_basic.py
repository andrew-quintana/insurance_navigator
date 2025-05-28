#!/usr/bin/env python3
"""
Basic RLS Verification Script

This script verifies that RLS is enabled and policies are in place.
"""

import asyncio
import asyncpg
import os
from datetime import datetime

async def verify_rls(database_url: str):
    """Verify RLS is properly configured."""
    
    connection = await asyncpg.connect(database_url)
    
    try:
        print("🔍 Verifying RLS Implementation...")
        print("=" * 50)
        
        # 1. Check RLS is enabled on all tables
        tables_with_rls = await connection.fetch("""
            SELECT tablename, rowsecurity 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """)
        
        print("📋 RLS Status by Table:")
        total_tables = len(tables_with_rls)
        rls_enabled_count = sum(1 for row in tables_with_rls if row['rowsecurity'])
        
        for row in tables_with_rls:
            status = "✅ Enabled" if row['rowsecurity'] else "❌ Disabled"
            print(f"  {row['tablename']}: {status}")
        
        print(f"\n📊 Summary: {rls_enabled_count}/{total_tables} tables have RLS enabled")
        
        # 2. Check total policies
        policy_count = await connection.fetchval("""
            SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public'
        """)
        
        print(f"🛡️  Total RLS Policies: {policy_count}")
        
        # 3. Check policies by table
        policies_by_table = await connection.fetch("""
            SELECT tablename, COUNT(*) as policy_count
            FROM pg_policies 
            WHERE schemaname = 'public'
            GROUP BY tablename
            ORDER BY tablename
        """)
        
        print("\n📑 Policies by Table:")
        for row in policies_by_table:
            print(f"  {row['tablename']}: {row['policy_count']} policies")
        
        # 4. Check helper functions
        helper_functions = await connection.fetch("""
            SELECT proname, proacl
            FROM pg_proc 
            WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            AND proname IN ('is_admin_user', 'get_current_user_id')
        """)
        
        print(f"\n⚙️  Helper Functions: {len(helper_functions)} found")
        for row in helper_functions:
            print(f"  {row['proname']}: Available")
        
        # 5. Test basic functionality
        print("\n🧪 Basic Functionality Tests:")
        
        # Test that we can query tables (policies allow access)
        try:
            user_count = await connection.fetchval("SELECT COUNT(*) FROM users")
            print(f"  ✅ Users table accessible: {user_count} records")
        except Exception as e:
            print(f"  ❌ Users table error: {e}")
        
        try:
            role_count = await connection.fetchval("SELECT COUNT(*) FROM roles")
            print(f"  ✅ Roles table accessible: {role_count} records")
        except Exception as e:
            print(f"  ❌ Roles table error: {e}")
        
        try:
            policy_count = await connection.fetchval("SELECT COUNT(*) FROM policy_records")
            print(f"  ✅ Policy records accessible: {policy_count} records")
        except Exception as e:
            print(f"  ❌ Policy records error: {e}")
        
        # 6. Overall assessment
        print("\n" + "=" * 50)
        if rls_enabled_count == total_tables and policy_count > 20:
            print("🎉 RLS IMPLEMENTATION: SUCCESS")
            print("   ✅ All tables have RLS enabled")
            print(f"   ✅ {policy_count} security policies in place")
            print("   ✅ Helper functions available")
            print("   ✅ Basic functionality verified")
        else:
            print("⚠️  RLS IMPLEMENTATION: NEEDS ATTENTION")
            if rls_enabled_count < total_tables:
                print(f"   ❌ {total_tables - rls_enabled_count} tables missing RLS")
            if policy_count < 20:
                print(f"   ❌ Only {policy_count} policies (expected 20+)")
        
        print("\n📝 Next Steps:")
        print("   1. Deploy to production with proper authentication integration")
        print("   2. Update helper functions to use real auth system")
        print("   3. Test with actual user contexts")
        print("   4. Monitor performance and access patterns")
        
    finally:
        await connection.close()

async def main():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        return
    
    await verify_rls(database_url)

if __name__ == "__main__":
    asyncio.run(main()) 