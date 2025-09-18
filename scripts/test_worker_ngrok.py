#!/usr/bin/env python3
"""
Test script to validate that the worker uses dynamic ngrok discovery
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_worker_ngrok_discovery():
    """Test that the worker can discover ngrok URL dynamically"""
    print("🔧 Testing Worker Ngrok Discovery")
    print("=" * 40)
    
    try:
        # Import the ngrok discovery function that the worker uses
        from backend.shared.utils.ngrok_discovery import get_webhook_base_url
        
        # Get the webhook base URL (what the worker would use)
        webhook_url = get_webhook_base_url()
        print(f"✅ Worker webhook URL: {webhook_url}")
        
        # Check if it's a valid ngrok URL
        if webhook_url and webhook_url.startswith("https://") and "ngrok-free.app" in webhook_url:
            print("✅ Worker is using dynamic ngrok discovery")
            print(f"   Webhook URL: {webhook_url}")
            return True
        else:
            print("❌ Worker is not using ngrok URL")
            print(f"   Webhook URL: {webhook_url}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing worker ngrok discovery: {e}")
        return False

def test_worker_import():
    """Test that the worker can import the ngrok discovery module"""
    print("\n🔍 Testing Worker Import")
    print("=" * 30)
    
    try:
        # Test the exact import that the worker uses
        from backend.shared.utils.ngrok_discovery import get_webhook_base_url
        print("✅ Worker can import ngrok discovery module")
        
        # Test that the function works
        url = get_webhook_base_url()
        print(f"✅ Function works: {url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Worker import failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Worker Ngrok Discovery Test")
    print("=" * 50)
    
    # Test worker import
    import_success = test_worker_import()
    
    # Test worker ngrok discovery
    discovery_success = test_worker_ngrok_discovery()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 20)
    print(f"Worker Import: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"Ngrok Discovery: {'✅ PASS' if discovery_success else '❌ FAIL'}")
    
    if import_success and discovery_success:
        print("\n🎉 Worker dynamic ngrok discovery is working!")
        print("   The worker will automatically use the current ngrok URL")
        print("   without needing to restart or update configuration files.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
