#!/usr/bin/env python3

import asyncio
import asyncpg
import os
import aiohttp
import json
from dotenv import load_dotenv

async def debug_doc_parser():
    load_dotenv()
    
    print('🔍 Debugging Doc-Parser Edge Function')
    print('=' * 40)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables")
        return
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    # Step 1: Find a recent document to test with
    print(f'\n1️⃣ Finding Test Document')
    print('-' * 25)
    
    # Look for a recent document with storage_path
    test_doc = await conn.fetchrow('''
        SELECT id, original_filename, storage_path, file_size, content_type,
               status, progress_percentage, created_at
        FROM documents 
        WHERE storage_path IS NOT NULL
        AND created_at > NOW() - INTERVAL '2 hours'
        ORDER BY created_at DESC
        LIMIT 1
    ''')
    
    if not test_doc:
        print('❌ No recent documents found for testing')
        await conn.close()
        return
    
    print(f'📄 Test Document Found:')
    print(f'   ID: {test_doc["id"]}')
    print(f'   Filename: {test_doc["original_filename"]}')
    print(f'   Storage Path: {test_doc["storage_path"]}')
    print(f'   File Size: {test_doc["file_size"]} bytes')
    print(f'   Content Type: {test_doc["content_type"]}')
    print(f'   Status: {test_doc["status"]}')
    
    # Step 2: Test doc-parser directly
    print(f'\n2️⃣ Testing Doc-Parser Directly')
    print('-' * 30)
    
    timeout = aiohttp.ClientTimeout(total=120)  # 2 minutes for parsing
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    doc_parser_payload = {
        'documentId': str(test_doc["id"])
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        doc_parser_url = f"{supabase_url}/functions/v1/doc-parser"
        
        print(f'🌐 Calling doc-parser...')
        print(f'   URL: {doc_parser_url}')
        print(f'   Document ID: {test_doc["id"]}')
        
        try:
            async with session.post(doc_parser_url, json=doc_parser_payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f'📊 Doc-Parser Response:')
                print(f'   Status Code: {status}')
                print(f'   Status Text: {response.reason}')
                print(f'   Response Length: {len(response_text)} characters')
                
                # Try to parse as JSON
                try:
                    response_json = json.loads(response_text)
                    print(f'   Response JSON: {json.dumps(response_json, indent=2)}')
                except:
                    print(f'   Response Text: {response_text[:500]}{"..." if len(response_text) > 500 else ""}')
                
                # Check response headers
                print(f'   Content-Type: {response.headers.get("Content-Type", "Not set")}')
                
        except asyncio.TimeoutError:
            print(f'❌ Doc-parser timeout after 2 minutes')
        except Exception as e:
            print(f'❌ Doc-parser error: {e}')
    
    # Step 3: Check storage bucket access
    print(f'\n3️⃣ Testing Storage Bucket Access')
    print('-' * 33)
    
    # Test direct storage access
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Test download from raw_documents bucket
        storage_url = f"{supabase_url}/storage/v1/object/raw_documents/{test_doc['storage_path']}"
        
        print(f'🗄️ Testing storage access...')
        print(f'   Storage URL: {storage_url}')
        
        try:
            async with session.get(storage_url, headers=headers) as storage_response:
                storage_status = storage_response.status
                storage_text = await storage_response.text()
                
                print(f'📊 Storage Response:')
                print(f'   Status Code: {storage_status}')
                print(f'   Status Text: {storage_response.reason}')
                print(f'   Response Length: {len(storage_text)} characters')
                
                if storage_status == 200:
                    print(f'✅ Storage access successful')
                    print(f'   File content preview: {storage_text[:100]}{"..." if len(storage_text) > 100 else ""}')
                else:
                    print(f'❌ Storage access failed: {storage_text}')
                    
        except Exception as e:
            print(f'❌ Storage access error: {e}')
    
    # Step 4: Check bucket existence and permissions
    print(f'\n4️⃣ Checking Bucket Configuration')
    print('-' * 32)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # List buckets
        buckets_url = f"{supabase_url}/storage/v1/bucket"
        
        try:
            async with session.get(buckets_url, headers=headers) as bucket_response:
                bucket_status = bucket_response.status
                bucket_data = await bucket_response.json() if bucket_response.content_type == 'application/json' else await bucket_response.text()
                
                print(f'📦 Bucket Configuration:')
                print(f'   Status: {bucket_status}')
                
                if bucket_status == 200 and isinstance(bucket_data, list):
                    bucket_names = [b.get('name', 'unknown') for b in bucket_data]
                    print(f'   Available buckets: {bucket_names}')
                    
                    # Check raw_documents bucket details
                    raw_docs_bucket = next((b for b in bucket_data if b.get('name') == 'raw_documents'), None)
                    if raw_docs_bucket:
                        print(f'✅ raw_documents bucket found:')
                        print(f'      Public: {raw_docs_bucket.get("public", "unknown")}')
                        print(f'      File size limit: {raw_docs_bucket.get("file_size_limit", "unknown")}')
                        print(f'      Allowed MIME types: {raw_docs_bucket.get("allowed_mime_types", "unknown")}')
                    else:
                        print(f'❌ raw_documents bucket not found')
                else:
                    print(f'❌ Failed to list buckets: {bucket_data}')
                    
        except Exception as e:
            print(f'❌ Bucket check error: {e}')
    
    # Step 5: Check document status after test
    print(f'\n5️⃣ Final Document Status')
    print('-' * 25)
    
    final_doc = await conn.fetchrow('''
        SELECT status, progress_percentage, content_extracted, 
               processing_status, upload_status, updated_at
        FROM documents 
        WHERE id = $1
    ''', test_doc["id"])
    
    print(f'📄 Document Status After Test:')
    print(f'   Status: {final_doc["status"]}')
    print(f'   Progress: {final_doc["progress_percentage"]}%')
    print(f'   Processing Status: {final_doc["processing_status"]}')
    print(f'   Upload Status: {final_doc["upload_status"]}')
    print(f'   Has Content: {"Yes" if final_doc["content_extracted"] else "No"}')
    print(f'   Last Updated: {final_doc["updated_at"]}')
    
    # Step 6: Analysis and recommendations
    print(f'\n📋 Analysis & Recommendations')
    print('=' * 32)
    
    print(f'🔍 Based on the tests above:')
    print(f'   • Check the doc-parser response status and error message')
    print(f'   • Verify storage bucket access is working')
    print(f'   • Confirm raw_documents bucket configuration')
    print(f'   • Look for any timeout or memory issues')
    
    print(f'\n📝 Common doc-parser failure causes:')
    print(f'   1. Storage path mismatch or missing files')
    print(f'   2. Bucket permissions or authentication issues')
    print(f'   3. Edge Function timeout (>150-400 seconds)')
    print(f'   4. Memory limits exceeded during processing')
    print(f'   5. LlamaParse API key issues or quotas')
    print(f'   6. Invalid file formats or corrupted files')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(debug_doc_parser()) 

import asyncio
import asyncpg
import os
import aiohttp
import json
from dotenv import load_dotenv

async def debug_doc_parser():
    load_dotenv()
    
    print('🔍 Debugging Doc-Parser Edge Function')
    print('=' * 40)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables")
        return
    
    # Connect to database
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    # Step 1: Find a recent document to test with
    print(f'\n1️⃣ Finding Test Document')
    print('-' * 25)
    
    # Look for a recent document with storage_path
    test_doc = await conn.fetchrow('''
        SELECT id, original_filename, storage_path, file_size, content_type,
               status, progress_percentage, created_at
        FROM documents 
        WHERE storage_path IS NOT NULL
        AND created_at > NOW() - INTERVAL '2 hours'
        ORDER BY created_at DESC
        LIMIT 1
    ''')
    
    if not test_doc:
        print('❌ No recent documents found for testing')
        await conn.close()
        return
    
    print(f'📄 Test Document Found:')
    print(f'   ID: {test_doc["id"]}')
    print(f'   Filename: {test_doc["original_filename"]}')
    print(f'   Storage Path: {test_doc["storage_path"]}')
    print(f'   File Size: {test_doc["file_size"]} bytes')
    print(f'   Content Type: {test_doc["content_type"]}')
    print(f'   Status: {test_doc["status"]}')
    
    # Step 2: Test doc-parser directly
    print(f'\n2️⃣ Testing Doc-Parser Directly')
    print('-' * 30)
    
    timeout = aiohttp.ClientTimeout(total=120)  # 2 minutes for parsing
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    doc_parser_payload = {
        'documentId': str(test_doc["id"])
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        doc_parser_url = f"{supabase_url}/functions/v1/doc-parser"
        
        print(f'🌐 Calling doc-parser...')
        print(f'   URL: {doc_parser_url}')
        print(f'   Document ID: {test_doc["id"]}')
        
        try:
            async with session.post(doc_parser_url, json=doc_parser_payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f'📊 Doc-Parser Response:')
                print(f'   Status Code: {status}')
                print(f'   Status Text: {response.reason}')
                print(f'   Response Length: {len(response_text)} characters')
                
                # Try to parse as JSON
                try:
                    response_json = json.loads(response_text)
                    print(f'   Response JSON: {json.dumps(response_json, indent=2)}')
                except:
                    print(f'   Response Text: {response_text[:500]}{"..." if len(response_text) > 500 else ""}')
                
                # Check response headers
                print(f'   Content-Type: {response.headers.get("Content-Type", "Not set")}')
                
        except asyncio.TimeoutError:
            print(f'❌ Doc-parser timeout after 2 minutes')
        except Exception as e:
            print(f'❌ Doc-parser error: {e}')
    
    # Step 3: Check storage bucket access
    print(f'\n3️⃣ Testing Storage Bucket Access')
    print('-' * 33)
    
    # Test direct storage access
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Test download from raw_documents bucket
        storage_url = f"{supabase_url}/storage/v1/object/raw_documents/{test_doc['storage_path']}"
        
        print(f'🗄️ Testing storage access...')
        print(f'   Storage URL: {storage_url}')
        
        try:
            async with session.get(storage_url, headers=headers) as storage_response:
                storage_status = storage_response.status
                storage_text = await storage_response.text()
                
                print(f'📊 Storage Response:')
                print(f'   Status Code: {storage_status}')
                print(f'   Status Text: {storage_response.reason}')
                print(f'   Response Length: {len(storage_text)} characters')
                
                if storage_status == 200:
                    print(f'✅ Storage access successful')
                    print(f'   File content preview: {storage_text[:100]}{"..." if len(storage_text) > 100 else ""}')
                else:
                    print(f'❌ Storage access failed: {storage_text}')
                    
        except Exception as e:
            print(f'❌ Storage access error: {e}')
    
    # Step 4: Check bucket existence and permissions
    print(f'\n4️⃣ Checking Bucket Configuration')
    print('-' * 32)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # List buckets
        buckets_url = f"{supabase_url}/storage/v1/bucket"
        
        try:
            async with session.get(buckets_url, headers=headers) as bucket_response:
                bucket_status = bucket_response.status
                bucket_data = await bucket_response.json() if bucket_response.content_type == 'application/json' else await bucket_response.text()
                
                print(f'📦 Bucket Configuration:')
                print(f'   Status: {bucket_status}')
                
                if bucket_status == 200 and isinstance(bucket_data, list):
                    bucket_names = [b.get('name', 'unknown') for b in bucket_data]
                    print(f'   Available buckets: {bucket_names}')
                    
                    # Check raw_documents bucket details
                    raw_docs_bucket = next((b for b in bucket_data if b.get('name') == 'raw_documents'), None)
                    if raw_docs_bucket:
                        print(f'✅ raw_documents bucket found:')
                        print(f'      Public: {raw_docs_bucket.get("public", "unknown")}')
                        print(f'      File size limit: {raw_docs_bucket.get("file_size_limit", "unknown")}')
                        print(f'      Allowed MIME types: {raw_docs_bucket.get("allowed_mime_types", "unknown")}')
                    else:
                        print(f'❌ raw_documents bucket not found')
                else:
                    print(f'❌ Failed to list buckets: {bucket_data}')
                    
        except Exception as e:
            print(f'❌ Bucket check error: {e}')
    
    # Step 5: Check document status after test
    print(f'\n5️⃣ Final Document Status')
    print('-' * 25)
    
    final_doc = await conn.fetchrow('''
        SELECT status, progress_percentage, content_extracted, 
               processing_status, upload_status, updated_at
        FROM documents 
        WHERE id = $1
    ''', test_doc["id"])
    
    print(f'📄 Document Status After Test:')
    print(f'   Status: {final_doc["status"]}')
    print(f'   Progress: {final_doc["progress_percentage"]}%')
    print(f'   Processing Status: {final_doc["processing_status"]}')
    print(f'   Upload Status: {final_doc["upload_status"]}')
    print(f'   Has Content: {"Yes" if final_doc["content_extracted"] else "No"}')
    print(f'   Last Updated: {final_doc["updated_at"]}')
    
    # Step 6: Analysis and recommendations
    print(f'\n📋 Analysis & Recommendations')
    print('=' * 32)
    
    print(f'🔍 Based on the tests above:')
    print(f'   • Check the doc-parser response status and error message')
    print(f'   • Verify storage bucket access is working')
    print(f'   • Confirm raw_documents bucket configuration')
    print(f'   • Look for any timeout or memory issues')
    
    print(f'\n📝 Common doc-parser failure causes:')
    print(f'   1. Storage path mismatch or missing files')
    print(f'   2. Bucket permissions or authentication issues')
    print(f'   3. Edge Function timeout (>150-400 seconds)')
    print(f'   4. Memory limits exceeded during processing')
    print(f'   5. LlamaParse API key issues or quotas')
    print(f'   6. Invalid file formats or corrupted files')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(debug_doc_parser()) 