#!/usr/bin/env python3

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

async def debug_upload_response():
    load_dotenv()
    
    print('🔍 Debugging Upload Handler Response')
    print('=' * 40)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'X-User-ID': '27b30e9d-0d06-4325-910f-20fe9d686f14',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    upload_metadata = {
        'filename': 'debug_test.txt',
        'contentType': 'text/plain',
        'fileSize': 100
    }
    
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_handler_url = f"{supabase_url}/functions/v1/upload-handler"
        
        try:
            async with session.post(upload_handler_url, json=upload_metadata, headers=headers) as response:
                status = response.status
                content_type = response.headers.get('Content-Type', 'Unknown')
                response_text = await response.text()
                
                print(f'📊 Raw Response Details:')
                print(f'   Status: {status}')
                print(f'   Content-Type: {content_type}')
                print(f'   Response Length: {len(response_text)}')
                print(f'   Raw Text: {response_text}')
                
                # Try to parse as JSON
                try:
                    response_json = json.loads(response_text)
                    print(f'\n📝 Parsed JSON:')
                    for key, value in response_json.items():
                        print(f'   {key}: {value}')
                        
                    print(f'\n🔍 Key Analysis:')
                    print(f'   Has documentId: {"documentId" in response_json}')
                    print(f'   Has uploadUrl: {"uploadUrl" in response_json}')
                    print(f'   UploadUrl value: {response_json.get("uploadUrl", "NOT FOUND")}')
                    print(f'   UploadUrl type: {type(response_json.get("uploadUrl"))}')
                    
                except json.JSONDecodeError as e:
                    print(f'❌ JSON Parse Error: {e}')
                    
        except Exception as e:
            print(f'❌ Request error: {e}')

if __name__ == "__main__":
    asyncio.run(debug_upload_response()) 

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

async def debug_upload_response():
    load_dotenv()
    
    print('🔍 Debugging Upload Handler Response')
    print('=' * 40)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'X-User-ID': '27b30e9d-0d06-4325-910f-20fe9d686f14',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    upload_metadata = {
        'filename': 'debug_test.txt',
        'contentType': 'text/plain',
        'fileSize': 100
    }
    
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_handler_url = f"{supabase_url}/functions/v1/upload-handler"
        
        try:
            async with session.post(upload_handler_url, json=upload_metadata, headers=headers) as response:
                status = response.status
                content_type = response.headers.get('Content-Type', 'Unknown')
                response_text = await response.text()
                
                print(f'📊 Raw Response Details:')
                print(f'   Status: {status}')
                print(f'   Content-Type: {content_type}')
                print(f'   Response Length: {len(response_text)}')
                print(f'   Raw Text: {response_text}')
                
                # Try to parse as JSON
                try:
                    response_json = json.loads(response_text)
                    print(f'\n📝 Parsed JSON:')
                    for key, value in response_json.items():
                        print(f'   {key}: {value}')
                        
                    print(f'\n🔍 Key Analysis:')
                    print(f'   Has documentId: {"documentId" in response_json}')
                    print(f'   Has uploadUrl: {"uploadUrl" in response_json}')
                    print(f'   UploadUrl value: {response_json.get("uploadUrl", "NOT FOUND")}')
                    print(f'   UploadUrl type: {type(response_json.get("uploadUrl"))}')
                    
                except json.JSONDecodeError as e:
                    print(f'❌ JSON Parse Error: {e}')
                    
        except Exception as e:
            print(f'❌ Request error: {e}')

if __name__ == "__main__":
    asyncio.run(debug_upload_response()) 