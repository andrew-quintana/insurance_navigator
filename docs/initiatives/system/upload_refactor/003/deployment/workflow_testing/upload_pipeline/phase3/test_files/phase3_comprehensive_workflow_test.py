#!/usr/bin/env python3
"""
Phase 3 Comprehensive Workflow Test
Tests both old and new API endpoints to ensure complete workflow functionality
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

class WorkflowTester:
    def __init__(self, api_url="***REMOVED***"):
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
            "email": f"comprehensive-test-{int(time.time())}@example.com",
            "password": "testpassword123",
            "name": "Comprehensive Test User"
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
    
    async def test_old_api_workflow(self):
        """Test the old API workflow (upload-document-backend)"""
        logger.info("🔍 Testing OLD API workflow...")
        
        # Create test file content
        test_content = f"""# Test Document for Old API Workflow

This is a test document for the old API workflow.

Document ID: {uuid.uuid4()}
Generated: {datetime.utcnow().isoformat()}
Test Type: Old API Workflow
""".encode('utf-8')
        
        file_sha256 = hashlib.sha256(test_content).hexdigest()
        logger.info(f"📄 Test document prepared - Size: {len(test_content)} bytes, SHA256: {file_sha256[:16]}...")
        
        # Test old API endpoint
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Create multipart form data for old API
        files = {"file": ("old_api_test.pdf", test_content, "application/pdf")}
        data = {
            "policy_id": f"policy-{uuid.uuid4().hex[:8]}",
            "document_type": "test_document"
        }
        
        logger.info(f"📤 Testing old API endpoint: /upload-document-backend")
        
        try:
            old_api_response = await self.client.post(
                f"{self.api_url}/upload-document-backend",
                data=data,
                files=files,
                headers=headers,
                timeout=60
            )
            
            logger.info(f"📊 Old API response: {old_api_response.status_code}")
            if old_api_response.status_code == 200:
                logger.info("✅ Old API workflow successful!")
                return True
            else:
                logger.warning(f"⚠️ Old API failed: {old_api_response.text}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Old API error: {e}")
            return False
    
    async def test_new_api_workflow(self):
        """Test the new API workflow (api/upload-pipeline/upload)"""
        logger.info("🔍 Testing NEW API workflow...")
        
        # Create test file content
        test_content = f"""# Test Document for New API Workflow

This is a test document for the new API workflow.

Document ID: {uuid.uuid4()}
Generated: {datetime.utcnow().isoformat()}
Test Type: New API Workflow
""".encode('utf-8')
        
        file_sha256 = hashlib.sha256(test_content).hexdigest()
        logger.info(f"📄 Test document prepared - Size: {len(test_content)} bytes, SHA256: {file_sha256[:16]}...")
        
        # Test new API endpoint
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        upload_request = {
            "filename": "new_api_test.pdf",
            "bytes_len": len(test_content),
            "mime": "application/pdf",
            "sha256": file_sha256,
            "ocr": False
        }
        
        logger.info(f"📤 Testing new API endpoint: /api/upload-pipeline/upload")
        
        try:
            new_api_response = await self.client.post(
                f"{self.api_url}/api/upload-pipeline/upload",
                json=upload_request,
                headers=headers,
                timeout=60
            )
            
            logger.info(f"📊 New API response: {new_api_response.status_code}")
            if new_api_response.status_code == 200:
                logger.info("✅ New API workflow successful!")
                result = new_api_response.json()
                logger.info(f"📋 Job ID: {result.get('job_id')}")
                logger.info(f"📋 Document ID: {result.get('document_id')}")
                logger.info(f"📋 Signed URL: {result.get('signed_url', '')[:100]}...")
                return True
            else:
                logger.warning(f"⚠️ New API failed: {new_api_response.text}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ New API error: {e}")
            return False
    
    async def check_api_endpoints(self):
        """Check what API endpoints are available"""
        logger.info("🔍 Checking available API endpoints...")
        
        try:
            openapi_response = await self.client.get(f"{self.api_url}/openapi.json", timeout=30)
            if openapi_response.status_code == 200:
                openapi_data = openapi_response.json()
                paths = list(openapi_data.get("paths", {}).keys())
                
                logger.info("📋 Available API endpoints:")
                for path in sorted(paths):
                    logger.info(f"  - {path}")
                
                # Check for specific endpoints
                has_old_api = "/upload-document-backend" in paths
                has_new_api = "/api/upload-pipeline/upload" in paths
                
                logger.info(f"✅ Old API endpoint available: {has_old_api}")
                logger.info(f"✅ New API endpoint available: {has_new_api}")
                
                return has_old_api, has_new_api
            else:
                logger.warning(f"⚠️ Could not fetch OpenAPI spec: {openapi_response.status_code}")
                return False, False
        except Exception as e:
            logger.warning(f"⚠️ Error checking API endpoints: {e}")
            return False, False
    
    async def monitor_worker_processing(self, job_id=None):
        """Monitor worker processing if we have a job ID"""
        if not job_id:
            logger.info("ℹ️ No job ID provided for monitoring")
            return
        
        logger.info(f"🔍 Monitoring worker processing for job: {job_id}")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        max_attempts = 60  # 1 minute with 1-second intervals
        
        for attempt in range(max_attempts):
            try:
                job_response = await self.client.get(
                    f"{self.api_url}/api/v2/jobs/{job_id}",
                    headers=headers,
                    timeout=30
                )
                
                if job_response.status_code == 200:
                    job_data = job_response.json()
                    status = job_data.get("status", "unknown")
                    state = job_data.get("state", "unknown")
                    
                    logger.info(f"📊 Job status (attempt {attempt + 1}/{max_attempts}): {status} | {state}")
                    
                    if status in ['complete', 'duplicate'] and state == "done":
                        logger.info(f"🎉 Job completed with status: {status}")
                        break
                    elif status in ['failed_parse', 'failed_chunking', 'failed_embedding']:
                        logger.error(f"❌ Job failed with status: {status}")
                        break
                else:
                    logger.warning(f"⚠️ Job status check failed: {job_response.status_code}")
            
            except Exception as e:
                logger.warning(f"⚠️ Job status check error: {e}")
            
            await asyncio.sleep(1)

async def main():
    """Main test function"""
    logger.info("🚀 Starting Comprehensive Workflow Test")
    logger.info("=" * 60)
    
    async with WorkflowTester() as tester:
        try:
            # Setup user
            await tester.setup_user()
            
            # Check available endpoints
            has_old_api, has_new_api = await tester.check_api_endpoints()
            
            # Test workflows based on available endpoints
            old_api_success = False
            new_api_success = False
            
            if has_old_api:
                old_api_success = await tester.test_old_api_workflow()
            
            if has_new_api:
                new_api_success = await tester.test_new_api_workflow()
            
            # Summary
            logger.info("")
            logger.info("📊 COMPREHENSIVE WORKFLOW TEST SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Old API available: {has_old_api}")
            logger.info(f"Old API test result: {'✅ SUCCESS' if old_api_success else '❌ FAILED'}")
            logger.info(f"New API available: {has_new_api}")
            logger.info(f"New API test result: {'✅ SUCCESS' if new_api_success else '❌ FAILED'}")
            
            if has_new_api and new_api_success:
                logger.info("🎉 New API workflow is working - Phase 3 ready!")
            elif has_old_api and old_api_success:
                logger.info("⚠️ Only old API is working - waiting for new API deployment")
            else:
                logger.error("❌ No working API endpoints found")
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())
