#!/usr/bin/env python3
"""
Test accessing the actual file that exists in storage
"""

import asyncio
import httpx
import os

async def test_actual_file_access():
    """Test accessing the actual file that exists"""
    
    # Supabase configuration
    supabase_url = "https://dfgzeastcxnoqshgyotp.supabase.co"
    supabase_storage_url = f"{supabase_url}/storage/v1"
    service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTY4MDQ4MywiZXhwIjoyMDY3MjU2NDgzfQ.yYQWEJkDtvFXg-F2Xe4mh9Xj_0QCp6gnXkDI6lEhDT8"
    
    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "apikey": service_role_key,
        "Content-Type": "application/json"
    }
    
    # Test the actual file that exists
    bucket = "files"
    key = "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/b8cfa47a_5e4390c2.pdf"
    
    print(f"Testing file access:")
    print(f"  Bucket: {bucket}")
    print(f"  Key: {key}")
    print(f"  Full URL: {supabase_storage_url}/object/{bucket}/{key}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Test HEAD request
            url = f"{supabase_storage_url}/object/{bucket}/{key}"
            print(f"\n1. Testing HEAD request to: {url}")
            
            response = await client.head(url, headers=headers)
            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("   ✅ File exists and is accessible!")
                
                # Test GET request
                print(f"\n2. Testing GET request...")
                get_response = await client.get(url, headers=headers)
                print(f"   Status: {get_response.status_code}")
                print(f"   Content length: {len(get_response.content) if get_response.content else 0}")
                
                if get_response.status_code == 200:
                    print("   ✅ File content downloaded successfully!")
                else:
                    print(f"   ❌ GET request failed: {get_response.text}")
            else:
                print(f"   ❌ HEAD request failed: {response.text}")
                
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_actual_file_access())
