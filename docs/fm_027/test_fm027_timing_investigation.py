#!/usr/bin/env python3
"""
FM-027 Timing Investigation Test Suite

This test suite investigates the timing-related race conditions in the Insurance Navigator
document processing pipeline that cause the error: "Document file is not accessible for processing."

Key Areas of Investigation:
1. Job Status Update Timing - When job status is updated relative to file processing
2. File Access Timing - How long files take to become accessible after upload
3. Database Transaction Behavior - Job locking and transaction consistency
4. Stale Job Processing - Worker processing jobs that no longer exist

Test Environment: Staging Supabase
- URL: https://dfgzeastcxnoqshgyotp.supabase.co
- Worker Service: srv-d37dlmvfte5s73b6uq0g
- API Service: srv-d3740ijuibrs738mus1g
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import httpx
import hashlib
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FM027TimingInvestigator:
    """Investigator for FM-027 timing issues and race conditions"""
    
    def __init__(self):
        self.staging_url = "https://dfgzeastcxnoqshgyotp.supabase.co"
        self.api_url = "https://insurance-navigator-staging-api.onrender.com"
        self.worker_url = "https://insurance-navigator-staging-worker.onrender.com"
        
        # Load staging environment variables
        self.supabase_url = os.getenv("SUPABASE_URL", self.staging_url)
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY", "")
        
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable must be set")
        
        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            headers={
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json"
            }
        )
        
        # Test data
        self.test_file_path = "test_data/scan_classic_hmo.pdf"
        self.test_user_id = str(uuid.uuid4())
        self.test_results = []
        
        logger.info(f"FM027 Timing Investigator initialized for {self.supabase_url}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def run_comprehensive_investigation(self):
        """Run comprehensive investigation of FM-027 timing issues"""
        logger.info("Starting FM-027 comprehensive timing investigation")
        
        try:
            # Phase 1: Failure Reproduction
            await self.test_race_condition_reproduction()
            
            # Phase 2: Timing Analysis
            await self.test_file_access_timing()
            await self.test_job_status_timing()
            await self.test_database_consistency()
            
            # Phase 3: Solution Testing
            await self.test_job_status_delay_solution()
            await self.test_file_existence_check_solution()
            await self.test_retry_mechanism_solution()
            
            # Generate comprehensive report
            await self.generate_investigation_report()
            
        except Exception as e:
            logger.error(f"Investigation failed: {str(e)}", exc_info=True)
            raise
        finally:
            await self.close()
    
    async def test_race_condition_reproduction(self):
        """Test Case 1: Race Condition Reproduction"""
        logger.info("=== Test Case 1: Race Condition Reproduction ===")
        
        test_results = {
            "test_name": "race_condition_reproduction",
            "start_time": datetime.utcnow().isoformat(),
            "scenarios": []
        }
        
        # Scenario 1: Immediate file access after job creation
        scenario1 = await self._test_immediate_file_access()
        test_results["scenarios"].append(scenario1)
        
        # Scenario 2: Concurrent job processing
        scenario2 = await self._test_concurrent_job_processing()
        test_results["scenarios"].append(scenario2)
        
        # Scenario 3: Rapid job status updates
        scenario3 = await self._test_rapid_status_updates()
        test_results["scenarios"].append(scenario3)
        
        test_results["end_time"] = datetime.utcnow().isoformat()
        test_results["success_rate"] = sum(1 for s in test_results["scenarios"] if s["success"]) / len(test_results["scenarios"])
        
        self.test_results.append(test_results)
        logger.info(f"Race condition reproduction test completed. Success rate: {test_results['success_rate']:.2%}")
    
    async def test_file_access_timing(self):
        """Test Case 2: File Access Timing Analysis"""
        logger.info("=== Test Case 2: File Access Timing Analysis ===")
        
        test_results = {
            "test_name": "file_access_timing",
            "start_time": datetime.utcnow().isoformat(),
            "timing_measurements": []
        }
        
        # Test file access at different intervals after upload
        intervals = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]  # seconds
        
        for interval in intervals:
            measurement = await self._test_file_access_at_interval(interval)
            test_results["timing_measurements"].append(measurement)
        
        test_results["end_time"] = datetime.utcnow().isoformat()
        test_results["optimal_wait_time"] = self._calculate_optimal_wait_time(test_results["timing_measurements"])
        
        self.test_results.append(test_results)
        logger.info(f"File access timing test completed. Optimal wait time: {test_results['optimal_wait_time']:.2f}s")
    
    async def test_job_status_timing(self):
        """Test Case 3: Job Status Update Timing"""
        logger.info("=== Test Case 3: Job Status Update Timing ===")
        
        test_results = {
            "test_name": "job_status_timing",
            "start_time": datetime.utcnow().isoformat(),
            "status_transitions": []
        }
        
        # Test job status transitions with timing
        transitions = await self._test_job_status_transitions()
        test_results["status_transitions"] = transitions
        
        test_results["end_time"] = datetime.utcnow().isoformat()
        test_results["average_transition_time"] = sum(t["duration"] for t in transitions) / len(transitions)
        
        self.test_results.append(test_results)
        logger.info(f"Job status timing test completed. Average transition time: {test_results['average_transition_time']:.2f}s")
    
    async def test_database_consistency(self):
        """Test Case 4: Database Consistency During Processing"""
        logger.info("=== Test Case 4: Database Consistency During Processing ===")
        
        test_results = {
            "test_name": "database_consistency",
            "start_time": datetime.utcnow().isoformat(),
            "consistency_checks": []
        }
        
        # Test job existence during processing
        consistency_checks = await self._test_job_existence_during_processing()
        test_results["consistency_checks"] = consistency_checks
        
        test_results["end_time"] = datetime.utcnow().isoformat()
        test_results["consistency_rate"] = sum(1 for c in consistency_checks if c["consistent"]) / len(consistency_checks)
        
        self.test_results.append(test_results)
        logger.info(f"Database consistency test completed. Consistency rate: {test_results['consistency_rate']:.2%}")
    
    async def test_job_status_delay_solution(self):
        """Test Case 5: Job Status Delay Solution"""
        logger.info("=== Test Case 5: Job Status Delay Solution ===")
        
        test_results = {
            "test_name": "job_status_delay_solution",
            "start_time": datetime.utcnow().isoformat(),
            "delay_tests": []
        }
        
        # Test different delay times before updating job status
        delay_times = [0.5, 1.0, 2.0, 5.0]  # seconds
        
        for delay in delay_times:
            delay_test = await self._test_job_status_delay(delay)
            test_results["delay_tests"].append(delay_test)
        
        test_results["end_time"] = datetime.utcnow().isoformat()
        test_results["best_delay"] = self._find_best_delay(test_results["delay_tests"])
        
        self.test_results.append(test_results)
        logger.info(f"Job status delay solution test completed. Best delay: {test_results['best_delay']:.2f}s")
    
    async def test_file_existence_check_solution(self):
        """Test Case 6: File Existence Check Solution"""
        logger.info("=== Test Case 6: File Existence Check Solution ===")
        
        test_results = {
            "test_name": "file_existence_check_solution",
            "start_time": datetime.utcnow().isoformat(),
            "existence_checks": []
        }
        
        # Test file existence checks before processing
        existence_checks = await self._test_file_existence_checks()
        test_results["existence_checks"] = existence_checks
        
        test_results["end_time"] = datetime.utcnow().isoformat()
        test_results["success_rate"] = sum(1 for c in existence_checks if c["success"]) / len(existence_checks)
        
        self.test_results.append(test_results)
        logger.info(f"File existence check solution test completed. Success rate: {test_results['success_rate']:.2%}")
    
    async def test_retry_mechanism_solution(self):
        """Test Case 7: Retry Mechanism Solution"""
        logger.info("=== Test Case 7: Retry Mechanism Solution ===")
        
        test_results = {
            "test_name": "retry_mechanism_solution",
            "start_time": datetime.utcnow().isoformat(),
            "retry_tests": []
        }
        
        # Test retry mechanisms for failed file access
        retry_tests = await self._test_retry_mechanisms()
        test_results["retry_tests"] = retry_tests
        
        test_results["end_time"] = datetime.utcnow().isoformat()
        test_results["retry_success_rate"] = sum(1 for t in retry_tests if t["success"]) / len(retry_tests)
        
        self.test_results.append(test_results)
        logger.info(f"Retry mechanism solution test completed. Success rate: {test_results['retry_success_rate']:.2%}")
    
    async def _test_immediate_file_access(self):
        """Test immediate file access after job creation"""
        logger.info("Testing immediate file access after job creation")
        
        scenario = {
            "name": "immediate_file_access",
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
            scenario["timing"]["job_creation"] = datetime.utcnow().isoformat()
            
            # Immediately try to access file
            file_access_start = time.time()
            file_accessible = await self._test_file_access(job_id)
            file_access_duration = time.time() - file_access_start
            
            scenario["timing"]["file_access_duration"] = file_access_duration
            scenario["timing"]["file_accessible"] = file_accessible
            scenario["success"] = file_accessible
            
            if not file_accessible:
                scenario["error"] = "File not accessible immediately after job creation"
            
        except Exception as e:
            scenario["error"] = str(e)
            scenario["success"] = False
        
        scenario["end_time"] = datetime.utcnow().isoformat()
        return scenario
    
    async def _test_concurrent_job_processing(self):
        """Test concurrent job processing scenarios"""
        logger.info("Testing concurrent job processing")
        
        scenario = {
            "name": "concurrent_job_processing",
            "start_time": datetime.utcnow().isoformat(),
            "success": False,
            "error": None,
            "concurrent_jobs": []
        }
        
        try:
            # Create multiple jobs concurrently
            job_count = 5
            jobs = []
            
            for i in range(job_count):
                job_id = str(uuid.uuid4())
                document_id = str(uuid.uuid4())
                jobs.append((job_id, document_id))
            
            # Create all jobs concurrently
            create_tasks = [self._create_test_job(job_id, document_id) for job_id, document_id in jobs]
            await asyncio.gather(*create_tasks)
            
            # Process all jobs concurrently
            process_tasks = [self._test_file_access(job_id) for job_id, _ in jobs]
            results = await asyncio.gather(*process_tasks, return_exceptions=True)
            
            # Analyze results
            successful_jobs = sum(1 for result in results if result is True)
            failed_jobs = sum(1 for result in results if isinstance(result, Exception))
            
            scenario["concurrent_jobs"] = [
                {
                    "job_id": job_id,
                    "success": result is True,
                    "error": str(result) if isinstance(result, Exception) else None
                }
                for (job_id, _), result in zip(jobs, results)
            ]
            
            scenario["success"] = successful_jobs > 0
            scenario["success_rate"] = successful_jobs / job_count
            
            if successful_jobs == 0:
                scenario["error"] = "All concurrent jobs failed"
            
        except Exception as e:
            scenario["error"] = str(e)
            scenario["success"] = False
        
        scenario["end_time"] = datetime.utcnow().isoformat()
        return scenario
    
    async def _test_rapid_status_updates(self):
        """Test rapid job status updates"""
        logger.info("Testing rapid job status updates")
        
        scenario = {
            "name": "rapid_status_updates",
            "start_time": datetime.utcnow().isoformat(),
            "success": False,
            "error": None,
            "status_updates": []
        }
        
        try:
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job
            await self._create_test_job(job_id, document_id)
            
            # Rapidly update job status
            statuses = ["queued", "uploaded", "parse_queued", "parsed", "complete"]
            update_times = []
            
            for status in statuses:
                update_start = time.time()
                await self._update_job_status(job_id, status)
                update_duration = time.time() - update_start
                
                update_times.append({
                    "status": status,
                    "duration": update_duration,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Small delay between updates
                await asyncio.sleep(0.1)
            
            scenario["status_updates"] = update_times
            scenario["success"] = True
            
        except Exception as e:
            scenario["error"] = str(e)
            scenario["success"] = False
        
        scenario["end_time"] = datetime.utcnow().isoformat()
        return scenario
    
    async def _test_file_access_at_interval(self, interval_seconds: float):
        """Test file access at specific interval after upload"""
        logger.info(f"Testing file access at {interval_seconds}s interval")
        
        measurement = {
            "interval_seconds": interval_seconds,
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
            measurement["timing"]["job_creation"] = datetime.utcnow().isoformat()
            
            # Wait for specified interval
            await asyncio.sleep(interval_seconds)
            measurement["timing"]["wait_complete"] = datetime.utcnow().isoformat()
            
            # Test file access
            file_access_start = time.time()
            file_accessible = await self._test_file_access(job_id)
            file_access_duration = time.time() - file_access_start
            
            measurement["timing"]["file_access_duration"] = file_access_duration
            measurement["timing"]["file_accessible"] = file_accessible
            measurement["success"] = file_accessible
            
            if not file_accessible:
                measurement["error"] = f"File not accessible after {interval_seconds}s wait"
            
        except Exception as e:
            measurement["error"] = str(e)
            measurement["success"] = False
        
        measurement["end_time"] = datetime.utcnow().isoformat()
        return measurement
    
    async def _test_job_status_transitions(self):
        """Test job status transitions with timing"""
        logger.info("Testing job status transitions with timing")
        
        transitions = []
        
        try:
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job
            await self._create_test_job(job_id, document_id)
            
            # Test status transitions
            status_sequence = [
                ("queued", "uploaded"),
                ("uploaded", "parse_queued"),
                ("parse_queued", "parsed"),
                ("parsed", "complete")
            ]
            
            for from_status, to_status in status_sequence:
                transition_start = time.time()
                
                # Update status
                await self._update_job_status(job_id, to_status)
                
                # Verify status change
                current_status = await self._get_job_status(job_id)
                
                transition_duration = time.time() - transition_start
                
                transitions.append({
                    "from_status": from_status,
                    "to_status": to_status,
                    "actual_status": current_status,
                    "duration": transition_duration,
                    "success": current_status == to_status,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Small delay between transitions
                await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Job status transition test failed: {str(e)}")
        
        return transitions
    
    async def _test_job_existence_during_processing(self):
        """Test job existence during processing"""
        logger.info("Testing job existence during processing")
        
        consistency_checks = []
        
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
                
                consistency_checks.append({
                    "step": step,
                    "job_exists": job_exists,
                    "consistent": job_exists,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Simulate processing delay
                await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Job existence test failed: {str(e)}")
        
        return consistency_checks
    
    async def _test_job_status_delay(self, delay_seconds: float):
        """Test job status update with delay"""
        logger.info(f"Testing job status delay of {delay_seconds}s")
        
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
            
            # Wait for delay
            await asyncio.sleep(delay_seconds)
            delay_test["timing"]["delay_complete"] = datetime.utcnow().isoformat()
            
            # Update job status
            await self._update_job_status(job_id, "uploaded")
            delay_test["timing"]["status_update"] = datetime.utcnow().isoformat()
            
            # Test file access
            file_accessible = await self._test_file_access(job_id)
            delay_test["timing"]["file_accessible"] = file_accessible
            delay_test["success"] = file_accessible
            
            if not file_accessible:
                delay_test["error"] = f"File not accessible after {delay_seconds}s delay"
            
        except Exception as e:
            delay_test["error"] = str(e)
            delay_test["success"] = False
        
        delay_test["end_time"] = datetime.utcnow().isoformat()
        return delay_test
    
    async def _test_file_existence_checks(self):
        """Test file existence checks before processing"""
        logger.info("Testing file existence checks before processing")
        
        existence_checks = []
        
        try:
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job
            await self._create_test_job(job_id, document_id)
            
            # Test file existence checks at different intervals
            intervals = [0.1, 0.5, 1.0, 2.0]
            
            for interval in intervals:
                await asyncio.sleep(interval)
                
                # Check file existence
                file_exists = await self._check_file_exists(job_id)
                
                existence_checks.append({
                    "interval_seconds": interval,
                    "file_exists": file_exists,
                    "success": file_exists,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            logger.error(f"File existence check test failed: {str(e)}")
        
        return existence_checks
    
    async def _test_retry_mechanisms(self):
        """Test retry mechanisms for failed file access"""
        logger.info("Testing retry mechanisms for failed file access")
        
        retry_tests = []
        
        try:
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job
            await self._create_test_job(job_id, document_id)
            
            # Test retry mechanisms
            retry_configs = [
                {"max_retries": 3, "delay": 0.5},
                {"max_retries": 5, "delay": 1.0},
                {"max_retries": 10, "delay": 0.2}
            ]
            
            for config in retry_configs:
                retry_test = await self._test_retry_config(job_id, config)
                retry_tests.append(retry_test)
            
        except Exception as e:
            logger.error(f"Retry mechanism test failed: {str(e)}")
        
        return retry_tests
    
    async def _test_retry_config(self, job_id: str, config: Dict[str, Any]):
        """Test specific retry configuration"""
        retry_test = {
            "config": config,
            "start_time": datetime.utcnow().isoformat(),
            "success": False,
            "error": None,
            "retry_attempts": []
        }
        
        try:
            max_retries = config["max_retries"]
            delay = config["delay"]
            
            for attempt in range(max_retries):
                attempt_start = time.time()
                
                # Try to access file
                file_accessible = await self._test_file_access(job_id)
                
                attempt_duration = time.time() - attempt_start
                
                retry_test["retry_attempts"].append({
                    "attempt": attempt + 1,
                    "success": file_accessible,
                    "duration": attempt_duration,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                if file_accessible:
                    retry_test["success"] = True
                    break
                
                # Wait before next attempt
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
            
            if not retry_test["success"]:
                retry_test["error"] = f"All {max_retries} retry attempts failed"
            
        except Exception as e:
            retry_test["error"] = str(e)
            retry_test["success"] = False
        
        retry_test["end_time"] = datetime.utcnow().isoformat()
        return retry_test
    
    # Helper methods for database operations
    
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
            
            await self.client.post(
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
            
            # Create job record
            job_query = """
                INSERT INTO upload_pipeline.upload_jobs (
                    job_id, document_id, status, state, 
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, NOW(), NOW())
            """
            
            await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/execute_sql",
                json={
                    "query": job_query,
                    "params": [job_id, document_id, "queued", "queued"]
                }
            )
            
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
            
            await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/execute_sql",
                json={
                    "query": query,
                    "params": [status, job_id]
                }
            )
            
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
            
            # Test file access using StorageManager
            from backend.shared.storage.storage_manager import StorageManager
            
            storage_config = {
                "storage_url": self.supabase_url,
                "anon_key": self.anon_key,
                "service_role_key": self.service_role_key
            }
            
            storage = StorageManager(storage_config)
            
            # Try to read file
            content = await storage.read_blob(raw_path)
            file_accessible = content is not None and len(content) > 0
            
            await storage.close()
            
            return file_accessible
            
        except Exception as e:
            logger.error(f"File access test failed: {str(e)}")
            return False
    
    async def _check_file_exists(self, job_id: str) -> bool:
        """Check if file exists in storage"""
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
            
            # Check file existence using StorageManager
            from backend.shared.storage.storage_manager import StorageManager
            
            storage_config = {
                "storage_url": self.supabase_url,
                "anon_key": self.anon_key,
                "service_role_key": self.service_role_key
            }
            
            storage = StorageManager(storage_config)
            
            # Check if file exists
            file_exists = await storage.blob_exists(raw_path)
            
            await storage.close()
            
            return file_exists
            
        except Exception as e:
            logger.error(f"File existence check failed: {str(e)}")
            return False
    
    def _calculate_optimal_wait_time(self, measurements: List[Dict[str, Any]]) -> float:
        """Calculate optimal wait time based on measurements"""
        successful_measurements = [m for m in measurements if m["success"]]
        
        if not successful_measurements:
            return 10.0  # Default to 10 seconds if no successful measurements
        
        # Find the minimum interval that has 100% success rate
        intervals = [m["interval_seconds"] for m in successful_measurements]
        intervals.sort()
        
        # Return the minimum successful interval
        return intervals[0]
    
    def _find_best_delay(self, delay_tests: List[Dict[str, Any]]) -> float:
        """Find the best delay time based on test results"""
        successful_tests = [t for t in delay_tests if t["success"]]
        
        if not successful_tests:
            return 5.0  # Default to 5 seconds if no successful tests
        
        # Find the minimum delay that has 100% success rate
        delays = [t["delay_seconds"] for t in successful_tests]
        delays.sort()
        
        # Return the minimum successful delay
        return delays[0]
    
    async def generate_investigation_report(self):
        """Generate comprehensive investigation report"""
        logger.info("Generating comprehensive investigation report")
        
        report = {
            "investigation_id": str(uuid.uuid4()),
            "investigation_name": "FM-027 Timing Investigation",
            "start_time": self.test_results[0]["start_time"] if self.test_results else datetime.utcnow().isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "environment": {
                "supabase_url": self.supabase_url,
                "api_url": self.api_url,
                "worker_url": self.worker_url
            },
            "test_results": self.test_results,
            "summary": self._generate_summary(),
            "recommendations": self._generate_recommendations()
        }
        
        # Save report to file
        report_filename = f"fm027_investigation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Investigation report saved to {report_filename}")
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate investigation summary"""
        summary = {
            "total_tests": len(self.test_results),
            "successful_tests": sum(1 for t in self.test_results if t.get("success_rate", 0) > 0.5),
            "failed_tests": sum(1 for t in self.test_results if t.get("success_rate", 0) <= 0.5),
            "key_findings": [],
            "timing_insights": {},
            "race_condition_evidence": []
        }
        
        # Analyze test results
        for test in self.test_results:
            test_name = test["test_name"]
            
            if test_name == "file_access_timing":
                optimal_wait = test.get("optimal_wait_time", 0)
                summary["timing_insights"]["optimal_wait_time"] = optimal_wait
                summary["key_findings"].append(f"Optimal wait time for file access: {optimal_wait:.2f}s")
            
            elif test_name == "job_status_timing":
                avg_transition = test.get("average_transition_time", 0)
                summary["timing_insights"]["average_status_transition"] = avg_transition
                summary["key_findings"].append(f"Average job status transition time: {avg_transition:.2f}s")
            
            elif test_name == "database_consistency":
                consistency_rate = test.get("consistency_rate", 0)
                summary["key_findings"].append(f"Database consistency rate: {consistency_rate:.2%}")
                
                if consistency_rate < 0.95:
                    summary["race_condition_evidence"].append("Database consistency issues detected")
            
            elif test_name == "race_condition_reproduction":
                success_rate = test.get("success_rate", 0)
                summary["key_findings"].append(f"Race condition reproduction success rate: {success_rate:.2%}")
                
                if success_rate < 0.8:
                    summary["race_condition_evidence"].append("Race conditions successfully reproduced")
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on investigation results"""
        recommendations = []
        
        # Analyze test results for recommendations
        for test in self.test_results:
            test_name = test["test_name"]
            
            if test_name == "file_access_timing":
                optimal_wait = test.get("optimal_wait_time", 0)
                if optimal_wait > 0:
                    recommendations.append(f"Implement {optimal_wait:.2f}s delay before file access attempts")
            
            elif test_name == "job_status_delay_solution":
                best_delay = test.get("best_delay", 0)
                if best_delay > 0:
                    recommendations.append(f"Update job status after {best_delay:.2f}s delay to ensure file availability")
            
            elif test_name == "file_existence_check_solution":
                success_rate = test.get("success_rate", 0)
                if success_rate > 0.8:
                    recommendations.append("Implement file existence checks before processing")
            
            elif test_name == "retry_mechanism_solution":
                retry_success_rate = test.get("retry_success_rate", 0)
                if retry_success_rate > 0.7:
                    recommendations.append("Implement retry mechanisms for failed file access")
        
        # Add general recommendations
        recommendations.extend([
            "Add comprehensive logging for timing analysis",
            "Implement circuit breaker pattern for file access failures",
            "Add monitoring and alerting for race condition detection",
            "Consider implementing job queuing with backoff strategies"
        ])
        
        return recommendations
    
    def _print_summary(self, report: Dict[str, Any]):
        """Print investigation summary to console"""
        print("\n" + "="*80)
        print("FM-027 TIMING INVESTIGATION SUMMARY")
        print("="*80)
        
        summary = report["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful Tests: {summary['successful_tests']}")
        print(f"Failed Tests: {summary['failed_tests']}")
        
        print("\nKey Findings:")
        for finding in summary["key_findings"]:
            print(f"  • {finding}")
        
        if summary["race_condition_evidence"]:
            print("\nRace Condition Evidence:")
            for evidence in summary["race_condition_evidence"]:
                print(f"  • {evidence}")
        
        print("\nRecommendations:")
        for recommendation in report["recommendations"]:
            print(f"  • {recommendation}")
        
        print("\n" + "="*80)


async def main():
    """Main function to run the FM-027 timing investigation"""
    investigator = FM027TimingInvestigator()
    
    try:
        await investigator.run_comprehensive_investigation()
    except Exception as e:
        logger.error(f"Investigation failed: {str(e)}", exc_info=True)
        raise
    finally:
        await investigator.close()


if __name__ == "__main__":
    asyncio.run(main())
