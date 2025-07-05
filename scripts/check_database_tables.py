#!/usr/bin/env python3
"""Check database tables and user data."""

import sys
import os
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.services.db_pool import get_db_pool

def get_db_connection() -> connection:
    """Create database connection from environment variables."""
    try:
        conn = psycopg2.connect(
            os.environ["SUPABASE_DB_URL"],
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)

def check_table_exists(conn: connection, table_name: str, schema: str = "public") -> bool:
    """Check if a table exists in the database."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = %s
            );
        """, (schema, table_name))
        return cur.fetchone()["exists"]

def check_rls_enabled(conn: connection, table_name: str, schema: str = "public") -> bool:
    """Check if RLS is enabled for a table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT relrowsecurity 
            FROM pg_class 
            WHERE oid = %s::regclass;
        """, (f"{schema}.{table_name}",))
        return cur.fetchone()["relrowsecurity"]

def check_policies(conn: connection, table_name: str, schema: str = "public") -> List[Dict]:
    """Get all policies for a table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT policyname, permissive, roles, cmd, qual, with_check
            FROM pg_policies
            WHERE schemaname = %s AND tablename = %s;
        """, (schema, table_name))
        return cur.fetchall()

def check_storage_bucket(conn: connection, bucket_id: str) -> Optional[Dict]:
    """Check if storage bucket exists and its configuration."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, name, public, file_size_limit, allowed_mime_types
            FROM storage.buckets
            WHERE id = %s;
        """, (bucket_id,))
        return cur.fetchone()

def check_database():
    """Check database tables and user data."""
    try:
        client = get_db_pool()
        if not client:
            print("Error: Could not get database client")
            return
            
        # List all tables
        tables = client.table('users').select('*').execute()
        
        print("📋 Database Tables:")
        print("-" * 40)
        print("  • users")
        
        # Check users table specifically
        print(f"\n👥 Users Table Analysis:")
        print("-" * 40)
        
        user_count = len(tables.data)
        print(f"Total users: {user_count}")
        
        # Check for any emails with test patterns
        test_patterns = ['test', '@example.com', 'storage_test', 'testuser', 'api_test']
        for pattern in test_patterns:
            matching_users = [u for u in tables.data if any(p in u.get('email', '') for p in test_patterns)]
            if matching_users:
                print(f"Users matching test patterns: {len(matching_users)}")
        
        # List all users with their details
        print(f"\n📝 All Users ({user_count}):")
        print("-" * 80)
        
        for user in tables.data:
            active_status = "✅" if user.get('is_active', True) else "❌"
            print(f"{active_status} {user.get('email')} | {user.get('name', 'N/A')} | {user.get('created_at')}")
        
        # Check documents table
        try:
            documents = client.table("documents").select("*").execute()
            print(f"\n📄 Documents: {len(documents.data)}")
        except Exception as e:
            print(f"📄 Documents table: Error - {e}")
                
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    """Main validation function."""
    print("🔍 Starting database validation...")
    
    conn = get_db_connection()
    
    # Check core tables
    required_tables = ["users", "documents"]
    for table in required_tables:
        if not check_table_exists(conn, table):
            print(f"❌ Required table '{table}' does not exist!")
            sys.exit(1)
        print(f"✅ Table '{table}' exists")
        
        if not check_rls_enabled(conn, table):
            print(f"❌ RLS not enabled for table '{table}'!")
            sys.exit(1)
        print(f"✅ RLS enabled for '{table}'")
        
        policies = check_policies(conn, table)
        if not policies:
            print(f"❌ No RLS policies found for '{table}'!")
            sys.exit(1)
        print(f"✅ Found {len(policies)} policies for '{table}'")
    
    # Check storage bucket
    bucket = check_storage_bucket(conn, "documents")
    if not bucket:
        print("❌ Documents storage bucket not found!")
        sys.exit(1)
    print("✅ Documents storage bucket exists")
    
    if bucket["public"]:
        print("⚠️ Warning: Documents bucket is public!")
    
    allowed_types = bucket["allowed_mime_types"]
    required_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    missing_types = set(required_types) - set(allowed_types)
    if missing_types:
        print(f"❌ Missing required MIME types: {missing_types}")
        sys.exit(1)
    print("✅ All required MIME types configured")
    
    print("\n✨ Database validation completed successfully!")

if __name__ == "__main__":
    main() 