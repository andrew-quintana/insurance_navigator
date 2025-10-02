#!/usr/bin/env python3
"""
Debug StorageManager blob_exists method
"""

import asyncio
import httpx
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from shared.storage.storage_manager import StorageManager

async def debug_storage_manager():
    """Debug the StorageManager blob_exists method"""
    
    print("🔍 Debugging StorageManager blob_exists method")
    print("=" * 60)
    
    # File that we know exists
    file_path = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/b8cfa47a_5e4390c2.pdf"
    
    print(f"Testing file: {file_path}")
    
    # Initialize StorageManager
    storage = StorageManager({
        "storage_url": "https://dfgzeastcxnoqshgyotp.supabase.co/storage/v1",
        "anon_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM",
        "service_role_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTY4MDQ4MywiZXhwIjoyMDY3MjU2NDgzfQ.yYQWEJkDtvFXg-F2Xe4mh9Xj_0QCp6gnXkDI6lEhDT8"
    })
    
    print(f"StorageManager initialized")
    print(f"Base URL: {storage.base_url}")
    print(f"Service role key: {storage.service_role_key[:20]}...")
    
    # Test path parsing
    print(f"\n1️⃣ TESTING PATH PARSING")
    print("-" * 40)
    
    try:
        bucket, key = storage._parse_storage_path(file_path)
        print(f"Parsed bucket: {bucket}")
        print(f"Parsed key: {key}")
    except Exception as e:
        print(f"❌ Path parsing failed: {str(e)}")
        return
    
    # Test URL construction
    print(f"\n2️⃣ TESTING URL CONSTRUCTION")
    print("-" * 40)
    
    storage_endpoint = f"{storage.base_url}/storage/v1/object/{bucket}/{key}"
    print(f"Storage endpoint: {storage_endpoint}")
    
    # Test direct HTTP request with StorageManager's client
    print(f"\n3️⃣ TESTING DIRECT HTTP WITH STORAGE MANAGER CLIENT")
    print("-" * 40)
    
    try:
        response = await storage.client.head(storage_endpoint)
        print(f"Status code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Success: {response.status_code == 200}")
        
        if response.status_code != 200:
            print(f"Response text: {response.text}")
    except Exception as e:
        print(f"❌ HTTP request failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test blob_exists method
    print(f"\n4️⃣ TESTING BLOB_EXISTS METHOD")
    print("-" * 40)
    
    try:
        exists = await storage.blob_exists(file_path)
        print(f"blob_exists result: {exists}")
    except Exception as e:
        print(f"❌ blob_exists failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Close the client
    await storage.close()

if __name__ == "__main__":
    asyncio.run(debug_storage_manager())
