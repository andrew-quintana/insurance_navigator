#!/usr/bin/env python3
"""
Compare StorageManager vs direct HTTP access
"""

import asyncio
import httpx
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from shared.storage.storage_manager import StorageManager

async def test_both_approaches():
    """Test both StorageManager and direct HTTP access"""
    
    print("🔍 Testing StorageManager vs Direct HTTP Access")
    print("=" * 60)
    
    # File that we know exists
    file_path = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/b8cfa47a_5e4390c2.pdf"
    
    print(f"Testing file: {file_path}")
    
    # Test 1: Direct HTTP access (we know this works)
    print(f"\n1️⃣ DIRECT HTTP ACCESS")
    print("-" * 40)
    
    supabase_url = "https://dfgzeastcxnoqshgyotp.supabase.co"
    supabase_storage_url = f"{supabase_url}/storage/v1"
    service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTY4MDQ4MywiZXhwIjoyMDY3MjU2NDgzfQ.yYQWEJkDtvFXg-F2Xe4mh9Xj_0QCp6gnXkDI6lEhDT8"
    
    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "apikey": service_role_key,
        "Content-Type": "application/json"
    }
    
    try:
        # Parse path
        if file_path.startswith('files/'):
            bucket = 'files'
            key = file_path[6:]  # Remove 'files/' prefix
        else:
            raise Exception(f"Invalid file path format: {file_path}")
        
        print(f"Parsed - Bucket: {bucket}, Key: {key}")
        
        # Direct HTTP request
        url = f"{supabase_storage_url}/object/{bucket}/{key}"
        print(f"URL: {url}")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.head(url, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Success: {response.status_code == 200}")
    except Exception as e:
        print(f"❌ Direct HTTP failed: {str(e)}")
    
    # Test 2: StorageManager
    print(f"\n2️⃣ STORAGE MANAGER")
    print("-" * 40)
    
    try:
        storage = StorageManager({
            "storage_url": supabase_storage_url,
            "anon_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM",
            "service_role_key": service_role_key
        })
        
        print(f"StorageManager initialized")
        
        # Test blob_exists
        exists = await storage.blob_exists(file_path)
        print(f"blob_exists result: {exists}")
        
        if exists:
            # Test read_blob
            content = await storage.read_blob(file_path)
            print(f"read_blob successful - {len(content)} bytes")
        else:
            print("File does not exist according to StorageManager")
            
    except Exception as e:
        print(f"❌ StorageManager failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_both_approaches())
