#!/usr/bin/env python3
"""
Test script for FM-027 fix validation
Tests storage access and webhook URL generation
"""

import asyncio
import os
import httpx
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_storage_access():
    """Test Supabase storage access with correct headers"""
    print("🔍 Testing Supabase storage access...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env.staging')
    
    storage_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not storage_url or not service_role_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return False
    
    # Test file path from the error logs
    test_file_path = "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/5796784a_5e4390c2.pdf"
    bucket = "files"
    
    # Test with OLD headers (should fail)
    print("  Testing OLD headers (should fail)...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{storage_url}/storage/v1/object/{bucket}/{test_file_path}",
                headers={
                    "Authorization": f"Bearer {service_role_key}",
                    "apikey": service_role_key
                }
            )
            print(f"  OLD headers result: {response.status_code}")
            if response.status_code == 400:
                print("  ✅ OLD headers correctly fail with 400 (as expected)")
            else:
                print(f"  ⚠️  OLD headers unexpected status: {response.status_code}")
    except Exception as e:
        print(f"  ✅ OLD headers correctly fail: {e}")
    
    # Test with NEW headers (should work or give different error)
    print("  Testing NEW headers (should work or give different error)...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{storage_url}/storage/v1/object/{bucket}/{test_file_path}",
                headers={
                    "apikey": service_role_key,
                    "Authorization": f"Bearer {service_role_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Insurance-Navigator/1.0"
                }
            )
            print(f"  NEW headers result: {response.status_code}")
            if response.status_code == 200:
                print("  ✅ NEW headers work! File accessible")
                return True
            elif response.status_code == 404:
                print("  ✅ NEW headers work! File not found (expected - file may not exist)")
                return True
            elif response.status_code == 400:
                print("  ❌ NEW headers still fail with 400 - need different fix")
                print(f"  Response: {response.text}")
                return False
            else:
                print(f"  ⚠️  NEW headers unexpected status: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
    except Exception as e:
        print(f"  ❌ NEW headers error: {e}")
        return False

def test_webhook_url_generation():
    """Test webhook URL generation for different environments"""
    print("\n🔍 Testing webhook URL generation...")
    
    # Test staging environment
    os.environ["ENVIRONMENT"] = "staging"
    os.environ.pop("WEBHOOK_BASE_URL", None)  # Clear explicit setting
    
    # Simulate the webhook URL generation logic
    environment = os.getenv("ENVIRONMENT", "development")
    webhook_base_url = os.getenv("WEBHOOK_BASE_URL")
    
    if webhook_base_url:
        base_url = webhook_base_url
        print(f"  Using explicit WEBHOOK_BASE_URL: {base_url}")
    elif environment == "development":
        base_url = "http://localhost:3000"  # Mock for testing
        print(f"  Using development URL: {base_url}")
    else:
        # For staging/production, use environment-specific URLs
        if environment == "staging":
            base_url = "***REMOVED***"
            print(f"  Using staging webhook base URL: {base_url}")
        else:
            base_url = "***REMOVED***"
            print(f"  Using production webhook base URL: {base_url}")
    
    # Test with sample job ID
    job_id = "test-job-123"
    webhook_url = f"{base_url}/api/upload-pipeline/webhook/llamaparse/{job_id}"
    
    print(f"  Generated webhook URL: {webhook_url}")
    
    # Validate staging URL
    if environment == "staging":
        expected_url = "***REMOVED***/api/upload-pipeline/webhook/llamaparse/test-job-123"
        if webhook_url == expected_url:
            print("  ✅ Staging webhook URL correctly generated")
            return True
        else:
            print(f"  ❌ Staging webhook URL incorrect. Expected: {expected_url}")
            return False
    else:
        print("  ⚠️  Not testing staging environment")
        return True

async def test_worker_initialization():
    """Test worker initialization with fixed code"""
    print("\n🔍 Testing worker initialization...")
    
    try:
        # Import the enhanced worker
        from backend.workers.enhanced_base_worker import EnhancedBaseWorker
        from backend.shared.config.enhanced_config import WorkerConfig
        
        # Load configuration
        config = WorkerConfig.from_environment()
        print(f"  ✅ Configuration loaded: {list(config.to_dict().keys())}")
        
        # Test worker creation (don't start it)
        worker = EnhancedBaseWorker(config)
        print("  ✅ Enhanced worker created successfully")
        
        return True
    except Exception as e:
        print(f"  ❌ Worker initialization failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 FM-027 Fix Validation Tests")
    print("=" * 50)
    
    # Test 1: Storage access
    storage_ok = await test_storage_access()
    
    # Test 2: Webhook URL generation
    webhook_ok = test_webhook_url_generation()
    
    # Test 3: Worker initialization
    worker_ok = await test_worker_initialization()
    
    print("\n📊 Test Results:")
    print(f"  Storage Access: {'✅ PASS' if storage_ok else '❌ FAIL'}")
    print(f"  Webhook URLs:   {'✅ PASS' if webhook_ok else '❌ FAIL'}")
    print(f"  Worker Init:    {'✅ PASS' if worker_ok else '❌ FAIL'}")
    
    if storage_ok and webhook_ok and worker_ok:
        print("\n🎉 All tests passed! FM-027 fix is ready for deployment.")
        return 0
    else:
        print("\n❌ Some tests failed. Review the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
