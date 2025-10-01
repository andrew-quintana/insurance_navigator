#!/usr/bin/env python3
"""
FM-027 Race Condition Reproduction Test

This script reproduces the race condition that causes the error:
"Document file is not accessible for processing. Please try uploading again."

The test simulates the timing issues between job creation and file access.
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

class FM027RaceConditionTest:
    """Test for reproducing FM-027 race conditions"""
    
    def __init__(self):
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
        
        logger.info(f"FM027 Race Condition Test initialized for {self.supabase_url}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.close()
    
    async def run_race_condition_tests(self):
        """Run comprehensive race condition tests"""
        logger.info("Starting FM-027 race condition reproduction tests")
        
        try:
            # Test 1: Immediate file access after job creation
            await self.test_immediate_file_access_race()
            
            # Test 2: Job status update timing
            await self.test_job_status_timing_race()
            
            # Test 3: Concurrent job processing race
            await self.test_concurrent_processing_race()
            
            # Test 4: File upload timing race
            await self.test_file_upload_timing_race()
            
            # Test 5: Database transaction race
            await self.test_database_transaction_race()
            
            # Generate comprehensive report
            await self.generate_race_condition_report()
            
        except Exception as e:
            logger.error(f"Race condition tests failed: {str(e)}", exc_info=True)
            raise
        finally:
            await self.close()
    
    async def test_immediate_file_access_race(self):
        """Test immediate file access after job creation (race condition)"""
        logger.info("=== Test 1: Immediate File Access Race Condition ===")
        
        test_result = {
            "test_name": "immediate_file_access_race",
            "start_time": datetime.utcnow().isoformat(),
            "scenarios": [],
            "race_condition_detected": False
        }
        
        try:
            # Scenario 1: Create job and immediately try to access file
            scenario1 = await self._test_immediate_access_scenario()
            test_result["scenarios"].append(scenario1)
            
            # Scenario 2: Create job, update status, immediately access file
            scenario2 = await self._test_status_update_immediate_access_scenario()
            test_result["scenarios"].append(scenario2)
            
            # Scenario 3: Create job, simulate file upload, immediately access
            scenario3 = await self._test_upload_immediate_access_scenario()
            test_result["scenarios"].append(scenario3)
            
            # Analyze results
            race_conditions = sum(1 for s in test_result["scenarios"] if s.get("race_condition", False))
            test_result["race_condition_detected"] = race_conditions > 0
            test_result["race_condition_count"] = race_conditions
            
            logger.info(f"Immediate file access race test: {race_conditions} race conditions detected")
            
        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"Immediate file access race test failed: {str(e)}")
        
        test_result["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(test_result)
    
    async def test_job_status_timing_race(self):
        """Test job status update timing race conditions"""
        logger.info("=== Test 2: Job Status Timing Race Condition ===")
        
        test_result = {
            "test_name": "job_status_timing_race",
            "start_time": datetime.utcnow().isoformat(),
            "timing_analysis": [],
            "race_condition_detected": False
        }
        
        try:
            # Test different timing scenarios
            timing_scenarios = [
                {"delay_before_status_update": 0.0, "description": "No delay"},
                {"delay_before_status_update": 0.1, "description": "100ms delay"},
                {"delay_before_status_update": 0.5, "description": "500ms delay"},
                {"delay_before_status_update": 1.0, "description": "1s delay"},
                {"delay_before_status_update": 2.0, "description": "2s delay"}
            ]
            
            for scenario in timing_scenarios:
                timing_result = await self._test_status_timing_scenario(scenario)
                test_result["timing_analysis"].append(timing_result)
            
            # Analyze timing results
            race_conditions = sum(1 for t in test_result["timing_analysis"] if t.get("race_condition", False))
            test_result["race_condition_detected"] = race_conditions > 0
            test_result["race_condition_count"] = race_conditions
            
            # Find optimal timing
            successful_timings = [t for t in test_result["timing_analysis"] if t.get("success", False)]
            if successful_timings:
                optimal_delay = min(t["delay_before_status_update"] for t in successful_timings)
                test_result["optimal_delay"] = optimal_delay
            
            logger.info(f"Job status timing race test: {race_conditions} race conditions detected")
            
        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"Job status timing race test failed: {str(e)}")
        
        test_result["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(test_result)
    
    async def test_concurrent_processing_race(self):
        """Test concurrent job processing race conditions"""
        logger.info("=== Test 3: Concurrent Processing Race Condition ===")
        
        test_result = {
            "test_name": "concurrent_processing_race",
            "start_time": datetime.utcnow().isoformat(),
            "concurrent_tests": [],
            "race_condition_detected": False
        }
        
        try:
            # Test different concurrency levels
            concurrency_levels = [2, 5, 10, 20]
            
            for level in concurrency_levels:
                concurrent_result = await self._test_concurrent_processing_scenario(level)
                test_result["concurrent_tests"].append(concurrent_result)
            
            # Analyze concurrent results
            race_conditions = sum(1 for t in test_result["concurrent_tests"] if t.get("race_condition", False))
            test_result["race_condition_detected"] = race_conditions > 0
            test_result["race_condition_count"] = race_conditions
            
            logger.info(f"Concurrent processing race test: {race_conditions} race conditions detected")
            
        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"Concurrent processing race test failed: {str(e)}")
        
        test_result["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(test_result)
    
    async def test_file_upload_timing_race(self):
        """Test file upload timing race conditions"""
        logger.info("=== Test 4: File Upload Timing Race Condition ===")
        
        test_result = {
            "test_name": "file_upload_timing_race",
            "start_time": datetime.utcnow().isoformat(),
            "upload_timing_tests": [],
            "race_condition_detected": False
        }
        
        try:
            # Test different upload timing scenarios
            upload_scenarios = [
                {"upload_delay": 0.0, "description": "Immediate upload"},
                {"upload_delay": 0.1, "description": "100ms upload delay"},
                {"upload_delay": 0.5, "description": "500ms upload delay"},
                {"upload_delay": 1.0, "description": "1s upload delay"},
                {"upload_delay": 2.0, "description": "2s upload delay"}
            ]
            
            for scenario in upload_scenarios:
                upload_result = await self._test_upload_timing_scenario(scenario)
                test_result["upload_timing_tests"].append(upload_result)
            
            # Analyze upload timing results
            race_conditions = sum(1 for t in test_result["upload_timing_tests"] if t.get("race_condition", False))
            test_result["race_condition_detected"] = race_conditions > 0
            test_result["race_condition_count"] = race_conditions
            
            logger.info(f"File upload timing race test: {race_conditions} race conditions detected")
            
        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"File upload timing race test failed: {str(e)}")
        
        test_result["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(test_result)
    
    async def test_database_transaction_race(self):
        """Test database transaction race conditions"""
        logger.info("=== Test 5: Database Transaction Race Condition ===")
        
        test_result = {
            "test_name": "database_transaction_race",
            "start_time": datetime.utcnow().isoformat(),
            "transaction_tests": [],
            "race_condition_detected": False
        }
        
        try:
            # Test different transaction scenarios
            transaction_scenarios = [
                {"scenario": "concurrent_job_creation", "description": "Concurrent job creation"},
                {"scenario": "concurrent_status_updates", "description": "Concurrent status updates"},
                {"scenario": "job_cleanup_during_processing", "description": "Job cleanup during processing"},
                {"scenario": "database_lock_contention", "description": "Database lock contention"}
            ]
            
            for scenario in transaction_scenarios:
                transaction_result = await self._test_transaction_scenario(scenario)
                test_result["transaction_tests"].append(transaction_result)
            
            # Analyze transaction results
            race_conditions = sum(1 for t in test_result["transaction_tests"] if t.get("race_condition", False))
            test_result["race_condition_detected"] = race_conditions > 0
            test_result["race_condition_count"] = race_conditions
            
            logger.info(f"Database transaction race test: {race_conditions} race conditions detected")
            
        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"Database transaction race test failed: {str(e)}")
        
        test_result["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(test_result)
    
    # Helper methods for test scenarios
    
    async def _test_immediate_access_scenario(self):
        """Test immediate file access scenario"""
        scenario = {
            "name": "immediate_access",
            "start_time": datetime.utcnow().isoformat(),
            "race_condition": False,
            "success": False,
            "error": None,
            "timing": {}
        }
        
        try:
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job
            await self._create_test_job(job_id, document_id)
            scenario["timing"]["job_creation"] = datetime.utcnow().isoformat()
            
            # Immediately try to access file (this should fail due to race condition)
            file_access_start = time.time()
            file_accessible = await self._test_file_access(job_id)
            file_access_duration = time.time() - file_access_start
            
            scenario["timing"]["file_access_duration"] = file_access_duration
            scenario["timing"]["file_accessible"] = file_accessible
            scenario["success"] = file_accessible
            scenario["race_condition"] = not file_accessible  # Race condition if file not accessible
            
            if not file_accessible:
                scenario["error"] = "File not accessible immediately after job creation - race condition detected"
            
        except Exception as e:
            scenario["error"] = str(e)
            scenario["success"] = False
            scenario["race_condition"] = True  # Exception indicates race condition
        
        scenario["end_time"] = datetime.utcnow().isoformat()
        return scenario
    
    async def _test_status_update_immediate_access_scenario(self):
        """Test status update followed by immediate file access"""
        scenario = {
            "name": "status_update_immediate_access",
            "start_time": datetime.utcnow().isoformat(),
            "race_condition": False,
            "success": False,
            "error": None,
            "timing": {}
        }
        
        try:
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job
            await self._create_test_job(job_id, document_id)
            scenario["timing"]["job_creation"] = datetime.utcnow().isoformat()
            
            # Update job status to uploaded
            await self._update_job_status(job_id, "uploaded")
            scenario["timing"]["status_update"] = datetime.utcnow().isoformat()
            
            # Immediately try to access file
            file_access_start = time.time()
            file_accessible = await self._test_file_access(job_id)
            file_access_duration = time.time() - file_access_start
            
            scenario["timing"]["file_access_duration"] = file_access_duration
            scenario["timing"]["file_accessible"] = file_accessible
            scenario["success"] = file_accessible
            scenario["race_condition"] = not file_accessible
            
            if not file_accessible:
                scenario["error"] = "File not accessible after status update - race condition detected"
            
        except Exception as e:
            scenario["error"] = str(e)
            scenario["success"] = False
            scenario["race_condition"] = True
        
        scenario["end_time"] = datetime.utcnow().isoformat()
        return scenario
    
    async def _test_upload_immediate_access_scenario(self):
        """Test file upload followed by immediate access"""
        scenario = {
            "name": "upload_immediate_access",
            "start_time": datetime.utcnow().isoformat(),
            "race_condition": False,
            "success": False,
            "error": None,
            "timing": {}
        }
        
        try:
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job
            await self._create_test_job(job_id, document_id)
            scenario["timing"]["job_creation"] = datetime.utcnow().isoformat()
            
            # Simulate file upload (update document status)
            await self._update_document_status(document_id, "uploaded")
            scenario["timing"]["file_upload"] = datetime.utcnow().isoformat()
            
            # Update job status
            await self._update_job_status(job_id, "uploaded")
            scenario["timing"]["status_update"] = datetime.utcnow().isoformat()
            
            # Immediately try to access file
            file_access_start = time.time()
            file_accessible = await self._test_file_access(job_id)
            file_access_duration = time.time() - file_access_start
            
            scenario["timing"]["file_access_duration"] = file_access_duration
            scenario["timing"]["file_accessible"] = file_accessible
            scenario["success"] = file_accessible
            scenario["race_condition"] = not file_accessible
            
            if not file_accessible:
                scenario["error"] = "File not accessible after upload - race condition detected"
            
        except Exception as e:
            scenario["error"] = str(e)
            scenario["success"] = False
            scenario["race_condition"] = True
        
        scenario["end_time"] = datetime.utcnow().isoformat()
        return scenario
    
    async def _test_status_timing_scenario(self, scenario_config):
        """Test status timing scenario"""
        timing_result = {
            "delay_before_status_update": scenario_config["delay_before_status_update"],
            "description": scenario_config["description"],
            "start_time": datetime.utcnow().isoformat(),
            "race_condition": False,
            "success": False,
            "error": None,
            "timing": {}
        }
        
        try:
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job
            await self._create_test_job(job_id, document_id)
            timing_result["timing"]["job_creation"] = datetime.utcnow().isoformat()
            
            # Wait for specified delay
            await asyncio.sleep(scenario_config["delay_before_status_update"])
            timing_result["timing"]["delay_complete"] = datetime.utcnow().isoformat()
            
            # Update job status
            await self._update_job_status(job_id, "uploaded")
            timing_result["timing"]["status_update"] = datetime.utcnow().isoformat()
            
            # Try to access file
            file_access_start = time.time()
            file_accessible = await self._test_file_access(job_id)
            file_access_duration = time.time() - file_access_start
            
            timing_result["timing"]["file_access_duration"] = file_access_duration
            timing_result["timing"]["file_accessible"] = file_accessible
            timing_result["success"] = file_accessible
            timing_result["race_condition"] = not file_accessible
            
            if not file_accessible:
                timing_result["error"] = f"File not accessible with {scenario_config['delay_before_status_update']}s delay"
            
        except Exception as e:
            timing_result["error"] = str(e)
            timing_result["success"] = False
            timing_result["race_condition"] = True
        
        timing_result["end_time"] = datetime.utcnow().isoformat()
        return timing_result
    
    async def _test_concurrent_processing_scenario(self, concurrency_level):
        """Test concurrent processing scenario"""
        concurrent_result = {
            "concurrency_level": concurrency_level,
            "start_time": datetime.utcnow().isoformat(),
            "race_condition": False,
            "success": False,
            "error": None,
            "concurrent_jobs": []
        }
        
        try:
            # Create multiple jobs concurrently
            jobs = []
            for i in range(concurrency_level):
                job_id = str(uuid.uuid4())
                document_id = str(uuid.uuid4())
                jobs.append((job_id, document_id))
            
            # Create all jobs concurrently
            create_tasks = [self._create_test_job(job_id, document_id) for job_id, document_id in jobs]
            await asyncio.gather(*create_tasks)
            
            # Update all job statuses concurrently
            update_tasks = [self._update_job_status(job_id, "uploaded") for job_id, _ in jobs]
            await asyncio.gather(*update_tasks)
            
            # Try to access all files concurrently
            access_tasks = [self._test_file_access(job_id) for job_id, _ in jobs]
            results = await asyncio.gather(*access_tasks, return_exceptions=True)
            
            # Analyze results
            successful_accesses = sum(1 for result in results if result is True)
            failed_accesses = sum(1 for result in results if isinstance(result, Exception) or result is False)
            
            concurrent_result["concurrent_jobs"] = [
                {
                    "job_id": job_id,
                    "file_accessible": result is True,
                    "error": str(result) if isinstance(result, Exception) else None
                }
                for (job_id, _), result in zip(jobs, results)
            ]
            
            concurrent_result["success"] = successful_accesses > 0
            concurrent_result["success_rate"] = successful_accesses / concurrency_level
            concurrent_result["race_condition"] = failed_accesses > 0
            
            if failed_accesses > 0:
                concurrent_result["error"] = f"{failed_accesses} out of {concurrency_level} jobs failed due to race conditions"
            
        except Exception as e:
            concurrent_result["error"] = str(e)
            concurrent_result["success"] = False
            concurrent_result["race_condition"] = True
        
        concurrent_result["end_time"] = datetime.utcnow().isoformat()
        return concurrent_result
    
    async def _test_upload_timing_scenario(self, scenario_config):
        """Test upload timing scenario"""
        upload_result = {
            "upload_delay": scenario_config["upload_delay"],
            "description": scenario_config["description"],
            "start_time": datetime.utcnow().isoformat(),
            "race_condition": False,
            "success": False,
            "error": None,
            "timing": {}
        }
        
        try:
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create job
            await self._create_test_job(job_id, document_id)
            upload_result["timing"]["job_creation"] = datetime.utcnow().isoformat()
            
            # Wait for upload delay
            await asyncio.sleep(scenario_config["upload_delay"])
            upload_result["timing"]["upload_delay_complete"] = datetime.utcnow().isoformat()
            
            # Simulate file upload
            await self._update_document_status(document_id, "uploaded")
            upload_result["timing"]["file_upload"] = datetime.utcnow().isoformat()
            
            # Update job status
            await self._update_job_status(job_id, "uploaded")
            upload_result["timing"]["status_update"] = datetime.utcnow().isoformat()
            
            # Try to access file
            file_access_start = time.time()
            file_accessible = await self._test_file_access(job_id)
            file_access_duration = time.time() - file_access_start
            
            upload_result["timing"]["file_access_duration"] = file_access_duration
            upload_result["timing"]["file_accessible"] = file_accessible
            upload_result["success"] = file_accessible
            upload_result["race_condition"] = not file_accessible
            
            if not file_accessible:
                upload_result["error"] = f"File not accessible with {scenario_config['upload_delay']}s upload delay"
            
        except Exception as e:
            upload_result["error"] = str(e)
            upload_result["success"] = False
            upload_result["race_condition"] = True
        
        upload_result["end_time"] = datetime.utcnow().isoformat()
        return upload_result
    
    async def _test_transaction_scenario(self, scenario_config):
        """Test transaction scenario"""
        transaction_result = {
            "scenario": scenario_config["scenario"],
            "description": scenario_config["description"],
            "start_time": datetime.utcnow().isoformat(),
            "race_condition": False,
            "success": False,
            "error": None,
            "timing": {}
        }
        
        try:
            if scenario_config["scenario"] == "concurrent_job_creation":
                # Test concurrent job creation
                jobs = []
                for i in range(5):
                    job_id = str(uuid.uuid4())
                    document_id = str(uuid.uuid4())
                    jobs.append((job_id, document_id))
                
                # Create jobs concurrently
                create_tasks = [self._create_test_job(job_id, document_id) for job_id, document_id in jobs]
                await asyncio.gather(*create_tasks)
                
                # Check if all jobs exist
                existence_tasks = [self._check_job_exists(job_id) for job_id, _ in jobs]
                existence_results = await asyncio.gather(*existence_tasks)
                
                transaction_result["success"] = all(existence_results)
                transaction_result["race_condition"] = not all(existence_results)
                
            elif scenario_config["scenario"] == "concurrent_status_updates":
                # Test concurrent status updates
                job_id = str(uuid.uuid4())
                document_id = str(uuid.uuid4())
                
                await self._create_test_job(job_id, document_id)
                
                # Update status concurrently
                update_tasks = [
                    self._update_job_status(job_id, "uploaded"),
                    self._update_job_status(job_id, "parse_queued"),
                    self._update_job_status(job_id, "parsed")
                ]
                
                await asyncio.gather(*update_tasks)
                
                # Check final status
                final_status = await self._get_job_status(job_id)
                transaction_result["success"] = final_status is not None
                transaction_result["race_condition"] = final_status is None
                
            elif scenario_config["scenario"] == "job_cleanup_during_processing":
                # Test job cleanup during processing
                job_id = str(uuid.uuid4())
                document_id = str(uuid.uuid4())
                
                await self._create_test_job(job_id, document_id)
                
                # Simulate processing delay
                await asyncio.sleep(0.1)
                
                # Check if job still exists
                job_exists = await self._check_job_exists(job_id)
                transaction_result["success"] = job_exists
                transaction_result["race_condition"] = not job_exists
                
            elif scenario_config["scenario"] == "database_lock_contention":
                # Test database lock contention
                job_id = str(uuid.uuid4())
                document_id = str(uuid.uuid4())
                
                await self._create_test_job(job_id, document_id)
                
                # Simulate concurrent database operations
                operations = [
                    self._update_job_status(job_id, "uploaded"),
                    self._get_job_status(job_id),
                    self._check_job_exists(job_id)
                ]
                
                results = await asyncio.gather(*operations, return_exceptions=True)
                transaction_result["success"] = not any(isinstance(r, Exception) for r in results)
                transaction_result["race_condition"] = any(isinstance(r, Exception) for r in results)
            
        except Exception as e:
            transaction_result["error"] = str(e)
            transaction_result["success"] = False
            transaction_result["race_condition"] = True
        
        transaction_result["end_time"] = datetime.utcnow().isoformat()
        return transaction_result
    
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
            
        except Exception as e:
            logger.error(f"Failed to update job status: {str(e)}")
            raise
    
    async def _update_document_status(self, document_id: str, status: str):
        """Update document status in database"""
        try:
            query = """
                UPDATE upload_pipeline.documents
                SET processing_status = $1, updated_at = NOW()
                WHERE document_id = $2
            """
            
            response = await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/execute_sql",
                json={
                    "query": query,
                    "params": [status, document_id]
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to update document status: {response.text}")
            
        except Exception as e:
            logger.error(f"Failed to update document status: {str(e)}")
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
    
    async def generate_race_condition_report(self):
        """Generate comprehensive race condition report"""
        logger.info("Generating FM-027 race condition report")
        
        report = {
            "test_id": str(uuid.uuid4()),
            "test_name": "FM-027 Race Condition Reproduction",
            "start_time": self.test_results[0]["start_time"] if self.test_results else datetime.utcnow().isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "environment": {
                "supabase_url": self.supabase_url
            },
            "test_results": self.test_results,
            "summary": self._generate_summary(),
            "recommendations": self._generate_recommendations(),
            "solutions": self._generate_solutions()
        }
        
        # Save report to file
        report_filename = f"fm027_race_condition_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Race condition report saved to {report_filename}")
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        summary = {
            "total_tests": len(self.test_results),
            "tests_with_race_conditions": sum(1 for t in self.test_results if t.get("race_condition_detected", False)),
            "total_race_conditions": sum(t.get("race_condition_count", 0) for t in self.test_results),
            "key_findings": [],
            "race_condition_evidence": []
        }
        
        # Analyze test results
        for test in self.test_results:
            test_name = test["test_name"]
            
            if test.get("race_condition_detected", False):
                summary["race_condition_evidence"].append(f"{test_name}: {test.get('race_condition_count', 0)} race conditions detected")
            
            if test_name == "immediate_file_access_race":
                race_count = test.get("race_condition_count", 0)
                summary["key_findings"].append(f"Immediate file access race conditions: {race_count}")
            
            elif test_name == "job_status_timing_race":
                race_count = test.get("race_condition_count", 0)
                optimal_delay = test.get("optimal_delay", None)
                summary["key_findings"].append(f"Job status timing race conditions: {race_count}")
                if optimal_delay is not None:
                    summary["key_findings"].append(f"Optimal delay for status updates: {optimal_delay:.2f}s")
            
            elif test_name == "concurrent_processing_race":
                race_count = test.get("race_condition_count", 0)
                summary["key_findings"].append(f"Concurrent processing race conditions: {race_count}")
            
            elif test_name == "file_upload_timing_race":
                race_count = test.get("race_condition_count", 0)
                summary["key_findings"].append(f"File upload timing race conditions: {race_count}")
            
            elif test_name == "database_transaction_race":
                race_count = test.get("race_condition_count", 0)
                summary["key_findings"].append(f"Database transaction race conditions: {race_count}")
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Analyze test results for recommendations
        for test in self.test_results:
            test_name = test["test_name"]
            
            if test.get("race_condition_detected", False):
                if test_name == "immediate_file_access_race":
                    recommendations.append("Implement file existence checks before processing")
                    recommendations.append("Add retry mechanisms for failed file access")
                
                elif test_name == "job_status_timing_race":
                    optimal_delay = test.get("optimal_delay")
                    if optimal_delay is not None:
                        recommendations.append(f"Implement {optimal_delay:.2f}s delay before job status updates")
                    else:
                        recommendations.append("Implement configurable delay before job status updates")
                
                elif test_name == "concurrent_processing_race":
                    recommendations.append("Implement job queuing with backoff strategies")
                    recommendations.append("Add concurrency limits for job processing")
                
                elif test_name == "file_upload_timing_race":
                    recommendations.append("Implement file upload verification before status updates")
                    recommendations.append("Add file availability checks before processing")
                
                elif test_name == "database_transaction_race":
                    recommendations.append("Implement database transaction locking")
                    recommendations.append("Add retry mechanisms for database operations")
        
        # Add general recommendations
        recommendations.extend([
            "Add comprehensive logging for timing analysis",
            "Implement circuit breaker pattern for file access failures",
            "Add monitoring and alerting for race condition detection",
            "Consider implementing job queuing with backoff strategies",
            "Add file existence checks before processing",
            "Implement retry mechanisms for failed file access",
            "Add job status update delays to ensure file availability"
        ])
        
        return recommendations
    
    def _generate_solutions(self) -> List[Dict[str, Any]]:
        """Generate specific solutions for race conditions"""
        solutions = [
            {
                "solution_name": "File Existence Check",
                "description": "Check if file exists before processing",
                "implementation": "Add file.blob_exists() check before processing",
                "code_example": """
# In worker processing
if not await storage.blob_exists(file_path):
    await asyncio.sleep(1.0)  # Wait and retry
    if not await storage.blob_exists(file_path):
        raise UserFacingError("File not accessible for processing")
                """,
                "priority": "high"
            },
            {
                "solution_name": "Job Status Update Delay",
                "description": "Add delay before updating job status to uploaded",
                "implementation": "Wait for file to be accessible before status update",
                "code_example": """
# In API service
await asyncio.sleep(2.0)  # Wait for file to be accessible
await update_job_status(job_id, "uploaded")
                """,
                "priority": "high"
            },
            {
                "solution_name": "Retry Mechanism",
                "description": "Implement retry mechanism for file access",
                "implementation": "Retry file access with exponential backoff",
                "code_example": """
# In worker
for attempt in range(max_retries):
    try:
        content = await storage.read_blob(file_path)
        break
    except Exception as e:
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise
                """,
                "priority": "medium"
            },
            {
                "solution_name": "Circuit Breaker",
                "description": "Implement circuit breaker for file access failures",
                "implementation": "Stop processing if too many file access failures",
                "code_example": """
# In worker
if self.circuit_breaker.is_open():
    raise ServiceUnavailableError("File access circuit breaker is open")
                """,
                "priority": "medium"
            },
            {
                "solution_name": "Job Queuing",
                "description": "Implement job queuing with backoff strategies",
                "implementation": "Queue jobs and process them with delays",
                "code_example": """
# In worker
await self.job_queue.put(job, delay=2.0)  # Queue with delay
                """,
                "priority": "low"
            }
        ]
        
        return solutions
    
    def _print_summary(self, report: Dict[str, Any]):
        """Print test summary to console"""
        print("\n" + "="*80)
        print("FM-027 RACE CONDITION REPRODUCTION SUMMARY")
        print("="*80)
        
        summary = report["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Tests with Race Conditions: {summary['tests_with_race_conditions']}")
        print(f"Total Race Conditions: {summary['total_race_conditions']}")
        
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
        
        print("\nSolutions:")
        for solution in report["solutions"]:
            print(f"  • {solution['solution_name']} ({solution['priority']} priority)")
            print(f"    {solution['description']}")
        
        print("\n" + "="*80)


async def main():
    """Main function to run the FM-027 race condition test"""
    tester = FM027RaceConditionTest()
    
    try:
        await tester.run_race_condition_tests()
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
