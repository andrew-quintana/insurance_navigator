#!/usr/bin/env python3
"""Check database tables and user data."""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.services.db_pool import get_db_pool

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

if __name__ == "__main__":
    check_database() 