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
        "${DATABASE_URL}/TLS configuration issues")
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
