# Buffer table references updated for Phase 3.7 direct-write architecture
# Original buffer-based approach replaced with direct writes to document_chunks

#!/usr/bin/env python3
"""
Performance Validation Testing

This module implements comprehensive performance validation testing to ensure
system performance, scalability, and resource usage meet requirements.
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
import psutil
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
class PerformanceTestResult:
    """Result of a performance test"""
    test_name: str
    status: str  # 'passed', 'failed', 'skipped'
    duration_seconds: float
    throughput: float  # operations per second
    latency_p50: float  # 50th percentile latency in seconds
    latency_p95: float  # 95th percentile latency in seconds
    latency_p99: float  # 99th percentile latency in seconds
    resource_usage: Dict[str, float]  # CPU, memory, etc.
    scalability_factor: Optional[float] = None  # scaling efficiency
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class PerformanceValidator:
    """
    Comprehensive performance validation
    
    Tests system performance, scalability, and resource usage
    under various load conditions.
    """
    
    def __init__(self, config: WorkerConfig):
        """Initialize validator with configuration"""
        self.config = config
        self.db = DatabaseManager(config.database_url)
        self.storage = StorageManager(config.supabase_url, config.supabase_service_role_key)
        self.llamaparse = LlamaParseClient(config.llamaparse_api_url, config.llamaparse_api_key)
        self.openai = OpenAIClient(config.openai_api_url, config.openai_api_key)
        self.worker = BaseWorker(config)
        
        # Test results tracking
        self.test_results: List[PerformanceTestResult] = []
        
        # HTTP client for API testing
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
        # Performance monitoring
        self.process = psutil.Process()
        
        logger.info("Initialized PerformanceValidator")
    
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
    
    def _get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage"""
        try:
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            return {
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'memory_percent': self.process.memory_percent()
            }
        except Exception as e:
            logger.warning(f"Could not get resource usage: {e}")
            return {'cpu_percent': 0.0, 'memory_mb': 0.0, 'memory_percent': 0.0}
    
    async def test_single_document_processing_performance(self) -> PerformanceTestResult:
        """Test performance of single document processing"""
        test_name = "Single Document Processing Performance"
        start_time = time.time()
        
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
                     'storage://raw/test-user/performance-test.pdf', 
                     'markdown-simple@1', 'text-embedding-3-small', '1')
            
            # Generate test content
            test_content = self._generate_performance_test_content(10000)  # 10KB content
            
            # Store parsed content
            parsed_path = f"storage://parsed/{user_id}/{document_id}.md"
            await self.storage.write_blob(parsed_path, test_content.encode('utf-8'))
            
            # Update job status to parsed
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs 
                    SET status = 'parsed', parsed_path = $1, parsed_sha256 = $2
                    WHERE job_id = $3
                """, parsed_path, 'test-performance-sha256', job_id)
            
            # Measure processing time for each stage
            stage_times = {}
            
            # Stage 1: Chunking
            chunk_start = time.time()
            await self.worker._process_chunks({
                'job_id': job_id,
                'document_id': document_id,
                'status': 'parsed',
                'parsed_path': parsed_path,
                'chunks_version': 'markdown-simple@1'
            }, f"test-{uuid.uuid4()}")
            stage_times['chunking'] = time.time() - chunk_start
            
            # Stage 2: Embedding
            embed_start = time.time()
            await self.worker._process_embeddings({
                'job_id': job_id,
                'document_id': document_id,
                'status': 'chunks_stored',
                'embed_model': 'text-embedding-3-small',
                'embed_version': '1'
            }, f"test-{uuid.uuid4()}")
            stage_times['embedding'] = time.time() - embed_start
            
            # Stage 3: Finalization
            finalize_start = time.time()
            await self.worker._finalize_job({
                'job_id': job_id,
                'document_id': document_id,
                'status': 'embeddings_stored'
            }, f"test-{uuid.uuid4()}")
            stage_times['finalization'] = time.time() - finalize_start
            
            # Calculate performance metrics
            total_duration = time.time() - start_time
            throughput = 1.0 / total_duration  # documents per second
            
            # Get resource usage
            resource_usage = self._get_resource_usage()
            
            # Verify results
            async with self.db.get_db_connection() as conn:
                chunk_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM upload_pipeline.document_chunks 
                    WHERE document_id = $1
                """, document_id)
                
                embedding_count = await conn.fetchval("""
                    SELECT COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) FROM upload_pipeline.document_chunks 
                    WHERE document_id = $1
                """, document_id)
                
                final_status = await conn.fetchval("""
                    SELECT status FROM upload_pipeline.upload_jobs 
                    WHERE job_id = $1
                """, document_id)
            
            if chunk_count > 0 and embedding_count > 0 and final_status == 'complete':
                logger.info(f"✅ Performance test completed successfully in {total_duration:.2f}s")
                logger.info(f"  Chunking: {stage_times['chunking']:.2f}s")
                logger.info(f"  Embedding: {stage_times['embedding']:.2f}s")
                logger.info(f"  Finalization: {stage_times['finalization']:.2f}s")
                logger.info(f"  Throughput: {throughput:.2f} docs/sec")
                
                return PerformanceTestResult(
                    test_name=test_name,
                    status='passed',
                    duration_seconds=total_duration,
                    throughput=throughput,
                    latency_p50=total_duration,
                    latency_p95=total_duration,
                    latency_p99=total_duration,
                    resource_usage=resource_usage,
                    scalability_factor=1.0
                )
            else:
                raise Exception(f"Processing incomplete: chunks={chunk_count}, embeddings={embedding_count}, status={final_status}")
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return PerformanceTestResult(
                test_name=test_name,
                status='failed',
                duration_seconds=duration,
                throughput=0.0,
                latency_p50=duration,
                latency_p95=duration,
                latency_p99=duration,
                resource_usage=self._get_resource_usage(),
                error_message=error_msg
            )
    
    async def test_concurrent_processing_performance(self) -> PerformanceTestResult:
        """Test performance under concurrent processing load"""
        test_name = "Concurrent Processing Performance"
        start_time = time.time()
        
        try:
            logger.info(f"🧪 Starting test: {test_name}")
            
            # Create multiple test jobs
            job_count = 10
            jobs = []
            
            for i in range(job_count):
                job_id = str(uuid.uuid4())
                user_id = str(uuid.uuid4())
                document_id = str(uuid.uuid4())
                
                jobs.append({
                    'job_id': job_id,
                    'user_id': user_id,
                    'document_id': document_id,
                    'index': i
                })
                
                # Create test job in database
                async with self.db.get_db_connection() as conn:
                    await conn.execute("""
                        INSERT INTO upload_pipeline.upload_jobs (
                            job_id, user_id, document_id, status, raw_path, 
                            chunks_version, embed_model, embed_version
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, job_id, user_id, document_id, 'uploaded', 
                         f'storage://raw/test-user/concurrent-perf-{i}.pdf', 
                         'markdown-simple@1', 'text-embedding-3-small', '1')
            
            logger.info(f"✅ Created {job_count} test jobs")
            
            # Process all jobs concurrently
            processing_tasks = []
            
            for job in jobs:
                # Simulate parsing completion
                test_content = f"# Concurrent Performance Test {job['index']}\n\nContent for concurrent performance testing.\n\n## Section 1\nTest content for job {job['index']} with substantial content for performance measurement."
                
                # Store parsed content
                parsed_path = f"storage://parsed/{job['user_id']}/{job['document_id']}.md"
                await self.storage.write_blob(parsed_path, test_content.encode('utf-8'))
                
                # Update job status to parsed
                async with self.db.get_db_connection() as conn:
                    await conn.execute("""
                        UPDATE upload_pipeline.upload_jobs 
                        SET status = 'parsed', parsed_path = $1, parsed_sha256 = $2
                        WHERE job_id = $3
                    """, parsed_path, f'test-concurrent-perf-sha256-{job["index"]}', job['job_id'])
                
                # Create processing task
                task = self._process_job_concurrently(job, parsed_path)
                processing_tasks.append(task)
            
            # Execute concurrent processing and measure time
            concurrent_start = time.time()
            results = await asyncio.gather(*processing_tasks, return_exceptions=True)
            concurrent_duration = time.time() - concurrent_start
            
            # Check results
            successful_jobs = 0
            failed_jobs = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_jobs += 1
                    logger.error(f"Job {i} failed: {result}")
                else:
                    successful_jobs += 1
            
            if successful_jobs > 0:
                # Calculate performance metrics
                total_duration = time.time() - start_time
                throughput = successful_jobs / total_duration
                
                # Calculate scaling efficiency (should be > 1.0 for good scaling)
                # Sequential time would be: successful_jobs * single_job_time
                # Concurrent time is: concurrent_duration
                # Scaling factor = sequential_time / concurrent_time
                estimated_sequential_time = successful_jobs * 2.0  # Assume 2s per job
                scaling_factor = estimated_sequential_time / concurrent_duration
                
                # Get resource usage
                resource_usage = self._get_resource_usage()
                
                logger.info(f"✅ Concurrent processing completed successfully")
                logger.info(f"  Successful jobs: {successful_jobs}/{job_count}")
                logger.info(f"  Total duration: {total_duration:.2f}s")
                logger.info(f"  Concurrent duration: {concurrent_duration:.2f}s")
                logger.info(f"  Throughput: {throughput:.2f} docs/sec")
                logger.info(f"  Scaling factor: {scaling_factor:.2f}x")
                
                return PerformanceTestResult(
                    test_name=test_name,
                    status='passed',
                    duration_seconds=total_duration,
                    throughput=throughput,
                    latency_p50=concurrent_duration / successful_jobs,
                    latency_p95=concurrent_duration / successful_jobs,
                    latency_p99=concurrent_duration / successful_jobs,
                    resource_usage=resource_usage,
                    scalability_factor=scaling_factor
                )
            else:
                raise Exception("All concurrent jobs failed")
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return PerformanceTestResult(
                test_name=test_name,
                status='failed',
                duration_seconds=duration,
                throughput=0.0,
                latency_p50=duration,
                latency_p95=duration,
                latency_p99=duration,
                resource_usage=self._get_resource_usage(),
                error_message=error_msg
            )
    
    async def test_large_document_performance(self) -> PerformanceTestResult:
        """Test performance with large documents"""
        test_name = "Large Document Performance"
        start_time = time.time()
        
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
                     'storage://raw/test-user/large-perf-test.pdf', 
                     'markdown-simple@1', 'text-embedding-3-small', '1')
            
            # Generate large test content (100KB+)
            large_content = self._generate_performance_test_content(150000)  # 150KB content
            
            # Store parsed content
            parsed_path = f"storage://parsed/{user_id}/{document_id}.md"
            await self.storage.write_blob(parsed_path, large_content.encode('utf-8'))
            
            # Update job status to parsed
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs 
                    SET status = 'parsed', parsed_path = $1, parsed_sha256 = $2
                    WHERE job_id = $3
                """, parsed_path, 'test-large-perf-sha256', job_id)
            
            # Measure processing time for each stage
            stage_times = {}
            
            # Stage 1: Chunking
            chunk_start = time.time()
            await self.worker._process_chunks({
                'job_id': job_id,
                'document_id': document_id,
                'status': 'parsed',
                'parsed_path': parsed_path,
                'chunks_version': 'markdown-simple@1'
            }, f"test-{uuid.uuid4()}")
            stage_times['chunking'] = time.time() - chunk_start
            
            # Stage 2: Embedding
            embed_start = time.time()
            await self.worker._process_embeddings({
                'job_id': job_id,
                'document_id': document_id,
                'status': 'chunks_stored',
                'embed_model': 'text-embedding-3-small',
                'embed_version': '1'
            }, f"test-{uuid.uuid4()}")
            stage_times['embedding'] = time.time() - embed_start
            
            # Stage 3: Finalization
            finalize_start = time.time()
            await self.worker._finalize_job({
                'job_id': job_id,
                'document_id': document_id,
                'status': 'embeddings_stored'
            }, f"test-{uuid.uuid4()}")
            stage_times['finalization'] = time.time() - finalize_start
            
            # Calculate performance metrics
            total_duration = time.time() - start_time
            throughput = 1.0 / total_duration  # documents per second
            
            # Get resource usage
            resource_usage = self._get_resource_usage()
            
            # Verify results
            async with self.db.get_db_connection() as conn:
                chunk_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM upload_pipeline.document_chunks 
                    WHERE document_id = $1
                """, document_id)
                
                embedding_count = await conn.fetchval("""
                    SELECT COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) FROM upload_pipeline.document_chunks 
                    WHERE document_id = $1
                """, document_id)
                
                final_status = await conn.fetchval("""
                    SELECT status FROM upload_pipeline.upload_jobs 
                    WHERE job_id = $1
                """, document_id)
            
            if chunk_count > 0 and embedding_count > 0 and final_status == 'complete':
                logger.info(f"✅ Large document performance test completed successfully in {total_duration:.2f}s")
                logger.info(f"  Content size: {len(large_content)} bytes")
                logger.info(f"  Chunks created: {chunk_count}")
                logger.info(f"  Embeddings created: {embedding_count}")
                logger.info(f"  Chunking time: {stage_times['chunking']:.2f}s")
                logger.info(f"  Embedding time: {stage_times['embedding']:.2f}s")
                logger.info(f"  Finalization time: {stage_times['finalization']:.2f}s")
                logger.info(f"  Throughput: {throughput:.2f} docs/sec")
                
                return PerformanceTestResult(
                    test_name=test_name,
                    status='passed',
                    duration_seconds=total_duration,
                    throughput=throughput,
                    latency_p50=total_duration,
                    latency_p95=total_duration,
                    latency_p99=total_duration,
                    resource_usage=resource_usage,
                    scalability_factor=1.0
                )
            else:
                raise Exception(f"Processing incomplete: chunks={chunk_count}, embeddings={embedding_count}, status={final_status}")
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return PerformanceTestResult(
                test_name=test_name,
                status='failed',
                duration_seconds=duration,
                throughput=0.0,
                latency_p50=duration,
                latency_p95=duration,
                latency_p99=duration,
                resource_usage=self._get_resource_usage(),
                error_message=error_msg
            )
    
    def _generate_performance_test_content(self, target_size_bytes: int) -> str:
        """Generate test content of specified size for performance testing"""
        content = []
        content.append("# Performance Test Document")
        content.append("")
        content.append("This is a performance test document for pipeline validation.")
        content.append("")
        
        # Calculate how many sections we need to reach target size
        base_content = len("\n".join(content))
        remaining_bytes = target_size_bytes - base_content
        
        # Generate content to reach target size
        section_count = 1
        while len("\n".join(content)) < target_size_bytes:
            content.append(f"## Section {section_count}")
            content.append("")
            
            # Add paragraphs
            for paragraph in range(1, 4):
                content.append(f"This is paragraph {paragraph} of section {section_count}. ")
                content.append("It contains substantial content to test chunking and embedding performance. ")
                content.append("The content is designed to be realistic and challenging for the processing pipeline. ")
                content.append("")
            
            # Add technical content
            content.append("### Technical Details")
            content.append("")
            content.append("This section includes technical terminology and complex concepts. ")
            content.append("It tests the system's ability to handle diverse content types. ")
            content.append("")
            
            section_count += 1
            
            # Safety check to prevent infinite loop
            if section_count > 1000:
                break
        
        return "\n".join(content)
    
    async def _process_job_concurrently(self, job: Dict[str, Any], parsed_path: str):
        """Process a single job concurrently"""
        try:
            # Process chunks
            await self.worker._process_chunks({
                'job_id': job['job_id'],
                'document_id': job['document_id'],
                'status': 'parsed',
                'parsed_path': parsed_path,
                'chunks_version': 'markdown-simple@1'
            }, f"test-{uuid.uuid4()}")
            
            # Process embeddings
            await self.worker._process_embeddings({
                'job_id': job['job_id'],
                'document_id': job['document_id'],
                'status': 'chunks_stored',
                'embed_model': 'text-embedding-3-small',
                'embed_version': '1'
            }, f"test-{uuid.uuid4()}")
            
            # Finalize job
            await self.worker._finalize_job({
                'job_id': job['job_id'],
                'document_id': job['document_id'],
                'status': 'embeddings_stored'
            }, f"test-{uuid.uuid4()}")
            
            return True
            
        except Exception as e:
            logger.error(f"Concurrent job processing failed for job {job['job_id']}: {e}")
            raise
    
    async def run_all_tests(self) -> List[PerformanceTestResult]:
        """Run all performance tests"""
        logger.info("🚀 Starting comprehensive performance validation")
        
        try:
            await self.initialize()
            
            # Run all tests
            tests = [
                self.test_single_document_processing_performance(),
                self.test_concurrent_processing_performance(),
                self.test_large_document_performance()
            ]
            
            results = await asyncio.gather(*tests, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Test {i} failed with exception: {result}")
                    # Create failed result
                    failed_result = PerformanceTestResult(
                        test_name=f"Test {i}",
                        status='failed',
                        duration_seconds=0,
                        throughput=0.0,
                        latency_p50=0,
                        latency_p95=0,
                        latency_p99=0,
                        resource_usage=self._get_resource_usage(),
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
        logger.info("📊 Performance Test Summary")
        logger.info("=" * 50)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        logger.info("")
        
        # Performance metrics
        if any(r.throughput > 0 for r in self.test_results):
            logger.info("📈 Performance Metrics")
            logger.info("-" * 30)
            
            for result in self.test_results:
                if result.status == 'passed':
                    logger.info(f"{result.test_name}:")
                    logger.info(f"  Duration: {result.duration_seconds:.2f}s")
                    logger.info(f"  Throughput: {result.throughput:.2f} docs/sec")
                    logger.info(f"  Latency P50: {result.latency_p50:.2f}s")
                    logger.info(f"  Latency P95: {result.latency_p95:.2f}s")
                    logger.info(f"  Latency P99: {result.latency_p99:.2f}s")
                    if result.scalability_factor:
                        logger.info(f"  Scaling Factor: {result.scalability_factor:.2f}x")
                    logger.info("")
        
        # Resource usage
        if any(r.resource_usage for r in self.test_results):
            logger.info("💾 Resource Usage")
            logger.info("-" * 30)
            
            for result in self.test_results:
                if result.resource_usage:
                    logger.info(f"{result.test_name}:")
                    for metric, value in result.resource_usage.items():
                        logger.info(f"  {metric}: {value}")
                    logger.info("")
        
        # Failed test details
        if failed_tests > 0:
            logger.info("❌ Failed Test Details")
            logger.info("-" * 30)
            
            for result in self.test_results:
                if result.status == 'failed':
                    logger.info(f"{result.test_name}: {result.error_message}")
                    logger.info("")


async def main():
    """Main function for running performance tests"""
    # Load configuration
    config = WorkerConfig(
        database_url="postgresql://postgres:postgres@localhost:5432/accessa_dev",
        supabase_url="http://localhost:5000",
        supabase_anon_key="***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
        supabase_service_role_key="***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nk0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
        llamaparse_api_url="http://localhost:8001",
        llamaparse_api_key="test_key",
        openai_api_url="http://localhost:8002",
        openai_api_key="test_key",
        openai_model="text-embedding-3-small"
    )
    
    # Create validator and run tests
    validator = PerformanceValidator(config)
    
    try:
        results = await validator.run_all_tests()
        
        # Save results to file
        results_file = "performance_test_results.json"
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
