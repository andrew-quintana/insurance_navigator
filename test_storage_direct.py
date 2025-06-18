#!/usr/bin/env python3

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

async def test_storage_direct():
    load_dotenv()
    
    print('🗄️ Testing Storage Access Direct')
    print('=' * 35)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Use the file we know was successfully uploaded
    storage_path = '27b30e9d-0d06-4325-910f-20fe9d686f14/58b3ea7c6bc22b82dac5ee2a51131195120fc48c8fac7bfdd4f023a6bd59cce5/simple_direct_test.txt'
    
    print(f'📁 Testing storage path: {storage_path}')
    
    timeout = aiohttp.ClientTimeout(total=60)
    
    # Test 1: Direct object access (same as upload worked)
    print(f'\n1️⃣ Testing Direct Object Access')
    print('-' * 33)
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'apikey': service_role_key
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        object_url = f"{supabase_url}/storage/v1/object/raw_documents/{storage_path}"
        
        print(f'📍 URL: {object_url}')
        
        try:
            async with session.get(object_url, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f'📊 Response:')
                print(f'   Status: {status} {response.reason}')
                print(f'   Content: {response_text[:100] if response_text else "Empty"}')
                
                if status == 200:
                    print(f'✅ Direct object access works!')
                else:
                    print(f'❌ Direct object access failed')
                    
        except Exception as e:
            print(f'❌ Direct access error: {e}')
    
    # Test 2: Storage client download (same method as doc-parser)
    print(f'\n2️⃣ Testing Storage Client Download')
    print('-' * 35)
    
    # Simulate the exact call that doc-parser makes
    download_url = f"{supabase_url}/storage/v1/object/raw_documents/{storage_path}"
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        print(f'📍 Download URL: {download_url}')
        
        try:
            async with session.get(download_url, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                content_type = response.headers.get('Content-Type', 'Unknown')
                
                print(f'📊 Storage Download Response:')
                print(f'   Status: {status} {response.reason}')
                print(f'   Content-Type: {content_type}')
                print(f'   Content Length: {len(response_text)}')
                print(f'   Content Preview: {response_text[:100] if response_text else "Empty"}')
                
                if status == 200:
                    print(f'✅ Storage download works!')
                    print(f'📝 File content matches what we uploaded')
                else:
                    print(f'❌ Storage download failed')
                    try:
                        error_json = json.loads(response_text)
                        print(f'   Error details: {error_json}')
                    except:
                        pass
                        
        except Exception as e:
            print(f'❌ Storage download error: {e}')
    
    # Test 3: Check bucket permissions and policies
    print(f'\n3️⃣ Testing Bucket Permissions')
    print('-' * 30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        bucket_url = f"{supabase_url}/storage/v1/bucket/raw_documents"
        
        try:
            async with session.get(bucket_url, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f'📊 Bucket Info Response:')
                print(f'   Status: {status}')
                print(f'   Content: {response_text}')
                
                if status == 200:
                    bucket_info = json.loads(response_text)
                    print(f'✅ Bucket accessible:')
                    print(f'   Public: {bucket_info.get("public", "unknown")}')
                    print(f'   File size limit: {bucket_info.get("file_size_limit", "unknown")}')
                else:
                    print(f'❌ Bucket access failed')
                    
        except Exception as e:
            print(f'❌ Bucket check error: {e}')
    
    # Test 4: List objects in bucket
    print(f'\n4️⃣ Testing Object Listing')
    print('-' * 26)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        list_url = f"{supabase_url}/storage/v1/object/list/raw_documents"
        
        # List objects in the user's folder
        user_folder = '27b30e9d-0d06-4325-910f-20fe9d686f14'
        list_payload = {
            'prefix': user_folder,
            'limit': 10
        }
        
        try:
            async with session.post(list_url, json=list_payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f'📊 Object List Response:')
                print(f'   Status: {status}')
                print(f'   Content: {response_text[:300] if response_text else "Empty"}')
                
                if status == 200:
                    objects = json.loads(response_text)
                    print(f'✅ Found {len(objects)} objects:')
                    for obj in objects[:3]:  # Show first 3
                        print(f'   - {obj.get("name", "unknown")}')
                else:
                    print(f'❌ Object listing failed')
                    
        except Exception as e:
            print(f'❌ Object listing error: {e}')

if __name__ == "__main__":
    asyncio.run(test_storage_direct()) 

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

async def test_storage_direct():
    load_dotenv()
    
    print('🗄️ Testing Storage Access Direct')
    print('=' * 35)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Use the file we know was successfully uploaded
    storage_path = '27b30e9d-0d06-4325-910f-20fe9d686f14/58b3ea7c6bc22b82dac5ee2a51131195120fc48c8fac7bfdd4f023a6bd59cce5/simple_direct_test.txt'
    
    print(f'📁 Testing storage path: {storage_path}')
    
    timeout = aiohttp.ClientTimeout(total=60)
    
    # Test 1: Direct object access (same as upload worked)
    print(f'\n1️⃣ Testing Direct Object Access')
    print('-' * 33)
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'apikey': service_role_key
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        object_url = f"{supabase_url}/storage/v1/object/raw_documents/{storage_path}"
        
        print(f'📍 URL: {object_url}')
        
        try:
            async with session.get(object_url, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f'📊 Response:')
                print(f'   Status: {status} {response.reason}')
                print(f'   Content: {response_text[:100] if response_text else "Empty"}')
                
                if status == 200:
                    print(f'✅ Direct object access works!')
                else:
                    print(f'❌ Direct object access failed')
                    
        except Exception as e:
            print(f'❌ Direct access error: {e}')
    
    # Test 2: Storage client download (same method as doc-parser)
    print(f'\n2️⃣ Testing Storage Client Download')
    print('-' * 35)
    
    # Simulate the exact call that doc-parser makes
    download_url = f"{supabase_url}/storage/v1/object/raw_documents/{storage_path}"
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        print(f'📍 Download URL: {download_url}')
        
        try:
            async with session.get(download_url, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                content_type = response.headers.get('Content-Type', 'Unknown')
                
                print(f'📊 Storage Download Response:')
                print(f'   Status: {status} {response.reason}')
                print(f'   Content-Type: {content_type}')
                print(f'   Content Length: {len(response_text)}')
                print(f'   Content Preview: {response_text[:100] if response_text else "Empty"}')
                
                if status == 200:
                    print(f'✅ Storage download works!')
                    print(f'📝 File content matches what we uploaded')
                else:
                    print(f'❌ Storage download failed')
                    try:
                        error_json = json.loads(response_text)
                        print(f'   Error details: {error_json}')
                    except:
                        pass
                        
        except Exception as e:
            print(f'❌ Storage download error: {e}')
    
    # Test 3: Check bucket permissions and policies
    print(f'\n3️⃣ Testing Bucket Permissions')
    print('-' * 30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        bucket_url = f"{supabase_url}/storage/v1/bucket/raw_documents"
        
        try:
            async with session.get(bucket_url, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f'📊 Bucket Info Response:')
                print(f'   Status: {status}')
                print(f'   Content: {response_text}')
                
                if status == 200:
                    bucket_info = json.loads(response_text)
                    print(f'✅ Bucket accessible:')
                    print(f'   Public: {bucket_info.get("public", "unknown")}')
                    print(f'   File size limit: {bucket_info.get("file_size_limit", "unknown")}')
                else:
                    print(f'❌ Bucket access failed')
                    
        except Exception as e:
            print(f'❌ Bucket check error: {e}')
    
    # Test 4: List objects in bucket
    print(f'\n4️⃣ Testing Object Listing')
    print('-' * 26)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        list_url = f"{supabase_url}/storage/v1/object/list/raw_documents"
        
        # List objects in the user's folder
        user_folder = '27b30e9d-0d06-4325-910f-20fe9d686f14'
        list_payload = {
            'prefix': user_folder,
            'limit': 10
        }
        
        try:
            async with session.post(list_url, json=list_payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f'📊 Object List Response:')
                print(f'   Status: {status}')
                print(f'   Content: {response_text[:300] if response_text else "Empty"}')
                
                if status == 200:
                    objects = json.loads(response_text)
                    print(f'✅ Found {len(objects)} objects:')
                    for obj in objects[:3]:  # Show first 3
                        print(f'   - {obj.get("name", "unknown")}')
                else:
                    print(f'❌ Object listing failed')
                    
        except Exception as e:
            print(f'❌ Object listing error: {e}')

if __name__ == "__main__":
    asyncio.run(test_storage_direct()) 