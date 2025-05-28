#!/usr/bin/env python3
"""List all users in the database."""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.services.db_pool import get_db_pool

async def list_all_users():
    """List all users in the database."""
    try:
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            users = await conn.fetch('''
                SELECT id, email, full_name, created_at, is_active 
                FROM users 
                ORDER BY created_at DESC 
                LIMIT 50
            ''')
            
            print(f"Found {len(users)} users in database:")
            print("-" * 80)
            
            for user in users:
                active_status = "✅" if user['is_active'] else "❌"
                print(f"{active_status} {user['email']} | {user['full_name']} | {user['created_at']}")
                
            print("-" * 80)
            print(f"Total: {len(users)} users")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(list_all_users()) 