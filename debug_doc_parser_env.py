#!/usr/bin/env python3

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

async def debug_doc_parser_env():
    load_dotenv()
    
    print('🔬 Debugging Doc-Parser Environment')
    print('=' * 40)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Use a minimal test payload to see what goes wrong
    document_id = 'cd05bfc9-60bf-4e3c-acd0-48a47c36fafb'
    
    print(f'📄 Testing document: {document_id}')
    print(f'🔑 Service key length: {len(service_role_key) if service_role_key else 0}')
    print(f'🌐 Supabase URL: {supabase_url}')
    
    timeout = aiohttp.ClientTimeout(total=30)  # Shorter timeout for debugging
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    payload = {
        'documentId': document_id
    }
    
    # First verify the document exists
    print(f'\n1️⃣ Verifying Document Exists')
    print('-' * 29)
    
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    document = await conn.fetchrow('''
        SELECT id, original_filename, storage_path, file_size, content_type, status
        FROM documents 
        WHERE id = $1
    ''', document_id)
    
    if document:
        print(f'✅ Document found in database:')
        print(f'   Filename: {document["original_filename"]}')
        print(f'   Storage Path: {document["storage_path"]}')
        print(f'   Status: {document["status"]}')
    else:
        print(f'❌ Document not found in database')
        await conn.close()
        return
    
    await conn.close()
    
    # Test the doc-parser with detailed error handling
    print(f'\n2️⃣ Testing Doc-Parser with Debug')
    print('-' * 34)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        doc_parser_url = f"{supabase_url}/functions/v1/doc-parser"
        
        print(f'🌐 Calling: {doc_parser_url}')
        print(f'📤 Payload: {payload}')
        print(f'🔑 Auth header: Bearer {service_role_key[:10]}...')
        
        try:
            async with session.post(doc_parser_url, json=payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                content_type = response.headers.get('Content-Type', 'Unknown')
                response_headers = dict(response.headers)
                
                print(f'\n📊 Complete Response Analysis:')
                print(f'   Status: {status} {response.reason}')
                print(f'   Content-Type: {content_type}')
                print(f'   Response Size: {len(response_text)} bytes')
                print(f'   Headers: {json.dumps({k: v for k, v in response_headers.items() if k.lower() not in ["authorization", "apikey"]}, indent=2)}')
                
                print(f'\n📝 Response Body:')
                print(f'{response_text}')
                
                # Analysis based on response
                if status == 400 and "Failed to download file" in response_text:
                    print(f'\n🔍 ISSUE IDENTIFIED: File Download Failure')
                    print(f'🚨 This suggests the doc-parser Edge Function cannot access storage')
                    print(f'💡 Possible causes:')
                    print(f'   1. Environment variables not set in Edge Function')
                    print(f'   2. Service role key not accessible within Edge Function')
                    print(f'   3. Supabase client initialization failing')
                    print(f'   4. Storage permissions issue within Edge Function context')
                    
                    print(f'\n🛠️ RECOMMENDED FIXES:')
                    print(f'   • Check Edge Function environment variables')
                    print(f'   • Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set')
                    print(f'   • Check Supabase dashboard for function logs')
                    print(f'   • Test with a simple storage access function')
                
                elif status == 500:
                    print(f'\n🔍 ISSUE: Internal Server Error')
                    print(f'🚨 Edge Function crashed or threw an exception')
                    print(f'💡 Check Edge Function logs for error details')
                    
                elif status == 200:
                    print(f'\n✅ SUCCESS: Doc-parser responded correctly')
                    try:
                        result = json.loads(response_text)
                        if result.get('success'):
                            print(f'🎉 Document processing completed!')
                        else:
                            print(f'⚠️ Processing failed: {result.get("error", "Unknown error")}')
                    except:
                        print(f'📄 Raw response (not JSON): {response_text[:200]}')
                        
        except asyncio.TimeoutError:
            print(f'❌ TIMEOUT: Doc-parser took longer than 30 seconds')
            print(f'💡 This suggests the function is hanging or in an infinite loop')
            print(f'🔍 Check for:')
            print(f'   • Network issues within Edge Function')
            print(f'   • Infinite loops in parsing logic')
            print(f'   • LlamaParse API timeouts')
            
        except Exception as e:
            print(f'❌ REQUEST ERROR: {e}')
            print(f'💡 This suggests a network or client-side issue')

if __name__ == "__main__":
    # Import asyncpg at the top
    import asyncpg
    asyncio.run(debug_doc_parser_env()) 

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

async def debug_doc_parser_env():
    load_dotenv()
    
    print('🔬 Debugging Doc-Parser Environment')
    print('=' * 40)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Use a minimal test payload to see what goes wrong
    document_id = 'cd05bfc9-60bf-4e3c-acd0-48a47c36fafb'
    
    print(f'📄 Testing document: {document_id}')
    print(f'🔑 Service key length: {len(service_role_key) if service_role_key else 0}')
    print(f'🌐 Supabase URL: {supabase_url}')
    
    timeout = aiohttp.ClientTimeout(total=30)  # Shorter timeout for debugging
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    payload = {
        'documentId': document_id
    }
    
    # First verify the document exists
    print(f'\n1️⃣ Verifying Document Exists')
    print('-' * 29)
    
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0,
        server_settings={'jit': 'off'}
    )
    
    document = await conn.fetchrow('''
        SELECT id, original_filename, storage_path, file_size, content_type, status
        FROM documents 
        WHERE id = $1
    ''', document_id)
    
    if document:
        print(f'✅ Document found in database:')
        print(f'   Filename: {document["original_filename"]}')
        print(f'   Storage Path: {document["storage_path"]}')
        print(f'   Status: {document["status"]}')
    else:
        print(f'❌ Document not found in database')
        await conn.close()
        return
    
    await conn.close()
    
    # Test the doc-parser with detailed error handling
    print(f'\n2️⃣ Testing Doc-Parser with Debug')
    print('-' * 34)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        doc_parser_url = f"{supabase_url}/functions/v1/doc-parser"
        
        print(f'🌐 Calling: {doc_parser_url}')
        print(f'📤 Payload: {payload}')
        print(f'🔑 Auth header: Bearer {service_role_key[:10]}...')
        
        try:
            async with session.post(doc_parser_url, json=payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                content_type = response.headers.get('Content-Type', 'Unknown')
                response_headers = dict(response.headers)
                
                print(f'\n📊 Complete Response Analysis:')
                print(f'   Status: {status} {response.reason}')
                print(f'   Content-Type: {content_type}')
                print(f'   Response Size: {len(response_text)} bytes')
                print(f'   Headers: {json.dumps({k: v for k, v in response_headers.items() if k.lower() not in ["authorization", "apikey"]}, indent=2)}')
                
                print(f'\n📝 Response Body:')
                print(f'{response_text}')
                
                # Analysis based on response
                if status == 400 and "Failed to download file" in response_text:
                    print(f'\n🔍 ISSUE IDENTIFIED: File Download Failure')
                    print(f'🚨 This suggests the doc-parser Edge Function cannot access storage')
                    print(f'💡 Possible causes:')
                    print(f'   1. Environment variables not set in Edge Function')
                    print(f'   2. Service role key not accessible within Edge Function')
                    print(f'   3. Supabase client initialization failing')
                    print(f'   4. Storage permissions issue within Edge Function context')
                    
                    print(f'\n🛠️ RECOMMENDED FIXES:')
                    print(f'   • Check Edge Function environment variables')
                    print(f'   • Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set')
                    print(f'   • Check Supabase dashboard for function logs')
                    print(f'   • Test with a simple storage access function')
                
                elif status == 500:
                    print(f'\n🔍 ISSUE: Internal Server Error')
                    print(f'🚨 Edge Function crashed or threw an exception')
                    print(f'💡 Check Edge Function logs for error details')
                    
                elif status == 200:
                    print(f'\n✅ SUCCESS: Doc-parser responded correctly')
                    try:
                        result = json.loads(response_text)
                        if result.get('success'):
                            print(f'🎉 Document processing completed!')
                        else:
                            print(f'⚠️ Processing failed: {result.get("error", "Unknown error")}')
                    except:
                        print(f'📄 Raw response (not JSON): {response_text[:200]}')
                        
        except asyncio.TimeoutError:
            print(f'❌ TIMEOUT: Doc-parser took longer than 30 seconds')
            print(f'💡 This suggests the function is hanging or in an infinite loop')
            print(f'🔍 Check for:')
            print(f'   • Network issues within Edge Function')
            print(f'   • Infinite loops in parsing logic')
            print(f'   • LlamaParse API timeouts')
            
        except Exception as e:
            print(f'❌ REQUEST ERROR: {e}')
            print(f'💡 This suggests a network or client-side issue')

if __name__ == "__main__":
    # Import asyncpg at the top
    import asyncpg
    asyncio.run(debug_doc_parser_env()) 