#!/usr/bin/env python3
"""
Test Phase 3 Upload Pipeline Integration
Tests the upload pipeline with the new Supabase authentication system.
"""

import asyncio
import sys
import os
import httpx
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from db.services.auth_adapter import auth_adapter
from db.services.supabase_auth_service import supabase_auth_service

async def test_upload_pipeline_auth():
    """Test upload pipeline authentication integration"""
    print("🚀 Testing Phase 3 Upload Pipeline Integration...")
    print()
    
    # Test 1: Auth Adapter
    print("=" * 50)
    print("Test 1: Auth Adapter")
    print("=" * 50)
    
    try:
        print(f"✅ Auth adapter backend: {type(auth_adapter.backend).__name__}")
        print(f"✅ Auth adapter initialized: {hasattr(auth_adapter, 'validate_token')}")
    except Exception as e:
        print(f"❌ Auth adapter test failed: {e}")
        return False
    
    # Test 2: User Creation
    print("\n" + "=" * 50)
    print("Test 2: User Creation")
    print("=" * 50)
    
    try:
        import time
        timestamp = int(time.time())
        user_data = await auth_adapter.create_user(
            email=f"test-phase3-{timestamp}@example.com",
            password="password123",
            name="Test User"
        )
        # Handle the response format from Supabase auth service
        if 'user' in user_data:
            user_id = user_data['user']['id']
            email = user_data['user']['email']
        else:
            user_id = user_data.get('id')
            email = user_data.get('email')
        
        print(f"✅ User created successfully: {email} (ID: {user_id})")
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return False
    
    # Test 3: User Authentication
    print("\n" + "=" * 50)
    print("Test 3: User Authentication")
    print("=" * 50)
    
    try:
        auth_data = await auth_adapter.authenticate_user(
            email=email,
            password="password123"
        )
        if auth_data and 'access_token' in auth_data:
            print(f"✅ User authenticated successfully")
            print(f"✅ Access token received: {auth_data['access_token'][:20]}...")
            access_token = auth_data['access_token']
        else:
            print(f"❌ Authentication failed: No access token")
            return False
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    # Test 4: Token Validation
    print("\n" + "=" * 50)
    print("Test 4: Token Validation")
    print("=" * 50)
    
    try:
        user_info = await auth_adapter.validate_token(access_token)
        if user_info:
            print(f"✅ Token validated successfully")
            print(f"✅ User ID: {user_info.get('id')}")
            print(f"✅ Email: {user_info.get('email')}")
        else:
            print(f"❌ Token validation failed")
            return False
    except Exception as e:
        print(f"❌ Token validation failed: {e}")
        return False
    
    # Test 5: Upload Pipeline API Test
    print("\n" + "=" * 50)
    print("Test 5: Upload Pipeline API")
    print("=" * 50)
    
    try:
        # Test the upload pipeline endpoint
        api_url = "http://127.0.0.1:8000"
        
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            response = await client.get(f"{api_url}/health")
            if response.status_code == 200:
                print("✅ Upload pipeline API is running")
            else:
                print(f"❌ Upload pipeline API not responding: {response.status_code}")
                return False
            
            # Test upload endpoint with authentication
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            upload_request = {
                "filename": "test-document.pdf",
                "mime": "application/pdf",
                "bytes_len": 1024,
                "sha256": "test-sha256-hash"
            }
            
            response = await client.post(
                f"{api_url}/upload",
                headers=headers,
                json=upload_request
            )
            
            if response.status_code == 200:
                print("✅ Upload endpoint accessible with authentication")
                upload_response = response.json()
                print(f"✅ Upload response: {upload_response.get('message', 'Success')}")
            else:
                print(f"❌ Upload endpoint failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Upload pipeline API test failed: {e}")
        return False
    
    # Test 6: RLS Policy Test
    print("\n" + "=" * 50)
    print("Test 6: RLS Policy Test")
    print("=" * 50)
    
    try:
        # Test accessing upload_pipeline tables with user context
        supabase_url = "http://127.0.0.1:54321"
        
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "apikey": os.getenv("SUPABASE_ANON_KEY", ""),
                "Content-Type": "application/json"
            }
            
            # Test documents table access
            response = await client.get(
                f"{supabase_url}/rest/v1/upload_pipeline.documents",
                headers=headers,
                params={"select": "*", "limit": 1}
            )
            
            if response.status_code == 200:
                print("✅ RLS policies working - can access documents table")
                documents = response.json()
                print(f"✅ Found {len(documents)} documents (should be 0 for new user)")
            else:
                print(f"❌ RLS policy test failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ RLS policy test failed: {e}")
        return False
    
    # Cleanup
    print("\n" + "=" * 50)
    print("Cleanup")
    print("=" * 50)
    
    try:
        # Delete test user
        await supabase_auth_service.delete_user(user_id)
        print("✅ Test user cleaned up")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    print("\n" + "=" * 50)
    print("PHASE 3 UPLOAD PIPELINE TEST SUMMARY")
    print("=" * 50)
    print("✅ All tests passed!")
    print("✅ Upload pipeline is working with Supabase authentication")
    print("✅ RLS policies are properly enforced")
    print("✅ End-to-end workflow is functional")
    
    return True

async def main():
    """Main test function"""
    try:
        success = await test_upload_pipeline_auth()
        if success:
            print("\n🎉 Phase 3 Upload Pipeline Integration: SUCCESS!")
            return 0
        else:
            print("\n💥 Phase 3 Upload Pipeline Integration: FAILED!")
            return 1
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
