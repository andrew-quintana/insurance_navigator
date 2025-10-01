#!/usr/bin/env python3
"""
FM-027 Simple Timing Test

A focused test to reproduce and analyze the timing issues in the Insurance Navigator
document processing pipeline that cause the error: "Document file is not accessible for processing."

This test focuses on the core race condition between job creation and file access.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FM027SimpleTimingTest:
    """Simple test for FM-027 timing issues"""
    
    def __init__(self):
        # Staging environment
        self.supabase_url = "***REMOVED***"
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable must be set")
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json"
            }
        )
        
        self.test_user_id = str(uuid.uuid4())
        self.test_results = []
        
        logger.info(f"FM027 Simple Timing Test initialized for {self.supabase_url}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def run_timing_tests(self):
        """Run focused timing tests"""
        logger.info("Starting FM-027 simple timing tests")
        
        try:
            # Test 1: Immediate file access after job creation
            await self.test_immediate_file_access()
            
            # Test 2: File access with different delays
            await self.test_file_access_with_delays()
            
            # Test 3: Job status update timing
            await self.test_job_status_timing()
            
            # Test 4: Database consistency
            await self.test_database_consistency()
            
            # Generate report
            await self.generate_simple_report()
            
        except Exception as e:
            logger.error(f"Timing tests failed: {str(e)}", exc_info=True)
            raise
        finally:
            await self.close()
    
    async def test_immediate_file_access(self):
        """Test immediate file access after job creation"""
        logger.info("=== Test 1: Immediate File Access After Job Creation ===")
        
        test_result = {
            "test_name": "immediate_file_access",
            "start_time": datetime.utcnow().isoformat(),
            "success": False,
            "error": None,
            "timing": {}
        }
        
        try:
            # Create test job
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job in database
            await self._create_test_job(job_id, document_id)
            test_result["timing"]["job_creation"] = datetime.utcnow().isoformat()
            
            # Immediately try to access file
            file_access_start = time.time()
            file_accessible = await self._test_file_access(job_id)
            file_access_duration = time.time() - file_access_start
            
            test_result["timing"]["file_access_duration"] = file_access_duration
            test_result["timing"]["file_accessible"] = file_accessible
            test_result["success"] = file_accessible
            
            if not file_accessible:
                test_result["error"] = "File not accessible immediately after job creation"
            
            logger.info(f"Immediate file access test: {'SUCCESS' if file_accessible else 'FAILED'}")
            
        except Exception as e:
            test_result["error"] = str(e)
            test_result["success"] = False
            logger.error(f"Immediate file access test failed: {str(e)}")
        
        test_result["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(test_result)
    
    async def test_file_access_with_delays(self):
        """Test file access with different delay intervals"""
        logger.info("=== Test 2: File Access With Different Delays ===")
        
        test_result = {
            "test_name": "file_access_with_delays",
            "start_time": datetime.utcnow().isoformat(),
            "delay_tests": [],
            "success": False
        }
        
        try:
            # Test different delay intervals
            delays = [0.1, 0.5, 1.0, 2.0, 5.0]  # seconds
            
            for delay in delays:
                delay_test = await self._test_file_access_with_delay(delay)
                test_result["delay_tests"].append(delay_test)
            
            # Calculate success rate
            successful_delays = sum(1 for dt in test_result["delay_tests"] if dt["success"])
            test_result["success_rate"] = successful_delays / len(test_result["delay_tests"])
            test_result["success"] = test_result["success_rate"] > 0.5
            
            logger.info(f"File access with delays test: {test_result['success_rate']:.2%} success rate")
            
        except Exception as e:
            test_result["error"] = str(e)
            test_result["success"] = False
            logger.error(f"File access with delays test failed: {str(e)}")
        
        test_result["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(test_result)
    
    async def test_job_status_timing(self):
        """Test job status update timing"""
        logger.info("=== Test 3: Job Status Update Timing ===")
        
        test_result = {
            "test_name": "job_status_timing",
            "start_time": datetime.utcnow().isoformat(),
            "status_transitions": [],
            "success": False
        }
        
        try:
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job
            await self._create_test_job(job_id, document_id)
            
            # Test status transitions with timing
            statuses = ["queued", "uploaded", "parse_queued", "parsed", "complete"]
            
            for i, status in enumerate(statuses):
                transition_start = time.time()
                
                # Update status
                await self._update_job_status(job_id, status)
                
                # Verify status change
                current_status = await self._get_job_status(job_id)
                
                transition_duration = time.time() - transition_start
                
                test_result["status_transitions"].append({
                    "status": status,
                    "actual_status": current_status,
                    "duration": transition_duration,
                    "success": current_status == status,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Small delay between transitions
                await asyncio.sleep(0.1)
            
            # Calculate success rate
            successful_transitions = sum(1 for st in test_result["status_transitions"] if st["success"])
            test_result["success_rate"] = successful_transitions / len(test_result["status_transitions"])
            test_result["success"] = test_result["success_rate"] > 0.8
            
            logger.info(f"Job status timing test: {test_result['success_rate']:.2%} success rate")
            
        except Exception as e:
            test_result["error"] = str(e)
            test_result["success"] = False
            logger.error(f"Job status timing test failed: {str(e)}")
        
        test_result["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(test_result)
    
    async def test_database_consistency(self):
        """Test database consistency during processing"""
        logger.info("=== Test 4: Database Consistency During Processing ===")
        
        test_result = {
            "test_name": "database_consistency",
            "start_time": datetime.utcnow().isoformat(),
            "consistency_checks": [],
            "success": False
        }
        
        try:
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job
            await self._create_test_job(job_id, document_id)
            
            # Simulate processing with existence checks
            processing_steps = [
                "job_created",
                "file_upload_started",
                "file_upload_completed",
                "processing_started",
                "processing_completed"
            ]
            
            for step in processing_steps:
                # Check if job exists
                job_exists = await self._check_job_exists(job_id)
                
                test_result["consistency_checks"].append({
                    "step": step,
                    "job_exists": job_exists,
                    "consistent": job_exists,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Simulate processing delay
                await asyncio.sleep(0.1)
            
            # Calculate consistency rate
            consistent_checks = sum(1 for cc in test_result["consistency_checks"] if cc["consistent"])
            test_result["consistency_rate"] = consistent_checks / len(test_result["consistency_checks"])
            test_result["success"] = test_result["consistency_rate"] > 0.95
            
            logger.info(f"Database consistency test: {test_result['consistency_rate']:.2%} consistency rate")
            
        except Exception as e:
            test_result["error"] = str(e)
            test_result["success"] = False
            logger.error(f"Database consistency test failed: {str(e)}")
        
        test_result["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(test_result)
    
    async def _test_file_access_with_delay(self, delay_seconds: float):
        """Test file access with specific delay"""
        delay_test = {
            "delay_seconds": delay_seconds,
            "start_time": datetime.utcnow().isoformat(),
            "success": False,
            "error": None,
            "timing": {}
        }
        
        try:
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job
            await self._create_test_job(job_id, document_id)
            delay_test["timing"]["job_creation"] = datetime.utcnow().isoformat()
            
            # Wait for specified delay
            await asyncio.sleep(delay_seconds)
            delay_test["timing"]["delay_complete"] = datetime.utcnow().isoformat()
            
            # Test file access
            file_access_start = time.time()
            file_accessible = await self._test_file_access(job_id)
            file_access_duration = time.time() - file_access_start
            
            delay_test["timing"]["file_access_duration"] = file_access_duration
            delay_test["timing"]["file_accessible"] = file_accessible
            delay_test["success"] = file_accessible
            
            if not file_accessible:
                delay_test["error"] = f"File not accessible after {delay_seconds}s delay"
            
        except Exception as e:
            delay_test["error"] = str(e)
            delay_test["success"] = False
        
        delay_test["end_time"] = datetime.utcnow().isoformat()
        return delay_test
    
    # Database helper methods
    
    async def _create_test_job(self, job_id: str, document_id: str):
        """Create a test job in the database"""
        try:
            # Create document record
            document_query = """
                INSERT INTO upload_pipeline.documents (
                    document_id, user_id, filename, mime, bytes_len, 
                    file_sha256, raw_path, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            """
            
            raw_path = f"files/user/{self.test_user_id}/raw/{document_id}.pdf"
            
            # Use direct SQL execution
            response = await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/execute_sql",
                json={
                    "query": document_query,
                    "params": [
                        document_id,
                        self.test_user_id,
                        "test_document.pdf",
                        "application/pdf",
                        1024,
                        "test_hash",
                        raw_path
                    ]
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to create document: {response.text}")
            
            # Create job record
            job_query = """
                INSERT INTO upload_pipeline.upload_jobs (
                    job_id, document_id, status, state, 
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, NOW(), NOW())
            """
            
            response = await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/execute_sql",
                json={
                    "query": job_query,
                    "params": [job_id, document_id, "queued", "queued"]
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to create job: {response.text}")
            
            logger.info(f"Created test job {job_id} with document {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to create test job: {str(e)}")
            raise
    
    async def _update_job_status(self, job_id: str, status: str):
        """Update job status in database"""
        try:
            query = """
                UPDATE upload_pipeline.upload_jobs
                SET status = $1, updated_at = NOW()
                WHERE job_id = $2
            """
            
            response = await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/execute_sql",
                json={
                    "query": query,
                    "params": [status, job_id]
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to update job status: {response.text}")
            
            logger.info(f"Updated job {job_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Failed to update job status: {str(e)}")
            raise
    
    async def _get_job_status(self, job_id: str) -> Optional[str]:
        """Get current job status"""
        try:
            query = """
                SELECT status FROM upload_pipeline.upload_jobs
                WHERE job_id = $1
            """
            
            response = await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/execute_sql",
                json={
                    "query": query,
                    "params": [job_id]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0:
                    return result[0]["status"]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get job status: {str(e)}")
            return None
    
    async def _check_job_exists(self, job_id: str) -> bool:
        """Check if job exists in database"""
        try:
            query = """
                SELECT COUNT(*) as count FROM upload_pipeline.upload_jobs
                WHERE job_id = $1
            """
            
            response = await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/execute_sql",
                json={
                    "query": query,
                    "params": [job_id]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0:
                    return result[0]["count"] > 0
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check job existence: {str(e)}")
            return False
    
    async def _test_file_access(self, job_id: str) -> bool:
        """Test if file is accessible for processing"""
        try:
            # Get job details
            query = """
                SELECT d.raw_path FROM upload_pipeline.upload_jobs uj
                JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                WHERE uj.job_id = $1
            """
            
            response = await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/execute_sql",
                json={
                    "query": query,
                    "params": [job_id]
                }
            )
            
            if response.status_code != 200:
                return False
            
            result = response.json()
            if not result or len(result) == 0:
                return False
            
            raw_path = result[0]["raw_path"]
            
            # Test file access using direct HTTP request
            # Extract bucket and key from path
            if raw_path.startswith("files/user/"):
                key = raw_path[6:]  # Remove "files/" prefix
                bucket = "files"
            else:
                return False
            
            # Test file access
            storage_endpoint = f"{self.supabase_url}/storage/v1/object/{bucket}/{key}"
            
            file_response = await self.client.get(storage_endpoint)
            file_accessible = file_response.status_code == 200
            
            return file_accessible
            
        except Exception as e:
            logger.error(f"File access test failed: {str(e)}")
            return False
    
    async def generate_simple_report(self):
        """Generate simple test report"""
        logger.info("Generating simple test report")
        
        report = {
            "test_id": str(uuid.uuid4()),
            "test_name": "FM-027 Simple Timing Test",
            "start_time": self.test_results[0]["start_time"] if self.test_results else datetime.utcnow().isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "environment": {
                "supabase_url": self.supabase_url
            },
            "test_results": self.test_results,
            "summary": self._generate_summary()
        }
        
        # Save report to file
        report_filename = f"fm027_simple_timing_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Test report saved to {report_filename}")
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        summary = {
            "total_tests": len(self.test_results),
            "successful_tests": sum(1 for t in self.test_results if t.get("success", False)),
            "failed_tests": sum(1 for t in self.test_results if not t.get("success", False)),
            "key_findings": [],
            "recommendations": []
        }
        
        # Analyze test results
        for test in self.test_results:
            test_name = test["test_name"]
            
            if test_name == "immediate_file_access":
                if not test.get("success", False):
                    summary["key_findings"].append("File not accessible immediately after job creation - race condition confirmed")
                    summary["recommendations"].append("Implement delay before file access attempts")
            
            elif test_name == "file_access_with_delays":
                success_rate = test.get("success_rate", 0)
                summary["key_findings"].append(f"File access success rate with delays: {success_rate:.2%}")
                
                if success_rate > 0.8:
                    summary["recommendations"].append("Implement file access retry mechanism with delays")
            
            elif test_name == "job_status_timing":
                success_rate = test.get("success_rate", 0)
                summary["key_findings"].append(f"Job status transition success rate: {success_rate:.2%}")
                
                if success_rate < 0.8:
                    summary["recommendations"].append("Improve job status update reliability")
            
            elif test_name == "database_consistency":
                consistency_rate = test.get("consistency_rate", 0)
                summary["key_findings"].append(f"Database consistency rate: {consistency_rate:.2%}")
                
                if consistency_rate < 0.95:
                    summary["recommendations"].append("Investigate database transaction issues")
        
        return summary
    
    def _print_summary(self, report: Dict[str, Any]):
        """Print test summary to console"""
        print("\n" + "="*60)
        print("FM-027 SIMPLE TIMING TEST SUMMARY")
        print("="*60)
        
        summary = report["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful Tests: {summary['successful_tests']}")
        print(f"Failed Tests: {summary['failed_tests']}")
        
        print("\nKey Findings:")
        for finding in summary["key_findings"]:
            print(f"  • {finding}")
        
        print("\nRecommendations:")
        for recommendation in summary["recommendations"]:
            print(f"  • {recommendation}")
        
        print("\n" + "="*60)


async def main():
    """Main function to run the FM-027 simple timing test"""
    tester = FM027SimpleTimingTest()
    
    try:
        await tester.run_timing_tests()
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
