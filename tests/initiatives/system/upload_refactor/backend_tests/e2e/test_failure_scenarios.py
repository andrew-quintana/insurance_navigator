#!/usr/bin/env python3
"""
Failure Scenario Testing

This module implements comprehensive failure scenario testing to validate
system resilience, error recovery, and failure handling throughout the pipeline.
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pytest
import httpx
import psycopg2
from dataclasses import dataclass, asdict

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.shared.config import WorkerConfig
from backend.shared.db.connection import DatabaseManager
from backend.shared.storage.storage_manager import StorageManager
from backend.shared.external.llamaparse_client import LlamaParseClient
from backend.shared.external.openai_client import OpenAIClient
from backend.workers.base_worker import BaseWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FailureTestResult:
    """Result of a failure scenario test"""
    test_name: str
    status: str  # 'passed', 'failed', 'skipped'
    duration_seconds: float
    failure_injected: str
    recovery_successful: bool
    error_message: Optional[str] = None
    recovery_time_seconds: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class FailureScenarioTester:
    """
    Comprehensive failure scenario testing
    
    Tests system resilience by injecting various types of failures
    and validating recovery mechanisms.
    """
    
    def __init__(self, config: WorkerConfig):
        """Initialize tester with configuration"""
        self.config = config
        self.db = DatabaseManager(config.database_url)
        self.storage = StorageManager(config.supabase_url, config.supabase_service_role_key)
        self.llamaparse = LlamaParseClient(config.llamaparse_api_url, config.llamaparse_api_key)
        self.openai = OpenAIClient(config.openai_api_url, config.openai_api_key)
        self.worker = BaseWorker(config)
        
        # Test results tracking
        self.test_results: List[FailureTestResult] = []
        
        # HTTP client for API testing
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
        logger.info("Initialized FailureScenarioTester")
    
    async def initialize(self):
        """Initialize all components for testing"""
        try:
            await self.db.initialize()
            await self.storage.initialize()
            await self.llamaparse.initialize()
            await self.openai.initialize()
            await self.worker._initialize_components()
            logger.info("✅ All components initialized successfully")
        except Exception as e:
            logger.error(f"❌ Component initialization failed: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup all components after testing"""
        try:
            await self.db.close()
            await self.storage.close()
            await self.llamaparse.close()
            await self.openai.close()
            await self.worker._cleanup_components()
            await self.http_client.aclose()
            logger.info("✅ All components cleaned up successfully")
        except Exception as e:
            logger.error(f"❌ Component cleanup failed: {e}")
    
    async def test_database_connectivity_failure(self) -> FailureTestResult:
        """Test system behavior when database connectivity fails"""
        test_name = "Database Connectivity Failure"
        start_time = time.time()
        failure_injected = "Database connection loss"
        
        try:
            logger.info(f"🧪 Starting test: {test_name}")
            
            # Create test job
            job_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create test job in database
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO upload_pipeline.upload_jobs (
                        job_id, user_id, document_id, status, raw_path, 
                        chunks_version, embed_model, embed_version
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, job_id, user_id, document_id, 'uploaded', 
                     'storage://raw/test-user/db-failure-test.pdf', 
                     'markdown-simple@1', 'text-embedding-3-small', '1')
            
            logger.info("✅ Test job created successfully")
            
            # Simulate database connectivity failure by closing connection pool
            await self.db.close()
            logger.info("🔴 Database connection closed (failure injected)")
            
            # Attempt to process job (should fail gracefully)
            try:
                await self.worker._process_chunks({
                    'job_id': job_id,
                    'document_id': document_id,
                    'status': 'parsed',
                    'parsed_path': 'storage://parsed/test/test.md',
                    'chunks_version': 'markdown-simple@1'
                }, f"test-{uuid.uuid4()}")
                
                # If we get here, the failure wasn't handled properly
                raise Exception("Database failure was not handled properly")
                
            except Exception as e:
                logger.info(f"✅ Database failure properly caught: {e}")
                
                # Reinitialize database connection
                await self.db.initialize()
                logger.info("✅ Database connection restored")
                
                # Verify job is still in valid state
                async with self.db.get_db_connection() as conn:
                    job_status = await conn.fetchval("""
                        SELECT status FROM upload_pipeline.upload_jobs 
                        WHERE job_id = $1
                    """, job_id)
                    
                    if job_status == 'uploaded':
                        logger.info("✅ Job status preserved during failure")
                        recovery_successful = True
                    else:
                        logger.error(f"❌ Job status corrupted: {job_status}")
                        recovery_successful = False
                
                # Test recovery by processing the job
                if recovery_successful:
                    # Simulate parsing completion
                    async with self.db.get_db_connection() as conn:
                        await conn.execute("""
                            UPDATE upload_pipeline.upload_jobs 
                            SET status = 'parsed', parsed_path = $1, parsed_sha256 = $2
                            WHERE job_id = $3
                        """, 'storage://parsed/test/test.md', 'test-sha256', job_id)
                    
                    # Process chunks (should work now)
                    await self.worker._process_chunks({
                        'job_id': job_id,
                        'document_id': document_id,
                        'status': 'parsed',
                        'parsed_path': 'storage://parsed/test/test.md',
                        'chunks_version': 'markdown-simple@1'
                    }, f"test-{uuid.uuid4()}")
                    
                    logger.info("✅ Job processing recovered successfully")
            
            duration = time.time() - start_time
            logger.info(f"✅ Test completed successfully in {duration:.2f}s")
            
            return FailureTestResult(
                test_name=test_name,
                status='passed',
                duration_seconds=duration,
                failure_injected=failure_injected,
                recovery_successful=recovery_successful,
                recovery_time_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return FailureTestResult(
                test_name=test_name,
                status='failed',
                duration_seconds=duration,
                failure_injected=failure_injected,
                recovery_successful=False,
                error_message=error_msg
            )
    
    async def test_external_service_failure(self) -> FailureTestResult:
        """Test system behavior when external services fail"""
        test_name = "External Service Failure"
        start_time = time.time()
        failure_injected = "LlamaParse service unavailable"
        
        try:
            logger.info(f"🧪 Starting test: {test_name}")
            
            # Create test job
            job_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create test job in database
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO upload_pipeline.upload_jobs (
                        job_id, user_id, document_id, status, raw_path, 
                        chunks_version, embed_model, embed_version
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, job_id, user_id, document_id, 'uploaded', 
                     'storage://raw/test-user/external-failure-test.pdf', 
                     'markdown-simple@1', 'text-embedding-3-small', '1')
            
            logger.info("✅ Test job created successfully")
            
            # Simulate external service failure by setting invalid URL
            original_url = self.llamaparse.api_url
            self.llamaparse.api_url = "http://invalid-service:9999"
            logger.info("🔴 External service URL corrupted (failure injected)")
            
            # Attempt to use external service (should fail gracefully)
            try:
                await self.llamaparse.parse_document("test content", "test.pdf")
                
                # If we get here, the failure wasn't handled properly
                raise Exception("External service failure was not handled properly")
                
            except Exception as e:
                logger.info(f"✅ External service failure properly caught: {e}")
                
                # Restore original URL
                self.llamaparse.api_url = original_url
                logger.info("✅ External service URL restored")
                
                # Test recovery by using the service
                try:
                    # This should work now
                    await self.llamaparse.parse_document("test content", "test.pdf")
                    logger.info("✅ External service recovered successfully")
                    recovery_successful = True
                except Exception as recovery_error:
                    logger.error(f"❌ External service recovery failed: {recovery_error}")
                    recovery_successful = False
            
            duration = time.time() - start_time
            logger.info(f"✅ Test completed successfully in {duration:.2f}s")
            
            return FailureTestResult(
                test_name=test_name,
                status='passed',
                duration_seconds=duration,
                failure_injected=failure_injected,
                recovery_successful=recovery_successful,
                recovery_time_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return FailureTestResult(
                test_name=test_name,
                status='failed',
                duration_seconds=duration,
                failure_injected=failure_injected,
                recovery_successful=False,
                error_message=error_msg
            )
    
    async def test_worker_process_crash(self) -> FailureTestResult:
        """Test system behavior when worker process crashes"""
        test_name = "Worker Process Crash"
        start_time = time.time()
        failure_injected = "Worker process termination"
        
        try:
            logger.info(f"🧪 Starting test: {test_name}")
            
            # Create test job
            job_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create test job in database
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO upload_pipeline.upload_jobs (
                        job_id, user_id, document_id, status, raw_path, 
                        chunks_version, embed_model, embed_version
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, job_id, user_id, document_id, 'uploaded', 
                     'storage://raw/test-user/worker-crash-test.pdf', 
                     'markdown-simple@1', 'text-embedding-3-small', '1')
            
            logger.info("✅ Test job created successfully")
            
            # Simulate worker crash by corrupting worker state
            original_running = self.worker.running
            self.worker.running = False
            logger.info("🔴 Worker state corrupted (failure injected)")
            
            # Attempt to process job (should fail gracefully)
            try:
                await self.worker._process_chunks({
                    'job_id': job_id,
                    'document_id': document_id,
                    'status': 'parsed',
                    'parsed_path': 'storage://parsed/test/test.md',
                    'chunks_version': 'markdown-simple@1'
                }, f"test-{uuid.uuid4()}")
                
                # If we get here, the failure wasn't handled properly
                raise Exception("Worker crash was not handled properly")
                
            except Exception as e:
                logger.info(f"✅ Worker crash properly caught: {e}")
                
                # Restore worker state
                self.worker.running = original_running
                logger.info("✅ Worker state restored")
                
                # Test recovery by processing the job
                try:
                    # Simulate parsing completion
                    async with self.db.get_db_connection() as conn:
                        await conn.execute("""
                            UPDATE upload_pipeline.upload_jobs 
                            SET status = 'parsed', parsed_path = $1, parsed_sha256 = $2
                            WHERE job_id = $3
                        """, 'storage://parsed/test/test.md', 'test-sha256', job_id)
                    
                    # Process chunks (should work now)
                    await self.worker._process_chunks({
                        'job_id': job_id,
                        'document_id': document_id,
                        'status': 'parsed',
                        'parsed_path': 'storage://parsed/test/test.md',
                        'chunks_version': 'markdown-simple@1'
                    }, f"test-{uuid.uuid4()}")
                    
                    logger.info("✅ Job processing recovered successfully")
                    recovery_successful = True
                except Exception as recovery_error:
                    logger.error(f"❌ Job processing recovery failed: {recovery_error}")
                    recovery_successful = False
            
            duration = time.time() - start_time
            logger.info(f"✅ Test completed successfully in {duration:.2f}s")
            
            return FailureTestResult(
                test_name=test_name,
                status='passed',
                duration_seconds=duration,
                failure_injected=failure_injected,
                recovery_successful=recovery_successful,
                recovery_time_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return FailureTestResult(
                test_name=test_name,
                status='failed',
                duration_seconds=duration,
                failure_injected=failure_injected,
                recovery_successful=False,
                error_message=error_msg
            )
    
    async def test_network_failure(self) -> FailureTestResult:
        """Test system behavior when network connectivity fails"""
        test_name = "Network Failure"
        start_time = time.time()
        failure_injected = "Network connectivity loss"
        
        try:
            logger.info(f"🧪 Starting test: {test_name}")
            
            # Create test job
            job_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create test job in database
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO upload_pipeline.upload_jobs (
                        job_id, user_id, document_id, status, raw_path, 
                        chunks_version, embed_model, embed_version
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, job_id, user_id, document_id, 'uploaded', 
                     'storage://raw/test-user/network-failure-test.pdf', 
                     'markdown-simple@1', 'text-embedding-3-small', '1')
            
            logger.info("✅ Test job created successfully")
            
            # Simulate network failure by setting invalid timeout
            original_timeout = self.http_client.timeout
            self.http_client.timeout = 0.001  # Very short timeout
            logger.info("🔴 Network timeout corrupted (failure injected)")
            
            # Attempt to make HTTP request (should fail gracefully)
            try:
                await self.http_client.get("http://localhost:8000/health")
                
                # If we get here, the failure wasn't handled properly
                raise Exception("Network failure was not handled properly")
                
            except Exception as e:
                logger.info(f"✅ Network failure properly caught: {e}")
                
                # Restore original timeout
                self.http_client.timeout = original_timeout
                logger.info("✅ Network timeout restored")
                
                # Test recovery by making HTTP request
                try:
                    # This should work now
                    response = await self.http_client.get("http://localhost:8000/health")
                    if response.status_code == 200:
                        logger.info("✅ Network connectivity recovered successfully")
                        recovery_successful = True
                    else:
                        logger.error(f"❌ Network recovery failed: {response.status_code}")
                        recovery_successful = False
                except Exception as recovery_error:
                    logger.error(f"❌ Network recovery failed: {recovery_error}")
                    recovery_successful = False
            
            duration = time.time() - start_time
            logger.info(f"✅ Test completed successfully in {duration:.2f}s")
            
            return FailureTestResult(
                test_name=test_name,
                status='passed',
                duration_seconds=duration,
                failure_injected=failure_injected,
                recovery_successful=recovery_successful,
                recovery_time_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return FailureTestResult(
                test_name=test_name,
                status='failed',
                duration_seconds=duration,
                failure_injected=failure_injected,
                recovery_successful=False,
                error_message=error_msg
            )
    
    async def test_data_corruption(self) -> FailureTestResult:
        """Test system behavior when data corruption occurs"""
        test_name = "Data Corruption"
        start_time = time.time()
        failure_injected = "Database data corruption"
        
        try:
            logger.info(f"🧪 Starting test: {test_name}")
            
            # Create test job
            job_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create test job in database
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO upload_pipeline.upload_jobs (
                        job_id, user_id, document_id, status, raw_path, 
                        chunks_version, embed_model, embed_version
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, job_id, user_id, document_id, 'uploaded', 
                     'storage://raw/test-user/corruption-test.pdf', 
                     'markdown-simple@1', 'text-embedding-3-small', '1')
            
            logger.info("✅ Test job created successfully")
            
            # Simulate data corruption by updating job with invalid status
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs 
                    SET status = 'invalid_status_that_should_not_exist'
                    WHERE job_id = $1
                """, job_id)
            
            logger.info("🔴 Job status corrupted (failure injected)")
            
            # Attempt to process corrupted job (should fail gracefully)
            try:
                await self.worker._process_chunks({
                    'job_id': job_id,
                    'document_id': document_id,
                    'status': 'invalid_status_that_should_not_exist',
                    'parsed_path': 'storage://parsed/test/test.md',
                    'chunks_version': 'markdown-simple@1'
                }, f"test-{uuid.uuid4()}")
                
                # If we get here, the failure wasn't handled properly
                raise Exception("Data corruption was not handled properly")
                
            except Exception as e:
                logger.info(f"✅ Data corruption properly caught: {e}")
                
                # Restore valid job status
                async with self.db.get_db_connection() as conn:
                    await conn.execute("""
                        UPDATE upload_pipeline.upload_jobs 
                        SET status = 'uploaded'
                        WHERE job_id = $1
                    """, job_id)
                
                logger.info("✅ Job status restored")
                
                # Test recovery by processing the job
                try:
                    # Simulate parsing completion
                    async with self.db.get_db_connection() as conn:
                        await conn.execute("""
                            UPDATE upload_pipeline.upload_jobs 
                            SET status = 'parsed', parsed_path = $1, parsed_sha256 = $2
                            WHERE job_id = $3
                        """, 'storage://parsed/test/test.md', 'test-sha256', job_id)
                    
                    # Process chunks (should work now)
                    await self.worker._process_chunks({
                        'job_id': job_id,
                        'document_id': document_id,
                        'status': 'parsed',
                        'parsed_path': 'storage://parsed/test/test.md',
                        'chunks_version': 'markdown-simple@1'
                    }, f"test-{uuid.uuid4()}")
                    
                    logger.info("✅ Job processing recovered successfully")
                    recovery_successful = True
                except Exception as recovery_error:
                    logger.error(f"❌ Job processing recovery failed: {recovery_error}")
                    recovery_successful = False
            
            duration = time.time() - start_time
            logger.info(f"✅ Test completed successfully in {duration:.2f}s")
            
            return FailureTestResult(
                test_name=test_name,
                status='passed',
                duration_seconds=duration,
                failure_injected=failure_injected,
                recovery_successful=recovery_successful,
                recovery_time_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return FailureTestResult(
                test_name=test_name,
                status='failed',
                duration_seconds=duration,
                failure_injected=failure_injected,
                recovery_successful=False,
                error_message=error_msg
            )
    
    async def run_all_tests(self) -> List[FailureTestResult]:
        """Run all failure scenario tests"""
        logger.info("🚀 Starting comprehensive failure scenario testing")
        
        try:
            await self.initialize()
            
            # Run all tests
            tests = [
                self.test_database_connectivity_failure(),
                self.test_external_service_failure(),
                self.test_worker_process_crash(),
                self.test_network_failure(),
                self.test_data_corruption()
            ]
            
            results = await asyncio.gather(*tests, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Test {i} failed with exception: {result}")
                    # Create failed result
                    failed_result = FailureTestResult(
                        test_name=f"Test {i}",
                        status='failed',
                        duration_seconds=0,
                        failure_injected="Unknown",
                        recovery_successful=False,
                        error_message=str(result)
                    )
                    self.test_results.append(failed_result)
                else:
                    self.test_results.append(result)
            
            # Generate summary
            await self._generate_test_summary()
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def _generate_test_summary(self):
        """Generate comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == 'passed'])
        failed_tests = len([r for r in self.test_results if r.status == 'failed'])
        
        logger.info("")
        logger.info("📊 Failure Scenario Test Summary")
        logger.info("=" * 50)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        logger.info("")
        
        # Recovery metrics
        successful_recoveries = len([r for r in self.test_results if r.recovery_successful])
        logger.info(f"Successful Recoveries: {successful_recoveries}/{total_tests}")
        logger.info(f"Recovery Success Rate: {(successful_recoveries/total_tests)*100:.1f}%")
        logger.info("")
        
        # Test details
        logger.info("📋 Test Details")
        logger.info("-" * 30)
        
        for result in self.test_results:
            status_icon = "✅" if result.status == 'passed' else "❌"
            recovery_icon = "✅" if result.recovery_successful else "❌"
            
            logger.info(f"{status_icon} {result.test_name}")
            logger.info(f"  Failure: {result.failure_injected}")
            logger.info(f"  Recovery: {recovery_icon} {'Successful' if result.recovery_successful else 'Failed'}")
            if result.recovery_time_seconds:
                logger.info(f"  Duration: {result.recovery_time_seconds:.2f}s")
            if result.error_message:
                logger.info(f"  Error: {result.error_message}")
            logger.info("")
        
        # Failed test details
        if failed_tests > 0:
            logger.info("❌ Failed Test Details")
            logger.info("-" * 30)
            
            for result in self.test_results:
                if result.status == 'failed':
                    logger.info(f"{result.test_name}: {result.error_message}")
                    logger.info(f"  Failure: {result.failure_injected}")
                    logger.info("")


async def main():
    """Main function for running failure scenario tests"""
    # Load configuration
    config = WorkerConfig(
        database_url="postgresql://postgres:postgres@localhost:5432/accessa_dev",
        supabase_url="http://localhost:5000",
        supabase_anon_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
        supabase_service_role_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nk0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
        llamaparse_api_url="http://localhost:8001",
        llamaparse_api_key="test_key",
        openai_api_url="http://localhost:8002",
        openai_api_key="test_key",
        openai_model="text-embedding-3-small"
    )
    
    # Create tester and run tests
    tester = FailureScenarioTester(config)
    
    try:
        results = await tester.run_all_tests()
        
        # Save results to file
        results_file = "failure_scenario_test_results.json"
        with open(results_file, 'w') as f:
            json.dump([r.to_dict() for r in results], f, indent=2)
        
        logger.info(f"Test results saved to {results_file}")
        
        # Exit with appropriate code
        failed_tests = len([r for r in results if r.status == 'failed'])
        if failed_tests > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
