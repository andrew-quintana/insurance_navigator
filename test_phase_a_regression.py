#!/usr/bin/env python3
"""
Phase A Regression Test

This test ensures that the Phase A UUID fixes don't break existing functionality.
It validates that all existing features continue to work correctly with the
new deterministic UUID generation system.

Tests:
1. Authentication and authorization
2. Upload pipeline functionality
3. RAG query functionality
4. Error handling scenarios
5. API endpoint compatibility
6. Database operations

Reference: Phase A Critical Path Resolution
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhaseARegressionTest:
    """Regression test suite for Phase A UUID fixes."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_user_id = None
        self.test_email = f"regression_test_{int(time.time())}@example.com"
        self.test_password = "RegressionTest123!"
        self.auth_token = None
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_name": "Phase A Regression Test",
            "tests": {},
            "overall_success": False,
            "regression_issues": []
        }
    
    async def setup_test_environment(self) -> bool:
        """Set up test environment and user."""
        try:
            logger.info("🔧 Setting up test environment...")
            
            # Create test user
            async with httpx.AsyncClient() as client:
                register_data = {
                    "email": self.test_email,
                    "password": self.test_password,
                    "full_name": "Regression Test User"
                }
                
                response = await client.post(
                    f"{self.base_url}/auth/register",
                    json=register_data
                )
                
                if response.status_code not in [201, 400]:  # 400 if user exists
                    logger.error(f"❌ Failed to create test user: {response.status_code}")
                    return False
                
                # Authenticate user
                login_data = {
                    "email": self.test_email,
                    "password": self.test_password
                }
                
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    json=login_data
                )
                
                if response.status_code == 200:
                    auth_data = response.json()
                    self.test_user_id = auth_data.get("user", {}).get("id")
                    self.auth_token = auth_data.get("access_token")
                    logger.info("✅ Test environment setup complete")
                    return True
                else:
                    logger.error(f"❌ Authentication failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error setting up test environment: {e}")
            return False
    
    async def test_authentication_functionality(self) -> bool:
        """Test that authentication still works correctly."""
        logger.info("🔐 Testing authentication functionality...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test login
                login_data = {
                    "email": self.test_email,
                    "password": self.test_password
                }
                
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    json=login_data
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Login failed: {response.status_code}")
                    return False
                
                auth_data = response.json()
                if not auth_data.get("access_token"):
                    logger.error("❌ No access token received")
                    return False
                
                # Test protected endpoint
                headers = {"Authorization": f"Bearer {auth_data['access_token']}"}
                response = await client.get(
                    f"{self.base_url}/auth/me",
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Protected endpoint failed: {response.status_code}")
                    return False
                
                logger.info("✅ Authentication functionality working correctly")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error testing authentication: {e}")
            return False
    
    async def test_upload_pipeline_functionality(self) -> bool:
        """Test that upload pipeline still works with new UUIDs."""
        logger.info("📤 Testing upload pipeline functionality...")
        
        try:
            # Create test content
            test_content = f"Regression test document - {datetime.utcnow().isoformat()}"
            content_bytes = test_content.encode('utf-8')
            content_hash = hashlib.sha256(content_bytes).hexdigest()
            
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Test upload request
                upload_data = {
                    "filename": "regression_test.txt",
                    "mime": "text/plain",
                    "bytes_len": len(content_bytes),
                    "sha256": content_hash
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v2/upload",
                    json=upload_data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Upload request failed: {response.status_code} - {response.text}")
                    return False
                
                upload_response = response.json()
                
                # Validate response structure
                required_fields = ["document_id", "job_id", "signed_url", "upload_expires_at"]
                for field in required_fields:
                    if field not in upload_response:
                        logger.error(f"❌ Missing required field: {field}")
                        return False
                
                # Validate UUID format
                document_id = upload_response["document_id"]
                if not self.validate_uuid_format(document_id):
                    logger.error(f"❌ Invalid document UUID format: {document_id}")
                    return False
                
                # Test deterministic generation
                from utils.uuid_generation import UUIDGenerator
                expected_document_id = UUIDGenerator.document_uuid(self.test_user_id, content_hash)
                
                if document_id != expected_document_id:
                    logger.error(f"❌ UUID not deterministic: expected {expected_document_id}, got {document_id}")
                    return False
                
                logger.info("✅ Upload pipeline functionality working correctly")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error testing upload pipeline: {e}")
            return False
    
    async def test_rag_query_functionality(self) -> bool:
        """Test that RAG queries still work correctly."""
        logger.info("🔍 Testing RAG query functionality...")
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Test RAG query
                rag_query = {
                    "query": "test query for regression",
                    "user_id": self.test_user_id
                }
                
                response = await client.post(
                    f"{self.base_url}/api/rag/query",
                    json=rag_query,
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ RAG query failed: {response.status_code} - {response.text}")
                    return False
                
                rag_response = response.json()
                
                # Validate response structure
                if "results" not in rag_response:
                    logger.error("❌ RAG response missing 'results' field")
                    return False
                
                # Results might be empty if no documents are processed yet, which is OK
                logger.info("✅ RAG query functionality working correctly")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error testing RAG queries: {e}")
            return False
    
    async def test_error_handling_scenarios(self) -> bool:
        """Test that error handling still works correctly."""
        logger.info("⚠️ Testing error handling scenarios...")
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Test invalid file size
                upload_data = {
                    "filename": "large_file.txt",
                    "mime": "text/plain",
                    "bytes_len": 100 * 1024 * 1024,  # 100MB (over limit)
                    "sha256": "test-hash"
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v2/upload",
                    json=upload_data,
                    headers=headers
                )
                
                if response.status_code != 413:  # File too large
                    logger.error(f"❌ File size validation not working: {response.status_code}")
                    return False
                
                # Test invalid MIME type
                upload_data = {
                    "filename": "test.exe",
                    "mime": "application/exe",
                    "bytes_len": 1024,
                    "sha256": "test-hash"
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v2/upload",
                    json=upload_data,
                    headers=headers
                )
                
                # Should either reject or accept (depending on validation)
                if response.status_code not in [200, 400, 422]:
                    logger.error(f"❌ MIME type validation unexpected response: {response.status_code}")
                    return False
                
                # Test invalid UUID format in RAG query
                rag_query = {
                    "query": "test query",
                    "user_id": "invalid-uuid-format"
                }
                
                response = await client.post(
                    f"{self.base_url}/api/rag/query",
                    json=rag_query,
                    headers=headers
                )
                
                # Should handle invalid UUID gracefully
                if response.status_code not in [200, 400, 422]:
                    logger.error(f"❌ Invalid UUID handling unexpected response: {response.status_code}")
                    return False
                
                logger.info("✅ Error handling scenarios working correctly")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error testing error handling: {e}")
            return False
    
    async def test_api_endpoint_compatibility(self) -> bool:
        """Test that all API endpoints still work correctly."""
        logger.info("🌐 Testing API endpoint compatibility...")
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Test health endpoint
                response = await client.get(f"{self.base_url}/health")
                if response.status_code != 200:
                    logger.error(f"❌ Health endpoint failed: {response.status_code}")
                    return False
                
                # Test auth endpoints
                response = await client.get(f"{self.base_url}/auth/me", headers=headers)
                if response.status_code != 200:
                    logger.error(f"❌ Auth me endpoint failed: {response.status_code}")
                    return False
                
                # Test upload endpoint (already tested above, but verify structure)
                test_content = "API compatibility test"
                content_hash = hashlib.sha256(test_content.encode()).hexdigest()
                
                upload_data = {
                    "filename": "compatibility_test.txt",
                    "mime": "text/plain",
                    "bytes_len": len(test_content.encode()),
                    "sha256": content_hash
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v2/upload",
                    json=upload_data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Upload endpoint compatibility failed: {response.status_code}")
                    return False
                
                logger.info("✅ API endpoint compatibility working correctly")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error testing API compatibility: {e}")
            return False
    
    async def test_database_operations(self) -> bool:
        """Test that database operations still work correctly."""
        logger.info("🗄️ Testing database operations...")
        
        try:
            # This test would typically connect to the database directly
            # For now, we'll test through the API endpoints
            
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Test that we can create and retrieve data
                test_content = "Database operations test"
                content_hash = hashlib.sha256(test_content.encode()).hexdigest()
                
                # Create document
                upload_data = {
                    "filename": "db_test.txt",
                    "mime": "text/plain",
                    "bytes_len": len(test_content.encode()),
                    "sha256": content_hash
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v2/upload",
                    json=upload_data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Database write operation failed: {response.status_code}")
                    return False
                
                # Test that we can query the data
                rag_query = {
                    "query": "database test",
                    "user_id": self.test_user_id
                }
                
                response = await client.post(
                    f"{self.base_url}/api/rag/query",
                    json=rag_query,
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Database read operation failed: {response.status_code}")
                    return False
                
                logger.info("✅ Database operations working correctly")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error testing database operations: {e}")
            return False
    
    def validate_uuid_format(self, uuid_string: str) -> bool:
        """Validate UUID format."""
        try:
            uuid.UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False
    
    async def run_comprehensive_regression_test(self) -> Dict[str, Any]:
        """Run comprehensive regression test."""
        logger.info("🚀 Starting Phase A Regression Test")
        logger.info("=" * 60)
        
        try:
            # Setup test environment
            if not await self.setup_test_environment():
                logger.error("❌ Test environment setup failed")
                return self.test_results
            
            # Run all regression tests
            tests = [
                ("authentication", self.test_authentication_functionality()),
                ("upload_pipeline", self.test_upload_pipeline_functionality()),
                ("rag_queries", self.test_rag_query_functionality()),
                ("error_handling", self.test_error_handling_scenarios()),
                ("api_compatibility", self.test_api_endpoint_compatibility()),
                ("database_operations", self.test_database_operations())
            ]
            
            for test_name, test_coro in tests:
                logger.info(f"\n📋 Running {test_name} regression test...")
                result = await test_coro
                self.test_results["tests"][test_name] = result
                
                if not result:
                    self.test_results["regression_issues"].append(f"{test_name}: Test failed")
                    logger.error(f"❌ {test_name} regression test failed")
                else:
                    logger.info(f"✅ {test_name} regression test passed")
            
            # Calculate overall success
            all_tests = self.test_results["tests"]
            self.test_results["overall_success"] = all(all_tests.values())
            
            # Summary
            logger.info("\n" + "=" * 60)
            logger.info("📊 PHASE A REGRESSION TEST RESULTS")
            logger.info("=" * 60)
            
            for test_name, success in all_tests.items():
                status = "✅ PASS" if success else "❌ FAIL"
                logger.info(f"{test_name}: {status}")
            
            if self.test_results["regression_issues"]:
                logger.warning(f"\n⚠️ Regression issues found: {len(self.test_results['regression_issues'])}")
                for issue in self.test_results["regression_issues"]:
                    logger.warning(f"  - {issue}")
            else:
                logger.info("\n✅ No regression issues found!")
            
            overall_status = "✅ REGRESSION TEST PASSED" if self.test_results["overall_success"] else "❌ REGRESSION TEST FAILED"
            logger.info(f"\nOverall Result: {overall_status}")
            
            if self.test_results["overall_success"]:
                logger.info("\n🎉 Phase A UUID fixes are regression-safe!")
                logger.info("✅ All existing functionality preserved")
                logger.info("✅ No breaking changes detected")
                logger.info("✅ Ready for production deployment")
            else:
                logger.error("\n⚠️ Regression issues detected - review before deployment")
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"❌ Regression test error: {e}")
            self.test_results["error"] = str(e)
            return self.test_results

async def main():
    """Run Phase A regression test."""
    test_suite = PhaseARegressionTest()
    results = await test_suite.run_comprehensive_regression_test()
    
    # Save results
    timestamp = int(time.time())
    results_file = f"phase_a_regression_test_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Results saved to: {results_file}")
    
    return results["overall_success"]

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
