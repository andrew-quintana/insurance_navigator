#!/usr/bin/env python3
"""
Simple endpoint test to verify basic functionality
"""

import requests
import json

BASE_URL = "***REMOVED***"

def test_basic_endpoints():
    """Test just the core working endpoints"""
    
    print("🧪 Testing Basic Working Endpoints")
    print("=" * 50)
    
    # Test health check
    print("1. Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health: {data.get('status')} - {data.get('services')}")
        else:
            print(f"   ❌ Health failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health error: {e}")
    
    # Test registration/login flow
    print("\n2. Authentication...")
    try:
        # Try registration
        reg_data = {
            "email": "quicktest@example.com",
            "password": "testpass123",
            "full_name": "Quick Test"
        }
        
        response = requests.post(f"{BASE_URL}/register", json=reg_data, timeout=15)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"   ✅ Registration successful: {token[:20]}...")
        elif response.status_code == 400:
            # User exists, try login
            login_data = {"email": reg_data["email"], "password": reg_data["password"]}
            response = requests.post(f"{BASE_URL}/login", json=login_data, timeout=15)
            if response.status_code == 200:
                token = response.json().get("access_token")
                print(f"   ✅ Login successful: {token[:20]}...")
            else:
                print(f"   ❌ Login failed: {response.status_code}")
                return
        else:
            print(f"   ❌ Auth failed: {response.status_code}")
            return
            
        # Test authenticated endpoint
        print("\n3. Authenticated Access...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/me", headers=headers, timeout=10)
        if response.status_code == 200:
            user = response.json()
            print(f"   ✅ User info: {user.get('email')}")
        else:
            print(f"   ❌ Auth check failed: {response.status_code}")
            
        # Test simple chat (this should tell us if the fix worked)
        print("\n4. Simple Chat Test...")
        chat_data = {
            "message": "Hello, can you help me?",
            "context": {"test": True}
        }
        response = requests.post(f"{BASE_URL}/chat", json=chat_data, headers=headers, timeout=20)
        if response.status_code == 200:
            chat_resp = response.json()
            print(f"   ✅ Chat working: {len(chat_resp.get('text', ''))} chars response")
        else:
            print(f"   ❌ Chat failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Auth test error: {e}")

if __name__ == "__main__":
    test_basic_endpoints() 