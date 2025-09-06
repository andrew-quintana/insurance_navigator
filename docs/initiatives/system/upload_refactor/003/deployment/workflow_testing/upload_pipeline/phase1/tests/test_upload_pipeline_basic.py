#!/usr/bin/env python3
"""
Basic test for upload pipeline components
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(__file__))

def test_imports():
    """Test that all upload pipeline modules can be imported"""
    try:
        from api.upload_pipeline.main import app
        from api.upload_pipeline.config import get_config
        from api.upload_pipeline.database import get_database
        from api.upload_pipeline.auth import get_current_user
        from api.upload_pipeline.models import UploadRequest, UploadResponse
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config():
    """Test configuration loading"""
    try:
        from api.upload_pipeline.config import get_config
        config = get_config()
        print(f"✅ Config loaded: environment={config.environment}")
        print(f"   Supabase URL: {config.supabase_url}")
        print(f"   Max file size: {config.max_file_size_bytes}")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

async def test_database_connection():
    """Test database connection"""
    try:
        from api.upload_pipeline.database import get_database
        db = get_database()
        await db.initialize()
        
        # Test health check
        is_healthy = await db.health_check()
        if is_healthy:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database health check failed")
            return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints using requests"""
    try:
        import requests
        
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint working: {data['status']}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test upload endpoint
        response = requests.post(
            "http://localhost:8000/test/upload",
            json={"filename": "test.pdf"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test upload endpoint working: {data['status']}")
        else:
            print(f"❌ Test upload endpoint failed: {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Running upload pipeline basic tests...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Config Test", test_config),
        ("Database Test", test_database_connection),
        ("API Endpoints Test", test_api_endpoints),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Summary: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
