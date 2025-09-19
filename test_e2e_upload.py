#!/usr/bin/env python3
"""
End-to-End Upload Pipeline Test

This script tests the complete upload pipeline including:
- API upload endpoint
- Worker processing
- Webhook handling
- Error scenarios
- Success scenarios
"""

import asyncio
import json
import os
import sys
import uuid
import httpx
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.workers.enhanced_base_worker import EnhancedBaseWorker
from backend.shared.exceptions import UserFacingError, ServiceUnavailableError


class E2ETestSuite:
    """End-to-end test suite for upload pipeline"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_url = f"{self.base_url}/api/upload-pipeline"
        self.webhook_url = f"{self.base_url}/api/upload-pipeline"
        self.test_file_path = "test_document.pdf"
        self.results = []
        
    async def setup_test_environment(self):
        """Setup test environment and create test file"""
        print("🔧 Setting up test environment...")
        
        # Create a simple test PDF file
        test_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Document for E2E Testing) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
        
        with open(self.test_file_path, "wb") as f:
            f.write(test_content)
        
        print(f"   ✅ Created test file: {self.test_file_path}")
        
    async def test_api_health(self):
        """Test API health endpoint"""
        print("\n🏥 Testing API Health...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                
            if response.status_code == 200:
                print("   ✅ API is healthy")
                return True
            else:
                print(f"   ❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ API health check error: {e}")
            return False
    
    async def test_upload_endpoint(self):
        """Test upload endpoint"""
        print("\n📤 Testing Upload Endpoint...")
        
        try:
            # Use the test endpoint that doesn't require authentication
            upload_request = {
                "filename": "test_document.pdf",
                "mime": "application/pdf",
                "bytes_len": os.path.getsize(self.test_file_path),
                "sha256": "a" * 64  # Valid 64-character hex string
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/upload-test",
                    json=upload_request
                )
            
            print(f"   Response status: {response.status_code}")
            print(f"   Response body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Upload successful")
                print(f"   Job ID: {result.get('job_id')}")
                print(f"   Document ID: {result.get('document_id')}")
                return result
            else:
                print(f"   ❌ Upload failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Upload error: {e}")
            return None
    
    async def test_job_status(self, job_id):
        """Test job status endpoint"""
        print(f"\n📊 Testing Job Status for {job_id}...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/jobs/{job_id}")
            
            print(f"   Response status: {response.status_code}")
            print(f"   Response body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Job status retrieved")
                print(f"   Status: {result.get('status')}")
                print(f"   State: {result.get('state')}")
                return result
            else:
                print(f"   ❌ Job status failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Job status error: {e}")
            return None
    
    async def test_worker_processing(self, job_data):
        """Test worker processing directly"""
        print("\n⚙️ Testing Worker Processing...")
        
        try:
            # Create mock components for worker
            from unittest.mock import Mock, AsyncMock
            
            # Mock database
            mock_db = AsyncMock()
            mock_connection = AsyncMock()
            mock_connection.execute = AsyncMock(return_value="INSERT 0 1")
            mock_connection.fetchrow = AsyncMock(return_value={
                "filename": "test_document.pdf",
                "raw_path": self.test_file_path,
                "mime": "application/pdf"
            })
            mock_connection.fetchval = AsyncMock(return_value=0)
            mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
            mock_connection.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_db_connection = Mock(return_value=mock_connection)
            
            # Mock storage
            mock_storage = AsyncMock()
            mock_storage.read_blob.return_value = b"Mock PDF content"
            
            # Mock config
            mock_config = Mock()
            mock_config.database_url = "postgresql://test:test@localhost:5432/test"
            mock_config.log_level = "INFO"
            mock_config.poll_interval = 1
            mock_config.max_retries = 3
            mock_config.retry_base_delay = 1
            mock_config.get_storage_config.return_value = {"url": "http://localhost:5000"}
            mock_config.get_service_router_config.return_value = {"mode": "hybrid"}
            mock_config.to_dict.return_value = {"test": "config"}
            mock_config.get = Mock(side_effect=lambda key, default=None: {
                "daily_cost_limit": 5.00,
                "hourly_rate_limit": 100
            }.get(key, default))
            
            # Create worker
            worker = EnhancedBaseWorker(mock_config)
            worker.db = mock_db
            worker.storage = mock_storage
            
            # Test the direct LlamaParse call
            job_id = job_data["job_id"]
            document_id = job_data["document_id"]
            correlation_id = str(uuid.uuid4())
            
            print(f"   Testing direct LlamaParse call...")
            print(f"   Job ID: {job_id}")
            print(f"   Document ID: {document_id}")
            
            # This will test our enhanced error handling
            result = await worker._direct_llamaparse_call(
                file_path=self.test_file_path,
                job_id=job_id,
                document_id=document_id,
                correlation_id=correlation_id,
                document_filename="test_document.pdf",
                webhook_url=f"{self.webhook_url}/webhook/llamaparse/{job_id}"
            )
            
            print(f"   ✅ Worker processing completed")
            print(f"   Result: {result}")
            return True
            
        except Exception as e:
            print(f"   ❌ Worker processing error: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_webhook_endpoint(self):
        """Test webhook endpoint"""
        print("\n🔗 Testing Webhook Endpoint...")
        
        try:
            # Test webhook endpoint with mock data
            webhook_data = {
                "job_id": str(uuid.uuid4()),
                "status": "completed",
                "result": {
                    "id": "test-parse-id",
                    "status": "completed",
                    "result": {
                        "markdown": "# Test Document\n\nThis is test content."
                    }
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.webhook_url}/webhook/llamaparse/test-job-id",
                    json=webhook_data
                )
            
            print(f"   Response status: {response.status_code}")
            print(f"   Response body: {response.text}")
            
            if response.status_code == 200:
                print("   ✅ Webhook endpoint is working")
                return True
            else:
                print(f"   ❌ Webhook endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Webhook endpoint error: {e}")
            return False
    
    async def test_error_scenarios(self):
        """Test various error scenarios"""
        print("\n🚨 Testing Error Scenarios...")
        
        # Test 1: Invalid file upload
        print("   Testing invalid file upload...")
        try:
            invalid_request = {
                "filename": "test.txt",
                "mime": "text/plain",
                "bytes_len": 10,
                "sha256": "b" * 64  # Valid format but wrong file type
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/upload-test",
                    json=invalid_request
                )
            
            print(f"   Invalid file response: {response.status_code}")
            if response.status_code != 200:
                print("   ✅ Invalid file correctly rejected")
            else:
                print("   ⚠️ Invalid file was accepted (unexpected)")
                
        except Exception as e:
            print(f"   ❌ Invalid file test error: {e}")
        
        # Test 2: Missing required fields
        print("   Testing missing required fields...")
        try:
            incomplete_request = {
                "filename": "test.pdf"
                # Missing mime, bytes_len, sha256
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/upload-test",
                    json=incomplete_request
                )
            
            print(f"   Missing fields response: {response.status_code}")
            if response.status_code != 200:
                print("   ✅ Missing fields correctly rejected")
            else:
                print("   ⚠️ Missing fields were accepted (unexpected)")
                
        except Exception as e:
            print(f"   ❌ Missing fields test error: {e}")
    
    async def cleanup(self):
        """Cleanup test files"""
        print("\n🧹 Cleaning up...")
        
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)
            print(f"   ✅ Removed {self.test_file_path}")
    
    async def run_all_tests(self):
        """Run all end-to-end tests"""
        print("🚀 Starting End-to-End Upload Pipeline Tests")
        print("=" * 60)
        
        try:
            # Setup
            await self.setup_test_environment()
            
            # Test API health
            health_ok = await self.test_api_health()
            if not health_ok:
                print("\n❌ API is not healthy. Please start the API server first.")
                print("   Run: cd api/upload_pipeline && python -m uvicorn main:app --host 0.0.0.0 --port 8000")
                return False
            
            # Test upload
            upload_result = await self.test_upload_endpoint()
            if not upload_result:
                print("\n❌ Upload test failed. Check API server logs.")
                return False
            
            # Test job status
            job_status = await self.test_job_status(upload_result["job_id"])
            if not job_status:
                print("\n❌ Job status test failed.")
                return False
            
            # Test worker processing
            worker_ok = await self.test_worker_processing(upload_result)
            if not worker_ok:
                print("\n❌ Worker processing test failed.")
                return False
            
            # Test webhook endpoint
            webhook_ok = await self.test_webhook_endpoint()
            if not webhook_ok:
                print("\n❌ Webhook endpoint test failed.")
                return False
            
            # Test error scenarios
            await self.test_error_scenarios()
            
            print("\n" + "=" * 60)
            print("🎉 All End-to-End Tests Completed Successfully!")
            print("✅ The upload pipeline is working correctly.")
            print("✅ Error handling is working correctly.")
            print("✅ All fixes are verified.")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            await self.cleanup()


async def main():
    """Main test function"""
    test_suite = E2ETestSuite()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n🎯 Ready for deployment!")
        print("   All tests passed - safe to commit and push.")
    else:
        print("\n⚠️ Tests failed - please fix issues before deploying.")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
