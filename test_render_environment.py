#!/usr/bin/env python3
"""
FM-027 Render Environment Test
Test the exact same configuration that would be used on Render
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from backend.shared.storage.storage_manager import StorageManager
from backend.shared.logging.structured_logger import StructuredLogger
from backend.workers.enhanced_base_worker import EnhancedBaseWorker
from backend.shared.config.worker_config import WorkerConfig

async def test_render_environment():
    """Test the exact worker environment configuration"""
    load_dotenv('.env.staging')
    
    logger = StructuredLogger("test_render_environment")
    
    print("🔬 FM-027 Render Environment Test")
    print("=" * 60)
    
    # Test 1: Check environment variables (same as worker)
    print("🧪 Test 1: Environment Variables")
    config = WorkerConfig.from_environment()
    
    print(f"  SUPABASE_URL: {config.supabase_url}")
    print(f"  SUPABASE_ANON_KEY present: {bool(config.supabase_anon_key)}")
    print(f"  SUPABASE_SERVICE_ROLE_KEY present: {bool(config.supabase_service_role_key)}")
    print(f"  Service Role Key Length: {len(config.supabase_service_role_key) if config.supabase_service_role_key else 0}")
    print()
    
    # Test 2: Initialize StorageManager with worker config
    print("🧪 Test 2: StorageManager with Worker Config")
    storage_config = {
        "storage_url": config.supabase_url,
        "anon_key": config.supabase_anon_key,
        "service_role_key": config.supabase_service_role_key,
        "timeout": 60
    }
    
    storage = StorageManager(storage_config)
    
    # Test file path
    test_file_path = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/c04117ab_5e4390c2.pdf"
    
    print(f"  Testing file path: {test_file_path}")
    
    try:
        exists = await storage.blob_exists(test_file_path)
        print(f"  Result: {exists}")
        if exists:
            print("  ✅ SUCCESS - File exists")
        else:
            print("  ❌ FAILED - File does not exist")
    except Exception as e:
        print(f"  💥 EXCEPTION: {e}")
        print(f"  Exception type: {type(e).__name__}")
    
    await storage.close()
    print()
    
    # Test 3: Check if worker can be initialized
    print("🧪 Test 3: Worker Initialization")
    try:
        # This would be the same as what happens on Render
        worker_config = WorkerConfig.from_environment()
        print(f"  Worker config loaded successfully")
        print(f"  Use mock storage: {worker_config.use_mock_storage}")
        print("  ✅ SUCCESS - Worker config loaded")
    except Exception as e:
        print(f"  💥 EXCEPTION: {e}")
        print(f"  Exception type: {type(e).__name__}")
    
    print()
    
    # Test 4: Check Python environment
    print("🧪 Test 4: Python Environment")
    print(f"  Python version: {sys.version}")
    print(f"  Platform: {sys.platform}")
    print(f"  Python executable: {sys.executable}")
    
    # Test 5: Check if httpx version is compatible
    try:
        import httpx
        print(f"  httpx version: {httpx.__version__}")
        print("  ✅ SUCCESS - httpx available")
    except Exception as e:
        print(f"  💥 EXCEPTION: {e}")
    
    print()
    print("🔬 Render Environment Test Complete")

if __name__ == "__main__":
    asyncio.run(test_render_environment())
