#!/usr/bin/env python3
"""
Phase 3 Current API Test
Tests the currently deployed API (v3.0.0) on Render.com
"""

import asyncio
import httpx
import json
import os
import time
import hashlib
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "https://insurance-navigator-api.onrender.com"
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class Phase3CurrentAPITester:
    """Test the currently deployed API (v3.0.0)"""
    
    def __init__(self):
        self.api_url = API_BASE_URL
        self.test_results = []
        
    def get_jwt_token(self) -> str:
        """Generate a test JWT token"""
        import jwt
        
        payload = {
            "sub": str(uuid4()),
            "email": "phase3-test@example.com",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "aud": "authenticated",
            "iss": SUPABASE_URL
        }
        
        return jwt.encode(payload, SUPABASE_SERVICE_ROLE_KEY, algorithm="HS256")
    
    async def test_api_health(self) -> Dict[str, Any]:
        """Test API health endpoint"""
        logger.info("🔍 Testing API health endpoint...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/health", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ API health check passed: {data['status']}")
                    return {
                        "test": "api_health",
                        "status": "passed",
                        "response": data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"❌ API health check failed: {response.status_code}")
                    return {
                        "test": "api_health",
                        "status": "failed",
                        "error": f"HTTP {response.status_code}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ API health check error: {e}")
            return {
                "test": "api_health",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_root_endpoint(self) -> Dict[str, Any]:
        """Test root endpoint"""
        logger.info("🔍 Testing root endpoint...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Root endpoint passed: {data}")
                    return {
                        "test": "root_endpoint",
                        "status": "passed",
                        "response": data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"❌ Root endpoint failed: {response.status_code}")
                    return {
                        "test": "root_endpoint",
                        "status": "failed",
                        "error": f"HTTP {response.status_code}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Root endpoint error: {e}")
            return {
                "test": "root_endpoint",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_auth_endpoints(self) -> Dict[str, Any]:
        """Test authentication endpoints"""
        logger.info("🔍 Testing authentication endpoints...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test registration endpoint
                registration_data = {
                    "email": f"phase3-test-{int(time.time())}@example.com",
                    "password": "testpassword123",
                    "name": "Phase 3 Test User"
                }
                
                response = await client.post(
                    f"{self.api_url}/register", 
                    json=registration_data, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Registration endpoint passed")
                    
                    # Test login endpoint
                    login_data = {
                        "email": registration_data["email"],
                        "password": registration_data["password"]
                    }
                    
                    login_response = await client.post(
                        f"{self.api_url}/login", 
                        json=login_data, 
                        timeout=30
                    )
                    
                    if login_response.status_code == 200:
                        login_data = login_response.json()
                        logger.info(f"✅ Login endpoint passed")
                        
                        return {
                            "test": "auth_endpoints",
                            "status": "passed",
                            "registration_response": data,
                            "login_response": login_data,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    else:
                        logger.error(f"❌ Login endpoint failed: {login_response.status_code}")
                        return {
                            "test": "auth_endpoints",
                            "status": "failed",
                            "error": f"Login failed: HTTP {login_response.status_code}",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                else:
                    logger.error(f"❌ Registration endpoint failed: {response.status_code}")
                    return {
                        "test": "auth_endpoints",
                        "status": "failed",
                        "error": f"Registration failed: HTTP {response.status_code}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Auth endpoints error: {e}")
            return {
                "test": "auth_endpoints",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_upload_endpoint(self) -> Dict[str, Any]:
        """Test upload endpoint"""
        logger.info("🔍 Testing upload endpoint...")
        
        try:
            # First register and login to get a token
            async with httpx.AsyncClient() as client:
                # Register
                registration_data = {
                    "email": f"phase3-upload-test-{int(time.time())}@example.com",
                    "password": "testpassword123",
                    "name": "Phase 3 Upload Test User"
                }
                
                reg_response = await client.post(
                    f"{self.api_url}/register", 
                    json=registration_data, 
                    timeout=30
                )
                
                if reg_response.status_code != 200:
                    return {
                        "test": "upload_endpoint",
                        "status": "failed",
                        "error": f"Registration failed: HTTP {reg_response.status_code}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                # Login
                login_data = {
                    "email": registration_data["email"],
                    "password": registration_data["password"]
                }
                
                login_response = await client.post(
                    f"{self.api_url}/login", 
                    json=login_data, 
                    timeout=30
                )
                
                if login_response.status_code != 200:
                    return {
                        "test": "upload_endpoint",
                        "status": "failed",
                        "error": f"Login failed: HTTP {login_response.status_code}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                login_result = login_response.json()
                token = login_result.get("access_token")
                
                if not token:
                    return {
                        "test": "upload_endpoint",
                        "status": "failed",
                        "error": "No access token received",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                # Test upload endpoint
                headers = {"Authorization": f"Bearer {token}"}
                
                # Create a test file
                test_content = b"Test PDF content for Phase 3 testing"
                test_file = ("test.pdf", test_content, "application/pdf")
                
                upload_data = {
                    "policy_id": "test-policy-123"
                }
                
                files = {"file": test_file}
                
                upload_response = await client.post(
                    f"{self.api_url}/upload-document-backend",
                    data=upload_data,
                    files=files,
                    headers=headers,
                    timeout=30
                )
                
                if upload_response.status_code == 200:
                    upload_result = upload_response.json()
                    logger.info(f"✅ Upload endpoint passed: {upload_result}")
                    return {
                        "test": "upload_endpoint",
                        "status": "passed",
                        "response": upload_result,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"❌ Upload endpoint failed: {upload_response.status_code}")
                    return {
                        "test": "upload_endpoint",
                        "status": "failed",
                        "error": f"Upload failed: HTTP {upload_response.status_code} - {upload_response.text}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Upload endpoint error: {e}")
            return {
                "test": "upload_endpoint",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_me_endpoint(self) -> Dict[str, Any]:
        """Test /me endpoint"""
        logger.info("🔍 Testing /me endpoint...")
        
        try:
            # First register and login to get a token
            async with httpx.AsyncClient() as client:
                # Register
                registration_data = {
                    "email": f"phase3-me-test-{int(time.time())}@example.com",
                    "password": "testpassword123",
                    "name": "Phase 3 Me Test User"
                }
                
                reg_response = await client.post(
                    f"{self.api_url}/register", 
                    json=registration_data, 
                    timeout=30
                )
                
                if reg_response.status_code != 200:
                    return {
                        "test": "me_endpoint",
                        "status": "failed",
                        "error": f"Registration failed: HTTP {reg_response.status_code}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                # Login
                login_data = {
                    "email": registration_data["email"],
                    "password": registration_data["password"]
                }
                
                login_response = await client.post(
                    f"{self.api_url}/login", 
                    json=login_data, 
                    timeout=30
                )
                
                if login_response.status_code != 200:
                    return {
                        "test": "me_endpoint",
                        "status": "failed",
                        "error": f"Login failed: HTTP {login_response.status_code}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                login_result = login_response.json()
                token = login_result.get("access_token")
                
                if not token:
                    return {
                        "test": "me_endpoint",
                        "status": "failed",
                        "error": "No access token received",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                # Test /me endpoint
                headers = {"Authorization": f"Bearer {token}"}
                
                me_response = await client.get(
                    f"{self.api_url}/me",
                    headers=headers,
                    timeout=30
                )
                
                if me_response.status_code == 200:
                    me_result = me_response.json()
                    logger.info(f"✅ /me endpoint passed: {me_result}")
                    return {
                        "test": "me_endpoint",
                        "status": "passed",
                        "response": me_result,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"❌ /me endpoint failed: {me_response.status_code}")
                    return {
                        "test": "me_endpoint",
                        "status": "failed",
                        "error": f"/me failed: HTTP {me_response.status_code} - {me_response.text}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ /me endpoint error: {e}")
            return {
                "test": "me_endpoint",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Phase 3 current API test"""
        logger.info("🚀 Starting Phase 3 Current API Test")
        logger.info("=" * 60)
        
        start_time = time.time()
        test_results = []
        
        # 1. Test API health
        logger.info("\n1️⃣ Testing API Health...")
        health_result = await self.test_api_health()
        test_results.append(health_result)
        
        # 2. Test root endpoint
        logger.info("\n2️⃣ Testing Root Endpoint...")
        root_result = await self.test_root_endpoint()
        test_results.append(root_result)
        
        # 3. Test authentication endpoints
        logger.info("\n3️⃣ Testing Authentication Endpoints...")
        auth_result = await self.test_auth_endpoints()
        test_results.append(auth_result)
        
        # 4. Test upload endpoint
        logger.info("\n4️⃣ Testing Upload Endpoint...")
        upload_result = await self.test_upload_endpoint()
        test_results.append(upload_result)
        
        # 5. Test /me endpoint
        logger.info("\n5️⃣ Testing /me Endpoint...")
        me_result = await self.test_me_endpoint()
        test_results.append(me_result)
        
        # Calculate summary
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r['status'] == 'passed'])
        failed_tests = len([r for r in test_results if r['status'] == 'failed'])
        skipped_tests = len([r for r in test_results if r['status'] == 'skipped'])
        
        total_time = time.time() - start_time
        
        summary = {
            "phase": "Phase 3 Current API Test",
            "timestamp": datetime.utcnow().isoformat(),
            "api_url": self.api_url,
            "api_version": "3.0.0",
            "total_duration": total_time,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "skipped_tests": skipped_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "test_results": test_results
        }
        
        # Log summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 PHASE 3 CURRENT API TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"API URL: {self.api_url}")
        logger.info(f"API Version: 3.0.0")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Skipped: {skipped_tests}")
        logger.info(f"Success Rate: {summary['summary']['success_rate']:.1f}%")
        logger.info(f"Total Duration: {total_time:.2f} seconds")
        
        return summary

async def main():
    """Main function"""
    tester = Phase3CurrentAPITester()
    
    try:
        # Run comprehensive test
        results = await tester.run_comprehensive_test()
        
        # Save results to file
        timestamp = int(time.time())
        filename = f"phase3_current_api_test_results_{timestamp}.json"
        filepath = f"docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/upload_pipeline/phase3/results/{filename}"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📁 Results saved to: {filepath}")
        
        # Return success/failure
        success = results['summary']['failed_tests'] == 0
        return success
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
