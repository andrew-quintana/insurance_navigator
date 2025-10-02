#!/usr/bin/env python3
"""
Test script to list files in the storage bucket to see what actually exists.
"""

import asyncio
import os
import sys
import httpx
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath('.'))

async def test_list_storage_files():
    """List files in the storage bucket to see what exists"""
    load_dotenv('.env.staging')
    
    print("🔬 List Storage Files Test")
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
    
    # List files in the specific directory
    bucket = "files"
    prefix = "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/"
    
    print(f"Listing files in bucket '{bucket}' with prefix '{prefix}'")
    print()
    
    try:
        # Use the Supabase Storage API to list files
        list_endpoint = f"{config['storage_url']}/storage/v1/object/list/{bucket}"
        
        params = {
            "prefix": prefix,
            "limit": 100
        }
        
        print(f"Endpoint: {list_endpoint}")
        print(f"Params: {params}")
        print()
        
        async with httpx.AsyncClient(timeout=60, headers=headers) as client:
            response = await client.post(list_endpoint, json=params)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print()
            
            if response.status_code == 200:
                files = response.json()
                print(f"Found {len(files)} files:")
                for file in files:
                    print(f"  - {file.get('name', 'unknown')}")
                    print(f"    Size: {file.get('metadata', {}).get('size', 'unknown')} bytes")
                    print(f"    Updated: {file.get('updated_at', 'unknown')}")
                    print()
            else:
                print(f"❌ FAILED - Status {response.status_code}")
                try:
                    error_response = response.json()
                    print(f"Error response: {json.dumps(error_response, indent=2)}")
                except:
                    print(f"Error response (text): {response.text}")
                
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        print(f"Exception type: {type(e).__name__}")
    
    print("🔬 List Storage Files Complete")

if __name__ == "__main__":
    asyncio.run(test_list_storage_files())