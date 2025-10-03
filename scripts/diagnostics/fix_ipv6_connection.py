#!/usr/bin/env python3
"""
IPv6 Connection Fix

This script implements the fix for the IPv6 connectivity issue by using
the Supavisor connection pooler instead of direct database connections.
"""

import asyncio
import asyncpg
import os

async def test_supavisor_connection():
    """Test the Supavisor connection pooler."""
    
    # Supavisor connection string (IPv4 compatible)
    supavisor_conn = "postgresql://postgres.your-project:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    
    print("🔍 Testing Supavisor Connection Pooler")
    print("-" * 50)
    print(f"Connection: {supavisor_conn[:80]}...")
    
    try:
        # Test connection
        conn = await asyncpg.connect(supavisor_conn, command_timeout=30)
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        
        print(f"✅ SUCCESS - PostgreSQL version: {version[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ FAILED - {e}")
        return False

async def test_direct_connection():
    """Test direct connection for comparison."""
    
    direct_conn = "postgresql://postgres:beqhar-qincyg-Syxxi8@db.your-project.supabase.co:5432/postgres"
    
    print("\n🔍 Testing Direct Connection (for comparison)")
    print("-" * 50)
    print(f"Connection: {direct_conn[:80]}...")
    
    try:
        conn = await asyncpg.connect(direct_conn, command_timeout=30)
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        
        print(f"✅ SUCCESS - PostgreSQL version: {version[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ FAILED - {e}")
        return False

def generate_environment_variables():
    """Generate the correct environment variables for Render."""
    
    print("\n🔧 GENERATING ENVIRONMENT VARIABLES")
    print("-" * 50)
    
    # Production environment variables with Supavisor
    env_vars = {
        'DATABASE_URL': 'postgresql://postgres.your-project:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres',
        'SUPABASE_DATABASE_URL': 'postgresql://postgres.your-project:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres',
        'DB_HOST': 'aws-0-us-west-1.pooler.supabase.com',
        'DB_PORT': '6543',
        'DB_NAME': 'postgres',
        'DB_USER': 'postgres.your-project',
        'DB_PASSWORD': 'beqhar-qincyg-Syxxi8',
        'DB_SSL_MODE': 'require',
        'DB_CONNECTION_TIMEOUT': '30',
        'DB_COMMAND_TIMEOUT': '30',
        'DB_POOL_MIN_SIZE': '5',
        'DB_POOL_MAX_SIZE': '20'
    }
    
    print("Production Environment Variables:")
    for key, value in env_vars.items():
        print(f"  {key}={value}")
    
    return env_vars

async def main():
    """Main function."""
    print("🚨 IPv6 CONNECTION FIX")
    print("=" * 60)
    
    # Test both connection types
    supavisor_success = await test_supavisor_connection()
    direct_success = await test_direct_connection()
    
    # Generate environment variables
    env_vars = generate_environment_variables()
    
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    print(f"Supavisor Connection: {'✅ SUCCESS' if supavisor_success else '❌ FAILED'}")
    print(f"Direct Connection: {'✅ SUCCESS' if direct_success else '❌ FAILED'}")
    
    if supavisor_success:
        print("\n🎯 RECOMMENDATION: Use Supavisor connection pooler")
        print("   - IPv4 compatible (avoids IPv6 issues)")
        print("   - Better connection management")
        print("   - Recommended for production environments")
        
        print("\n📋 NEXT STEPS:")
        print("1. Update Render environment variables with the Supavisor connection")
        print("2. Deploy the updated configuration")
        print("3. Verify the connection works in production")
        
        return True
    else:
        print("\n❌ Both connection methods failed")
        print("   This suggests a deeper network or configuration issue")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
