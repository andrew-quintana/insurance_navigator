#!/usr/bin/env python3
"""
Test script to validate ngrok URL discovery functionality
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.shared.utils.ngrok_discovery import (
    get_ngrok_url,
    get_api_base_url,
    get_webhook_base_url,
    is_ngrok_available,
    get_ngrok_dashboard_url
)

def test_ngrok_discovery():
    """Test ngrok URL discovery functionality"""
    print("🔍 Testing Ngrok URL Discovery")
    print("=" * 40)
    
    # Test 1: Check if ngrok is available
    print("\n1. Checking ngrok availability...")
    available = is_ngrok_available()
    print(f"   Ngrok available: {'✅ Yes' if available else '❌ No'}")
    
    if not available:
        print("   ⚠️  Start ngrok with: ngrok http 8000")
        return False
    
    # Test 2: Get ngrok URL
    print("\n2. Getting ngrok URL...")
    ngrok_url = get_ngrok_url()
    if ngrok_url:
        print(f"   ✅ Ngrok URL: {ngrok_url}")
    else:
        print("   ❌ Failed to get ngrok URL")
        return False
    
    # Test 3: Get API base URL
    print("\n3. Getting API base URL...")
    api_url = get_api_base_url()
    print(f"   API Base URL: {api_url}")
    
    # Test 4: Get webhook base URL
    print("\n4. Getting webhook base URL...")
    webhook_url = get_webhook_base_url()
    print(f"   Webhook Base URL: {webhook_url}")
    
    # Test 5: Get dashboard URL
    print("\n5. Getting dashboard URL...")
    dashboard_url = get_ngrok_dashboard_url()
    print(f"   Dashboard URL: {dashboard_url}")
    
    # Test 6: Validate URLs
    print("\n6. Validating URLs...")
    if ngrok_url and ngrok_url.startswith("https://"):
        print("   ✅ Ngrok URL format is correct")
    else:
        print("   ❌ Ngrok URL format is incorrect")
        return False
    
    if api_url == ngrok_url:
        print("   ✅ API URL matches ngrok URL")
    else:
        print(f"   ⚠️  API URL ({api_url}) doesn't match ngrok URL ({ngrok_url})")
    
    if webhook_url == ngrok_url:
        print("   ✅ Webhook URL matches ngrok URL")
    else:
        print(f"   ⚠️  Webhook URL ({webhook_url}) doesn't match ngrok URL ({ngrok_url})")
    
    print("\n🎉 All tests completed!")
    return True

def test_worker_integration():
    """Test worker integration with ngrok discovery"""
    print("\n🔧 Testing Worker Integration")
    print("=" * 40)
    
    try:
        # Test importing the worker with ngrok discovery
        from backend.workers.enhanced_base_worker import EnhancedBaseWorker
        print("   ✅ Enhanced worker imports successfully")
        
        # Test that the worker can use ngrok discovery
        from backend.shared.utils.ngrok_discovery import get_webhook_base_url
        webhook_url = get_webhook_base_url()
        print(f"   ✅ Worker can get webhook URL: {webhook_url}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Worker integration failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Ngrok Discovery Test Suite")
    print("=" * 50)
    
    # Test ngrok discovery
    discovery_success = test_ngrok_discovery()
    
    # Test worker integration
    worker_success = test_worker_integration()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 20)
    print(f"Ngrok Discovery: {'✅ PASS' if discovery_success else '❌ FAIL'}")
    print(f"Worker Integration: {'✅ PASS' if worker_success else '❌ FAIL'}")
    
    if discovery_success and worker_success:
        print("\n🎉 All tests passed! Dynamic ngrok discovery is working.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
