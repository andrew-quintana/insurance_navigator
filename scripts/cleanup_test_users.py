#!/usr/bin/env python3
"""
Cleanup Test Users Script

This script removes all test users created during API integration testing.
It identifies test users by email patterns and removes them from the database.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.services.user_service import get_user_service
from db.services.db_pool import get_db_pool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cleanup_test_users():
    """Delete all test users and their related data."""
    print("🧹 Starting test user cleanup...")
    
    try:
        # Get database pool
        pool = await get_db_pool()
        
        async with pool.get_connection() as conn:
            # Find all test users
            test_users = await conn.fetch('''
                SELECT id, email, full_name FROM users 
                WHERE email LIKE '%test%' 
                   OR email LIKE '%@example.com'
                   OR email LIKE '%storage_test%'
                   OR email LIKE '%testuser%'
                   OR email LIKE '%api_test%'
                   OR email LIKE '%_test_%'
                ORDER BY email
            ''')
            
            print(f"Found {len(test_users)} test users:")
            
            if len(test_users) > 0:
                for user in test_users:
                    print(f"  - {user['email']} ({user['full_name']})")
                
                # Ask for confirmation
                confirm = input(f"\nDelete all {len(test_users)} test users? (y/N): ").strip().lower()
                
                if confirm == 'y':
                    # Start transaction
                    async with conn.transaction():
                        # Delete related data first (conversations, documents, etc.)
                        print("🗑️  Deleting related conversation data...")
                        conv_deleted = await conn.execute('''
                            DELETE FROM conversation_messages 
                            WHERE conversation_id IN (
                                SELECT id FROM conversations 
                                WHERE user_id IN (
                                    SELECT id FROM users 
                                    WHERE email LIKE '%test%' 
                                       OR email LIKE '%@example.com'
                                       OR email LIKE '%storage_test%'
                                       OR email LIKE '%testuser%'
                                       OR email LIKE '%api_test%'
                                       OR email LIKE '%_test_%'
                                )
                            )
                        ''')
                        print(f"   Deleted {conv_deleted} conversation messages")
                        
                        conv_deleted = await conn.execute('''
                            DELETE FROM conversations 
                            WHERE user_id IN (
                                SELECT id FROM users 
                                WHERE email LIKE '%test%' 
                                   OR email LIKE '%@example.com'
                                   OR email LIKE '%storage_test%'
                                   OR email LIKE '%testuser%'
                                   OR email LIKE '%api_test%'
                                   OR email LIKE '%_test_%'
                            )
                        ''')
                        print(f"   Deleted {conv_deleted} conversations")
                        
                        # Delete document metadata
                        print("🗑️  Deleting document metadata...")
                        doc_deleted = await conn.execute('''
                            DELETE FROM document_metadata 
                            WHERE uploaded_by IN (
                                SELECT id FROM users 
                                WHERE email LIKE '%test%' 
                                   OR email LIKE '%@example.com'
                                   OR email LIKE '%storage_test%'
                                   OR email LIKE '%testuser%'
                                   OR email LIKE '%api_test%'
                                   OR email LIKE '%_test_%'
                            )
                        ''')
                        print(f"   Deleted {doc_deleted} document records")
                        
                        # Delete workflow states
                        print("🗑️  Deleting workflow states...")
                        workflow_deleted = await conn.execute('''
                            DELETE FROM workflow_states 
                            WHERE user_id IN (
                                SELECT id FROM users 
                                WHERE email LIKE '%test%' 
                                   OR email LIKE '%@example.com'
                                   OR email LIKE '%storage_test%'
                                   OR email LIKE '%testuser%'
                                   OR email LIKE '%api_test%'
                                   OR email LIKE '%_test_%'
                            )
                        ''')
                        print(f"   Deleted {workflow_deleted} workflow states")
                        
                        # Delete agent states
                        print("🗑️  Deleting agent states...")
                        agent_deleted = await conn.execute('''
                            DELETE FROM agent_states 
                            WHERE conversation_id IN (
                                SELECT id FROM conversations 
                                WHERE user_id IN (
                                    SELECT id FROM users 
                                    WHERE email LIKE '%test%' 
                                       OR email LIKE '%@example.com'
                                       OR email LIKE '%storage_test%'
                                       OR email LIKE '%testuser%'
                                       OR email LIKE '%api_test%'
                                       OR email LIKE '%_test_%'
                                )
                            )
                        ''')
                        print(f"   Deleted {agent_deleted} agent states")
                        
                        # Finally delete the users
                        print("🗑️  Deleting test users...")
                        user_deleted = await conn.execute('''
                            DELETE FROM users 
                            WHERE email LIKE '%test%' 
                               OR email LIKE '%@example.com'
                               OR email LIKE '%storage_test%'
                               OR email LIKE '%testuser%'
                               OR email LIKE '%api_test%'
                               OR email LIKE '%_test_%'
                        ''')
                        
                        print(f"\n✅ Successfully deleted {user_deleted} test users and all related data!")
                        print("✅ Database cleanup complete!")
                        
                else:
                    print("❌ Cleanup cancelled")
            else:
                print("✅ No test users found to delete")
                
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        print(f"❌ Cleanup failed: {str(e)}")
        return False
    
    return True

def main():
    """Main entry point."""
    print("Insurance Navigator - Test User Cleanup")
    print("=" * 50)
    
    # Run the cleanup
    success = asyncio.run(cleanup_test_users())
    
    if success:
        print("\n🎉 Cleanup completed successfully!")
    else:
        print("\n💥 Cleanup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 