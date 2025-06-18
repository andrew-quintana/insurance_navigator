#!/usr/bin/env python3

import asyncio
import asyncpg
import os
import aiohttp
import json
import tempfile
from pathlib import Path
from dotenv import load_dotenv

async def test_mvp_end_to_end():
    load_dotenv()
    
    print('🚀 Testing MVP End-to-End Document Processing')
    print('=' * 55)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, anon_key, service_role_key]):
        print("❌ Missing required environment variables")
        return
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    print(f'📊 Pre-test Status Check')
    print('-' * 30)
    
    # Check current document count and status
    doc_stats = await conn.fetch('''
        SELECT status, COUNT(*) as count
        FROM documents 
        GROUP BY status
        ORDER BY count DESC
    ''')
    
    print('📄 Current documents:')
    for stat in doc_stats:
        print(f'   {stat["status"]}: {stat["count"]}')
    
    # Check pending jobs
    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(5)')
    print(f'⏳ Pending jobs: {len(pending_jobs)}')
    
    # Create a simple test document
    print(f'\n📄 Step 1: Creating Test Document')
    print('-' * 30)
    
    test_content = """
    Test Document for MVP End-to-End Processing
    
    This is a simple test document to verify that:
    1. File upload works correctly
    2. Storage bucket is accessible
    3. Queue processing functions
    4. Document parsing completes
    5. Text extraction succeeds
    
    Patient Information:
    - Name: John Doe
    - Policy Number: MVP-TEST-12345
    - Coverage Type: Health Insurance
    - Effective Date: 2024-01-01
    
    This document should be successfully processed by the MVP system.
    """
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    print(f'✅ Created test file: {Path(temp_file_path).name}')
    print(f'📝 Content length: {len(test_content)} characters')
    
    # Step 2: Upload document via upload-handler
    print(f'\n⬆️ Step 2: Uploading Document')
    print('-' * 30)
    
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'X-User-ID': 'test-user-mvp',
        'apikey': service_role_key
    }
    
    # For form upload, we need different approach
    # First, register the upload with metadata
    upload_metadata = {
        'filename': 'mvp_test_document.txt',
        'contentType': 'text/plain',
        'fileSize': len(test_content.encode('utf-8'))
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_url = f"{supabase_url}/functions/v1/upload-handler"
        
        try:
            async with session.post(upload_url, data=upload_metadata, headers=headers) as response:
                upload_status = response.status
                upload_response = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f'📤 Upload Status: {upload_status}')
                print(f'📝 Upload Response: {upload_response}')
                
                if upload_status == 200:
                    document_id = upload_response.get('documentId')
                    print(f'✅ Upload successful! Document ID: {document_id}')
                else:
                    print(f'❌ Upload failed: {upload_response}')
                    await conn.close()
                    os.unlink(temp_file_path)
                    return
                    
        except Exception as e:
            print(f'❌ Upload error: {e}')
            await conn.close()
            os.unlink(temp_file_path)
            return
    
    # Step 3: Monitor document processing
    print(f'\n⏳ Step 3: Monitoring Document Processing')
    print('-' * 30)
    
    # Check document was created
    document = await conn.fetchrow('''
        SELECT id, original_filename, status, storage_path, progress_percentage, created_at
        FROM documents 
        WHERE id = $1
    ''', document_id)
    
    if document:
        print(f'📄 Document created:')
        print(f'   ID: {document["id"]}')
        print(f'   Filename: {document["original_filename"]}')
        print(f'   Status: {document["status"]}')
        print(f'   Storage Path: {document["storage_path"]}')
        print(f'   Progress: {document["progress_percentage"]}%')
    else:
        print(f'❌ Document not found in database')
        await conn.close()
        os.unlink(temp_file_path)
        return
    
    # Step 4: Trigger queue processing
    print(f'\n🔄 Step 4: Triggering Queue Processing')
    print('-' * 30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        job_processor_url = f"{supabase_url}/functions/v1/job-processor"
        job_headers = {
            'Authorization': f'Bearer {service_role_key}',
            'Content-Type': 'application/json',
            'apikey': service_role_key
        }
        
        try:
            async with session.post(job_processor_url, headers=job_headers, json={}) as response:
                job_status = response.status
                job_response = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f'🔄 Job Processor Status: {job_status}')
                print(f'📝 Job Processor Response: {job_response}')
                
        except Exception as e:
            print(f'❌ Job processor error: {e}')
    
    # Step 5: Monitor processing completion
    print(f'\n👀 Step 5: Monitoring Processing Progress')
    print('-' * 30)
    
    max_wait_seconds = 120  # 2 minutes max wait
    check_interval = 10     # Check every 10 seconds
    checks = 0
    max_checks = max_wait_seconds // check_interval
    
    while checks < max_checks:
        # Check document status
        current_doc = await conn.fetchrow('''
            SELECT status, progress_percentage, extracted_text, error_message, updated_at
            FROM documents 
            WHERE id = $1
        ''', document_id)
        
        checks += 1
        print(f'🔍 Check {checks}/{max_checks}: Status = {current_doc["status"]}, Progress = {current_doc["progress_percentage"]}%')
        
        if current_doc["status"] == 'completed':
            print(f'✅ Processing completed successfully!')
            if current_doc["extracted_text"]:
                text_length = len(current_doc["extracted_text"])
                print(f'📝 Extracted text length: {text_length} characters')
                
                # Show first 200 characters of extracted text
                preview = current_doc["extracted_text"][:200]
                print(f'📖 Text preview: "{preview}..."')
            break
        elif current_doc["status"] == 'failed':
            print(f'❌ Processing failed!')
            if current_doc["error_message"]:
                print(f'💥 Error: {current_doc["error_message"]}')
            break
        elif current_doc["status"] in ['parsing', 'processing']:
            print(f'⏳ Still processing... (Progress: {current_doc["progress_percentage"]}%)')
        
        if checks < max_checks:
            await asyncio.sleep(check_interval)
    
    # Final status report
    print(f'\n📊 Final Status Report')
    print('-' * 30)
    
    final_doc = await conn.fetchrow('''
        SELECT status, progress_percentage, extracted_text, error_message, 
               content_type, file_size, storage_path
        FROM documents 
        WHERE id = $1
    ''', document_id)
    
    print(f'📄 Final Document Status:')
    print(f'   Status: {final_doc["status"]}')
    print(f'   Progress: {final_doc["progress_percentage"]}%')
    print(f'   Content Type: {final_doc["content_type"]}')
    print(f'   File Size: {final_doc["file_size"]} bytes')
    print(f'   Storage Path: {final_doc["storage_path"]}')
    print(f'   Has Extracted Text: {"Yes" if final_doc["extracted_text"] else "No"}')
    if final_doc["error_message"]:
        print(f'   Error: {final_doc["error_message"]}')
    
    # Check processing jobs
    job_status = await conn.fetch('''
        SELECT status, created_at, updated_at, retry_count, error_message
        FROM processing_jobs 
        WHERE document_id = $1
        ORDER BY created_at DESC
    ''')
    
    print(f'\n🔧 Processing Jobs ({len(job_status)} total):')
    for i, job in enumerate(job_status):
        print(f'   Job {i+1}: {job["status"]} (retries: {job["retry_count"]})')
        if job["error_message"]:
            print(f'           Error: {job["error_message"]}')
    
    # Overall result
    print(f'\n🎯 MVP Test Result')
    print('=' * 30)
    
    if final_doc["status"] == 'completed' and final_doc["extracted_text"]:
        print('✅ MVP END-TO-END TEST PASSED!')
        print('🎉 Document processing pipeline is working correctly')
        print('📋 Features verified:')
        print('   ✓ File upload via upload-handler')
        print('   ✓ Storage bucket access (raw_documents)')
        print('   ✓ Queue processing and job management')
        print('   ✓ Document parsing via doc-parser')
        print('   ✓ Text extraction and storage')
    elif final_doc["status"] == 'failed':
        print('❌ MVP END-TO-END TEST FAILED')
        print('💥 Document processing failed')
        print('🔍 Check error messages above for debugging')
    else:
        print('⚠️ MVP END-TO-END TEST INCOMPLETE')
        print(f'📊 Final status: {final_doc["status"]}')
        print('⏰ Processing may need more time or manual intervention')
    
    await conn.close()
    os.unlink(temp_file_path)
    print(f'\n🧹 Cleanup: Removed temporary test file')

if __name__ == "__main__":
    asyncio.run(test_mvp_end_to_end()) 

import asyncio
import asyncpg
import os
import aiohttp
import json
import tempfile
from pathlib import Path
from dotenv import load_dotenv

async def test_mvp_end_to_end():
    load_dotenv()
    
    print('🚀 Testing MVP End-to-End Document Processing')
    print('=' * 55)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, anon_key, service_role_key]):
        print("❌ Missing required environment variables")
        return
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    print(f'📊 Pre-test Status Check')
    print('-' * 30)
    
    # Check current document count and status
    doc_stats = await conn.fetch('''
        SELECT status, COUNT(*) as count
        FROM documents 
        GROUP BY status
        ORDER BY count DESC
    ''')
    
    print('📄 Current documents:')
    for stat in doc_stats:
        print(f'   {stat["status"]}: {stat["count"]}')
    
    # Check pending jobs
    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(5)')
    print(f'⏳ Pending jobs: {len(pending_jobs)}')
    
    # Create a simple test document
    print(f'\n📄 Step 1: Creating Test Document')
    print('-' * 30)
    
    test_content = """
    Test Document for MVP End-to-End Processing
    
    This is a simple test document to verify that:
    1. File upload works correctly
    2. Storage bucket is accessible
    3. Queue processing functions
    4. Document parsing completes
    5. Text extraction succeeds
    
    Patient Information:
    - Name: John Doe
    - Policy Number: MVP-TEST-12345
    - Coverage Type: Health Insurance
    - Effective Date: 2024-01-01
    
    This document should be successfully processed by the MVP system.
    """
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    print(f'✅ Created test file: {Path(temp_file_path).name}')
    print(f'📝 Content length: {len(test_content)} characters')
    
    # Step 2: Upload document via upload-handler
    print(f'\n⬆️ Step 2: Uploading Document')
    print('-' * 30)
    
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'X-User-ID': 'test-user-mvp',
        'apikey': service_role_key
    }
    
    # For form upload, we need different approach
    # First, register the upload with metadata
    upload_metadata = {
        'filename': 'mvp_test_document.txt',
        'contentType': 'text/plain',
        'fileSize': len(test_content.encode('utf-8'))
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_url = f"{supabase_url}/functions/v1/upload-handler"
        
        try:
            async with session.post(upload_url, data=upload_metadata, headers=headers) as response:
                upload_status = response.status
                upload_response = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f'📤 Upload Status: {upload_status}')
                print(f'📝 Upload Response: {upload_response}')
                
                if upload_status == 200:
                    document_id = upload_response.get('documentId')
                    print(f'✅ Upload successful! Document ID: {document_id}')
                else:
                    print(f'❌ Upload failed: {upload_response}')
                    await conn.close()
                    os.unlink(temp_file_path)
                    return
                    
        except Exception as e:
            print(f'❌ Upload error: {e}')
            await conn.close()
            os.unlink(temp_file_path)
            return
    
    # Step 3: Monitor document processing
    print(f'\n⏳ Step 3: Monitoring Document Processing')
    print('-' * 30)
    
    # Check document was created
    document = await conn.fetchrow('''
        SELECT id, original_filename, status, storage_path, progress_percentage, created_at
        FROM documents 
        WHERE id = $1
    ''', document_id)
    
    if document:
        print(f'📄 Document created:')
        print(f'   ID: {document["id"]}')
        print(f'   Filename: {document["original_filename"]}')
        print(f'   Status: {document["status"]}')
        print(f'   Storage Path: {document["storage_path"]}')
        print(f'   Progress: {document["progress_percentage"]}%')
    else:
        print(f'❌ Document not found in database')
        await conn.close()
        os.unlink(temp_file_path)
        return
    
    # Step 4: Trigger queue processing
    print(f'\n🔄 Step 4: Triggering Queue Processing')
    print('-' * 30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        job_processor_url = f"{supabase_url}/functions/v1/job-processor"
        job_headers = {
            'Authorization': f'Bearer {service_role_key}',
            'Content-Type': 'application/json',
            'apikey': service_role_key
        }
        
        try:
            async with session.post(job_processor_url, headers=job_headers, json={}) as response:
                job_status = response.status
                job_response = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f'🔄 Job Processor Status: {job_status}')
                print(f'📝 Job Processor Response: {job_response}')
                
        except Exception as e:
            print(f'❌ Job processor error: {e}')
    
    # Step 5: Monitor processing completion
    print(f'\n👀 Step 5: Monitoring Processing Progress')
    print('-' * 30)
    
    max_wait_seconds = 120  # 2 minutes max wait
    check_interval = 10     # Check every 10 seconds
    checks = 0
    max_checks = max_wait_seconds // check_interval
    
    while checks < max_checks:
        # Check document status
        current_doc = await conn.fetchrow('''
            SELECT status, progress_percentage, extracted_text, error_message, updated_at
            FROM documents 
            WHERE id = $1
        ''', document_id)
        
        checks += 1
        print(f'🔍 Check {checks}/{max_checks}: Status = {current_doc["status"]}, Progress = {current_doc["progress_percentage"]}%')
        
        if current_doc["status"] == 'completed':
            print(f'✅ Processing completed successfully!')
            if current_doc["extracted_text"]:
                text_length = len(current_doc["extracted_text"])
                print(f'📝 Extracted text length: {text_length} characters')
                
                # Show first 200 characters of extracted text
                preview = current_doc["extracted_text"][:200]
                print(f'📖 Text preview: "{preview}..."')
            break
        elif current_doc["status"] == 'failed':
            print(f'❌ Processing failed!')
            if current_doc["error_message"]:
                print(f'💥 Error: {current_doc["error_message"]}')
            break
        elif current_doc["status"] in ['parsing', 'processing']:
            print(f'⏳ Still processing... (Progress: {current_doc["progress_percentage"]}%)')
        
        if checks < max_checks:
            await asyncio.sleep(check_interval)
    
    # Final status report
    print(f'\n📊 Final Status Report')
    print('-' * 30)
    
    final_doc = await conn.fetchrow('''
        SELECT status, progress_percentage, extracted_text, error_message, 
               content_type, file_size, storage_path
        FROM documents 
        WHERE id = $1
    ''', document_id)
    
    print(f'📄 Final Document Status:')
    print(f'   Status: {final_doc["status"]}')
    print(f'   Progress: {final_doc["progress_percentage"]}%')
    print(f'   Content Type: {final_doc["content_type"]}')
    print(f'   File Size: {final_doc["file_size"]} bytes')
    print(f'   Storage Path: {final_doc["storage_path"]}')
    print(f'   Has Extracted Text: {"Yes" if final_doc["extracted_text"] else "No"}')
    if final_doc["error_message"]:
        print(f'   Error: {final_doc["error_message"]}')
    
    # Check processing jobs
    job_status = await conn.fetch('''
        SELECT status, created_at, updated_at, retry_count, error_message
        FROM processing_jobs 
        WHERE document_id = $1
        ORDER BY created_at DESC
    ''')
    
    print(f'\n🔧 Processing Jobs ({len(job_status)} total):')
    for i, job in enumerate(job_status):
        print(f'   Job {i+1}: {job["status"]} (retries: {job["retry_count"]})')
        if job["error_message"]:
            print(f'           Error: {job["error_message"]}')
    
    # Overall result
    print(f'\n🎯 MVP Test Result')
    print('=' * 30)
    
    if final_doc["status"] == 'completed' and final_doc["extracted_text"]:
        print('✅ MVP END-TO-END TEST PASSED!')
        print('🎉 Document processing pipeline is working correctly')
        print('📋 Features verified:')
        print('   ✓ File upload via upload-handler')
        print('   ✓ Storage bucket access (raw_documents)')
        print('   ✓ Queue processing and job management')
        print('   ✓ Document parsing via doc-parser')
        print('   ✓ Text extraction and storage')
    elif final_doc["status"] == 'failed':
        print('❌ MVP END-TO-END TEST FAILED')
        print('💥 Document processing failed')
        print('🔍 Check error messages above for debugging')
    else:
        print('⚠️ MVP END-TO-END TEST INCOMPLETE')
        print(f'📊 Final status: {final_doc["status"]}')
        print('⏰ Processing may need more time or manual intervention')
    
    await conn.close()
    os.unlink(temp_file_path)
    print(f'\n🧹 Cleanup: Removed temporary test file')

if __name__ == "__main__":
    asyncio.run(test_mvp_end_to_end()) 