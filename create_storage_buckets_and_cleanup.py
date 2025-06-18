#!/usr/bin/env python3

import asyncio
import asyncpg
import os
import aiohttp
from dotenv import load_dotenv

async def create_storage_buckets_and_cleanup():
    load_dotenv()
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not service_role_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return
    
    print('🔧 Creating Storage Buckets and Cleaning Up Old Data')
    print('=' * 60)
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    # Step 1: Create missing storage buckets
    print('\n📦 Step 1: Creating Missing Storage Buckets')
    print('-' * 40)
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    # Create raw_documents bucket
    bucket_config = {
        'name': 'raw_documents',
        'public': False,
        'file_size_limit': 52428800,  # 50MB
        'allowed_mime_types': ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        bucket_url = f"{supabase_url}/storage/v1/bucket"
        
        try:
            async with session.post(bucket_url, json=bucket_config, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f'✅ Created raw_documents bucket: {result}')
                elif response.status == 409:
                    print('✅ raw_documents bucket already exists')
                else:
                    error_text = await response.text()
                    print(f'⚠️ Bucket creation response ({response.status}): {error_text}')
        except Exception as e:
            print(f'❌ Failed to create bucket: {e}')
    
    # Step 2: Clean up old stuck documents and jobs
    print('\n🧹 Step 2: Cleaning Up Old Stuck Data')
    print('-' * 40)
    
    # Get all stuck/failed documents older than 1 hour
    old_docs = await conn.fetch('''
        SELECT id, original_filename, status, created_at,
               EXTRACT(EPOCH FROM (NOW() - created_at))/3600 as age_hours
        FROM documents 
        WHERE (status IN ('pending', 'parsing', 'failed') OR storage_path IS NULL)
        AND created_at < NOW() - INTERVAL '1 hour'
        ORDER BY created_at DESC
    ''')
    
    print(f'📋 Found {len(old_docs)} old stuck documents to clean up:')
    for doc in old_docs:
        print(f'   📄 {doc["original_filename"]} | Status: {doc["status"]} | Age: {doc["age_hours"]:.1f}h')
    
    if old_docs:
        # Delete old stuck processing jobs
        job_delete_count = await conn.execute('''
            DELETE FROM processing_jobs 
            WHERE document_id = ANY($1)
        ''', [doc["id"] for doc in old_docs])
        
        print(f'🗑️ Deleted {job_delete_count.split()[-1]} old processing jobs')
        
        # Delete old stuck documents
        doc_delete_count = await conn.execute('''
            DELETE FROM documents 
            WHERE id = ANY($1)
        ''', [doc["id"] for doc in old_docs])
        
        print(f'🗑️ Deleted {doc_delete_count.split()[-1]} old stuck documents')
    
    # Step 3: Reset any remaining stuck jobs
    print('\n🔄 Step 3: Resetting Current Stuck Jobs')
    print('-' * 40)
    
    # Reset jobs stuck in 'running' status for > 5 minutes
    reset_count = await conn.execute('''
        UPDATE processing_jobs 
        SET status = 'pending',
            updated_at = NOW(),
            retry_count = 0
        WHERE status = 'running' 
        AND created_at < NOW() - INTERVAL '5 minutes'
    ''')
    
    print(f'🔄 Reset {reset_count.split()[-1]} stuck jobs to pending')
    
    # Reset documents stuck in 'parsing' status
    doc_reset_count = await conn.execute('''
        UPDATE documents 
        SET status = 'pending',
            progress_percentage = 0,
            updated_at = NOW()
        WHERE status = 'parsing'
        AND updated_at < NOW() - INTERVAL '5 minutes'
    ''')
    
    print(f'📄 Reset {doc_reset_count.split()[-1]} documents from parsing to pending')
    
    # Step 4: Update doc-parser to use correct bucket
    print('\n⚙️ Step 4: Bucket Configuration Status')
    print('-' * 40)
    print('📝 TODO: Update doc-parser Edge Function to use raw_documents bucket')
    print('📝 Current: doc-parser uses "documents" bucket')
    print('📝 Required: doc-parser should use "raw_documents" bucket')
    print('📝 Location: db/supabase/functions/doc-parser/index.ts line ~45')
    
    # Step 5: Verify current queue status
    print('\n📊 Step 5: Current Queue Status')
    print('-' * 40)
    
    # Check pending jobs
    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
    print(f'⏳ Pending jobs ready for processing: {len(pending_jobs)}')
    
    # Check document status distribution
    doc_status = await conn.fetch('''
        SELECT status, COUNT(*) as count
        FROM documents 
        GROUP BY status
        ORDER BY count DESC
    ''')
    
    print(f'📄 Document status distribution:')
    for status in doc_status:
        print(f'   {status["status"]}: {status["count"]} documents')
    
    # Step 6: Check if buckets exist
    print('\n🔍 Step 6: Verifying Storage Buckets')
    print('-' * 40)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        buckets_url = f"{supabase_url}/storage/v1/bucket"
        
        try:
            async with session.get(buckets_url, headers=headers) as response:
                if response.status == 200:
                    buckets = await response.json()
                    bucket_names = [b['name'] for b in buckets]
                    print(f'📦 Available buckets: {bucket_names}')
                    
                    if 'raw_documents' in bucket_names:
                        print('✅ raw_documents bucket exists')
                    else:
                        print('❌ raw_documents bucket missing')
                        
                    if 'documents' in bucket_names:
                        print('✅ documents bucket exists')
                    else:
                        print('❌ documents bucket missing')
                else:
                    error_text = await response.text()
                    print(f'❌ Failed to list buckets: {response.status} - {error_text}')
        except Exception as e:
            print(f'❌ Failed to check buckets: {e}')
    
    await conn.close()
    
    print(f'\n🎉 Cleanup Complete!')
    print(f'📝 Next Steps:')
    print(f'   1. Update doc-parser to use raw_documents bucket')
    print(f'   2. Test queue processing with: python test_edge_function_auth.py')
    print(f'   3. Upload a new document to test end-to-end')

if __name__ == "__main__":
    asyncio.run(create_storage_buckets_and_cleanup()) 

import asyncio
import asyncpg
import os
import aiohttp
from dotenv import load_dotenv

async def create_storage_buckets_and_cleanup():
    load_dotenv()
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not service_role_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return
    
    print('🔧 Creating Storage Buckets and Cleaning Up Old Data')
    print('=' * 60)
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    # Step 1: Create missing storage buckets
    print('\n📦 Step 1: Creating Missing Storage Buckets')
    print('-' * 40)
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    # Create raw_documents bucket
    bucket_config = {
        'name': 'raw_documents',
        'public': False,
        'file_size_limit': 52428800,  # 50MB
        'allowed_mime_types': ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        bucket_url = f"{supabase_url}/storage/v1/bucket"
        
        try:
            async with session.post(bucket_url, json=bucket_config, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f'✅ Created raw_documents bucket: {result}')
                elif response.status == 409:
                    print('✅ raw_documents bucket already exists')
                else:
                    error_text = await response.text()
                    print(f'⚠️ Bucket creation response ({response.status}): {error_text}')
        except Exception as e:
            print(f'❌ Failed to create bucket: {e}')
    
    # Step 2: Clean up old stuck documents and jobs
    print('\n🧹 Step 2: Cleaning Up Old Stuck Data')
    print('-' * 40)
    
    # Get all stuck/failed documents older than 1 hour
    old_docs = await conn.fetch('''
        SELECT id, original_filename, status, created_at,
               EXTRACT(EPOCH FROM (NOW() - created_at))/3600 as age_hours
        FROM documents 
        WHERE (status IN ('pending', 'parsing', 'failed') OR storage_path IS NULL)
        AND created_at < NOW() - INTERVAL '1 hour'
        ORDER BY created_at DESC
    ''')
    
    print(f'📋 Found {len(old_docs)} old stuck documents to clean up:')
    for doc in old_docs:
        print(f'   📄 {doc["original_filename"]} | Status: {doc["status"]} | Age: {doc["age_hours"]:.1f}h')
    
    if old_docs:
        # Delete old stuck processing jobs
        job_delete_count = await conn.execute('''
            DELETE FROM processing_jobs 
            WHERE document_id = ANY($1)
        ''', [doc["id"] for doc in old_docs])
        
        print(f'🗑️ Deleted {job_delete_count.split()[-1]} old processing jobs')
        
        # Delete old stuck documents
        doc_delete_count = await conn.execute('''
            DELETE FROM documents 
            WHERE id = ANY($1)
        ''', [doc["id"] for doc in old_docs])
        
        print(f'🗑️ Deleted {doc_delete_count.split()[-1]} old stuck documents')
    
    # Step 3: Reset any remaining stuck jobs
    print('\n🔄 Step 3: Resetting Current Stuck Jobs')
    print('-' * 40)
    
    # Reset jobs stuck in 'running' status for > 5 minutes
    reset_count = await conn.execute('''
        UPDATE processing_jobs 
        SET status = 'pending',
            updated_at = NOW(),
            retry_count = 0
        WHERE status = 'running' 
        AND created_at < NOW() - INTERVAL '5 minutes'
    ''')
    
    print(f'🔄 Reset {reset_count.split()[-1]} stuck jobs to pending')
    
    # Reset documents stuck in 'parsing' status
    doc_reset_count = await conn.execute('''
        UPDATE documents 
        SET status = 'pending',
            progress_percentage = 0,
            updated_at = NOW()
        WHERE status = 'parsing'
        AND updated_at < NOW() - INTERVAL '5 minutes'
    ''')
    
    print(f'📄 Reset {doc_reset_count.split()[-1]} documents from parsing to pending')
    
    # Step 4: Update doc-parser to use correct bucket
    print('\n⚙️ Step 4: Bucket Configuration Status')
    print('-' * 40)
    print('📝 TODO: Update doc-parser Edge Function to use raw_documents bucket')
    print('📝 Current: doc-parser uses "documents" bucket')
    print('📝 Required: doc-parser should use "raw_documents" bucket')
    print('📝 Location: db/supabase/functions/doc-parser/index.ts line ~45')
    
    # Step 5: Verify current queue status
    print('\n📊 Step 5: Current Queue Status')
    print('-' * 40)
    
    # Check pending jobs
    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
    print(f'⏳ Pending jobs ready for processing: {len(pending_jobs)}')
    
    # Check document status distribution
    doc_status = await conn.fetch('''
        SELECT status, COUNT(*) as count
        FROM documents 
        GROUP BY status
        ORDER BY count DESC
    ''')
    
    print(f'📄 Document status distribution:')
    for status in doc_status:
        print(f'   {status["status"]}: {status["count"]} documents')
    
    # Step 6: Check if buckets exist
    print('\n🔍 Step 6: Verifying Storage Buckets')
    print('-' * 40)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        buckets_url = f"{supabase_url}/storage/v1/bucket"
        
        try:
            async with session.get(buckets_url, headers=headers) as response:
                if response.status == 200:
                    buckets = await response.json()
                    bucket_names = [b['name'] for b in buckets]
                    print(f'📦 Available buckets: {bucket_names}')
                    
                    if 'raw_documents' in bucket_names:
                        print('✅ raw_documents bucket exists')
                    else:
                        print('❌ raw_documents bucket missing')
                        
                    if 'documents' in bucket_names:
                        print('✅ documents bucket exists')
                    else:
                        print('❌ documents bucket missing')
                else:
                    error_text = await response.text()
                    print(f'❌ Failed to list buckets: {response.status} - {error_text}')
        except Exception as e:
            print(f'❌ Failed to check buckets: {e}')
    
    await conn.close()
    
    print(f'\n🎉 Cleanup Complete!')
    print(f'📝 Next Steps:')
    print(f'   1. Update doc-parser to use raw_documents bucket')
    print(f'   2. Test queue processing with: python test_edge_function_auth.py')
    print(f'   3. Upload a new document to test end-to-end')

if __name__ == "__main__":
    asyncio.run(create_storage_buckets_and_cleanup()) 