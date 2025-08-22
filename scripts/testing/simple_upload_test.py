#!/usr/bin/env python3
"""
Simple Upload Test - Basic functionality test
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
JWT_TOKEN = "***REMOVED***.eyJzdWIiOiIxMjNlNDU2Ny1lODliLTEyZDMtYTQ1Ni00MjY2MTQxNzQwMDAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo1NDMyMSIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsInJvbGUiOiJ1c2VyIiwiaWF0IjoxNzU1ODk1MTEyLCJleHAiOjE3NTU5ODE1MTIsIm5iZiI6MTc1NTg5NTExMn0.YNSseeKTFuNqR8Apwot2_2MRcKlkVOBbDy3sV1HN3yU"

def test_upload():
    """Test basic upload functionality"""
    print("🚀 Testing Upload Endpoint")
    
    # Test data
    test_data = {
        "filename": "test_document.pdf",
        "bytes_len": 1000,
        "mime": "application/pdf",
        "sha256": "a" * 64,  # 64 character hash
        "ocr": False
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JWT_TOKEN}"
    }
    
    print(f"📤 POST to {API_BASE_URL}/api/v2/upload")
    print(f"📋 Data: {json.dumps(test_data, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/api/v2/upload",
            headers=headers,
            json=test_data,
            timeout=30
        )
        end_time = time.time()
        
        print(f"⏱️  Response time: {end_time - start_time:.3f}s")
        print(f"📊 HTTP Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Success! Response: {json.dumps(result, indent=2)}")
                return True
            except json.JSONDecodeError:
                print(f"⚠️  Success but invalid JSON: {response.text}")
                return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout after 30s")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 Connection error: {e}")
        return False
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Simple Upload Test")
    print("=" * 40)
    
    success = test_upload()
    
    if success:
        print("\n✅ Test completed successfully")
        exit(0)
    else:
        print("\n❌ Test failed")
        exit(1)
