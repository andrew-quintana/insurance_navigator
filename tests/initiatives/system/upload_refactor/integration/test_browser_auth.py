#!/usr/bin/env python3
"""
Test script to simulate the exact browser authentication flow
This helps identify where the "gray screen flash" issue occurs
"""

import requests
import json
import time
import threading
import concurrent.futures

BASE_URL = "http://localhost:8000"

def test_browser_auth_flow():
    """Test the complete browser authentication flow"""
    
    print("🧪 Testing Browser Authentication Flow")
    print("=" * 50)
    
    # Step 1: Register a new user (simulating registration form)
    print("\n📝 Step 1: Registration")
    register_data = {
        "email": f"browsertest_{int(time.time())}@example.com",
        "password": "testpass123",
        "name": "Browser Test User"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=register_data)
    print(f"Registration status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.text}")
        return
    
    token_data = response.json()
    access_token = token_data["access_token"]
    token_type = token_data["token_type"]
    
    print(f"✅ Registration successful")
    print(f"Token type: {token_type}")
    print(f"Token length: {len(access_token)}")
    
    # Step 2: Simulate what browser does - store in "localStorage"
    print(f"\n💾 Step 2: Storing tokens (simulating localStorage)")
    stored_token = access_token
    stored_token_type = token_type
    print(f"Stored token type: '{stored_token_type}'")
    
    # Step 3: Simulate immediate redirect to welcome page (/me check)
    print(f"\n🔍 Step 3: Welcome page auth check (immediate)")
    auth_header = f"{stored_token_type} {stored_token}"
    print(f"Authorization header: '{auth_header[:50]}...'")
    
    headers = {"Authorization": auth_header}
    
    # Make the /me request exactly like frontend does
    response = requests.get(f"{BASE_URL}/me", headers=headers)
    print(f"/me response status: {response.status_code}")
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ Auth successful - User: {user_data['name']}")
    else:
        print(f"❌ Auth failed: {response.text}")
        return
    
    # Step 4: Simulate login flow (for returning users)
    print(f"\n🔐 Step 4: Testing login flow")
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    print(f"Login status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    login_token_data = response.json()
    login_token = login_token_data["access_token"]
    login_token_type = login_token_data["token_type"]
    
    print(f"✅ Login successful")
    print(f"Login token type: {login_token_type}")
    
    # Step 5: Simulate immediate redirect to chat (potential gray screen area)
    print(f"\n💬 Step 5: Chat page auth check (potential gray screen)")
    
    # Simulate the exact frontend auth header construction
    auth_header = f"{login_token_type or 'Bearer'} {login_token}"
    print(f"Chat auth header: '{auth_header[:50]}...'")
    
    headers = {"Authorization": auth_header}
    response = requests.get(f"{BASE_URL}/me", headers=headers)
    print(f"Chat /me response status: {response.status_code}")
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ Chat auth successful - User: {user_data['name']}")
        
        # Step 6: Test actual chat message
        print(f"\n💭 Step 6: Sending chat message")
        chat_data = {"message": "What are Medicare benefits?"}
        headers["Content-Type"] = "application/json"
        
        response = requests.post(f"{BASE_URL}/chat", json=chat_data, headers=headers)
        print(f"Chat message status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Chat message successful")
        else:
            print(f"❌ Chat message failed: {response.text}")
            
    else:
        print(f"❌ Chat auth failed: {response.text}")
    
    print(f"\n🏁 Test Complete")

def test_concurrent_auth_requests():
    """Test for race conditions with multiple simultaneous auth requests"""
    print("\n🏃‍♂️ Testing Concurrent Authentication Requests")
    print("=" * 50)
    
    # First, get a valid token
    register_data = {
        "email": f"concurrent_{int(time.time())}@example.com",
        "password": "testpass123",
        "name": "Concurrent Test User"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=register_data)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.text}")
        return
    
    token_data = response.json()
    access_token = token_data["access_token"]
    token_type = token_data["token_type"]
    
    print(f"✅ Got token for concurrent testing")
    
    # Simulate multiple simultaneous /me requests (like React strict mode or multiple useEffect calls)
    def make_auth_request(request_id):
        headers = {"Authorization": f"{token_type} {access_token}"}
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/me", headers=headers)
        end_time = time.time()
        return {
            "id": request_id,
            "status": response.status_code,
            "time": end_time - start_time,
            "success": response.status_code == 200
        }
    
    # Make 5 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_auth_request, i) for i in range(5)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Analyze results
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    avg_time = sum(r["time"] for r in results) / len(results)
    
    print(f"📊 Concurrent request results:")
    print(f"   ✅ Successful: {successful}/5")
    print(f"   ❌ Failed: {failed}/5")
    print(f"   ⏱️ Average time: {avg_time:.3f}s")
    
    if failed > 0:
        print(f"⚠️ Some concurrent requests failed - potential race condition!")
        for r in results:
            if not r["success"]:
                print(f"   Request {r['id']}: Status {r['status']}")
    else:
        print(f"✅ All concurrent requests succeeded")

def test_rapid_login_redirect():
    """Test rapid login -> redirect scenario that might cause gray screen"""
    print("\n⚡ Testing Rapid Login -> Redirect Scenario")
    print("=" * 50)
    
    # Register user
    register_data = {
        "email": f"rapid_{int(time.time())}@example.com",
        "password": "testpass123",
        "name": "Rapid Test User"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=register_data)
    if response.status_code != 200:
        print(f"❌ Registration failed")
        return
    
    # Simulate rapid login -> immediate auth check (like browser redirect)
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    
    print("🔐 Step 1: Login")
    login_response = requests.post(f"{BASE_URL}/login", json=login_data)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"❌ Login failed")
        return
    
    token_data = login_response.json()
    
    # Immediately check auth (simulating instant redirect)
    print("⚡ Step 2: Immediate auth check (simulating redirect)")
    headers = {"Authorization": f"{token_data['token_type']} {token_data['access_token']}"}
    
    # Make request with minimal delay (simulating browser redirect)
    time.sleep(0.001)  # 1ms delay to simulate minimal browser processing
    auth_response = requests.get(f"{BASE_URL}/me", headers=headers)
    
    print(f"Immediate auth status: {auth_response.status_code}")
    
    if auth_response.status_code == 200:
        print("✅ Immediate auth successful - no gray screen issue")
    else:
        print(f"❌ Immediate auth failed - potential gray screen cause!")
        print(f"Response: {auth_response.text}")

if __name__ == "__main__":
    test_browser_auth_flow()
    test_concurrent_auth_requests()
    test_rapid_login_redirect() 