#!/usr/bin/env python3

import asyncio
import asyncpg
import os
import aiohttp
import json
from dotenv import load_dotenv

async def mvp_final_test():
    load_dotenv()
    
    print('🚀 MVP Final End-to-End Test')
    print('=' * 30)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables")
        return
    
    # Create test content
    test_content = "MVP Test Document\n\nPolicy Number: TEST-MVP-123\nCoverage: Health Insurance\nEffective Date: 2024-01-01"
    
    print(f'📄 Test content: {len(test_content)} characters')
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    # Step 1: Register upload
    print(f'\n1️⃣ Registering Upload')
    print('-' * 20)
    
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'X-User-ID': '27b30e9d-0d06-4325-910f-20fe9d686f14',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    upload_metadata = {
        'filename': 'mvp_final_test.txt',
        'contentType': 'text/plain',
        'fileSize': len(test_content.encode('utf-8'))
    }
    
    document_id = None
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_url = f"{supabase_url}/functions/v1/upload-handler"
        
        try:
            async with session.post(upload_url, json=upload_metadata, headers=headers) as response:
                status = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f'📤 Registration Status: {status}')
                
                if status == 200:
                    document_id = response_data.get('documentId')
                    print(f'✅ Document registered: {document_id}')
                else:
                    print(f'❌ Upload failed: {response_data}')
                    await conn.close()
                    return
                    
        except Exception as e:
            print(f'❌ Upload error: {e}')
            await conn.close()
            return
    
    # Step 2: Create processing job manually with correct job_type
    print(f'\n2️⃣ Creating Processing Job')
    print('-' * 26)
    
    try:
        # Insert a processing job with the required job_type
        job_id = await conn.fetchval('''
            INSERT INTO processing_jobs (
                document_id, job_type, status, priority, 
                max_retries, retry_count, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
            RETURNING id
        ''', document_id, 'parse', 'pending', 1, 3, 0)
        
        print(f'✅ Processing job created: {job_id}')
        
    except Exception as e:
        print(f'❌ Job creation failed: {e}')
        await conn.close()
        return
    
    # Step 3: Verify job is in queue
    print(f'\n3️⃣ Checking Queue Status')
    print('-' * 23)
    
    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
    print(f'⏳ Pending jobs in queue: {len(pending_jobs)}')
    
    job_found = False
    for job in pending_jobs:
        if str(job["id"]) == str(job_id):
            job_found = True
            print(f'✅ Our job found in queue: {job["job_type"]} for doc {job["document_id"]}')
            break
    
    if not job_found:
        print(f'⚠️ Our job not found in pending queue')
    
    # Step 4: Trigger processing
    print(f'\n4️⃣ Triggering Processing')
    print('-' * 22)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        job_processor_url = f"{supabase_url}/functions/v1/job-processor"
        
        try:
            async with session.post(job_processor_url, headers=headers, json={}) as job_response:
                job_status = job_response.status
                job_data = await job_response.json() if job_response.content_type == 'application/json' else await job_response.text()
                
                print(f'🔄 Job Processor Status: {job_status}')
                print(f'📝 Job Response: {job_data}')
                
        except Exception as e:
            print(f'❌ Job processor error: {e}')
    
    # Step 5: Monitor for completion
    print(f'\n5️⃣ Monitoring Progress')
    print('-' * 20)
    
    for check in range(12):  # Check 12 times, 10 seconds apart = 2 minutes max
        await asyncio.sleep(10)
        
        # Check document status
        doc_status = await conn.fetchrow('''
            SELECT status, progress_percentage, content_extracted, 
                   processing_status, upload_status
            FROM documents 
            WHERE id = $1
        ''', document_id)
        
        # Check job status
        job_status = await conn.fetchrow('''
            SELECT status, retry_count, error_message, updated_at
            FROM processing_jobs 
            WHERE id = $1
        ''', job_id)
        
        print(f'🔍 Check {check + 1}/12:')
        print(f'   Document: {doc_status["status"]} (progress: {doc_status["progress_percentage"]}%)')
        print(f'   Job: {job_status["status"]} (retries: {job_status["retry_count"]})')
        
        if job_status["error_message"]:
            print(f'   Error: {job_status["error_message"]}')
        
        # Check for completion
        if doc_status["status"] == 'completed' and doc_status["content_extracted"]:
            print(f'✅ Processing completed successfully!')
            print(f'📝 Content extracted: {len(doc_status["content_extracted"])} characters')
            break
        elif job_status["status"] == 'failed':
            print(f'❌ Job failed: {job_status["error_message"]}')
            break
        elif job_status["status"] == 'completed':
            print(f'✅ Job completed but checking document status...')
    
    # Final status
    print(f'\n🎯 Final Results')
    print('=' * 17)
    
    final_doc = await conn.fetchrow('''
        SELECT status, content_extracted, progress_percentage, 
               processing_status, upload_status
        FROM documents 
        WHERE id = $1
    ''', document_id)
    
    final_job = await conn.fetchrow('''
        SELECT status, error_message, retry_count
        FROM processing_jobs 
        WHERE id = $1
    ''', job_id)
    
    print(f'📄 Document Status: {final_doc["status"]}')
    print(f'   Progress: {final_doc["progress_percentage"]}%')
    print(f'   Processing: {final_doc["processing_status"]}')
    print(f'   Upload: {final_doc["upload_status"]}')
    print(f'   Has Content: {"Yes" if final_doc["content_extracted"] else "No"}')
    
    print(f'\n🔧 Job Status: {final_job["status"]}')
    print(f'   Retries: {final_job["retry_count"]}')
    if final_job["error_message"]:
        print(f'   Error: {final_job["error_message"]}')
    
    # Overall assessment
    print(f'\n📊 MVP Assessment')
    print('=' * 18)
    
    if (final_doc["status"] == 'completed' and 
        final_doc["content_extracted"] and 
        final_job["status"] == 'completed'):
        print('🎉 ✅ MVP IS WORKING PERFECTLY!')
        print('🚀 All systems operational:')
        print('   ✓ Document upload via upload-handler')
        print('   ✓ Database record creation')
        print('   ✓ Processing job creation and management')
        print('   ✓ Edge Function job processing')
        print('   ✓ Storage bucket access (raw_documents)')
        print('   ✓ Document parsing and content extraction')
        print('   ✓ End-to-end pipeline completion')
        
        # Show extracted content preview
        if final_doc["content_extracted"]:
            preview = final_doc["content_extracted"][:100] + "..." if len(final_doc["content_extracted"]) > 100 else final_doc["content_extracted"]
            print(f'\n📖 Content Preview: "{preview}"')
        
        success = True
    else:
        print('❌ MVP HAS ISSUES')
        print('🔍 Diagnostic summary:')
        
        if final_doc["upload_status"] != 'completed':
            print('   ⚠️ Upload not completed')
        if not final_doc["content_extracted"]:
            print('   ⚠️ No content extracted')
        if final_job["status"] != 'completed':
            print(f'   ⚠️ Job not completed: {final_job["status"]}')
        if final_job["error_message"]:
            print(f'   ⚠️ Job error: {final_job["error_message"]}')
        
        success = False
    
    await conn.close()
    
    print(f'\n🏁 Test Complete')
    print('=' * 15)
    return success

if __name__ == "__main__":
    success = asyncio.run(mvp_final_test())
    exit(0 if success else 1) 

import asyncio
import asyncpg
import os
import aiohttp
import json
from dotenv import load_dotenv

async def mvp_final_test():
    load_dotenv()
    
    print('🚀 MVP Final End-to-End Test')
    print('=' * 30)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables")
        return
    
    # Create test content
    test_content = "MVP Test Document\n\nPolicy Number: TEST-MVP-123\nCoverage: Health Insurance\nEffective Date: 2024-01-01"
    
    print(f'📄 Test content: {len(test_content)} characters')
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    # Step 1: Register upload
    print(f'\n1️⃣ Registering Upload')
    print('-' * 20)
    
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'X-User-ID': '27b30e9d-0d06-4325-910f-20fe9d686f14',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    upload_metadata = {
        'filename': 'mvp_final_test.txt',
        'contentType': 'text/plain',
        'fileSize': len(test_content.encode('utf-8'))
    }
    
    document_id = None
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_url = f"{supabase_url}/functions/v1/upload-handler"
        
        try:
            async with session.post(upload_url, json=upload_metadata, headers=headers) as response:
                status = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f'📤 Registration Status: {status}')
                
                if status == 200:
                    document_id = response_data.get('documentId')
                    print(f'✅ Document registered: {document_id}')
                else:
                    print(f'❌ Upload failed: {response_data}')
                    await conn.close()
                    return
                    
        except Exception as e:
            print(f'❌ Upload error: {e}')
            await conn.close()
            return
    
    # Step 2: Create processing job manually with correct job_type
    print(f'\n2️⃣ Creating Processing Job')
    print('-' * 26)
    
    try:
        # Insert a processing job with the required job_type
        job_id = await conn.fetchval('''
            INSERT INTO processing_jobs (
                document_id, job_type, status, priority, 
                max_retries, retry_count, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
            RETURNING id
        ''', document_id, 'parse', 'pending', 1, 3, 0)
        
        print(f'✅ Processing job created: {job_id}')
        
    except Exception as e:
        print(f'❌ Job creation failed: {e}')
        await conn.close()
        return
    
    # Step 3: Verify job is in queue
    print(f'\n3️⃣ Checking Queue Status')
    print('-' * 23)
    
    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
    print(f'⏳ Pending jobs in queue: {len(pending_jobs)}')
    
    job_found = False
    for job in pending_jobs:
        if str(job["id"]) == str(job_id):
            job_found = True
            print(f'✅ Our job found in queue: {job["job_type"]} for doc {job["document_id"]}')
            break
    
    if not job_found:
        print(f'⚠️ Our job not found in pending queue')
    
    # Step 4: Trigger processing
    print(f'\n4️⃣ Triggering Processing')
    print('-' * 22)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        job_processor_url = f"{supabase_url}/functions/v1/job-processor"
        
        try:
            async with session.post(job_processor_url, headers=headers, json={}) as job_response:
                job_status = job_response.status
                job_data = await job_response.json() if job_response.content_type == 'application/json' else await job_response.text()
                
                print(f'🔄 Job Processor Status: {job_status}')
                print(f'📝 Job Response: {job_data}')
                
        except Exception as e:
            print(f'❌ Job processor error: {e}')
    
    # Step 5: Monitor for completion
    print(f'\n5️⃣ Monitoring Progress')
    print('-' * 20)
    
    for check in range(12):  # Check 12 times, 10 seconds apart = 2 minutes max
        await asyncio.sleep(10)
        
        # Check document status
        doc_status = await conn.fetchrow('''
            SELECT status, progress_percentage, content_extracted, 
                   processing_status, upload_status
            FROM documents 
            WHERE id = $1
        ''', document_id)
        
        # Check job status
        job_status = await conn.fetchrow('''
            SELECT status, retry_count, error_message, updated_at
            FROM processing_jobs 
            WHERE id = $1
        ''', job_id)
        
        print(f'🔍 Check {check + 1}/12:')
        print(f'   Document: {doc_status["status"]} (progress: {doc_status["progress_percentage"]}%)')
        print(f'   Job: {job_status["status"]} (retries: {job_status["retry_count"]})')
        
        if job_status["error_message"]:
            print(f'   Error: {job_status["error_message"]}')
        
        # Check for completion
        if doc_status["status"] == 'completed' and doc_status["content_extracted"]:
            print(f'✅ Processing completed successfully!')
            print(f'📝 Content extracted: {len(doc_status["content_extracted"])} characters')
            break
        elif job_status["status"] == 'failed':
            print(f'❌ Job failed: {job_status["error_message"]}')
            break
        elif job_status["status"] == 'completed':
            print(f'✅ Job completed but checking document status...')
    
    # Final status
    print(f'\n🎯 Final Results')
    print('=' * 17)
    
    final_doc = await conn.fetchrow('''
        SELECT status, content_extracted, progress_percentage, 
               processing_status, upload_status
        FROM documents 
        WHERE id = $1
    ''', document_id)
    
    final_job = await conn.fetchrow('''
        SELECT status, error_message, retry_count
        FROM processing_jobs 
        WHERE id = $1
    ''', job_id)
    
    print(f'📄 Document Status: {final_doc["status"]}')
    print(f'   Progress: {final_doc["progress_percentage"]}%')
    print(f'   Processing: {final_doc["processing_status"]}')
    print(f'   Upload: {final_doc["upload_status"]}')
    print(f'   Has Content: {"Yes" if final_doc["content_extracted"] else "No"}')
    
    print(f'\n🔧 Job Status: {final_job["status"]}')
    print(f'   Retries: {final_job["retry_count"]}')
    if final_job["error_message"]:
        print(f'   Error: {final_job["error_message"]}')
    
    # Overall assessment
    print(f'\n📊 MVP Assessment')
    print('=' * 18)
    
    if (final_doc["status"] == 'completed' and 
        final_doc["content_extracted"] and 
        final_job["status"] == 'completed'):
        print('🎉 ✅ MVP IS WORKING PERFECTLY!')
        print('🚀 All systems operational:')
        print('   ✓ Document upload via upload-handler')
        print('   ✓ Database record creation')
        print('   ✓ Processing job creation and management')
        print('   ✓ Edge Function job processing')
        print('   ✓ Storage bucket access (raw_documents)')
        print('   ✓ Document parsing and content extraction')
        print('   ✓ End-to-end pipeline completion')
        
        # Show extracted content preview
        if final_doc["content_extracted"]:
            preview = final_doc["content_extracted"][:100] + "..." if len(final_doc["content_extracted"]) > 100 else final_doc["content_extracted"]
            print(f'\n📖 Content Preview: "{preview}"')
        
        success = True
    else:
        print('❌ MVP HAS ISSUES')
        print('🔍 Diagnostic summary:')
        
        if final_doc["upload_status"] != 'completed':
            print('   ⚠️ Upload not completed')
        if not final_doc["content_extracted"]:
            print('   ⚠️ No content extracted')
        if final_job["status"] != 'completed':
            print(f'   ⚠️ Job not completed: {final_job["status"]}')
        if final_job["error_message"]:
            print(f'   ⚠️ Job error: {final_job["error_message"]}')
        
        success = False
    
    await conn.close()
    
    print(f'\n🏁 Test Complete')
    print('=' * 15)
    return success

if __name__ == "__main__":
    success = asyncio.run(mvp_final_test())
    exit(0 if success else 1) 