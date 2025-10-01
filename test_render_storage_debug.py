#!/usr/bin/env python3
"""
Test script to debug the Render storage issue by making the exact same requests
that are failing in the Render environment.
"""

import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath('.'))

from backend.shared.storage.storage_manager import StorageManager
from backend.shared.logging.structured_logger import StructuredLogger

async def test_render_storage_debug():
    """Test the exact same storage requests that are failing on Render"""
    load_dotenv('.env.staging')
    
    logger = StructuredLogger("test_render_storage_debug")
    
    print("🔬 Render Storage Debug Test")
    print("=" * 60)
    
    # Use the same configuration as Render
    config = {
        "storage_url": os.getenv("SUPABASE_URL"),
        "anon_key": os.getenv("SUPABASE_ANON_KEY"),
        "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        "timeout": 60
    }
    
    print(f"Configuration:")
    print(f"  Storage URL: {config['storage_url']}")
    print(f"  Service Role Key Present: {bool(config['service_role_key'])}")
    print(f"  Service Role Key Length: {len(config['service_role_key']) if config['service_role_key'] else 0}")
    print()
    
    # Test the exact file path that's failing on Render
    test_file_path = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/471c37fa_5e4390c2.pdf"
    
    print(f"Testing file path: {test_file_path}")
    print()
    
    # Create HTTP client with same headers as Render
    headers = {
        "apikey": config['service_role_key'],
        "Authorization": f"Bearer {config['service_role_key']}"
    }
    
    print(f"HTTP Headers:")
    for key, value in headers.items():
        print(f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}")
    print()
    
    # Test 1: HEAD request (what blob_exists does)
    print("🧪 Test 1: HEAD request (blob_exists method)")
    try:
        bucket, key = "files", "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/471c37fa_5e4390c2.pdf"
        storage_endpoint = f"{config['storage_url']}/storage/v1/object/{bucket}/{key}"
        
        print(f"  Endpoint: {storage_endpoint}")
        
        async with httpx.AsyncClient(timeout=60, headers=headers) as client:
            response = await client.head(storage_endpoint)
            
            print(f"  Status Code: {response.status_code}")
            print(f"  Response Headers: {dict(response.headers)}")
            
            # Try to read response body even for HEAD request
            try:
                response_body = response.text
                print(f"  Response Body: {response_body}")
            except Exception as e:
                print(f"  Response Body Error: {e}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS - File exists")
            else:
                print(f"   ❌ FAILED - Status {response.status_code}")
                
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    print()
    
    # Test 2: GET request (what read_blob does)
    print("🧪 Test 2: GET request (read_blob method)")
    try:
        bucket, key = "files", "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/471c37fa_5e4390c2.pdf"
        storage_endpoint = f"{config['storage_url']}/storage/v1/object/{bucket}/{key}"
        
        print(f"  Endpoint: {storage_endpoint}")
        
        async with httpx.AsyncClient(timeout=60, headers=headers) as client:
            response = await client.get(storage_endpoint)
            
            print(f"  Status Code: {response.status_code}")
            print(f"  Response Headers: {dict(response.headers)}")
            print(f"  Content Length: {len(response.content) if response.content else 0}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS - File accessible")
                print(f"   Content preview: {response.content[:50]}...")
            else:
                print(f"   ❌ FAILED - Status {response.status_code}")
                try:
                    print(f"   Error response: {response.text}")
                except:
                    print(f"   Error response (bytes): {response.content[:200]}")
                
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    print()
    
    # Test 3: Test with a different file path that might work
    print("🧪 Test 3: Test with different file path")
    try:
        # Try the file path that worked in our local tests
        test_file_path_2 = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/c04117ab_5e4390c2.pdf"
        bucket, key = "files", "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/c04117ab_5e4390c2.pdf"
        storage_endpoint = f"{config['storage_url']}/storage/v1/object/{bucket}/{key}"
        
        print(f"  Endpoint: {storage_endpoint}")
        
        async with httpx.AsyncClient(timeout=60, headers=headers) as client:
            response = await client.head(storage_endpoint)
            
            print(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS - Alternative file exists")
            else:
                print(f"   ❌ FAILED - Status {response.status_code}")
                try:
                    print(f"   Error response: {response.text}")
                except:
                    print(f"   Error response (bytes): {response.content[:200]}")
                
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    print()
    
    # Test 4: Test URL encoding
    print("🧪 Test 4: Test URL encoding")
    try:
        # Check if the issue is with URL encoding
        import urllib.parse
        encoded_key = urllib.parse.quote(key, safe='/')
        storage_endpoint_encoded = f"{config['storage_url']}/storage/v1/object/{bucket}/{encoded_key}"
        
        print(f"  Original key: {key}")
        print(f"  Encoded key: {encoded_key}")
        print(f"  Encoded endpoint: {storage_endpoint_encoded}")
        
        async with httpx.AsyncClient(timeout=60, headers=headers) as client:
            response = await client.head(storage_endpoint_encoded)
            
            print(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS - URL encoding fixed it")
            else:
                print(f"   ❌ FAILED - Status {response.status_code}")
                try:
                    print(f"   Error response: {response.text}")
                except:
                    print(f"   Error response (bytes): {response.content[:200]}")
                
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    print()
    
    print("🔬 Render Storage Debug Complete")

if __name__ == "__main__":
    asyncio.run(test_render_storage_debug())
