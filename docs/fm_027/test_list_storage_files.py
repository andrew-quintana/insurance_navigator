#!/usr/bin/env python3
"""
FM-027: List Files in Supabase Storage

This script lists all files in the Supabase Storage bucket to see what's actually there.
"""

import asyncio
import httpx
import os
import json
from datetime import datetime

async def list_storage_files():
    """List all files in the Supabase Storage bucket"""
    print("🔍 Listing files in Supabase Storage...")
    
    # Supabase configuration
    supabase_url = "https://dfgzeastcxnoqshgyotp.supabase.co"
    supabase_storage_url = f"{supabase_url}/storage/v1"
    service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTY4MDQ4MywiZXhwIjoyMDY3MjU2NDgzfQ.yYQWEJkDtvFXg-F2Xe4mh9Xj_0QCp6gnXkDI6lEhDT8"
    
    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "apikey": service_role_key,
        "Content-Type": "application/json"
    }
    
    # List files in the 'files' bucket
    bucket_name = "files"
    list_url = f"{supabase_storage_url}/object/list/{bucket_name}"
    
    print(f"🔍 Listing bucket: {bucket_name}")
    print(f"🌐 URL: {list_url}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # List root directory
            response = await client.post(list_url, headers=headers, json={"prefix": "", "limit": 1000})
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                files = response.json()  # Response is directly a list
                
                print(f"✅ Found {len(files)} items in bucket '{bucket_name}'")
                print("=" * 60)
                
                if files:
                    for i, file_info in enumerate(files, 1):
                        print(f"{i:3d}. Raw data: {file_info}")
                        print(f"     Type: {type(file_info)}")
                        if isinstance(file_info, dict):
                            for key, value in file_info.items():
                                print(f"     {key}: {value}")
                        print()
                        
                        # If it's a directory, list its contents
                        if isinstance(file_info, dict) and file_info.get("name"):
                            dir_name = file_info["name"]
                            print(f"     🔍 Listing contents of directory '{dir_name}':")
                            try:
                                dir_response = await client.post(list_url, headers=headers, json={"prefix": dir_name, "limit": 1000})
                                if dir_response.status_code == 200:
                                    dir_files = dir_response.json()
                                    print(f"     📁 Found {len(dir_files)} items in '{dir_name}':")
                                    for j, dir_file in enumerate(dir_files, 1):
                                        print(f"         {j:3d}. {dir_file}")
                                        
                                        # If it's another directory, list its contents too
                                        if isinstance(dir_file, dict) and dir_file.get("name"):
                                            subdir_name = f"{dir_name}/{dir_file['name']}"
                                            print(f"         🔍 Listing contents of subdirectory '{subdir_name}':")
                                            try:
                                                subdir_response = await client.post(list_url, headers=headers, json={"prefix": subdir_name, "limit": 1000})
                                                if subdir_response.status_code == 200:
                                                    subdir_files = subdir_response.json()
                                                    print(f"         📁 Found {len(subdir_files)} items in '{subdir_name}':")
                                                    for k, subdir_file in enumerate(subdir_files, 1):
                                                        print(f"             {k:3d}. {subdir_file}")
                                                        
                                                        # If it's another directory, list its contents too (3 levels deep)
                                                        if isinstance(subdir_file, dict) and subdir_file.get("name"):
                                                            subsubdir_name = f"{subdir_name}/{subdir_file['name']}"
                                                            print(f"             🔍 Listing contents of sub-subdirectory '{subsubdir_name}':")
                                                            try:
                                                                subsubdir_response = await client.post(list_url, headers=headers, json={"prefix": subsubdir_name, "limit": 1000})
                                                                if subsubdir_response.status_code == 200:
                                                                    subsubdir_files = subsubdir_response.json()
                                                                    print(f"             📁 Found {len(subsubdir_files)} items in '{subsubdir_name}':")
                                                                    for l, subsubdir_file in enumerate(subsubdir_files, 1):
                                                                        print(f"                 {l:3d}. {subsubdir_file}")
                                                                else:
                                                                    print(f"             ❌ Failed to list sub-subdirectory '{subsubdir_name}': {subsubdir_response.status_code}")
                                                            except Exception as e:
                                                                print(f"             💥 Error listing sub-subdirectory '{subsubdir_name}': {str(e)}")
                                                            print()
                                                else:
                                                    print(f"         ❌ Failed to list subdirectory '{subdir_name}': {subdir_response.status_code}")
                                            except Exception as e:
                                                print(f"         💥 Error listing subdirectory '{subdir_name}': {str(e)}")
                                            print()
                                else:
                                    print(f"     ❌ Failed to list directory '{dir_name}': {dir_response.status_code}")
                            except Exception as e:
                                print(f"     💥 Error listing directory '{dir_name}': {str(e)}")
                            print()
                else:
                    print("❌ No files found in the bucket!")
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"storage_files_list_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump({
                        "bucket": bucket_name,
                        "timestamp": datetime.now().isoformat(),
                        "file_count": len(files),
                        "files": files
                    }, f, indent=2)
                
                print(f"💾 Results saved to: {filename}")
                
            else:
                print(f"❌ Failed to list files - Status: {response.status_code}")
                print(f"📝 Response: {response.text}")
                
    except Exception as e:
        print(f"💥 Error listing files: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function"""
    print("🚀 FM-027: List Files in Supabase Storage")
    print("=" * 60)
    
    await list_storage_files()

if __name__ == "__main__":
    asyncio.run(main())
