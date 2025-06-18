#!/usr/bin/env python3

import asyncio
import asyncpg
import os
import aiohttp
import json
from dotenv import load_dotenv

async def simple_direct_upload_test():
    load_dotenv()
    
    print('🎯 Simple Direct Upload Test (MVP Validation)')
    print('=' * 50)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables")
        return False
    
    # Create test content
    test_content = "Simple MVP Test\nPolicy: SIMPLE-001\nStatus: Testing direct upload to storage"
    
    print(f'📄 Test content: {len(test_content)} characters')
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    # Step 1: Manually create document record
    print(f'\n1️⃣ Creating Document Record')
    print('-' * 29)
    
    user_id = '27b30e9d-0d06-4325-910f-20fe9d686f14'
    filename = 'simple_direct_test.txt'
    content_type = 'text/plain'
    file_size = len(test_content.encode('utf-8'))
    
    # Create hash for storage path
    import hashlib
    file_hash = hashlib.sha256(f"{filename}-{file_size}-{user_id}".encode()).hexdigest()
    storage_path = f"{user_id}/{file_hash}/{filename}"
    
    try:
        document_id = await conn.fetchval('''
            INSERT INTO documents (
                user_id, original_filename, file_size, content_type,
                storage_path, status, progress_percentage, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            RETURNING id
        ''', user_id, filename, file_size, content_type, storage_path, 'pending', 0)
        
        print(f'✅ Document record created: {document_id}')
        print(f'   Storage Path: {storage_path}')
        
    except Exception as e:
        print(f'❌ Document creation failed: {e}')
        await conn.close()
        return False
    
    # Step 2: Direct upload to storage bucket
    print(f'\n2️⃣ Direct Upload to Storage')
    print('-' * 29)
    
    timeout = aiohttp.ClientTimeout(total=60)
    storage_headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': content_type,
        'apikey': service_role_key
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Upload directly to storage
        storage_upload_url = f"{supabase_url}/storage/v1/object/raw_documents/{storage_path}"
        
        try:
            async with session.post(storage_upload_url, data=test_content.encode('utf-8'), headers=storage_headers) as upload_response:
                upload_status = upload_response.status
                upload_text = await upload_response.text()
                
                print(f'📤 Storage Upload:')
                print(f'   URL: {storage_upload_url}')
                print(f'   Status: {upload_status}')
                print(f'   Response: {upload_text[:100] if upload_text else "Empty response"}')
                
                if upload_status in [200, 201]:
                    print(f'✅ File uploaded to storage successfully!')
                    
                    # Update document status
                    await conn.execute('''
                        UPDATE documents 
                        SET status = 'processing', progress_percentage = 10, updated_at = NOW()
                        WHERE id = $1
                    ''', document_id)
                    
                else:
                    print(f'❌ Storage upload failed: {upload_text}')
                    await conn.close()
                    return False
                    
        except Exception as e:
            print(f'❌ Storage upload error: {e}')
            await conn.close()
            return False
    
    # Step 3: Create processing job
    print(f'\n3️⃣ Creating Processing Job')
    print('-' * 26)
    
    try:
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
        return False
    
    # Step 4: Trigger job processing
    print(f'\n4️⃣ Triggering Job Processing')
    print('-' * 28)
    
    job_headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        job_processor_url = f"{supabase_url}/functions/v1/job-processor"
        
        try:
            async with session.post(job_processor_url, headers=job_headers, json={}) as job_response:
                job_status = job_response.status
                job_data = await job_response.json() if job_response.content_type == 'application/json' else await job_response.text()
                
                print(f'🔄 Job Processing:')
                print(f'   Status: {job_status}')
                print(f'   Response: {job_data}')
                
        except Exception as e:
            print(f'❌ Job processing error: {e}')
    
    # Step 5: Monitor processing completion
    print(f'\n5️⃣ Monitoring Processing')
    print('-' * 24)
    
    success = False
    for check in range(8):  # 80 seconds max
        await asyncio.sleep(10)
        
        # Check document and job status
        doc_status = await conn.fetchrow('''
            SELECT status, progress_percentage, content_extracted, 
                   processing_status, upload_status
            FROM documents 
            WHERE id = $1
        ''', document_id)
        
        job_status = await conn.fetchrow('''
            SELECT status, retry_count, error_message
            FROM processing_jobs 
            WHERE id = $1
        ''', job_id)
        
        print(f'🔍 Check {check + 1}/8:')
        print(f'   Document: {doc_status["status"]} (progress: {doc_status["progress_percentage"]}%)')
        print(f'   Job: {job_status["status"]} (retries: {job_status["retry_count"]})')
        
        if job_status["error_message"]:
            print(f'   Error: {job_status["error_message"]}')
        
        # Check for completion
        if doc_status["status"] == 'completed' and doc_status["content_extracted"]:
            print(f'✅ Processing completed successfully!')
            print(f'📝 Content extracted: {len(doc_status["content_extracted"])} characters')
            success = True
            break
        elif job_status["status"] == 'failed':
            print(f'❌ Job failed: {job_status["error_message"]}')
            break
    
    # Final results
    print(f'\n🎯 Final Results')
    print('=' * 17)
    
    final_doc = await conn.fetchrow('''
        SELECT status, content_extracted, progress_percentage
        FROM documents 
        WHERE id = $1
    ''', document_id)
    
    final_job = await conn.fetchrow('''
        SELECT status, error_message, retry_count
        FROM processing_jobs 
        WHERE id = $1
    ''', job_id)
    
    print(f'📄 Document Status: {final_doc["status"]} (progress: {final_doc["progress_percentage"]}%)')
    print(f'🔧 Job Status: {final_job["status"]} (retries: {final_job["retry_count"]})')
    
    if final_job["error_message"]:
        print(f'   Error: {final_job["error_message"]}')
    
    # Success assessment
    if success and final_doc["content_extracted"]:
        print(f'\n🎉 ✅ MVP DIRECT UPLOAD SUCCESS!')
        print(f'🚀 Core pipeline verified:')
        print(f'   ✓ Direct storage upload works')
        print(f'   ✓ Document parsing functional')
        print(f'   ✓ Content extraction working')
        print(f'   ✓ Job queue processing operational')
        
        # Show content preview
        content_preview = final_doc["content_extracted"][:100] + "..." if len(final_doc["content_extracted"]) > 100 else final_doc["content_extracted"]
        print(f'\n📖 Extracted Content: "{content_preview}"')
        
    else:
        print(f'\n❌ MVP PIPELINE STILL HAS ISSUES')
        if not final_doc["content_extracted"]:
            print(f'   ⚠️ No content extracted')
        if final_job["status"] != 'completed':
            print(f'   ⚠️ Job failed: {final_job["error_message"]}')
    
    await conn.close()
    return success

if __name__ == "__main__":
    success = asyncio.run(simple_direct_upload_test())
    print(f'\n🏁 Result: {"SUCCESS" if success else "FAILED"}')
    exit(0 if success else 1) 

import asyncio
import asyncpg
import os
import aiohttp
import json
from dotenv import load_dotenv

async def simple_direct_upload_test():
    load_dotenv()
    
    print('🎯 Simple Direct Upload Test (MVP Validation)')
    print('=' * 50)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables")
        return False
    
    # Create test content
    test_content = "Simple MVP Test\nPolicy: SIMPLE-001\nStatus: Testing direct upload to storage"
    
    print(f'📄 Test content: {len(test_content)} characters')
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    # Step 1: Manually create document record
    print(f'\n1️⃣ Creating Document Record')
    print('-' * 29)
    
    user_id = '27b30e9d-0d06-4325-910f-20fe9d686f14'
    filename = 'simple_direct_test.txt'
    content_type = 'text/plain'
    file_size = len(test_content.encode('utf-8'))
    
    # Create hash for storage path
    import hashlib
    file_hash = hashlib.sha256(f"{filename}-{file_size}-{user_id}".encode()).hexdigest()
    storage_path = f"{user_id}/{file_hash}/{filename}"
    
    try:
        document_id = await conn.fetchval('''
            INSERT INTO documents (
                user_id, original_filename, file_size, content_type,
                storage_path, status, progress_percentage, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            RETURNING id
        ''', user_id, filename, file_size, content_type, storage_path, 'pending', 0)
        
        print(f'✅ Document record created: {document_id}')
        print(f'   Storage Path: {storage_path}')
        
    except Exception as e:
        print(f'❌ Document creation failed: {e}')
        await conn.close()
        return False
    
    # Step 2: Direct upload to storage bucket
    print(f'\n2️⃣ Direct Upload to Storage')
    print('-' * 29)
    
    timeout = aiohttp.ClientTimeout(total=60)
    storage_headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': content_type,
        'apikey': service_role_key
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Upload directly to storage
        storage_upload_url = f"{supabase_url}/storage/v1/object/raw_documents/{storage_path}"
        
        try:
            async with session.post(storage_upload_url, data=test_content.encode('utf-8'), headers=storage_headers) as upload_response:
                upload_status = upload_response.status
                upload_text = await upload_response.text()
                
                print(f'📤 Storage Upload:')
                print(f'   URL: {storage_upload_url}')
                print(f'   Status: {upload_status}')
                print(f'   Response: {upload_text[:100] if upload_text else "Empty response"}')
                
                if upload_status in [200, 201]:
                    print(f'✅ File uploaded to storage successfully!')
                    
                    # Update document status
                    await conn.execute('''
                        UPDATE documents 
                        SET status = 'processing', progress_percentage = 10, updated_at = NOW()
                        WHERE id = $1
                    ''', document_id)
                    
                else:
                    print(f'❌ Storage upload failed: {upload_text}')
                    await conn.close()
                    return False
                    
        except Exception as e:
            print(f'❌ Storage upload error: {e}')
            await conn.close()
            return False
    
    # Step 3: Create processing job
    print(f'\n3️⃣ Creating Processing Job')
    print('-' * 26)
    
    try:
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
        return False
    
    # Step 4: Trigger job processing
    print(f'\n4️⃣ Triggering Job Processing')
    print('-' * 28)
    
    job_headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        job_processor_url = f"{supabase_url}/functions/v1/job-processor"
        
        try:
            async with session.post(job_processor_url, headers=job_headers, json={}) as job_response:
                job_status = job_response.status
                job_data = await job_response.json() if job_response.content_type == 'application/json' else await job_response.text()
                
                print(f'🔄 Job Processing:')
                print(f'   Status: {job_status}')
                print(f'   Response: {job_data}')
                
        except Exception as e:
            print(f'❌ Job processing error: {e}')
    
    # Step 5: Monitor processing completion
    print(f'\n5️⃣ Monitoring Processing')
    print('-' * 24)
    
    success = False
    for check in range(8):  # 80 seconds max
        await asyncio.sleep(10)
        
        # Check document and job status
        doc_status = await conn.fetchrow('''
            SELECT status, progress_percentage, content_extracted, 
                   processing_status, upload_status
            FROM documents 
            WHERE id = $1
        ''', document_id)
        
        job_status = await conn.fetchrow('''
            SELECT status, retry_count, error_message
            FROM processing_jobs 
            WHERE id = $1
        ''', job_id)
        
        print(f'🔍 Check {check + 1}/8:')
        print(f'   Document: {doc_status["status"]} (progress: {doc_status["progress_percentage"]}%)')
        print(f'   Job: {job_status["status"]} (retries: {job_status["retry_count"]})')
        
        if job_status["error_message"]:
            print(f'   Error: {job_status["error_message"]}')
        
        # Check for completion
        if doc_status["status"] == 'completed' and doc_status["content_extracted"]:
            print(f'✅ Processing completed successfully!')
            print(f'📝 Content extracted: {len(doc_status["content_extracted"])} characters')
            success = True
            break
        elif job_status["status"] == 'failed':
            print(f'❌ Job failed: {job_status["error_message"]}')
            break
    
    # Final results
    print(f'\n🎯 Final Results')
    print('=' * 17)
    
    final_doc = await conn.fetchrow('''
        SELECT status, content_extracted, progress_percentage
        FROM documents 
        WHERE id = $1
    ''', document_id)
    
    final_job = await conn.fetchrow('''
        SELECT status, error_message, retry_count
        FROM processing_jobs 
        WHERE id = $1
    ''', job_id)
    
    print(f'📄 Document Status: {final_doc["status"]} (progress: {final_doc["progress_percentage"]}%)')
    print(f'🔧 Job Status: {final_job["status"]} (retries: {final_job["retry_count"]})')
    
    if final_job["error_message"]:
        print(f'   Error: {final_job["error_message"]}')
    
    # Success assessment
    if success and final_doc["content_extracted"]:
        print(f'\n🎉 ✅ MVP DIRECT UPLOAD SUCCESS!')
        print(f'🚀 Core pipeline verified:')
        print(f'   ✓ Direct storage upload works')
        print(f'   ✓ Document parsing functional')
        print(f'   ✓ Content extraction working')
        print(f'   ✓ Job queue processing operational')
        
        # Show content preview
        content_preview = final_doc["content_extracted"][:100] + "..." if len(final_doc["content_extracted"]) > 100 else final_doc["content_extracted"]
        print(f'\n📖 Extracted Content: "{content_preview}"')
        
    else:
        print(f'\n❌ MVP PIPELINE STILL HAS ISSUES')
        if not final_doc["content_extracted"]:
            print(f'   ⚠️ No content extracted')
        if final_job["status"] != 'completed':
            print(f'   ⚠️ Job failed: {final_job["error_message"]}')
    
    await conn.close()
    return success

if __name__ == "__main__":
    success = asyncio.run(simple_direct_upload_test())
    print(f'\n🏁 Result: {"SUCCESS" if success else "FAILED"}')
    exit(0 if success else 1) 