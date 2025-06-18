#!/usr/bin/env python3

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

async def test_doc_parser_direct():
    load_dotenv()
    
    print('🔬 Testing Doc-Parser Directly')
    print('=' * 35)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Use the document we just successfully uploaded
    document_id = 'cd05bfc9-60bf-4e3c-acd0-48a47c36fafb'
    
    print(f'📄 Testing with document: {document_id}')
    print(f'📁 File: simple_direct_test.txt')
    
    timeout = aiohttp.ClientTimeout(total=120)
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    payload = {
        'documentId': document_id
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        doc_parser_url = f"{supabase_url}/functions/v1/doc-parser"
        
        print(f'\n🌐 Calling doc-parser...')
        print(f'   URL: {doc_parser_url}')
        print(f'   Payload: {payload}')
        
        try:
            async with session.post(doc_parser_url, json=payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                content_type = response.headers.get('Content-Type', 'Unknown')
                
                print(f'\n📊 Doc-Parser Response:')
                print(f'   Status: {status} {response.reason}')
                print(f'   Content-Type: {content_type}')
                print(f'   Response Length: {len(response_text)}')
                
                print(f'\n📝 Response Content:')
                print(f'{response_text}')
                
                # Try to parse as JSON if possible
                try:
                    if content_type.startswith('application/json'):
                        response_json = json.loads(response_text)
                        print(f'\n🔍 Parsed JSON:')
                        for key, value in response_json.items():
                            if isinstance(value, str) and len(value) > 100:
                                print(f'   {key}: {value[:100]}...')
                            else:
                                print(f'   {key}: {value}')
                except:
                    pass
                
                print(f'\n📈 Analysis:')
                if status == 200:
                    print(f'✅ Doc-parser working correctly!')
                    if 'success' in response_text.lower():
                        print(f'✅ Document processed successfully')
                elif status == 400:
                    print(f'❌ Bad Request - likely file access issue')
                elif status == 500:
                    print(f'❌ Internal Server Error - likely processing issue')
                    print(f'   Check: LlamaParse API key, memory limits, dependencies')
                elif status >= 500:
                    print(f'❌ Server Error - Edge Function issue')
                else:
                    print(f'⚠️ Unexpected status code')
                
        except asyncio.TimeoutError:
            print(f'❌ Doc-parser timeout after 2 minutes')
            print(f'   This suggests the function is hanging or taking too long')
        except Exception as e:
            print(f'❌ Doc-parser error: {e}')

if __name__ == "__main__":
    asyncio.run(test_doc_parser_direct()) 

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

async def test_doc_parser_direct():
    load_dotenv()
    
    print('🔬 Testing Doc-Parser Directly')
    print('=' * 35)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Use the document we just successfully uploaded
    document_id = 'cd05bfc9-60bf-4e3c-acd0-48a47c36fafb'
    
    print(f'📄 Testing with document: {document_id}')
    print(f'📁 File: simple_direct_test.txt')
    
    timeout = aiohttp.ClientTimeout(total=120)
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    payload = {
        'documentId': document_id
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        doc_parser_url = f"{supabase_url}/functions/v1/doc-parser"
        
        print(f'\n🌐 Calling doc-parser...')
        print(f'   URL: {doc_parser_url}')
        print(f'   Payload: {payload}')
        
        try:
            async with session.post(doc_parser_url, json=payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                content_type = response.headers.get('Content-Type', 'Unknown')
                
                print(f'\n📊 Doc-Parser Response:')
                print(f'   Status: {status} {response.reason}')
                print(f'   Content-Type: {content_type}')
                print(f'   Response Length: {len(response_text)}')
                
                print(f'\n📝 Response Content:')
                print(f'{response_text}')
                
                # Try to parse as JSON if possible
                try:
                    if content_type.startswith('application/json'):
                        response_json = json.loads(response_text)
                        print(f'\n🔍 Parsed JSON:')
                        for key, value in response_json.items():
                            if isinstance(value, str) and len(value) > 100:
                                print(f'   {key}: {value[:100]}...')
                            else:
                                print(f'   {key}: {value}')
                except:
                    pass
                
                print(f'\n📈 Analysis:')
                if status == 200:
                    print(f'✅ Doc-parser working correctly!')
                    if 'success' in response_text.lower():
                        print(f'✅ Document processed successfully')
                elif status == 400:
                    print(f'❌ Bad Request - likely file access issue')
                elif status == 500:
                    print(f'❌ Internal Server Error - likely processing issue')
                    print(f'   Check: LlamaParse API key, memory limits, dependencies')
                elif status >= 500:
                    print(f'❌ Server Error - Edge Function issue')
                else:
                    print(f'⚠️ Unexpected status code')
                
        except asyncio.TimeoutError:
            print(f'❌ Doc-parser timeout after 2 minutes')
            print(f'   This suggests the function is hanging or taking too long')
        except Exception as e:
            print(f'❌ Doc-parser error: {e}')

if __name__ == "__main__":
    asyncio.run(test_doc_parser_direct()) 