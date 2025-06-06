#!/usr/bin/env python3
"""
Fix database user creation with proper asyncpg configuration for pgbouncer
"""

import asyncio
import os
import asyncpg
from supabase import create_client

async def fix_database_users():
    """Create test users with proper asyncpg configuration"""
    database_url = os.getenv('DATABASE_URL')
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    print("🔧 Creating test users with proper configuration...")
    
    try:
        # Connect with statement_cache_size=0 for pgbouncer compatibility
        conn = await asyncpg.connect(database_url, statement_cache_size=0)
        
        # Test users to create
        test_users = [
            ('00000000-0000-0000-0000-000000000000', 'test-user-zero@example.com', 'Test User Zero'),
            ('00000000-0000-0000-0000-000000000001', 'test-user-one@example.com', 'Test User One')
        ]
        
        for user_id, email, full_name in test_users:
            try:
                # Check if user exists first
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)",
                    user_id
                )
                
                if not exists:
                    # Insert user
                    await conn.execute(
                        """INSERT INTO users (id, email, full_name, hashed_password, created_at, updated_at)
                           VALUES ($1, $2, $3, 'test_hash', NOW(), NOW())""",
                        user_id, email, full_name
                    )
                    print(f"✅ Created user: {email}")
                else:
                    print(f"ℹ️ User already exists: {email}")
                    
            except Exception as e:
                print(f"❌ Failed to create user {email}: {str(e)}")
        
        await conn.close()
        
        # Now test with Supabase client
        print("\n🧪 Testing document creation...")
        supabase = create_client(supabase_url, supabase_service_key)
        
        test_document = {
            'user_id': '00000000-0000-0000-0000-000000000001',
            'original_filename': 'test_final.pdf',
            'file_size': 1024,
            'content_type': 'application/pdf',
            'file_hash': 'final_test_hash',
            'status': 'pending',
            'progress_percentage': 0,
            'total_chunks': 1,
            'processed_chunks': 0,
            'failed_chunks': 0,
            'storage_path': 'test/final_test_hash/test_final.pdf'
        }
        
        # Test document creation
        doc_result = supabase.table('documents').insert(test_document).execute()
        if doc_result.data:
            doc_id = doc_result.data[0]['id']
            print(f"✅ Document creation: SUCCESS (ID: {doc_id})")
            
            # Test progress tracking
            progress_update = {
                'user_id': '00000000-0000-0000-0000-000000000001',
                'document_id': doc_id,
                'payload': {
                    'type': 'final_test',
                    'progress': 100,
                    'status': 'completed'
                }
            }
            
            progress_result = supabase.table('realtime_progress_updates').insert(progress_update).execute()
            if progress_result.data:
                print("✅ Progress tracking: SUCCESS")
                
                # Clean up
                supabase.table('realtime_progress_updates').delete().eq('document_id', doc_id).execute()
            else:
                print("❌ Progress tracking: FAILED")
                
            # Clean up document
            supabase.table('documents').delete().eq('id', doc_id).execute()
            print("🧹 Cleaned up test data")
        else:
            print("❌ Document creation: FAILED")
            
        print("\n✅ Database fixes complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database fix failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(fix_database_users()) 