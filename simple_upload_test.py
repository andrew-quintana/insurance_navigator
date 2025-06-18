#!/usr/bin/env python3

import asyncio
import asyncpg
import os
import aiohttp
import json
import tempfile
from dotenv import load_dotenv

async def simple_upload_test():
    load_dotenv()
    
    print('🧪 Simple Upload Test for MVP')
    print('=' * 35)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables")
        return
    
    # Create test content
    test_content = "This is a simple test document for MVP validation. Policy Number: TEST-123"
    
    print(f'📄 Test content: {len(test_content)} characters')
    
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
                    upload_url_signed = response_data.get('uploadUrl')
                    print(f'✅ Upload registered! Document ID: {document_id}')
                    
                    # Step 2: Upload the actual file content (if required)
                    if upload_url_signed:
                        print(f'\n2️⃣ Uploading File Content')
                        print('-' * 25)
                        
                        # Upload to signed URL
                        file_headers = {'Content-Type': 'text/plain'}
                        async with session.put(upload_url_signed, data=test_content.encode('utf-8'), headers=file_headers) as upload_response:
                            upload_status = upload_response.status
                            print(f'📤 File Upload Status: {upload_status}')
                            
                            if upload_status in [200, 201]:
                                print(f'✅ File uploaded successfully!')
                            else:
                                upload_error = await upload_response.text()
                                print(f'❌ File upload failed: {upload_error}')
                                return
                    
                    # Step 3: Check document status in database
                    print(f'\n3️⃣ Checking Database Status')
                    print('-' * 25)
                    
                    conn = await asyncpg.connect(
                        os.getenv('DATABASE_URL'), 
                        statement_cache_size=0,
                        server_settings={'jit': 'off'}
                    )
                    
                    document = await conn.fetchrow('''
                        SELECT id, original_filename, status, storage_path, progress_percentage, 
                               file_size, content_type, created_at
                        FROM documents 
                        WHERE id = $1
                    ''', document_id)
                    
                    if document:
                        print(f'📄 Document in database:')
                        print(f'   ID: {document["id"]}')
                        print(f'   Filename: {document["original_filename"]}')
                        print(f'   Status: {document["status"]}')
                        print(f'   Storage Path: {document["storage_path"]}')
                        print(f'   Progress: {document["progress_percentage"]}%')
                        print(f'   File Size: {document["file_size"]} bytes')
                        print(f'   Content Type: {document["content_type"]}')
                        
                        # Step 4: Trigger processing
                        print(f'\n4️⃣ Triggering Processing')
                        print('-' * 22)
                        
                        job_processor_url = f"{supabase_url}/functions/v1/job-processor"
                        async with session.post(job_processor_url, headers=headers, json={}) as job_response:
                            job_status = job_response.status
                            job_data = await job_response.json() if job_response.content_type == 'application/json' else await job_response.text()
                            
                            print(f'🔄 Job Processor Status: {job_status}')
                            print(f'📝 Job Response: {job_data}')
                        
                        # Step 5: Monitor for a short time
                        print(f'\n5️⃣ Brief Status Monitoring')
                        print('-' * 25)
                        
                        for check in range(6):  # Check 6 times, 10 seconds apart
                            await asyncio.sleep(10)
                            
                            current_doc = await conn.fetchrow('''
                                SELECT status, progress_percentage, extracted_text, error_message
                                FROM documents 
                                WHERE id = $1
                            ''', document_id)
                            
                            print(f'🔍 Check {check + 1}/6: Status = {current_doc["status"]}, Progress = {current_doc["progress_percentage"]}%')
                            
                            if current_doc["status"] == 'completed':
                                print(f'✅ Processing completed!')
                                if current_doc["extracted_text"]:
                                    print(f'📝 Extracted text length: {len(current_doc["extracted_text"])}')
                                break
                            elif current_doc["status"] == 'failed':
                                print(f'❌ Processing failed: {current_doc["error_message"]}')
                                break
                        
                        print(f'\n🎯 Test Summary')
                        print('=' * 20)
                        
                        final_doc = await conn.fetchrow('''
                            SELECT status, extracted_text, error_message
                            FROM documents 
                            WHERE id = $1
                        ''', document_id)
                        
                        if final_doc["status"] == 'completed' and final_doc["extracted_text"]:
                            print('✅ MVP UPLOAD AND PROCESSING WORKING!')
                        elif final_doc["status"] == 'failed':
                            print(f'❌ Processing failed: {final_doc["error_message"]}')
                        else:
                            print(f'⏳ Processing still in progress: {final_doc["status"]}')
                        
                        await conn.close()
                        
                    else:
                        print(f'❌ Document not found in database')
                        
                else:
                    print(f'❌ Upload registration failed: {response_data}')
                    
        except Exception as e:
            print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(simple_upload_test()) 

import asyncio
import asyncpg
import os
import aiohttp
import json
import tempfile
from dotenv import load_dotenv

async def simple_upload_test():
    load_dotenv()
    
    print('🧪 Simple Upload Test for MVP')
    print('=' * 35)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables")
        return
    
    # Create test content
    test_content = "This is a simple test document for MVP validation. Policy Number: TEST-123"
    
    print(f'📄 Test content: {len(test_content)} characters')
    
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
                    upload_url_signed = response_data.get('uploadUrl')
                    print(f'✅ Upload registered! Document ID: {document_id}')
                    
                    # Step 2: Upload the actual file content (if required)
                    if upload_url_signed:
                        print(f'\n2️⃣ Uploading File Content')
                        print('-' * 25)
                        
                        # Upload to signed URL
                        file_headers = {'Content-Type': 'text/plain'}
                        async with session.put(upload_url_signed, data=test_content.encode('utf-8'), headers=file_headers) as upload_response:
                            upload_status = upload_response.status
                            print(f'📤 File Upload Status: {upload_status}')
                            
                            if upload_status in [200, 201]:
                                print(f'✅ File uploaded successfully!')
                            else:
                                upload_error = await upload_response.text()
                                print(f'❌ File upload failed: {upload_error}')
                                return
                    
                    # Step 3: Check document status in database
                    print(f'\n3️⃣ Checking Database Status')
                    print('-' * 25)
                    
                    conn = await asyncpg.connect(
                        os.getenv('DATABASE_URL'), 
                        statement_cache_size=0,
                        server_settings={'jit': 'off'}
                    )
                    
                    document = await conn.fetchrow('''
                        SELECT id, original_filename, status, storage_path, progress_percentage, 
                               file_size, content_type, created_at
                        FROM documents 
                        WHERE id = $1
                    ''', document_id)
                    
                    if document:
                        print(f'📄 Document in database:')
                        print(f'   ID: {document["id"]}')
                        print(f'   Filename: {document["original_filename"]}')
                        print(f'   Status: {document["status"]}')
                        print(f'   Storage Path: {document["storage_path"]}')
                        print(f'   Progress: {document["progress_percentage"]}%')
                        print(f'   File Size: {document["file_size"]} bytes')
                        print(f'   Content Type: {document["content_type"]}')
                        
                        # Step 4: Trigger processing
                        print(f'\n4️⃣ Triggering Processing')
                        print('-' * 22)
                        
                        job_processor_url = f"{supabase_url}/functions/v1/job-processor"
                        async with session.post(job_processor_url, headers=headers, json={}) as job_response:
                            job_status = job_response.status
                            job_data = await job_response.json() if job_response.content_type == 'application/json' else await job_response.text()
                            
                            print(f'🔄 Job Processor Status: {job_status}')
                            print(f'📝 Job Response: {job_data}')
                        
                        # Step 5: Monitor for a short time
                        print(f'\n5️⃣ Brief Status Monitoring')
                        print('-' * 25)
                        
                        for check in range(6):  # Check 6 times, 10 seconds apart
                            await asyncio.sleep(10)
                            
                            current_doc = await conn.fetchrow('''
                                SELECT status, progress_percentage, extracted_text, error_message
                                FROM documents 
                                WHERE id = $1
                            ''', document_id)
                            
                            print(f'🔍 Check {check + 1}/6: Status = {current_doc["status"]}, Progress = {current_doc["progress_percentage"]}%')
                            
                            if current_doc["status"] == 'completed':
                                print(f'✅ Processing completed!')
                                if current_doc["extracted_text"]:
                                    print(f'📝 Extracted text length: {len(current_doc["extracted_text"])}')
                                break
                            elif current_doc["status"] == 'failed':
                                print(f'❌ Processing failed: {current_doc["error_message"]}')
                                break
                        
                        print(f'\n🎯 Test Summary')
                        print('=' * 20)
                        
                        final_doc = await conn.fetchrow('''
                            SELECT status, extracted_text, error_message
                            FROM documents 
                            WHERE id = $1
                        ''', document_id)
                        
                        if final_doc["status"] == 'completed' and final_doc["extracted_text"]:
                            print('✅ MVP UPLOAD AND PROCESSING WORKING!')
                        elif final_doc["status"] == 'failed':
                            print(f'❌ Processing failed: {final_doc["error_message"]}')
                        else:
                            print(f'⏳ Processing still in progress: {final_doc["status"]}')
                        
                        await conn.close()
                        
                    else:
                        print(f'❌ Document not found in database')
                        
                else:
                    print(f'❌ Upload registration failed: {response_data}')
                    
        except Exception as e:
            print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(simple_upload_test()) 