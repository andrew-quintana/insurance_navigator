#!/usr/bin/env python3
"""
Test script to verify the blob_exists GET fix works correctly.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath('.'))

from backend.shared.storage.storage_manager import StorageManager
from backend.shared.logging.structured_logger import StructuredLogger

async def test_blob_exists_get_fix():
    """Test the updated blob_exists method with GET requests"""
    load_dotenv('.env.staging')
    
    logger = StructuredLogger("test_blob_exists_get_fix")
    
    print("🔬 Blob Exists GET Fix Test")
    print("=" * 60)
    
    config = {
        "storage_url": os.getenv("SUPABASE_URL"),
        "anon_key": os.getenv("SUPABASE_ANON_KEY"),
        "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        "timeout": 60
    }
    
    print(f"Configuration:")
    print(f"  Storage URL: {config['storage_url']}")
    print(f"  Service Role Key Present: {bool(config['service_role_key'])}")
    print()
    
    storage = StorageManager(config)
    
    # Test 1: File that exists
    test_file_path_1 = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/471c37fa_5e4390c2.pdf"
    
    print(f"🧪 Test 1: File that exists - {test_file_path_1}")
    try:
        exists = await storage.blob_exists(test_file_path_1)
        print(f"   Result: {exists}")
        if exists:
            print("   ✅ SUCCESS - File exists")
        else:
            print("   ❌ FAILED - File does not exist")
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    print()
    
    # Test 2: File that doesn't exist
    test_file_path_2 = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/nonexistent_file.pdf"
    
    print(f"🧪 Test 2: File that doesn't exist - {test_file_path_2}")
    try:
        exists = await storage.blob_exists(test_file_path_2)
        print(f"   Result: {exists}")
        if not exists:
            print("   ✅ SUCCESS - File correctly identified as not existing")
        else:
            print("   ❌ FAILED - File incorrectly identified as existing")
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    print()
    
    # Test 3: File that was failing in our local tests
    test_file_path_3 = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/c04117ab_5e4390c2.pdf"
    
    print(f"🧪 Test 3: File that was failing locally - {test_file_path_3}")
    try:
        exists = await storage.blob_exists(test_file_path_3)
        print(f"   Result: {exists}")
        if not exists:
            print("   ✅ SUCCESS - File correctly identified as not existing")
        else:
            print("   ❌ FAILED - File incorrectly identified as existing")
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    print()
    
    await storage.close()
    print("🔬 Blob Exists GET Fix Test Complete")

if __name__ == "__main__":
    asyncio.run(test_blob_exists_get_fix())
