#!/usr/bin/env python3

import asyncio
import asyncpg
import os
import aiohttp
import json
from dotenv import load_dotenv

async def complete_upload_test():
    load_dotenv()
    
    print('🎯 Complete Upload Test (Initialize + Upload + Process)')
    print('=' * 55)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables")
        return False
    
    # Create test content
    test_content = "MVP Complete Upload Test\n\nThis document tests the complete upload flow:\n1. Initialize upload\n2. Upload file content\n3. Trigger processing\n4. Verify extraction\n\nPolicy Number: COMPLETE-TEST-456\nCoverage: Full MVP Test\nStatus: Testing Complete Pipeline"
    test_bytes = test_content.encode('utf-8')
    
    print(f'📄 Test content: {len(test_content)} characters ({len(test_bytes)} bytes)')
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    timeout = aiohttp.ClientTimeout(total=120)
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'X-User-ID': '27b30e9d-0d06-4325-910f-20fe9d686f14',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    # Step 1: Initialize upload
    print(f'\n1️⃣ Initializing Upload')
    print('-' * 22)
    
    upload_metadata = {
        'filename': 'complete_test.txt',
        'contentType': 'text/plain',
        'fileSize': len(test_bytes)
    }
    
    document_id = None
    upload_url = None
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_handler_url = f"{supabase_url}/functions/v1/upload-handler"
        
        try:
            async with session.post(upload_handler_url, json=upload_metadata, headers=headers) as response:
                status = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f'📤 Upload Initialization:')
                print(f'   Status: {status}')
                
                if status == 200:
                    document_id = response_data.get('documentId')
                    upload_url = response_data.get('uploadUrl')
                    storage_path = response_data.get('path')
                    
                    print(f'✅ Upload initialized successfully!')
                    print(f'   Document ID: {document_id}')
                    print(f'   Storage Path: {storage_path}')
                    print(f'   Upload URL: {upload_url[:60] + "..." if len(upload_url) > 60 else upload_url}')
                else:
                    print(f'❌ Upload initialization failed: {response_data}')
                    await conn.close()
                    return False
                    
        except Exception as e:
            print(f'❌ Upload initialization error: {e}')
            await conn.close()
            return False
    
    # Step 2: Upload actual file content
    print(f'\n2️⃣ Uploading File Content')
    print('-' * 26)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_headers = {
            'Content-Type': 'text/plain',
            'Content-Length': str(len(test_bytes))
        }
        
        try:
            async with session.put(upload_url, data=test_bytes, headers=upload_headers) as upload_response:
                upload_status = upload_response.status
                upload_text = await upload_response.text()
                
                print(f'📤 File Upload:')
                print(f'   Status: {upload_status}')
                print(f'   Response: {upload_text[:100] if upload_text else "Empty response"}')
                
                if upload_status in [200, 201, 204]:
                    print(f'✅ File uploaded successfully to storage!')
                else:
                    print(f'❌ File upload failed: {upload_text}')
                    await conn.close()
                    return False
                    
        except Exception as e:
            print(f'❌ File upload error: {e}')
            await conn.close()
            return False
    
    # Step 3: Verify document status
    print(f'\n3️⃣ Checking Document Status')
    print('-' * 27)
    
    document = await conn.fetchrow('''
        SELECT id, original_filename, status, storage_path, 
               upload_status, processing_status, progress_percentage,
               file_size, content_type, created_at
        FROM documents 
        WHERE id = $1
    ''', document_id)
    
    if document:
        print(f'📄 Document Status:')
        print(f'   Status: {document["status"]}')
        print(f'   Upload Status: {document["upload_status"]}')
        print(f'   Processing Status: {document["processing_status"]}')
        print(f'   Progress: {document["progress_percentage"]}%')
        print(f'   Storage Path: {document["storage_path"]}')
    else:
        print(f'❌ Document not found in database')
        await conn.close()
        return False
    
    # Step 4: Create processing job
    print(f'\n4️⃣ Creating Processing Job')
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
    
    # Step 5: Trigger job processing
    print(f'\n5️⃣ Triggering Job Processing')
    print('-' * 28)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        job_processor_url = f"{supabase_url}/functions/v1/job-processor"
        
        try:
            async with session.post(job_processor_url, headers=headers, json={}) as job_response:
                job_status = job_response.status
                job_data = await job_response.json() if job_response.content_type == 'application/json' else await job_response.text()
                
                print(f'🔄 Job Processing:')
                print(f'   Status: {job_status}')
                print(f'   Response: {job_data}')
                
        except Exception as e:
            print(f'❌ Job processing error: {e}')
    
    # Step 6: Monitor processing completion
    print(f'\n6️⃣ Monitoring Processing')
    print('-' * 24)
    
    success = False
    for check in range(12):  # 2 minutes max
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
        
        print(f'🔍 Check {check + 1}/12:')
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
    
    print(f'📄 Final Document Status:')
    print(f'   Status: {final_doc["status"]}')
    print(f'   Upload: {final_doc["upload_status"]}')
    print(f'   Processing: {final_doc["processing_status"]}')
    print(f'   Progress: {final_doc["progress_percentage"]}%')
    print(f'   Has Content: {"Yes" if final_doc["content_extracted"] else "No"}')
    
    print(f'\n🔧 Final Job Status: {final_job["status"]}')
    if final_job["error_message"]:
        print(f'   Error: {final_job["error_message"]}')
    
    # Success assessment
    if success and final_doc["content_extracted"]:
        print(f'\n🎉 ✅ COMPLETE MVP SUCCESS!')
        print(f'🚀 Full pipeline working:')
        print(f'   ✓ Upload initialization (upload-handler)')
        print(f'   ✓ File content upload to raw_documents bucket')
        print(f'   ✓ Job creation and queue management')
        print(f'   ✓ Edge Function job processing')
        print(f'   ✓ Document parsing (doc-parser)')
        print(f'   ✓ Content extraction and storage')
        print(f'   ✓ End-to-end pipeline completion')
        
        # Show content preview
        content_preview = final_doc["content_extracted"][:150] + "..." if len(final_doc["content_extracted"]) > 150 else final_doc["content_extracted"]
        print(f'\n📖 Extracted Content Preview:')
        print(f'"{content_preview}"')
        
    else:
        print(f'\n❌ MVP PIPELINE HAS REMAINING ISSUES')
        if not final_doc["content_extracted"]:
            print(f'   ⚠️ No content extracted - check doc-parser logs')
        if final_job["status"] != 'completed':
            print(f'   ⚠️ Job not completed: {final_job["status"]}')
    
    await conn.close()
    return success

if __name__ == "__main__":
    success = asyncio.run(complete_upload_test())
    print(f'\n🏁 Test Result: {"SUCCESS" if success else "FAILED"}')
    exit(0 if success else 1) 

import asyncio
import asyncpg
import os
import aiohttp
import json
from dotenv import load_dotenv

async def complete_upload_test():
    load_dotenv()
    
    print('🎯 Complete Upload Test (Initialize + Upload + Process)')
    print('=' * 55)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables")
        return False
    
    # Create test content
    test_content = "MVP Complete Upload Test\n\nThis document tests the complete upload flow:\n1. Initialize upload\n2. Upload file content\n3. Trigger processing\n4. Verify extraction\n\nPolicy Number: COMPLETE-TEST-456\nCoverage: Full MVP Test\nStatus: Testing Complete Pipeline"
    test_bytes = test_content.encode('utf-8')
    
    print(f'📄 Test content: {len(test_content)} characters ({len(test_bytes)} bytes)')
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    timeout = aiohttp.ClientTimeout(total=120)
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'X-User-ID': '27b30e9d-0d06-4325-910f-20fe9d686f14',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    # Step 1: Initialize upload
    print(f'\n1️⃣ Initializing Upload')
    print('-' * 22)
    
    upload_metadata = {
        'filename': 'complete_test.txt',
        'contentType': 'text/plain',
        'fileSize': len(test_bytes)
    }
    
    document_id = None
    upload_url = None
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_handler_url = f"{supabase_url}/functions/v1/upload-handler"
        
        try:
            async with session.post(upload_handler_url, json=upload_metadata, headers=headers) as response:
                status = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f'📤 Upload Initialization:')
                print(f'   Status: {status}')
                
                if status == 200:
                    document_id = response_data.get('documentId')
                    upload_url = response_data.get('uploadUrl')
                    storage_path = response_data.get('path')
                    
                    print(f'✅ Upload initialized successfully!')
                    print(f'   Document ID: {document_id}')
                    print(f'   Storage Path: {storage_path}')
                    print(f'   Upload URL: {upload_url[:60] + "..." if len(upload_url) > 60 else upload_url}')
                else:
                    print(f'❌ Upload initialization failed: {response_data}')
                    await conn.close()
                    return False
                    
        except Exception as e:
            print(f'❌ Upload initialization error: {e}')
            await conn.close()
            return False
    
    # Step 2: Upload actual file content
    print(f'\n2️⃣ Uploading File Content')
    print('-' * 26)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_headers = {
            'Content-Type': 'text/plain',
            'Content-Length': str(len(test_bytes))
        }
        
        try:
            async with session.put(upload_url, data=test_bytes, headers=upload_headers) as upload_response:
                upload_status = upload_response.status
                upload_text = await upload_response.text()
                
                print(f'📤 File Upload:')
                print(f'   Status: {upload_status}')
                print(f'   Response: {upload_text[:100] if upload_text else "Empty response"}')
                
                if upload_status in [200, 201, 204]:
                    print(f'✅ File uploaded successfully to storage!')
                else:
                    print(f'❌ File upload failed: {upload_text}')
                    await conn.close()
                    return False
                    
        except Exception as e:
            print(f'❌ File upload error: {e}')
            await conn.close()
            return False
    
    # Step 3: Verify document status
    print(f'\n3️⃣ Checking Document Status')
    print('-' * 27)
    
    document = await conn.fetchrow('''
        SELECT id, original_filename, status, storage_path, 
               upload_status, processing_status, progress_percentage,
               file_size, content_type, created_at
        FROM documents 
        WHERE id = $1
    ''', document_id)
    
    if document:
        print(f'📄 Document Status:')
        print(f'   Status: {document["status"]}')
        print(f'   Upload Status: {document["upload_status"]}')
        print(f'   Processing Status: {document["processing_status"]}')
        print(f'   Progress: {document["progress_percentage"]}%')
        print(f'   Storage Path: {document["storage_path"]}')
    else:
        print(f'❌ Document not found in database')
        await conn.close()
        return False
    
    # Step 4: Create processing job
    print(f'\n4️⃣ Creating Processing Job')
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
    
    # Step 5: Trigger job processing
    print(f'\n5️⃣ Triggering Job Processing')
    print('-' * 28)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        job_processor_url = f"{supabase_url}/functions/v1/job-processor"
        
        try:
            async with session.post(job_processor_url, headers=headers, json={}) as job_response:
                job_status = job_response.status
                job_data = await job_response.json() if job_response.content_type == 'application/json' else await job_response.text()
                
                print(f'🔄 Job Processing:')
                print(f'   Status: {job_status}')
                print(f'   Response: {job_data}')
                
        except Exception as e:
            print(f'❌ Job processing error: {e}')
    
    # Step 6: Monitor processing completion
    print(f'\n6️⃣ Monitoring Processing')
    print('-' * 24)
    
    success = False
    for check in range(12):  # 2 minutes max
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
        
        print(f'🔍 Check {check + 1}/12:')
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
    
    print(f'📄 Final Document Status:')
    print(f'   Status: {final_doc["status"]}')
    print(f'   Upload: {final_doc["upload_status"]}')
    print(f'   Processing: {final_doc["processing_status"]}')
    print(f'   Progress: {final_doc["progress_percentage"]}%')
    print(f'   Has Content: {"Yes" if final_doc["content_extracted"] else "No"}')
    
    print(f'\n🔧 Final Job Status: {final_job["status"]}')
    if final_job["error_message"]:
        print(f'   Error: {final_job["error_message"]}')
    
    # Success assessment
    if success and final_doc["content_extracted"]:
        print(f'\n🎉 ✅ COMPLETE MVP SUCCESS!')
        print(f'🚀 Full pipeline working:')
        print(f'   ✓ Upload initialization (upload-handler)')
        print(f'   ✓ File content upload to raw_documents bucket')
        print(f'   ✓ Job creation and queue management')
        print(f'   ✓ Edge Function job processing')
        print(f'   ✓ Document parsing (doc-parser)')
        print(f'   ✓ Content extraction and storage')
        print(f'   ✓ End-to-end pipeline completion')
        
        # Show content preview
        content_preview = final_doc["content_extracted"][:150] + "..." if len(final_doc["content_extracted"]) > 150 else final_doc["content_extracted"]
        print(f'\n📖 Extracted Content Preview:')
        print(f'"{content_preview}"')
        
    else:
        print(f'\n❌ MVP PIPELINE HAS REMAINING ISSUES')
        if not final_doc["content_extracted"]:
            print(f'   ⚠️ No content extracted - check doc-parser logs')
        if final_job["status"] != 'completed':
            print(f'   ⚠️ Job not completed: {final_job["status"]}')
    
    await conn.close()
    return success

if __name__ == "__main__":
    success = asyncio.run(complete_upload_test())
    print(f'\n🏁 Test Result: {"SUCCESS" if success else "FAILED"}')
    exit(0 if success else 1) 