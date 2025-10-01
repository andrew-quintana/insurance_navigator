#!/usr/bin/env python3
"""
FM-027 Bytes Fix Test
Test the new read_blob_bytes method for binary PDF files
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from backend.shared.storage.storage_manager import StorageManager
from backend.shared.logging.structured_logger import StructuredLogger

async def test_bytes_fix():
    """Test the read_blob_bytes method for PDF files"""
    load_dotenv('.env.staging')
    
    logger = StructuredLogger("test_fm027_bytes_fix")
    
    print("🔬 FM-027 Bytes Fix Test")
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
    print(f"  Service Role Key Present: {bool(config['service_role_key'])}")
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
    
    # Test 2: Read blob as bytes (this is the new method)
    print("🧪 Test 2: read_blob_bytes() - New method for binary files")
    try:
        content_bytes = await storage.read_blob_bytes(test_file_path)
        if content_bytes:
            print(f"   Result: {len(content_bytes)} bytes read")
            print(f"   Preview (first 50 bytes): {content_bytes[:50]}")
            print(f"   Is bytes: {isinstance(content_bytes, bytes)}")
            print("   ✅ SUCCESS - Binary content read")
        else:
            print("   ❌ FAILED - No content")
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    
    print()
    
    # Test 3: Compare with old method (should fail or be corrupted)
    print("🧪 Test 3: read_blob() - Old method for comparison")
    try:
        content_text = await storage.read_blob(test_file_path)
        if content_text:
            print(f"   Result: {len(content_text)} characters read")
            print(f"   Preview (first 100 chars): {content_text[:100]}")
            print(f"   Is string: {isinstance(content_text, str)}")
            print("   ⚠️  WARNING - This method works but may corrupt binary data")
        else:
            print("   ❌ FAILED - No content")
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    
    print()
    
    # Test 4: Verify PDF header
    print("🧪 Test 4: Verify PDF header in bytes")
    try:
        content_bytes = await storage.read_blob_bytes(test_file_path)
        if content_bytes and content_bytes.startswith(b'%PDF'):
            print(f"   Result: Valid PDF header detected")
            print(f"   Header: {content_bytes[:10]}")
            print("   ✅ SUCCESS - Valid PDF file")
        else:
            print("   ❌ FAILED - Invalid PDF header")
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        print(f"   Exception type: {type(e).__name__}")
    
    # Close the storage manager
    await storage.close()
    
    print()
    print("🔬 Test Complete")

if __name__ == "__main__":
    asyncio.run(test_bytes_fix())
