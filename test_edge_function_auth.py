#!/usr/bin/env python3
"""
Test Edge Function Authentication
Tests if the fixed service role key works for manual processing
"""

import asyncio
import aiohttp
import json
import os

async def test_edge_function_auth():
    print("🧪 Testing Edge Function Authentication")
    print("=" * 50)
    
    # Use your correct service role key
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase_url = "https://jhrespvvhbnloxrieycf.supabase.co"
    
    if not service_role_key:
        print("❌ SUPABASE_SERVICE_ROLE_KEY not found in environment")
        return
    
    print(f"🔑 Using service role key: {service_role_key[:20]}...")
    
    # Test document ID from our stuck documents
    test_doc_id = "08c6d14e-1fec-4d9c-bb00-07b14bd542d4"
    test_user_id = "27b30e9d-0d06-4325-910f-20fe9d686f14"
    
    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
        "X-User-ID": test_user_id
    }
    
    payload = {
        "document_id": test_doc_id,
        "filename": "scan_classic_hmo.pdf"
    }
    
    async with aiohttp.ClientSession() as session:
        # Test job-processor
        job_processor_url = f"{supabase_url}/functions/v1/job-processor"
        
        print(f"\n🎯 Testing job-processor Edge Function...")
        print(f"📍 URL: {job_processor_url}")
        print(f"📄 Document ID: {test_doc_id}")
        
        try:
            async with session.post(job_processor_url, json=payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f"📊 Response Status: {status}")
                print(f"📝 Response: {response_text}")
                
                if status == 200:
                    print("✅ Edge Function authentication WORKING!")
                    try:
                        result = json.loads(response_text)
                        print(f"🎉 Processing result: {result}")
                    except:
                        print(f"⚠️  Response not JSON: {response_text}")
                elif status == 401:
                    print("❌ Authentication FAILED - service role key issue")
                elif status == 400:
                    print("⚠️  Bad request - check payload format")
                else:
                    print(f"❌ Unexpected error: {status}")
                    
        except Exception as e:
            print(f"❌ Error calling Edge Function: {e}")
        
        # Also test upload-handler to see if it's working
        print(f"\n🎯 Testing upload-handler status check...")
        upload_handler_url = f"{supabase_url}/functions/v1/upload-handler?documentId={test_doc_id}"
        
        try:
            async with session.get(upload_handler_url, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f"📊 Upload Handler Status: {status}")
                print(f"📝 Response: {response_text}")
                
        except Exception as e:
            print(f"❌ Error calling upload-handler: {e}")

if __name__ == "__main__":
    asyncio.run(test_edge_function_auth()) 
"""
Test Edge Function Authentication
Tests if the fixed service role key works for manual processing
"""

import asyncio
import aiohttp
import json
import os

async def test_edge_function_auth():
    print("🧪 Testing Edge Function Authentication")
    print("=" * 50)
    
    # Use your correct service role key
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase_url = "https://jhrespvvhbnloxrieycf.supabase.co"
    
    if not service_role_key:
        print("❌ SUPABASE_SERVICE_ROLE_KEY not found in environment")
        return
    
    print(f"🔑 Using service role key: {service_role_key[:20]}...")
    
    # Test document ID from our stuck documents
    test_doc_id = "08c6d14e-1fec-4d9c-bb00-07b14bd542d4"
    test_user_id = "27b30e9d-0d06-4325-910f-20fe9d686f14"
    
    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
        "X-User-ID": test_user_id
    }
    
    payload = {
        "document_id": test_doc_id,
        "filename": "scan_classic_hmo.pdf"
    }
    
    async with aiohttp.ClientSession() as session:
        # Test job-processor
        job_processor_url = f"{supabase_url}/functions/v1/job-processor"
        
        print(f"\n🎯 Testing job-processor Edge Function...")
        print(f"📍 URL: {job_processor_url}")
        print(f"📄 Document ID: {test_doc_id}")
        
        try:
            async with session.post(job_processor_url, json=payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f"📊 Response Status: {status}")
                print(f"📝 Response: {response_text}")
                
                if status == 200:
                    print("✅ Edge Function authentication WORKING!")
                    try:
                        result = json.loads(response_text)
                        print(f"🎉 Processing result: {result}")
                    except:
                        print(f"⚠️  Response not JSON: {response_text}")
                elif status == 401:
                    print("❌ Authentication FAILED - service role key issue")
                elif status == 400:
                    print("⚠️  Bad request - check payload format")
                else:
                    print(f"❌ Unexpected error: {status}")
                    
        except Exception as e:
            print(f"❌ Error calling Edge Function: {e}")
        
        # Also test upload-handler to see if it's working
        print(f"\n🎯 Testing upload-handler status check...")
        upload_handler_url = f"{supabase_url}/functions/v1/upload-handler?documentId={test_doc_id}"
        
        try:
            async with session.get(upload_handler_url, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f"📊 Upload Handler Status: {status}")
                print(f"📝 Response: {response_text}")
                
        except Exception as e:
            print(f"❌ Error calling upload-handler: {e}")

if __name__ == "__main__":
    asyncio.run(test_edge_function_auth()) 