#!/usr/bin/env python3
"""
Test script to simulate the exact Render environment conditions.
"""

import asyncio
import os
import sys
import httpx
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath('.'))

async def test_render_environment_simulation():
    """Simulate the exact Render environment conditions"""
    load_dotenv('.env.staging')
    
    print("🔬 Render Environment Simulation Test")
    print("=" * 60)
    
    # Use the same configuration as Render
    config = {
        "storage_url": os.getenv("SUPABASE_URL"),
        "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    }
    
    # Test the exact same file that's failing on Render
    test_file_path = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/471c37fa_5e4390c2.pdf"
    
    print(f"Testing file path: {test_file_path}")
    print()
    
    # Simulate the exact HTTP client configuration from StorageManager
    headers = {
        "apikey": config['service_role_key'],
        "Authorization": f"Bearer {config['service_role_key']}"
    }
    
    # Test with the exact same timeout as Render
    timeout = httpx.Timeout(60)
    
    print(f"HTTP Headers:")
    for key, value in headers.items():
        print(f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}")
    print(f"Timeout: {timeout}")
    print()
    
    # Test 1: HEAD request with exact same configuration as Render
    print("🧪 Test 1: HEAD request (exact Render simulation)")
    try:
        bucket, key = "files", "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/471c37fa_5e4390c2.pdf"
        storage_endpoint = f"{config['storage_url']}/storage/v1/object/{bucket}/{key}"
        
        print(f"  Endpoint: {storage_endpoint}")
        
        # Use the exact same client configuration as StorageManager
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            response = await client.head(storage_endpoint)
            
            print(f"  Status Code: {response.status_code}")
            print(f"  Response Headers: {dict(response.headers)}")
            
            # Try to read response body
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
    
    # Test 2: Test with different User-Agent (simulate Render environment)
    print("🧪 Test 2: HEAD request with Render-like User-Agent")
    try:
        headers_with_ua = headers.copy()
        headers_with_ua["User-Agent"] = "python-httpx/0.28.1"
        
        print(f"  Headers with User-Agent: {headers_with_ua}")
        
        async with httpx.AsyncClient(timeout=timeout, headers=headers_with_ua) as client:
            response = await client.head(storage_endpoint)
            
            print(f"  Status Code: {response.status_code}")
            print(f"  Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS - File exists with User-Agent")
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
    
    # Test 3: Test with different Accept headers
    print("🧪 Test 3: HEAD request with different Accept headers")
    try:
        headers_with_accept = headers.copy()
        headers_with_accept["Accept"] = "*/*"
        headers_with_accept["Accept-Encoding"] = "gzip, deflate"
        headers_with_accept["Connection"] = "keep-alive"
        headers_with_accept["User-Agent"] = "python-httpx/0.28.1"
        
        print(f"  Headers with Accept: {headers_with_accept}")
        
        async with httpx.AsyncClient(timeout=timeout, headers=headers_with_accept) as client:
            response = await client.head(storage_endpoint)
            
            print(f"  Status Code: {response.status_code}")
            print(f"  Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS - File exists with Accept headers")
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
    
    # Test 4: Test with GET request to see if it's a HEAD-specific issue
    print("🧪 Test 4: GET request (to see if HEAD is the issue)")
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            response = await client.get(storage_endpoint)
            
            print(f"  Status Code: {response.status_code}")
            print(f"  Response Headers: {dict(response.headers)}")
            print(f"  Content Length: {len(response.content) if response.content else 0}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS - File accessible via GET")
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
    
    print("🔬 Render Environment Simulation Complete")

if __name__ == "__main__":
    asyncio.run(test_render_environment_simulation())
