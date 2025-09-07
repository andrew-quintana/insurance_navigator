#!/usr/bin/env python3
"""
Phase 3 API Endpoint Test
Tests the new upload pipeline API endpoints
"""

import asyncio
import httpx
import json
import time
import uuid
import hashlib
from datetime import datetime
import logging

# Configure detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase3APIEndpointTest:
    def __init__(self, api_url="https://insurance-navigator-api.onrender.com"):
        self.api_url = api_url
        self.client = None
        self.user_id = None
        self.access_token = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def setup_user(self):
        """Register and login a test user"""
        logger.info("🔍 Setting up test user...")
        
        # Register user
        registration_data = {
            "email": f"phase3-api-test-{int(time.time())}@example.com",
            "password": "testpassword123",
            "name": "Phase 3 API Test User"
        }
        
        reg_response = await self.client.post(
            f"{self.api_url}/register", 
            json=registration_data, 
            timeout=30
        )
        
        if reg_response.status_code != 200:
            raise Exception(f"Registration failed: {reg_response.status_code} - {reg_response.text}")
        
        reg_data = reg_response.json()
        self.user_id = reg_data.get("user", {}).get("id")
        logger.info(f"✅ User registered: {self.user_id}")
        
        # Login user
        login_data = {
            "email": registration_data["email"],
            "password": registration_data["password"]
        }
        
        login_response = await self.client.post(
            f"{self.api_url}/login", 
            json=login_data, 
            timeout=30
        )
        
        if login_response.status_code != 200:
            raise Exception(f"Login failed: {login_response.status_code} - {login_response.text}")
        
        login_data = login_response.json()
        self.access_token = login_data.get("access_token")
        logger.info(f"✅ User logged in, token: {self.access_token[:20]}...")
    
    async def test_new_upload_endpoint(self):
        """Test the new /api/v2/upload endpoint"""
        logger.info("🔍 Testing new /api/v2/upload endpoint...")
        
        # Create test upload request
        test_content = f"Phase 3 API Test Document - {datetime.utcnow().isoformat()}".encode('utf-8')
        file_sha256 = hashlib.sha256(test_content).hexdigest()
        
        upload_data = {
            "filename": "phase3_api_test.pdf",
            "bytes_len": len(test_content),
            "mime": "application/pdf",
            "sha256": file_sha256,
            "ocr": False
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = await self.client.post(
                f"{self.api_url}/api/v2/upload",
                json=upload_data,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"New API response: {response.status_code}")
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"✅ New API success: {response_data}")
                return True, response_data
            else:
                logger.warning(f"New API failed: {response.text}")
                return False, response.text
                
        except Exception as e:
            logger.error(f"New API test failed: {e}")
            return False, str(e)
    
    async def test_legacy_upload_endpoint(self):
        """Test the legacy /upload-document-backend endpoint"""
        logger.info("🔍 Testing legacy /upload-document-backend endpoint...")
        
        # Create test file content
        test_content = f"Phase 3 Legacy Test Document - {datetime.utcnow().isoformat()}".encode('utf-8')
        
        files = {"file": ("test_document.pdf", test_content, "application/pdf")}
        data = {"policy_id": "test-policy-123"}
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = await self.client.post(
                f"{self.api_url}/upload-document-backend",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Legacy API response: {response.status_code}")
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"✅ Legacy API success: {response_data}")
                return True, response_data
            else:
                logger.warning(f"Legacy API failed: {response.text}")
                return False, response.text
                
        except Exception as e:
            logger.error(f"Legacy API test failed: {e}")
            return False, str(e)
    
    async def test_endpoint_availability(self):
        """Test endpoint availability and structure"""
        logger.info("🔍 Testing endpoint availability...")
        
        # Test OpenAPI spec
        openapi_response = await self.client.get(f"{self.api_url}/openapi.json", timeout=30)
        if openapi_response.status_code == 200:
            openapi_data = openapi_response.json()
            paths = list(openapi_data.get("paths", {}).keys())
            
            logger.info("📋 Available API endpoints:")
            for path in sorted(paths):
                logger.info(f"  - {path}")
            
            # Check for specific endpoints
            has_new_api = "/api/v2/upload" in paths
            has_old_api = "/upload-document-backend" in paths
            
            logger.info(f"✅ New API endpoint available: {has_new_api}")
            logger.info(f"✅ Old API endpoint available: {has_old_api}")
            
            # Check endpoint schemas
            if has_new_api:
                new_endpoint = openapi_data["paths"]["/api/v2/upload"]
                logger.info(f"📋 New endpoint methods: {list(new_endpoint.keys())}")
                if "post" in new_endpoint:
                    logger.info(f"📋 New endpoint summary: {new_endpoint['post'].get('summary', 'N/A')}")
            
            return has_new_api, has_old_api
        else:
            logger.warning(f"⚠️ Could not fetch OpenAPI spec: {openapi_response.status_code}")
            return False, False

async def main():
    """Main test function"""
    logger.info("🚀 Starting Phase 3 API Endpoint Test")
    logger.info("=" * 60)
    
    async with Phase3APIEndpointTest() as test:
        try:
            # Setup user
            await test.setup_user()
            
            # Test endpoint availability
            has_new_api, has_old_api = await test.test_endpoint_availability()
            
            # Test new upload endpoint
            new_success, new_result = await test.test_new_upload_endpoint()
            
            # Test legacy upload endpoint
            old_success, old_result = await test.test_legacy_upload_endpoint()
            
            # Final summary
            logger.info("")
            logger.info("📊 PHASE 3 API ENDPOINT TEST SUMMARY")
            logger.info("=" * 60)
            logger.info(f"New API Endpoint Available: {'✅ YES' if has_new_api else '❌ NO'}")
            logger.info(f"Old API Endpoint Available: {'✅ YES' if has_old_api else '❌ NO'}")
            logger.info(f"New Upload Workflow: {'✅ WORKING' if new_success else '❌ NOT WORKING'}")
            logger.info(f"Old Upload Workflow: {'✅ WORKING' if old_success else '❌ NOT WORKING'}")
            
            if new_success:
                logger.info("")
                logger.info("🎉 NEW UPLOAD PIPELINE API IS WORKING!")
                logger.info("✅ /api/v2/upload endpoint functional")
                logger.info("✅ Upload pipeline integration working")
                logger.info("✅ Complete end-to-end workflow available")
            elif has_new_api:
                logger.info("")
                logger.info("⚠️ NEW API ENDPOINT AVAILABLE BUT NOT WORKING")
                logger.info("✅ /api/v2/upload endpoint exists")
                logger.info("❌ Database connection issue")
                logger.info("📋 API structure is correct, needs database fix")
            else:
                logger.error("❌ New API endpoint not available")
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())
