#!/usr/bin/env python3
"""
Test script to capture the actual error response from Supabase.
"""

import asyncio
import os
import sys
import httpx
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath('.'))

async def test_supabase_error_response():
    """Test to capture the actual error response from Supabase"""
    load_dotenv('.env.staging')
    
    print("🔬 Supabase Error Response Test")
    print("=" * 60)
    
    # Use the same configuration as Render
    config = {
        "storage_url": os.getenv("SUPABASE_URL"),
        "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    }
    
    headers = {
        "apikey": config['service_role_key'],
        "Authorization": f"Bearer {config['service_role_key']}"
    }
    
    # Test with a file that doesn't exist to see the error response
    test_file_path = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/nonexistent_file.pdf"
    
    print(f"Testing with nonexistent file: {test_file_path}")
    print()
    
    try:
        bucket, key = "files", "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/nonexistent_file.pdf"
        storage_endpoint = f"{config['storage_url']}/storage/v1/object/{bucket}/{key}"
        
        print(f"Endpoint: {storage_endpoint}")
        print()
        
        async with httpx.AsyncClient(timeout=60, headers=headers) as client:
            # Test HEAD request
            print("🧪 Test 1: HEAD request (should fail)")
            try:
                response = await client.head(storage_endpoint)
                print(f"  Status Code: {response.status_code}")
                print(f"  Response Headers: {dict(response.headers)}")
                
                # Try to read response body
                try:
                    response_body = response.text
                    print(f"  Response Body: {response_body}")
                except Exception as e:
                    print(f"  Response Body Error: {e}")
                    # Try to read as bytes
                    try:
                        response_bytes = response.content
                        print(f"  Response Bytes: {response_bytes}")
                    except Exception as e2:
                        print(f"  Response Bytes Error: {e2}")
                
            except Exception as e:
                print(f"  💥 EXCEPTION: {e}")
                print(f"  Exception type: {type(e).__name__}")
            
            print()
            
            # Test GET request
            print("🧪 Test 2: GET request (should fail)")
            try:
                response = await client.get(storage_endpoint)
                print(f"  Status Code: {response.status_code}")
                print(f"  Response Headers: {dict(response.headers)}")
                
                # Try to read response body
                try:
                    response_body = response.text
                    print(f"  Response Body: {response_body}")
                except Exception as e:
                    print(f"  Response Body Error: {e}")
                    # Try to read as bytes
                    try:
                        response_bytes = response.content
                        print(f"  Response Bytes: {response_bytes}")
                    except Exception as e2:
                        print(f"  Response Bytes Error: {e2}")
                
            except Exception as e:
                print(f"  💥 EXCEPTION: {e}")
                print(f"  Exception type: {type(e).__name__}")
            
            print()
            
            # Test with the actual file that's failing on Render
            print("🧪 Test 3: Test with the actual failing file")
            test_file_path_2 = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/471c37fa_5e4390c2.pdf"
            bucket2, key2 = "files", "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/471c37fa_5e4390c2.pdf"
            storage_endpoint_2 = f"{config['storage_url']}/storage/v1/object/{bucket2}/{key2}"
            
            print(f"  Endpoint: {storage_endpoint_2}")
            
            try:
                response = await client.head(storage_endpoint_2)
                print(f"  Status Code: {response.status_code}")
                print(f"  Response Headers: {dict(response.headers)}")
                
                if response.status_code != 200:
                    # Try to read response body
                    try:
                        response_body = response.text
                        print(f"  Response Body: {response_body}")
                    except Exception as e:
                        print(f"  Response Body Error: {e}")
                        # Try to read as bytes
                        try:
                            response_bytes = response.content
                            print(f"  Response Bytes: {response_bytes}")
                        except Exception as e2:
                            print(f"  Response Bytes Error: {e2}")
                else:
                    print("  ✅ SUCCESS - File exists")
                
            except Exception as e:
                print(f"  💥 EXCEPTION: {e}")
                print(f"  Exception type: {type(e).__name__}")
            
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        print(f"Exception type: {type(e).__name__}")
    
    print()
    print("🔬 Supabase Error Response Test Complete")

if __name__ == "__main__":
    asyncio.run(test_supabase_error_response())
