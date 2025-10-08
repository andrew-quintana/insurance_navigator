#!/usr/bin/env python3
"""
Simple Database Connectivity Test

Basic test to identify the production database connectivity issue.
"""

import asyncio
import os
import socket
import ssl
import time
import asyncpg

async def test_basic_connectivity():
    """Test basic connectivity to production database."""
    host = "db.your-project.supabase.co"
    port = 5432
    
    print(f"🔍 Testing connectivity to {host}:{port}")
    
    # Test 1: Basic socket connection
    try:
        print("1. Testing basic socket connection...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print("   ✅ Socket connection successful")
        else:
            print(f"   ❌ Socket connection failed with error code: {result}")
            return False
    except Exception as e:
        print(f"   ❌ Socket connection failed: {e}")
        return False
    
    # Test 2: SSL handshake
    try:
        print("2. Testing SSL handshake...")
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        ssl_sock = context.wrap_socket(sock, server_hostname=host)
        print(f"   ✅ SSL handshake successful - Protocol: {ssl_sock.version()}")
        ssl_sock.close()
    except Exception as e:
        print(f"   ❌ SSL handshake failed: {e}")
        return False
    
    # Test 3: Database connection with different SSL modes
    print("3. Testing database connections with different SSL modes...")
    
    ssl_modes = ['disable', 'prefer', 'require']
    
    for ssl_mode in ssl_modes:
        try:
            print(f"   Testing SSL mode: {ssl_mode}")
            conn = await asyncpg.connect(
                host=host,
                port=port,
                database="postgres",
                user="postgres",
                password="beqhar-qincyg-Syxxi8",
                ssl=ssl_mode,
                command_timeout=30
            )
            
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            
            print(f"   ✅ Database connection successful with SSL mode: {ssl_mode}")
            print(f"   📊 PostgreSQL version: {version[:50]}...")
            return True
            
        except Exception as e:
            print(f"   ❌ Database connection failed with SSL mode {ssl_mode}: {e}")
    
    return False

async def test_connection_strings():
    """Test different connection string formats."""
    print("\n4. Testing connection string formats...")
    
    # Use environment variables for database connection
    db_url = os.getenv("DATABASE_URL", "postgresql://***REDACTED***@db.your-project.supabase.co:5432/postgres")
    connection_strings = [
        db_url,
        f"{db_url}?sslmode=require",
        f"{db_url}?ssl=require",
    ]
    
    for i, conn_str in enumerate(connection_strings, 1):
        try:
            print(f"   Testing connection string format {i}...")
            conn = await asyncpg.connect(conn_str, command_timeout=30)
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            
            print(f"   ✅ Connection string {i} successful")
            print(f"   📊 PostgreSQL version: {version[:50]}...")
            return True
            
        except Exception as e:
            print(f"   ❌ Connection string {i} failed: {e}")
    
    return False

async def main():
    """Main test function."""
    print("🚨 PRODUCTION DATABASE CONNECTIVITY TEST")
    print("=" * 60)
    
    # Test basic connectivity
    basic_success = await test_basic_connectivity()
    
    # Test connection strings
    conn_str_success = await test_connection_strings()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Basic Connectivity: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"Connection Strings: {'✅ PASS' if conn_str_success else '❌ FAIL'}")
    
    if basic_success or conn_str_success:
        print("\n🎉 SUCCESS: Database connectivity is working!")
        print("The issue may be environment-specific or configuration-related.")
    else:
        print("\n❌ FAILURE: Database connectivity is not working.")
        print("This suggests a network or configuration issue.")
    
    return basic_success or conn_str_success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
