#!/usr/bin/env python3
"""
FM-027 Worker Storage Debug Test
Test the actual StorageManager behavior in a worker-like context
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from backend.shared.storage.storage_manager import StorageManager
from backend.shared.logging.structured_logger import StructuredLogger

async def test_worker_storage_behavior():
    """Test StorageManager behavior in worker context"""
    load_dotenv('.env.staging')
    
    logger = StructuredLogger("test_worker_storage")
    
    print("🔬 FM-027 Worker Storage Debug Test")
    print("=" * 60)
    
    # Initialize StorageManager with worker-like configuration
    config = {
        "storage_url": os.getenv("SUPABASE_URL"),
        "anon_key": os.getenv("SUPABASE_ANON_KEY"),
        "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        "timeout": 60
    }
    
    print(f"Configuration:")
    print(f"  Storage URL: {config['storage_url']}")
    print(f"  Anon Key Present: {bool(config['anon_key'])}")
    print(f"  Service Role Key Present: {bool(config['service_role_key'])}")
    print(f"  Service Role Key Length: {len(config['service_role_key']) if config['service_role_key'] else 0}")
    print()
    
    # Initialize StorageManager
    storage = StorageManager(config)
    
    # Test file path (same as used in worker)
    test_file_path = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/c04117ab_5e4390c2.pdf"
    
    print(f"Testing file path: {test_file_path}")
    print()
    
    # Test 1: Check if blob exists (this is what the worker does)
    print("🧪 Test 1: blob_exists() - This is what the worker calls")
    try:
        exists = await storage.blob_exists(test_file_path)
        print(f"   Result: {exists}")
        if exists:
            print("   ✅ SUCCESS - File exists")
        else:
            print("   ❌ FAILED - File does not exist")
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    
    print()
    
    # Test 2: Get blob metadata
    print("🧪 Test 2: get_blob_metadata() - Additional test")
    try:
        metadata = await storage.get_blob_metadata(test_file_path)
        print(f"   Result: {metadata}")
        if metadata:
            print("   ✅ SUCCESS - Metadata retrieved")
        else:
            print("   ❌ FAILED - No metadata")
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    
    print()
    
    # Test 3: Read blob content (small test)
    print("🧪 Test 3: read_blob() - Read first 100 bytes")
    try:
        content = await storage.read_blob(test_file_path)
        if content:
            print(f"   Result: {len(content)} bytes read")
            print(f"   Preview: {content[:100]}...")
            print("   ✅ SUCCESS - Content read")
        else:
            print("   ❌ FAILED - No content")
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    
    print()
    
    # Test 4: Check HTTP client headers
    print("🧪 Test 4: HTTP Client Headers")
    print(f"   Client headers: {dict(storage.client.headers)}")
    
    # Close the storage manager
    await storage.close()
    
    print()
    print("🔬 Test Complete")

if __name__ == "__main__":
    asyncio.run(test_worker_storage_behavior())