#!/usr/bin/env python3
"""
Test script to verify database connection with SSL configuration.
This can be run locally to test the connection before deploying.
"""

import asyncio
import os
import sys
from asyncpg import create_pool

async def test_database_connection():
    """Test database connection with SSL configuration."""
    
    # Test both direct and pooler URLs
    test_urls = [
        "postgresql://postgres:beqhar-qincyg-Syxxi8@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres?sslmode=require",
        "postgresql://postgres.znvwzkdblknkkztqyfnu:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
    ]
    
    for i, db_url in enumerate(test_urls, 1):
        print(f"\n=== Testing Connection {i} ===")
        print(f"URL: {db_url[:50]}...")
        
        try:
            # Create a small connection pool for testing
            pool = await create_pool(
                db_url,
                min_size=1,
                max_size=2,
                command_timeout=30,
                ssl="require"
            )
            
            # Test the connection
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                print(f"✅ Connection successful! Result: {result}")
                
                # Test schema access
                await conn.execute("SET search_path TO upload_pipeline, public")
                print("✅ Schema set successfully")
                
                # Test a simple query
                tables = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'upload_pipeline'
                    ORDER BY table_name
                """)
                print(f"✅ Found {len(tables)} tables in upload_pipeline schema")
                for table in tables[:5]:  # Show first 5 tables
                    print(f"   - {table['table_name']}")
                if len(tables) > 5:
                    print(f"   ... and {len(tables) - 5} more")
            
            await pool.close()
            print("✅ Connection pool closed successfully")
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            
            # Provide specific guidance based on error type
            if "Network is unreachable" in str(e):
                print("   💡 This suggests network connectivity issues")
                print("   💡 Try using the pooler URL instead of direct connection")
            elif "SSL" in str(e) or "certificate" in str(e).lower():
                print("   💡 This suggests SSL/TLS configuration issues")
                print("   💡 Make sure sslmode=require is set in the connection string")
            elif "authentication" in str(e).lower():
                print("   💡 This suggests authentication issues")
                print("   💡 Check that the service role key is correct")
            elif "timeout" in str(e).lower():
                print("   💡 This suggests timeout issues")
                print("   💡 The database might be slow to respond or unreachable")

async def main():
    """Main test function."""
    print("🔍 Testing Supabase Database Connection with SSL")
    print("=" * 60)
    
    await test_database_connection()
    
    print("\n" + "=" * 60)
    print("🎯 Test completed!")
    print("\nIf both connections failed, check:")
    print("1. Network connectivity to Supabase")
    print("2. SSL/TLS configuration")
    print("3. Authentication credentials")
    print("4. Firewall settings")

if __name__ == "__main__":
    asyncio.run(main())
