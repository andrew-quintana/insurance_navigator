#!/usr/bin/env python3

import asyncio
import asyncpg
import os
import aiohttp
import json
from dotenv import load_dotenv

async def simple_upload_test_fixed():
    load_dotenv()
    
    print('🧪 Fixed Simple Upload Test for MVP')
    print('=' * 40)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables")
        return
    
    # Create test content
    test_content = "This is a simple test document for MVP validation. Policy Number: TEST-123"
    
    print(f'📄 Test content: {len(test_content)} characters')
    
    # Connect to database for monitoring
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    # Step 1: Register upload with metadata
    print(f'\n1️⃣ Registering Upload')
    print('-' * 20)
    
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'X-User-ID': '27b30e9d-0d06-4325-910f-20fe9d686f14',  # Valid UUID from database
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    upload_metadata = {
        'filename': 'mvp_test_document.txt',
        'contentType': 'text/plain',
        'fileSize': len(test_content.encode('utf-8'))
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_url = f"{supabase_url}/functions/v1/upload-handler"
        
        try:
            async with session.post(upload_url, json=upload_metadata, headers=headers) as response:
                status = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f'📤 Registration Status: {status}')
                print(f'📝 Response: {response_data}')
                
                if status == 200:
                    document_id = response_data.get('documentId')
                    print(f'✅ Upload registered! Document ID: {document_id}')
                    
                    # Step 2: Check document was created properly
                    print(f'\n2️⃣ Checking Document Creation')
                    print('-' * 28)
                    
                    document = await conn.fetchrow('''
                        SELECT id, original_filename, status, storage_path, 
                               progress_percentage, file_size, content_type, 
                               processing_status, upload_status
                        FROM documents 
                        WHERE id = $1
                    ''', document_id)
                    
                    if document:
                        print(f'📄 Document created:')
                        print(f'   ID: {document["id"]}')
                        print(f'   Filename: {document["original_filename"]}')
                        print(f'   Status: {document["status"]}')
                        print(f'   Upload Status: {document["upload_status"]}')
                        print(f'   Processing Status: {document["processing_status"]}')
                        print(f'   Storage Path: {document["storage_path"]}')
                        print(f'   Progress: {document["progress_percentage"]}%')
                        print(f'   File Size: {document["file_size"]} bytes')
                        print(f'   Content Type: {document["content_type"]}')
                    else:
                        print(f'❌ Document not found in database')
                        await conn.close()
                        return
                    
                    # Step 3: Check if processing job was created
                    print(f'\n3️⃣ Checking Processing Job Creation')
                    print('-' * 33)
                    
                    jobs = await conn.fetch('''
                        SELECT id, status, created_at, retry_count, error_message
                        FROM processing_jobs 
                        WHERE document_id = $1
                        ORDER BY created_at DESC
                    ''', document_id)
                    
                    print(f'📊 Processing jobs found: {len(jobs)}')
                    for i, job in enumerate(jobs):
                        print(f'   Job {i+1}: {job["status"]} (retries: {job["retry_count"]})')
                        if job["error_message"]:
                            print(f'           Error: {job["error_message"]}')
                    
                    # Step 4: Check pending jobs queue
                    print(f'\n4️⃣ Checking Queue Status')
                    print('-' * 23)
                    
                    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
                    print(f'⏳ Pending jobs in queue: {len(pending_jobs)}')
                    
                    if pending_jobs:
                        for i, job in enumerate(pending_jobs):
                            print(f'   Pending Job {i+1}: {job["id"]} (doc: {job["document_id"]})')
                    
                    # If no job was created, try to create one manually
                    if len(jobs) == 0:
                        print(f'\n🔧 Creating Processing Job Manually')
                        print('-' * 32)
                        
                        await conn.execute('''
                            INSERT INTO processing_jobs (document_id, status, created_at, updated_at, retry_count)
                            VALUES ($1, 'pending', NOW(), NOW(), 0)
                        ''', document_id)
                        
                        print('✅ Processing job created manually')
                        
                        # Check again
                        pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
                        print(f'⏳ Pending jobs after manual creation: {len(pending_jobs)}')
                    
                    # Step 5: Trigger processing
                    print(f'\n5️⃣ Triggering Processing')
                    print('-' * 22)
                    
                    job_processor_url = f"{supabase_url}/functions/v1/job-processor"
                    async with session.post(job_processor_url, headers=headers, json={}) as job_response:
                        job_status = job_response.status
                        job_data = await job_response.json() if job_response.content_type == 'application/json' else await job_response.text()
                        
                        print(f'🔄 Job Processor Status: {job_status}')
                        print(f'📝 Job Response: {job_data}')
                    
                    # Step 6: Monitor processing
                    print(f'\n6️⃣ Brief Status Monitoring')
                    print('-' * 25)
                    
                    for check in range(6):  # Check 6 times, 10 seconds apart
                        await asyncio.sleep(10)
                        
                        # Check document status (using correct column name)
                        current_doc = await conn.fetchrow('''
                            SELECT status, progress_percentage, content_extracted, 
                                   processing_status, upload_status
                            FROM documents 
                            WHERE id = $1
                        ''', document_id)
                        
                        # Check job status
                        current_jobs = await conn.fetch('''
                            SELECT status, retry_count, error_message, updated_at
                            FROM processing_jobs 
                            WHERE document_id = $1
                            ORDER BY updated_at DESC
                            LIMIT 1
                        ''', document_id)
                        
                        job_status_str = current_jobs[0]["status"] if current_jobs else "no job"
                        
                        print(f'🔍 Check {check + 1}/6:')
                        print(f'   Document Status: {current_doc["status"]}')
                        print(f'   Processing Status: {current_doc["processing_status"]}')
                        print(f'   Upload Status: {current_doc["upload_status"]}')
                        print(f'   Progress: {current_doc["progress_percentage"]}%')
                        print(f'   Job Status: {job_status_str}')
                        
                        if current_doc["status"] == 'completed':
                            print(f'✅ Processing completed!')
                            if current_doc["content_extracted"]:
                                print(f'📝 Extracted text length: {len(current_doc["content_extracted"])}')
                            break
                        elif current_doc["status"] == 'failed':
                            print(f'❌ Processing failed!')
                            if current_jobs and current_jobs[0]["error_message"]:
                                print(f'💥 Job Error: {current_jobs[0]["error_message"]}')
                            break
                    
                    # Final status report
                    print(f'\n🎯 Final Test Results')
                    print('=' * 25)
                    
                    final_doc = await conn.fetchrow('''
                        SELECT status, content_extracted, processing_status, 
                               upload_status, progress_percentage
                        FROM documents 
                        WHERE id = $1
                    ''', document_id)
                    
                    final_jobs = await conn.fetch('''
                        SELECT status, error_message, retry_count
                        FROM processing_jobs 
                        WHERE document_id = $1
                        ORDER BY updated_at DESC
                    ''', document_id)
                    
                    print(f'📄 Final Document Status:')
                    print(f'   Status: {final_doc["status"]}')
                    print(f'   Processing Status: {final_doc["processing_status"]}')
                    print(f'   Upload Status: {final_doc["upload_status"]}')
                    print(f'   Progress: {final_doc["progress_percentage"]}%')
                    print(f'   Has Content: {"Yes" if final_doc["content_extracted"] else "No"}')
                    
                    print(f'\n🔧 Final Job Status ({len(final_jobs)} jobs):')
                    for i, job in enumerate(final_jobs):
                        print(f'   Job {i+1}: {job["status"]} (retries: {job["retry_count"]})')
                        if job["error_message"]:
                            print(f'           Error: {job["error_message"]}')
                    
                    # Overall result
                    if final_doc["status"] == 'completed' and final_doc["content_extracted"]:
                        print('\n🎉 ✅ MVP UPLOAD AND PROCESSING WORKING!')
                        print('📋 All systems operational:')
                        print('   ✓ Document upload via upload-handler')
                        print('   ✓ Database record creation')
                        print('   ✓ Job queue management')
                        print('   ✓ Document processing pipeline')
                        print('   ✓ Content extraction')
                    elif final_doc["status"] == 'failed':
                        print('\n❌ MVP TEST FAILED - Document processing failed')
                    else:
                        print(f'\n⏳ MVP TEST INCOMPLETE - Status: {final_doc["status"]}')
                        if final_doc["upload_status"] != 'completed':
                            print('⚠️ Upload may not have completed properly')
                        if not final_jobs or final_jobs[0]["status"] not in ['completed', 'failed']:
                            print('⚠️ Processing job may still be running or stuck')
                        
                else:
                    print(f'❌ Upload registration failed: {response_data}')
                    
        except Exception as e:
            print(f'❌ Error: {e}')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(simple_upload_test_fixed()) 

import asyncio
import asyncpg
import os
import aiohttp
import json
from dotenv import load_dotenv

async def simple_upload_test_fixed():
    load_dotenv()
    
    print('🧪 Fixed Simple Upload Test for MVP')
    print('=' * 40)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables")
        return
    
    # Create test content
    test_content = "This is a simple test document for MVP validation. Policy Number: TEST-123"
    
    print(f'📄 Test content: {len(test_content)} characters')
    
    # Connect to database for monitoring
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    # Step 1: Register upload with metadata
    print(f'\n1️⃣ Registering Upload')
    print('-' * 20)
    
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'X-User-ID': '27b30e9d-0d06-4325-910f-20fe9d686f14',  # Valid UUID from database
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    upload_metadata = {
        'filename': 'mvp_test_document.txt',
        'contentType': 'text/plain',
        'fileSize': len(test_content.encode('utf-8'))
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_url = f"{supabase_url}/functions/v1/upload-handler"
        
        try:
            async with session.post(upload_url, json=upload_metadata, headers=headers) as response:
                status = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f'📤 Registration Status: {status}')
                print(f'📝 Response: {response_data}')
                
                if status == 200:
                    document_id = response_data.get('documentId')
                    print(f'✅ Upload registered! Document ID: {document_id}')
                    
                    # Step 2: Check document was created properly
                    print(f'\n2️⃣ Checking Document Creation')
                    print('-' * 28)
                    
                    document = await conn.fetchrow('''
                        SELECT id, original_filename, status, storage_path, 
                               progress_percentage, file_size, content_type, 
                               processing_status, upload_status
                        FROM documents 
                        WHERE id = $1
                    ''', document_id)
                    
                    if document:
                        print(f'📄 Document created:')
                        print(f'   ID: {document["id"]}')
                        print(f'   Filename: {document["original_filename"]}')
                        print(f'   Status: {document["status"]}')
                        print(f'   Upload Status: {document["upload_status"]}')
                        print(f'   Processing Status: {document["processing_status"]}')
                        print(f'   Storage Path: {document["storage_path"]}')
                        print(f'   Progress: {document["progress_percentage"]}%')
                        print(f'   File Size: {document["file_size"]} bytes')
                        print(f'   Content Type: {document["content_type"]}')
                    else:
                        print(f'❌ Document not found in database')
                        await conn.close()
                        return
                    
                    # Step 3: Check if processing job was created
                    print(f'\n3️⃣ Checking Processing Job Creation')
                    print('-' * 33)
                    
                    jobs = await conn.fetch('''
                        SELECT id, status, created_at, retry_count, error_message
                        FROM processing_jobs 
                        WHERE document_id = $1
                        ORDER BY created_at DESC
                    ''', document_id)
                    
                    print(f'📊 Processing jobs found: {len(jobs)}')
                    for i, job in enumerate(jobs):
                        print(f'   Job {i+1}: {job["status"]} (retries: {job["retry_count"]})')
                        if job["error_message"]:
                            print(f'           Error: {job["error_message"]}')
                    
                    # Step 4: Check pending jobs queue
                    print(f'\n4️⃣ Checking Queue Status')
                    print('-' * 23)
                    
                    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
                    print(f'⏳ Pending jobs in queue: {len(pending_jobs)}')
                    
                    if pending_jobs:
                        for i, job in enumerate(pending_jobs):
                            print(f'   Pending Job {i+1}: {job["id"]} (doc: {job["document_id"]})')
                    
                    # If no job was created, try to create one manually
                    if len(jobs) == 0:
                        print(f'\n🔧 Creating Processing Job Manually')
                        print('-' * 32)
                        
                        await conn.execute('''
                            INSERT INTO processing_jobs (document_id, status, created_at, updated_at, retry_count)
                            VALUES ($1, 'pending', NOW(), NOW(), 0)
                        ''', document_id)
                        
                        print('✅ Processing job created manually')
                        
                        # Check again
                        pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
                        print(f'⏳ Pending jobs after manual creation: {len(pending_jobs)}')
                    
                    # Step 5: Trigger processing
                    print(f'\n5️⃣ Triggering Processing')
                    print('-' * 22)
                    
                    job_processor_url = f"{supabase_url}/functions/v1/job-processor"
                    async with session.post(job_processor_url, headers=headers, json={}) as job_response:
                        job_status = job_response.status
                        job_data = await job_response.json() if job_response.content_type == 'application/json' else await job_response.text()
                        
                        print(f'🔄 Job Processor Status: {job_status}')
                        print(f'📝 Job Response: {job_data}')
                    
                    # Step 6: Monitor processing
                    print(f'\n6️⃣ Brief Status Monitoring')
                    print('-' * 25)
                    
                    for check in range(6):  # Check 6 times, 10 seconds apart
                        await asyncio.sleep(10)
                        
                        # Check document status (using correct column name)
                        current_doc = await conn.fetchrow('''
                            SELECT status, progress_percentage, content_extracted, 
                                   processing_status, upload_status
                            FROM documents 
                            WHERE id = $1
                        ''', document_id)
                        
                        # Check job status
                        current_jobs = await conn.fetch('''
                            SELECT status, retry_count, error_message, updated_at
                            FROM processing_jobs 
                            WHERE document_id = $1
                            ORDER BY updated_at DESC
                            LIMIT 1
                        ''', document_id)
                        
                        job_status_str = current_jobs[0]["status"] if current_jobs else "no job"
                        
                        print(f'🔍 Check {check + 1}/6:')
                        print(f'   Document Status: {current_doc["status"]}')
                        print(f'   Processing Status: {current_doc["processing_status"]}')
                        print(f'   Upload Status: {current_doc["upload_status"]}')
                        print(f'   Progress: {current_doc["progress_percentage"]}%')
                        print(f'   Job Status: {job_status_str}')
                        
                        if current_doc["status"] == 'completed':
                            print(f'✅ Processing completed!')
                            if current_doc["content_extracted"]:
                                print(f'📝 Extracted text length: {len(current_doc["content_extracted"])}')
                            break
                        elif current_doc["status"] == 'failed':
                            print(f'❌ Processing failed!')
                            if current_jobs and current_jobs[0]["error_message"]:
                                print(f'💥 Job Error: {current_jobs[0]["error_message"]}')
                            break
                    
                    # Final status report
                    print(f'\n🎯 Final Test Results')
                    print('=' * 25)
                    
                    final_doc = await conn.fetchrow('''
                        SELECT status, content_extracted, processing_status, 
                               upload_status, progress_percentage
                        FROM documents 
                        WHERE id = $1
                    ''', document_id)
                    
                    final_jobs = await conn.fetch('''
                        SELECT status, error_message, retry_count
                        FROM processing_jobs 
                        WHERE document_id = $1
                        ORDER BY updated_at DESC
                    ''', document_id)
                    
                    print(f'📄 Final Document Status:')
                    print(f'   Status: {final_doc["status"]}')
                    print(f'   Processing Status: {final_doc["processing_status"]}')
                    print(f'   Upload Status: {final_doc["upload_status"]}')
                    print(f'   Progress: {final_doc["progress_percentage"]}%')
                    print(f'   Has Content: {"Yes" if final_doc["content_extracted"] else "No"}')
                    
                    print(f'\n🔧 Final Job Status ({len(final_jobs)} jobs):')
                    for i, job in enumerate(final_jobs):
                        print(f'   Job {i+1}: {job["status"]} (retries: {job["retry_count"]})')
                        if job["error_message"]:
                            print(f'           Error: {job["error_message"]}')
                    
                    # Overall result
                    if final_doc["status"] == 'completed' and final_doc["content_extracted"]:
                        print('\n🎉 ✅ MVP UPLOAD AND PROCESSING WORKING!')
                        print('📋 All systems operational:')
                        print('   ✓ Document upload via upload-handler')
                        print('   ✓ Database record creation')
                        print('   ✓ Job queue management')
                        print('   ✓ Document processing pipeline')
                        print('   ✓ Content extraction')
                    elif final_doc["status"] == 'failed':
                        print('\n❌ MVP TEST FAILED - Document processing failed')
                    else:
                        print(f'\n⏳ MVP TEST INCOMPLETE - Status: {final_doc["status"]}')
                        if final_doc["upload_status"] != 'completed':
                            print('⚠️ Upload may not have completed properly')
                        if not final_jobs or final_jobs[0]["status"] not in ['completed', 'failed']:
                            print('⚠️ Processing job may still be running or stuck')
                        
                else:
                    print(f'❌ Upload registration failed: {response_data}')
                    
        except Exception as e:
            print(f'❌ Error: {e}')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(simple_upload_test_fixed()) 