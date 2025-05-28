#!/usr/bin/env python3
"""Check database tables and user data."""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.services.db_pool import get_db_pool

async def check_database():
    """Check database tables and user data."""
    try:
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            # List all tables
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            
            print("📋 Database Tables:")
            print("-" * 40)
            for table in tables:
                print(f"  • {table['table_name']}")
            
            # Check users table specifically
            print(f"\n👥 Users Table Analysis:")
            print("-" * 40)
            
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            print(f"Total users: {user_count}")
            
            # Check if there are any deleted users or soft deletes
            try:
                deleted_count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = false")
                print(f"Inactive users: {deleted_count}")
            except:
                print("No is_active column found")
            
            # Check for any emails with test patterns
            test_patterns = ['%test%', '%@example.com', '%storage_test%', '%testuser%', '%api_test%']
            for pattern in test_patterns:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM users WHERE email LIKE '{pattern}'")
                if count > 0:
                    print(f"Users matching '{pattern}': {count}")
            
            # List all users with their details
            users = await conn.fetch("""
                SELECT id, email, full_name, created_at, is_active 
                FROM users 
                ORDER BY created_at DESC
            """)
            
            print(f"\n📝 All Users ({len(users)}):")
            print("-" * 80)
            
            for user in users:
                active_status = "✅" if user['is_active'] else "❌"
                print(f"{active_status} {user['email']} | {user['full_name']} | {user['created_at']}")
            
            # Check conversations table
            try:
                conv_count = await conn.fetchval("SELECT COUNT(*) FROM conversations")
                print(f"\n💬 Conversations: {conv_count}")
            except Exception as e:
                print(f"\n💬 Conversations table: Error - {e}")
            
            # Check document metadata
            try:
                doc_count = await conn.fetchval("SELECT COUNT(*) FROM document_metadata")
                print(f"📄 Documents: {doc_count}")
            except Exception as e:
                print(f"📄 Documents table: Error - {e}")
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_database()) 