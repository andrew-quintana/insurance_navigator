#!/usr/bin/env python3
"""
Phase 3 Upload Pipeline Test
Test the current deployed API with document upload
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# Configuration
API_BASE_URL = "***REMOVED***"
FRONTEND_URL = "https://insurancenavigator.vercel.app"

async def test_upload_pipeline():
    """Test the upload pipeline with the deployed API"""
    print("🚀 Phase 3 Upload Pipeline Test")
    print("=" * 50)
    
    # Test files
    test_files = [
        "examples/simulated_insurance_document.pdf",
        "examples/scan_classic_hmo.pdf"
    ]
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Test API health
        print("\n1. Testing API Health...")
        try:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API Health: {health_data['status']}")
                print(f"   Services: {health_data.get('services', {})}")
            else:
                print(f"❌ API Health failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API Health error: {e}")
            return False
        
        # 2. Test authentication
        print("\n2. Testing Authentication...")
        try:
            # Try to register a test user
            auth_data = {
                "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
                "password": "TestPassword123!",
                "name": "Test User"
            }
            
            response = await client.post(f"{API_BASE_URL}/register", json=auth_data)
            if response.status_code == 200:
                auth_result = response.json()
                print(f"✅ User registered: {auth_result.get('user', {}).get('email')}")
                token = auth_result.get('access_token')
                headers = {"Authorization": f"Bearer {token}"}
            else:
                print(f"⚠️  Registration failed: {response.status_code} - {response.text}")
                # Try login instead
                login_data = {
                    "email": "test@example.com",
                    "password": "TestPassword123!"
                }
                response = await client.post(f"{API_BASE_URL}/login", json=login_data)
                if response.status_code == 200:
                    auth_result = response.json()
                    print(f"✅ User logged in: {auth_result.get('user', {}).get('email')}")
                    token = auth_result.get('access_token')
                    headers = {"Authorization": f"Bearer {token}"}
                else:
                    print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
        
        # 3. Test document upload
        print("\n3. Testing Document Upload...")
        for file_path in test_files:
            if not os.path.exists(file_path):
                print(f"⚠️  Test file not found: {file_path}")
                continue
                
            print(f"\n📤 Uploading {file_path}...")
            try:
                with open(file_path, 'rb') as f:
                    files = {
                        'file': (os.path.basename(file_path), f, 'application/pdf')
                    }
                    data = {
                        'policy_id': f"test_policy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    }
                    
                    response = await client.post(
                        f"{API_BASE_URL}/upload-document-backend",
                        files=files,
                        data=data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"✅ Upload successful: {file_path}")
                        print(f"   Response: {json.dumps(result, indent=2)}")
                        results.append({
                            "file": file_path,
                            "status": "success",
                            "response": result
                        })
                    else:
                        print(f"❌ Upload failed: {response.status_code}")
                        print(f"   Error: {response.text}")
                        results.append({
                            "file": file_path,
                            "status": "failed",
                            "error": response.text
                        })
                        
            except Exception as e:
                print(f"❌ Upload error: {e}")
                results.append({
                    "file": file_path,
                    "status": "error",
                    "error": str(e)
                })
        
        # 4. Test frontend accessibility
        print("\n4. Testing Frontend...")
        try:
            response = await client.get(FRONTEND_URL)
            if response.status_code == 200:
                print(f"✅ Frontend accessible: {FRONTEND_URL}")
            else:
                print(f"❌ Frontend error: {response.status_code}")
        except Exception as e:
            print(f"❌ Frontend error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    successful_uploads = [r for r in results if r['status'] == 'success']
    failed_uploads = [r for r in results if r['status'] in ['failed', 'error']]
    
    print(f"✅ Successful uploads: {len(successful_uploads)}")
    print(f"❌ Failed uploads: {len(failed_uploads)}")
    
    if successful_uploads:
        print("\n🎉 Upload pipeline is working!")
        print("You can now check the logs to see the processing status.")
    else:
        print("\n⚠️  No successful uploads. Check the errors above.")
    
    return len(successful_uploads) > 0

if __name__ == "__main__":
    success = asyncio.run(test_upload_pipeline())
    exit(0 if success else 1)
