"""
Real API Integration Testing for Phase 3.5

This script tests the complete real API integration flow:
1. Document upload to LlamaParse
2. Real webhook processing
3. Database state updates
4. Storage operations
5. Error handling scenarios

This is the missing real API testing that should have been done in Phase 3.5.
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.shared.external.llamaparse_real import RealLlamaParseService
from backend.shared.config.enhanced_config import get_config
from backend.shared.db.connection import DatabaseManager
from backend.shared.storage.storage_manager import StorageManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealAPIIntegrationTest:
    """Comprehensive real API integration testing for Phase 3.5."""
    
    def __init__(self):
        self.config = get_config()
        self.test_results = {}
        self.cost_tracking = {
            "llamaparse_requests": 0,
            "total_cost_estimate": 0.0,
            "start_time": datetime.utcnow()
        }
        
        # Test configuration
        self.max_test_cost = 5.00  # $5.00 maximum test cost
        self.test_document_size_limit = 1024 * 1024  # 1MB limit for test documents
        
    async def setup_test_environment(self):
        """Set up test environment and validate configuration."""
        logger.info("Setting up real API test environment...")
        
        # Validate API keys
        if not self.config.llamaparse.api_key:
            raise ValueError("LlamaParse API key not configured")
        
        if not self.config.llamaparse.webhook_secret:
            raise ValueError("LlamaParse webhook secret not configured")
        
        # Initialize services
        self.llamaparse_service = RealLlamaParseService(
            api_key=self.config.llamaparse.api_key,
            base_url=self.config.llamaparse.base_url,
            webhook_secret=self.config.llamaparse.webhook_secret
        )
        
        self.db_manager = DatabaseManager(self.config.database_url)
        await self.db_manager.initialize()
        
        self.storage_manager = StorageManager(
            url=self.config.supabase.url,
            anon_key=self.config.supabase.anon_key,
            service_role_key=self.config.supabase.service_role_key
        )
        
        # Test service availability
        await self._test_service_availability()
        
        logger.info("Test environment setup complete")
    
    async def _test_service_availability(self):
        """Test that all required services are available."""
        logger.info("Testing service availability...")
        
        # Test LlamaParse service
        llamaparse_health = await self.llamaparse_service.get_health()
        if not llamaparse_health.is_healthy:
            raise RuntimeError(f"LlamaParse service unhealthy: {llamaparse_health.last_error}")
        
        logger.info(f"LlamaParse service healthy (response time: {llamaparse_health.response_time_ms}ms)")
        
        # Test database connection
        try:
            async with self.db_manager.get_db_connection() as conn:
                await conn.execute("SELECT 1")
            logger.info("Database connection successful")
        except Exception as e:
            raise RuntimeError(f"Database connection failed: {e}")
        
        # Test storage connection
        try:
            # Test with a simple operation
            test_path = f"test://availability_check/{uuid4()}"
            await self.storage_manager.write_blob(test_path, "test", "text/plain")
            await self.storage_manager.delete_blob(test_path)
            logger.info("Storage connection successful")
        except Exception as e:
            raise RuntimeError(f"Storage connection failed: {e}")
    
    def create_test_document(self, content: str = None) -> str:
        """Create a test document for parsing."""
        if content is None:
            content = f"""# Test Insurance Document {uuid4()}

This is a test insurance document created for Phase 3.5 real API integration testing.

## Policy Information
- Policy Number: TEST-{uuid4().hex[:8].upper()}
- Policy Type: Comprehensive Coverage
- Effective Date: {datetime.utcnow().strftime('%Y-%m-%d')}
- Premium: $1,200.00 annually

## Coverage Details
- Liability Coverage: $500,000
- Property Damage: $100,000
- Medical Payments: $10,000
- Uninsured Motorist: $500,000

## Terms and Conditions
This is a test document for validation purposes only. The content is designed to test the complete parsing pipeline including:
- Markdown formatting
- Structured content
- Multiple sections
- Realistic insurance terminology

## Contact Information
- Insurance Company: Test Insurance Co.
- Agent: Test Agent
- Phone: (555) 123-4567
- Email: test@testinsurance.com

Generated for testing at: {datetime.utcnow().isoformat()}
"""
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        temp_file.write(content)
        temp_file.close()
        
        return temp_file.name
    
    async def test_complete_parsing_flow(self) -> Dict[str, Any]:
        """Test the complete document parsing flow with real LlamaParse API."""
        logger.info("Testing complete parsing flow...")
        
        test_start = time.time()
        test_id = str(uuid4())
        
        try:
            # Step 1: Create test document
            logger.info("Step 1: Creating test document...")
            test_doc_path = self.create_test_document()
            test_doc_size = os.path.getsize(test_doc_path)
            
            if test_doc_size > self.test_document_size_limit:
                raise ValueError(f"Test document too large: {test_doc_size} bytes")
            
            logger.info(f"Test document created: {test_doc_path} ({test_doc_size} bytes)")
            
            # Step 2: Submit document to LlamaParse
            logger.info("Step 2: Submitting document to LlamaParse...")
            
            # Create webhook URL for testing
            webhook_url = f"{self.config.api.base_url}/webhooks/llamaparse"
            correlation_id = f"test-{test_id}"
            
            parse_response = await self.llamaparse_service.parse_document(
                file_path=test_doc_path,
                webhook_url=webhook_url,
                correlation_id=correlation_id
            )
            
            if not parse_response.parse_job_id:
                raise RuntimeError("No parse job ID returned from LlamaParse")
            
            logger.info(f"Document submitted successfully: {parse_response.parse_job_id}")
            self.cost_tracking["llamaparse_requests"] += 1
            
            # Step 3: Monitor parsing progress
            logger.info("Step 3: Monitoring parsing progress...")
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    status_response = await self.llamaparse_service.get_parse_status(
                        parse_response.parse_job_id
                    )
                    
                    status = status_response.get("status", "unknown")
                    logger.info(f"Parse status: {status}")
                    
                    if status in ["completed", "parsed"]:
                        logger.info("Parsing completed successfully")
                        break
                    elif status in ["failed", "error"]:
                        error_msg = status_response.get("error", "Unknown error")
                        raise RuntimeError(f"Parsing failed: {error_msg}")
                    
                    # Wait before next check
                    await asyncio.sleep(10)
                    
                except Exception as e:
                    logger.warning(f"Status check failed: {e}")
                    await asyncio.sleep(5)
            
            else:
                raise RuntimeError("Parsing did not complete within timeout")
            
            # Step 4: Verify webhook processing
            logger.info("Step 4: Verifying webhook processing...")
            
            # Wait for webhook processing
            await asyncio.sleep(5)
            
            # Check database for job updates
            async with self.db_manager.get_db_connection() as conn:
                job = await conn.fetchrow("""
                    SELECT status, parsed_path, parsed_sha256, updated_at
                    FROM upload_pipeline.upload_jobs
                    WHERE correlation_id = $1
                """, correlation_id)
                
                if not job:
                    raise RuntimeError("Job not found in database after webhook processing")
                
                logger.info(f"Job status in database: {job['status']}")
                
                if job['status'] != 'parsed':
                    raise RuntimeError(f"Expected status 'parsed', got '{job['status']}'")
                
                if not job['parsed_path']:
                    raise RuntimeError("No parsed_path set in database")
                
                if not job['parsed_sha256']:
                    raise RuntimeError("No parsed_sha256 set in database")
            
            # Step 5: Verify storage operations
            logger.info("Step 5: Verifying storage operations...")
            
            # Check if parsed content was stored
            parsed_content = await self.storage_manager.read_blob(job['parsed_path'])
            if not parsed_content:
                raise RuntimeError("Parsed content not found in storage")
            
            logger.info(f"Parsed content retrieved: {len(parsed_content)} bytes")
            
            # Step 6: Verify event logging
            logger.info("Step 6: Verifying event logging...")
            
            async with self.db_manager.get_db_connection() as conn:
                events = await conn.fetch("""
                    SELECT type, code, severity, payload
                    FROM upload_pipeline.events
                    WHERE correlation_id = $1
                    ORDER BY ts
                """, correlation_id)
                
                if not events:
                    raise RuntimeError("No events logged for webhook processing")
                
                # Check for parse completion event
                parse_events = [e for e in events if e['code'] == 'parse_completed']
                if not parse_events:
                    raise RuntimeError("No parse completion event found")
                
                logger.info(f"Events logged: {len(events)} total, {len(parse_events)} parse events")
            
            # Test completed successfully
            test_duration = time.time() - test_start
            logger.info(f"Complete parsing flow test PASSED in {test_duration:.2f} seconds")
            
            return {
                "success": True,
                "test_id": test_id,
                "parse_job_id": parse_response.parse_job_id,
                "correlation_id": correlation_id,
                "duration_seconds": test_duration,
                "document_size_bytes": test_doc_size,
                "events_logged": len(events),
                "parsed_content_size": len(parsed_content)
            }
            
        except Exception as e:
            test_duration = time.time() - test_start
            logger.error(f"Complete parsing flow test FAILED after {test_duration:.2f} seconds: {e}")
            
            return {
                "success": False,
                "test_id": test_id,
                "error": str(e),
                "duration_seconds": test_duration
            }
        
        finally:
            # Cleanup
            try:
                if 'test_doc_path' in locals():
                    os.unlink(test_doc_path)
                    logger.info("Test document cleaned up")
            except Exception as e:
                logger.warning(f"Failed to cleanup test document: {e}")
    
    async def test_error_scenarios(self) -> Dict[str, Any]:
        """Test error handling scenarios with real API."""
        logger.info("Testing error scenarios...")
        
        test_results = {}
        
        # Test 1: Invalid API key
        logger.info("Test 1: Invalid API key scenario...")
        try:
            invalid_service = RealLlamaParseService(
                api_key="invalid_key",
                base_url=self.config.llamaparse.base_url
            )
            
            await invalid_service.parse_document("test.pdf")
            test_results["invalid_api_key"] = {"success": False, "expected_error": True}
            
        except Exception as e:
            if "Invalid LlamaParse API key" in str(e):
                test_results["invalid_api_key"] = {"success": True, "error_handled": True}
                logger.info("Invalid API key error handled correctly")
            else:
                test_results["invalid_api_key"] = {"success": False, "unexpected_error": str(e)}
        
        # Test 2: Invalid file path
        logger.info("Test 2: Invalid file path scenario...")
        try:
            await self.llamaparse_service.parse_document("nonexistent_file.pdf")
            test_results["invalid_file_path"] = {"success": False, "expected_error": True}
            
        except Exception as e:
            if "not found" in str(e).lower() or "file" in str(e).lower():
                test_results["invalid_file_path"] = {"success": True, "error_handled": True}
                logger.info("Invalid file path error handled correctly")
            else:
                test_results["invalid_file_path"] = {"success": False, "unexpected_error": str(e)}
        
        # Test 3: Rate limiting (if applicable)
        logger.info("Test 3: Rate limiting scenario...")
        try:
            # Submit multiple requests quickly
            responses = []
            for i in range(5):
                response = await self.llamaparse_service.parse_document(
                    self.create_test_document(f"Rate limit test {i}"),
                    correlation_id=f"rate-limit-test-{i}"
                )
                responses.append(response)
                await asyncio.sleep(0.1)  # Very quick requests
            
            test_results["rate_limiting"] = {"success": True, "requests_processed": len(responses)}
            logger.info("Rate limiting test completed")
            
        except Exception as e:
            if "rate limit" in str(e).lower():
                test_results["rate_limiting"] = {"success": True, "rate_limit_enforced": True}
                logger.info("Rate limiting enforced correctly")
            else:
                test_results["rate_limiting"] = {"success": False, "error": str(e)}
        
        return test_results
    
    async def test_webhook_signature_verification(self) -> Dict[str, Any]:
        """Test webhook signature verification with real signatures."""
        logger.info("Testing webhook signature verification...")
        
        test_results = {}
        
        # Test 1: Valid signature
        logger.info("Test 1: Valid webhook signature...")
        try:
            test_payload = json.dumps({
                "test": "webhook_signature_verification",
                "timestamp": datetime.utcnow().isoformat()
            }).encode()
            
            # Generate valid signature
            import hmac
            import hashlib
            valid_signature = hmac.new(
                self.config.llamaparse.webhook_secret.encode(),
                test_payload,
                hashlib.sha256
            ).hexdigest()
            
            # Verify signature
            is_valid = self.llamaparse_service.verify_webhook_signature(
                test_payload, valid_signature
            )
            
            if is_valid:
                test_results["valid_signature"] = {"success": True, "verified": True}
                logger.info("Valid signature verification passed")
            else:
                test_results["valid_signature"] = {"success": False, "verification_failed": True}
                
        except Exception as e:
            test_results["valid_signature"] = {"success": False, "error": str(e)}
        
        # Test 2: Invalid signature
        logger.info("Test 2: Invalid webhook signature...")
        try:
            test_payload = json.dumps({"test": "invalid_signature"}).encode()
            invalid_signature = "invalid_signature_hash"
            
            is_valid = self.llamaparse_service.verify_webhook_signature(
                test_payload, invalid_signature
            )
            
            if not is_valid:
                test_results["invalid_signature"] = {"success": True, "rejected": True}
                logger.info("Invalid signature correctly rejected")
            else:
                test_results["invalid_signature"] = {"success": False, "accepted_invalid": True}
                
        except Exception as e:
            test_results["invalid_signature"] = {"success": False, "error": str(e)}
        
        return test_results
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all comprehensive real API tests."""
        logger.info("Starting comprehensive real API integration testing...")
        
        start_time = time.time()
        
        try:
            # Setup
            await self.setup_test_environment()
            
            # Run tests
            test_results = {}
            
            # Test 1: Complete parsing flow
            logger.info("=" * 60)
            logger.info("TEST 1: Complete Parsing Flow")
            logger.info("=" * 60)
            test_results["complete_parsing_flow"] = await self.test_complete_parsing_flow()
            
            # Test 2: Error scenarios
            logger.info("=" * 60)
            logger.info("TEST 2: Error Scenarios")
            logger.info("=" * 60)
            test_results["error_scenarios"] = await self.test_error_scenarios()
            
            # Test 3: Webhook signature verification
            logger.info("=" * 60)
            logger.info("TEST 3: Webhook Signature Verification")
            logger.info("=" * 60)
            test_results["webhook_signature_verification"] = await self.test_webhook_signature_verification()
            
            # Calculate overall results
            total_tests = 0
            passed_tests = 0
            
            for test_category, results in test_results.items():
                if isinstance(results, dict):
                    if results.get("success") is True:
                        passed_tests += 1
                    total_tests += 1
                elif isinstance(results, list):
                    for result in results:
                        if result.get("success") is True:
                            passed_tests += 1
                        total_tests += 1
            
            overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Final results
            final_results = {
                "overall_success": overall_success_rate >= 80,  # 80% threshold
                "success_rate_percent": overall_success_rate,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "test_results": test_results,
                "cost_tracking": self.cost_tracking,
                "total_duration_seconds": time.time() - start_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("=" * 60)
            logger.info("COMPREHENSIVE TESTING COMPLETE")
            logger.info("=" * 60)
            logger.info(f"Overall Success Rate: {overall_success_rate:.1f}%")
            logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
            logger.info(f"Total Duration: {final_results['total_duration_seconds']:.2f} seconds")
            logger.info(f"LlamaParse Requests: {self.cost_tracking['llamaparse_requests']}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Comprehensive testing failed: {e}")
            return {
                "overall_success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        finally:
            # Cleanup
            try:
                await self.llamaparse_service.close()
                logger.info("Services cleaned up")
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")

async def main():
    """Main function for running real API integration tests."""
    logger.info("Starting Phase 3.5 Real API Integration Testing")
    
    tester = RealAPIIntegrationTest()
    results = await tester.run_comprehensive_tests()
    
    # Print results summary
    print("\n" + "=" * 80)
    print("PHASE 3.5 REAL API INTEGRATION TESTING RESULTS")
    print("=" * 80)
    
    if results.get("overall_success"):
        print("✅ OVERALL TEST RESULT: PASSED")
    else:
        print("❌ OVERALL TEST RESULT: FAILED")
    
    print(f"Success Rate: {results.get('success_rate_percent', 0):.1f}%")
    print(f"Tests Passed: {results.get('passed_tests', 0)}/{results.get('total_tests', 0)}")
    print(f"Total Duration: {results.get('total_duration_seconds', 0):.2f} seconds")
    print(f"LlamaParse Requests: {results.get('cost_tracking', {}).get('llamaparse_requests', 0)}")
    
    if results.get("error"):
        print(f"Error: {results['error']}")
    
    print("=" * 80)
    
    # Save results to file
    results_file = f"real_api_test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Detailed results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
