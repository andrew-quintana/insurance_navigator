#!/usr/bin/env python3
"""
IPv6 Connection Issue Investigation

This script investigates the IPv6 connectivity issue that may be causing
the "Network is unreachable" error in Render deployments.
"""

import asyncio
import socket
import ssl
import asyncpg
import subprocess
import sys
from typing import List, Dict, Any

def test_ipv6_support():
    """Test if the system supports IPv6."""
    print("🔍 Testing IPv6 Support")
    print("-" * 40)
    
    try:
        # Test IPv6 socket creation
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.close()
        print("✅ IPv6 socket creation: SUCCESS")
        ipv6_supported = True
    except Exception as e:
        print(f"❌ IPv6 socket creation: FAILED - {e}")
        ipv6_supported = False
    
    # Test DNS resolution for both IPv4 and IPv6
    host = "db.your-project.supabase.co"
    
    try:
        # Test IPv4 resolution
        ipv4_addrs = socket.getaddrinfo(host, 5432, socket.AF_INET, socket.SOCK_STREAM)
        print(f"✅ IPv4 resolution: {len(ipv4_addrs)} addresses found")
        for addr in ipv4_addrs:
            print(f"   - {addr[4][0]}:{addr[4][1]}")
    except Exception as e:
        print(f"❌ IPv4 resolution: FAILED - {e}")
    
    try:
        # Test IPv6 resolution
        ipv6_addrs = socket.getaddrinfo(host, 5432, socket.AF_INET6, socket.SOCK_STREAM)
        print(f"✅ IPv6 resolution: {len(ipv6_addrs)} addresses found")
        for addr in ipv6_addrs:
            print(f"   - {addr[4][0]}:{addr[4][1]}")
    except Exception as e:
        print(f"❌ IPv6 resolution: FAILED - {e}")
    
    return ipv6_supported

def test_connection_strings():
    """Test different connection string formats."""
    print("\n🔍 Testing Connection String Formats")
    print("-" * 40)
    
    # Test different connection string formats
    connection_strings = [
        # Direct connection (IPv6)
        "postgresql://postgres:beqhar-qincyg-Syxxi8@db.your-project.supabase.co:5432/postgres",
        
        # With IPv4 preference
        "postgresql://postgres:beqhar-qincyg-Syxxi8@db.your-project.supabase.co:5432/postgres?prefer_socket_families=ipv4",
        
        # With SSL mode
        "postgresql://postgres:beqhar-qincyg-Syxxi8@db.your-project.supabase.co:5432/postgres?sslmode=require",
        
        # With IPv4 preference and SSL
        "postgresql://postgres:beqhar-qincyg-Syxxi8@db.your-project.supabase.co:5432/postgres?sslmode=require&prefer_socket_families=ipv4",
        
        # With connection timeout
        "postgresql://postgres:beqhar-qincyg-Syxxi8@db.your-project.supabase.co:5432/postgres?sslmode=require&connect_timeout=30&prefer_socket_families=ipv4",
    ]
    
    results = []
    
    for i, conn_str in enumerate(connection_strings, 1):
        print(f"\nTesting connection string {i}:")
        print(f"   {conn_str[:80]}...")
        
        try:
            # Test connection
            conn = asyncio.run(asyncpg.connect(conn_str, command_timeout=10))
            version = asyncio.run(conn.fetchval("SELECT version()"))
            asyncio.run(conn.close())
            
            print(f"   ✅ SUCCESS - PostgreSQL version: {version[:50]}...")
            results.append({"success": True, "connection_string": conn_str})
            
        except Exception as e:
            print(f"   ❌ FAILED - {e}")
            results.append({"success": False, "connection_string": conn_str, "error": str(e)})
    
    return results

def test_supavisor_connection():
    """Test Supavisor connection pooler."""
    print("\n🔍 Testing Supavisor Connection Pooler")
    print("-" * 40)
    
    # Supavisor connection string (IPv4 compatible)
    supavisor_conn = "postgresql://postgres.your-project:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    
    print(f"Testing Supavisor connection:")
    print(f"   {supavisor_conn[:80]}...")
    
    try:
        conn = asyncio.run(asyncpg.connect(supavisor_conn, command_timeout=10))
        version = asyncio.run(conn.fetchval("SELECT version()"))
        asyncio.run(conn.close())
        
        print(f"   ✅ SUCCESS - PostgreSQL version: {version[:50]}...")
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED - {e}")
        return False

def test_manual_connection():
    """Test manual connection with specific parameters."""
    print("\n🔍 Testing Manual Connection Parameters")
    print("-" * 40)
    
    # Test with explicit IPv4 preference
    try:
        print("Testing with IPv4 preference...")
        conn = asyncio.run(asyncpg.connect(
            host="db.your-project.supabase.co",
            port=5432,
            database="postgres",
            user="postgres",
            password="beqhar-qincyg-Syxxi8",
            ssl="require",
            command_timeout=10,
            # Force IPv4
            server_settings={"application_name": "insurance_navigator"}
        ))
        
        version = asyncio.run(conn.fetchval("SELECT version()"))
        asyncio.run(conn.close())
        
        print(f"   ✅ SUCCESS - PostgreSQL version: {version[:50]}...")
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED - {e}")
        return False

def check_render_environment():
    """Check if we're in a Render-like environment."""
    print("\n🔍 Checking Environment")
    print("-" * 40)
    
    # Check for Render environment variables
    render_vars = ["RENDER", "RENDER_EXTERNAL_URL", "PORT"]
    for var in render_vars:
        value = subprocess.getenv(var, "NOT SET")
        print(f"   {var}: {value}")
    
    # Check network interfaces
    try:
        result = subprocess.run(["ip", "addr", "show"], capture_output=True, text=True)
        if result.returncode == 0:
            print("   Network interfaces:")
            for line in result.stdout.split('\n'):
                if 'inet ' in line or 'inet6' in line:
                    print(f"     {line.strip()}")
    except Exception as e:
        print(f"   Could not check network interfaces: {e}")

def main():
    """Main investigation function."""
    print("🚨 IPv6 CONNECTION ISSUE INVESTIGATION")
    print("=" * 60)
    
    # Test IPv6 support
    ipv6_supported = test_ipv6_support()
    
    # Test connection strings
    conn_results = test_connection_strings()
    
    # Test Supavisor
    supavisor_success = test_supavisor_connection()
    
    # Test manual connection
    manual_success = test_manual_connection()
    
    # Check environment
    check_render_environment()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INVESTIGATION SUMMARY")
    print("=" * 60)
    
    print(f"IPv6 Support: {'✅ YES' if ipv6_supported else '❌ NO'}")
    print(f"Supavisor Connection: {'✅ SUCCESS' if supavisor_success else '❌ FAILED'}")
    print(f"Manual Connection: {'✅ SUCCESS' if manual_success else '❌ FAILED'}")
    
    successful_connections = [r for r in conn_results if r["success"]]
    print(f"Successful Connection Strings: {len(successful_connections)}/{len(conn_results)}")
    
    if successful_connections:
        print("\n✅ WORKING CONNECTION STRINGS:")
        for result in successful_connections:
            print(f"   - {result['connection_string']}")
    
    if supavisor_success:
        print("\n🎯 RECOMMENDATION: Use Supavisor connection pooler")
        print("   This avoids IPv6 issues and provides better connection management")
    
    return len(successful_connections) > 0 or supavisor_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
