#!/usr/bin/env python3
"""
FM-027 Fix Verification Test

This test verifies that the FM-027 fix works correctly by testing
the enhanced storage manager with multiple network paths.
"""

import asyncio
import httpx
import os
import time
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.staging')

# Import the fix
import sys
sys.path.append('/Users/aq_home/1Projects/accessa/insurance_navigator')
from backend.shared.storage.storage_manager_fm027_fix import FM027StorageManagerFix
from backend.monitoring.fm027_monitoring import FM027Monitor

async def test_fm027_fix():
    """Test the FM-027 fix implementation."""
    print("FM-027 Fix Verification Test")
    print("=" * 50)
    
    # Get environment variables
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase_url = os.getenv('SUPABASE_URL')
    test_file_path = 'files/user/8d65c725-ff38-4726-809e-018c05dfb874/raw/9966956e_222c3864.pdf'
    
    print(f"Testing file: {test_file_path}")
    print(f"Supabase URL: {supabase_url}")
    print(f"Service role key present: {bool(service_role_key)}")
    print()
    
    # Test 1: Basic functionality
    print("Test 1: Basic FM-027 Fix Functionality")
    print("-" * 40)
    
    fix = FM027StorageManagerFix(supabase_url, service_role_key, service_role_key)
    
    # Test blob_exists
    print("Testing blob_exists...")
    exists = await fix.blob_exists_with_fm027_fix(test_file_path)
    print(f"File exists: {exists}")
    
    if exists:
        print("✅ blob_exists test passed")
    else:
        print("❌ blob_exists test failed")
        return False
    
    # Test get_file
    print("\nTesting get_file...")
    content = await fix.get_file_with_fm027_fix(test_file_path)
    if content:
        print(f"✅ get_file test passed - {len(content)} bytes")
    else:
        print("❌ get_file test failed")
        return False
    
    # Test 2: Network path testing
    print("\nTest 2: Network Path Testing")
    print("-" * 40)
    
    # Test each network path individually
    for i, path_config in enumerate(fix.network_paths):
        print(f"Testing network path {i+1}: {path_config['user_agent']}")
        
        success, result = await fix._test_network_path(f"{supabase_url}/storage/v1/object/{test_file_path}", path_config)
        
        if success:
            print(f"  ✅ Success - {result['status_code']} - {result['response_time']:.3f}s - CF-Ray: {result['cf_ray']}")
        else:
            print(f"  ❌ Failed - {result['status_code']} - {result['error_message']}")
    
    # Test 3: Monitoring system
    print("\nTest 3: Monitoring System")
    print("-" * 40)
    
    monitor = FM027Monitor(supabase_url, service_role_key, test_file_path)
    
    # Run a few test cycles
    for i in range(5):
        print(f"Monitoring test {i+1}/5...")
        result = await monitor.test_storage_access()
        
        if result['success']:
            print(f"  ✅ Success - {result['status_code']} - {result['response_time']:.3f}s - CF-Ray: {result['cf_ray']}")
        else:
            print(f"  ❌ Failed - {result['status_code']} - {result.get('error', 'Unknown error')}")
        
        await asyncio.sleep(1)  # Wait 1 second between tests
    
    # Get health status
    health = monitor.get_health_status()
    print(f"\nHealth Status: {health['health_status']}")
    print(f"Success Rate: {health['success_rate']:.1f}%")
    print(f"Total Requests: {health['total_requests']}")
    print(f"Consecutive Failures: {health['consecutive_failures']}")
    
    # Test 4: Integration test
    print("\nTest 4: Integration Test")
    print("-" * 40)
    
    # Simulate the worker environment by testing with the exact same configuration
    print("Simulating worker environment...")
    
    worker_headers = {
        'apikey': service_role_key,
        'authorization': f'Bearer {service_role_key}',
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate',
        'connection': 'keep-alive',
        'user-agent': 'python-httpx/0.28.1'
    }
    
    url = f'{supabase_url}/storage/v1/object/{test_file_path}'
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=worker_headers)
            
            if response.status_code == 200:
                print(f"✅ Worker simulation successful - {response.status_code} - {len(response.content)} bytes")
                print(f"  CF-Ray: {response.headers.get('cf-ray', 'N/A')}")
                print(f"  Cache Status: {response.headers.get('cf-cache-status', 'N/A')}")
            else:
                print(f"❌ Worker simulation failed - {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Worker simulation exception - {e}")
        return False
    
    # Test 5: Performance test
    print("\nTest 5: Performance Test")
    print("-" * 40)
    
    start_time = time.time()
    success_count = 0
    total_tests = 10
    
    for i in range(total_tests):
        exists = await fix.blob_exists_with_fm027_fix(test_file_path)
        if exists:
            success_count += 1
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / total_tests
    
    print(f"Performance test results:")
    print(f"  Total tests: {total_tests}")
    print(f"  Successful: {success_count}")
    print(f"  Success rate: {success_count/total_tests*100:.1f}%")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Average time per test: {avg_time:.3f}s")
    
    if success_count == total_tests:
        print("✅ Performance test passed")
    else:
        print("❌ Performance test failed")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! FM-027 fix is working correctly.")
    print("=" * 50)
    
    return True

async def main():
    """Main test function."""
    try:
        success = await test_fm027_fix()
        if success:
            print("\n✅ FM-027 fix verification completed successfully")
            return 0
        else:
            print("\n❌ FM-027 fix verification failed")
            return 1
    except Exception as e:
        print(f"\n❌ FM-027 fix verification error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)