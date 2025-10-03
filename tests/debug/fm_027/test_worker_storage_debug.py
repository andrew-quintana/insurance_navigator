#!/usr/bin/env python3
"""
FM-027: Worker Storage Debug Test
Debug the exact storage configuration the worker is using
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load staging environment
load_dotenv('.env.staging')

async def test_worker_storage_config():
    """Test the exact storage configuration the worker uses"""
    
    print("🔧 FM-027: Worker Storage Configuration Debug")
    print("=" * 60)
    
    # Get environment variables like the worker does
    supabase_url = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    print(f"SUPABASE_URL: {supabase_url}")
    print(f"SERVICE_ROLE_KEY: {service_role_key[:20]}..." if service_role_key else "SERVICE_ROLE_KEY: NOT SET")
    
    # Test the exact file from the worker logs
    file_path = "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/fd5b5f12_5e4390c2.pdf"
    
    print(f"\nTesting file: {file_path}")
    print(f"Full URL: {supabase_url}/storage/v1/object/files/{file_path}")
    
    async with httpx.AsyncClient() as client:
        # Test with the exact same configuration the worker uses
        response = await client.head(
            f"{supabase_url}/storage/v1/object/files/{file_path}",
            headers={
                "Authorization": f"Bearer {service_role_key}",
                "apikey": service_role_key
            }
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"Response Text: {response.text}")
            
            # Test with different URL patterns
            print("\nTesting alternative URL patterns:")
            
            # Test with https://dfgzeastcxnoqshgyotp.supabase.co directly
            direct_url = "https://dfgzeastcxnoqshgyotp.supabase.co"
            response2 = await client.head(
                f"{direct_url}/storage/v1/object/files/{file_path}",
                headers={
                    "Authorization": f"Bearer {service_role_key}",
                    "apikey": service_role_key
                }
            )
            
            print(f"Direct URL Status: {response2.status_code}")
            if response2.status_code == 200:
                print("✅ Direct URL works - worker might be using wrong base URL")
            else:
                print(f"❌ Direct URL also fails: {response2.text}")
        else:
            print("✅ Worker configuration works correctly")
    
    # Test StorageManager initialization like the worker does
    print("\n" + "=" * 60)
    print("Testing StorageManager initialization...")
    
    try:
        from backend.shared.storage.storage_manager import StorageManager
        
        # Use the same config the worker uses
        storage_config = {
            "storage_url": supabase_url,
            "service_role_key": service_role_key
        }
        
        print(f"StorageManager config: {storage_config}")
        
        storage_manager = StorageManager(storage_config)
        
        # Test blob_exists with the exact path
        full_path = f"files/{file_path}"
        print(f"Testing blob_exists with path: {full_path}")
        
        file_exists = await storage_manager.blob_exists(full_path)
        print(f"StorageManager blob_exists result: {file_exists}")
        
        if file_exists:
            print("✅ StorageManager works correctly")
        else:
            print("❌ StorageManager fails - this is the issue!")
            
            # Debug the StorageManager's actual request
            print("\nDebugging StorageManager request...")
            bucket, key = storage_manager._parse_storage_path(full_path)
            print(f"Parsed bucket: {bucket}")
            print(f"Parsed key: {key}")
            
            actual_endpoint = f"{supabase_url}/storage/v1/object/{bucket}/{key}"
            print(f"Actual endpoint: {actual_endpoint}")
            
            # Test the actual endpoint
            async with httpx.AsyncClient() as client:
                debug_response = await client.head(
                    actual_endpoint,
                    headers={
                        "Authorization": f"Bearer {service_role_key}",
                        "apikey": service_role_key
                    }
                )
                
                print(f"Debug endpoint status: {debug_response.status_code}")
                if debug_response.status_code != 200:
                    print(f"Debug endpoint response: {debug_response.text}")
        
        await storage_manager.close()
        
    except Exception as e:
        print(f"❌ StorageManager test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_worker_storage_config())
