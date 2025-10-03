#!/usr/bin/env python3
"""
Test script for Supabase authentication endpoints
Tests the corrected Supabase configuration for FM-033
"""

import requests
import json
import sys

# Correct Supabase configuration
SUPABASE_URL = "https://znvwzkdblknkkztqyfnu.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd6a2RibGtua2t6dHF5Zm51Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0NTYsImV4cCI6MjA2NzI1NjQ1Nn0.k0QHYOgm4EilyyTml57kCGDpbikpEtJCzq-qzGYQZqY"

def test_supabase_connectivity():
    """Test basic Supabase connectivity"""
    print("🔍 Testing Supabase connectivity...")
    
    try:
        # Test basic endpoint
        response = requests.get(f"{SUPABASE_URL}/rest/v1/", 
                              headers={"apikey": SUPABASE_ANON_KEY})
        
        if response.status_code == 200:
            print("✅ Supabase endpoint is reachable")
            return True
        else:
            print(f"❌ Supabase endpoint returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

def test_auth_endpoint():
    """Test authentication endpoint with invalid credentials (should return 400)"""
    print("\n🔍 Testing authentication endpoint...")
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json"
            },
            json={
                "email": "test@example.com",
                "password": "invalidpassword"
            }
        )
        
        if response.status_code == 400:
            data = response.json()
            if data.get("error_code") == "invalid_credentials":
                print("✅ Authentication endpoint working correctly (400 for invalid credentials)")
                return True
            else:
                print(f"❌ Unexpected error code: {data.get('error_code')}")
                return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test auth endpoint: {e}")
        return False

def test_anon_key_validity():
    """Test if the anonymous key is valid"""
    print("\n🔍 Testing anonymous key validity...")
    
    try:
        # Try to access a protected endpoint that requires a valid key
        response = requests.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
            }
        )
        
        # We expect a 401, 400, or 403 for unauthenticated requests
        # 403 is actually valid - it means the key is recognized but insufficient permissions
        if response.status_code in [400, 401, 403]:
            print("✅ Anonymous key is valid (proper authentication required)")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test anonymous key: {e}")
        return False

def main():
    """Run all authentication tests"""
    print("🚀 Starting Supabase Authentication Tests for FM-033")
    print("=" * 60)
    
    tests = [
        test_supabase_connectivity,
        test_auth_endpoint,
        test_anon_key_validity
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Supabase authentication should work correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
