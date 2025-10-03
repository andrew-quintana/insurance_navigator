#!/usr/bin/env python3
"""
Test script for Chat API authentication investigation (FM-034)
Tests the chat API endpoint authentication and token validation
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "https://insurance-navigator-staging-api.onrender.com"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat"
SUPABASE_URL = "https://znvwzkdblknkkztqyfnu.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd6a2RibGtua2t6dHF5Zm51Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0NTYsImV4cCI6MjA2NzI1NjQ1Nn0.k0QHYOgm4EilyyTml57kCGDpbikpEtJCzq-qzGYQZqY"

def test_api_connectivity():
    """Test basic API server connectivity"""
    print("🔍 Testing API server connectivity...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            print("✅ API server is reachable")
            return True
        else:
            print(f"❌ API server returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to API server: {e}")
        return False

def test_chat_endpoint_without_auth():
    """Test chat endpoint without authentication (should return 401)"""
    print("\n🔍 Testing chat endpoint without authentication...")
    
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json={"message": "test message"},
            timeout=10
        )
        
        if response.status_code == 401:
            print("✅ Chat endpoint correctly requires authentication (401)")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test chat endpoint: {e}")
        return False

def test_chat_endpoint_with_invalid_token():
    """Test chat endpoint with invalid token (should return 401)"""
    print("\n🔍 Testing chat endpoint with invalid token...")
    
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer invalid_token_12345"
            },
            json={"message": "test message"},
            timeout=10
        )
        
        if response.status_code == 401:
            print("✅ Chat endpoint correctly rejects invalid tokens (401)")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test chat endpoint with invalid token: {e}")
        return False

def test_chat_endpoint_with_supabase_anon_key():
    """Test chat endpoint with Supabase anonymous key"""
    print("\n🔍 Testing chat endpoint with Supabase anonymous key...")
    
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
            },
            json={"message": "test message"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("❌ Chat endpoint rejects Supabase anonymous key (401)")
            print("This suggests the API expects a different token format")
            return False
        elif response.status_code == 200:
            print("✅ Chat endpoint accepts Supabase anonymous key")
            return True
        else:
            print(f"❓ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test chat endpoint with Supabase key: {e}")
        return False

def test_supabase_auth_flow():
    """Test Supabase authentication flow to get valid user token"""
    print("\n🔍 Testing Supabase authentication flow...")
    
    try:
        # Test with invalid credentials first
        response = requests.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json"
            },
            json={
                "email": "test@example.com",
                "password": "invalidpassword"
            },
            timeout=10
        )
        
        if response.status_code == 400:
            data = response.json()
            if data.get("error_code") == "invalid_credentials":
                print("✅ Supabase authentication endpoint working correctly")
                print("Note: Would need valid credentials to get user token")
                return True
            else:
                print(f"❌ Unexpected Supabase error: {data}")
                return False
        else:
            print(f"❌ Unexpected Supabase status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test Supabase auth flow: {e}")
        return False

def test_api_cors_configuration():
    """Test API CORS configuration"""
    print("\n🔍 Testing API CORS configuration...")
    
    try:
        # Test preflight request
        response = requests.options(
            CHAT_ENDPOINT,
            headers={
                "Origin": "https://insurance-navigator-ui.vercel.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type"
            },
            timeout=10
        )
        
        print(f"CORS Preflight Status: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 204]:
            print("✅ CORS preflight request successful")
            return True
        else:
            print(f"❌ CORS preflight failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test CORS: {e}")
        return False

def main():
    """Run all chat API authentication tests"""
    print("🚀 Starting Chat API Authentication Tests for FM-034")
    print("=" * 70)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Chat Endpoint: {CHAT_ENDPOINT}")
    print(f"Supabase URL: {SUPABASE_URL}")
    print("=" * 70)
    
    tests = [
        test_api_connectivity,
        test_chat_endpoint_without_auth,
        test_chat_endpoint_with_invalid_token,
        test_chat_endpoint_with_supabase_anon_key,
        test_supabase_auth_flow,
        test_api_cors_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Chat API authentication should work correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        print("\n🔍 Key Findings:")
        print("- If API connectivity fails: Check API server status")
        print("- If 401 errors persist: Check authentication middleware")
        print("- If Supabase key rejected: Check token validation logic")
        print("- If CORS fails: Check CORS configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main())
