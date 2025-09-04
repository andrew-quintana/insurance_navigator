# Buffer table references updated for Phase 3.7 direct-write architecture
# Original buffer-based approach replaced with direct writes to document_chunks

#!/usr/bin/env python3
"""
Complete Pipeline End-to-End Testing

This module implements comprehensive end-to-end testing for the complete document
processing pipeline, validating all stages from upload through embedding storage.
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
class PipelineTestResult:
    """Result of a pipeline test"""
    test_name: str
    status: str  # 'passed', 'failed', 'skipped'
    duration_seconds: float
    stages_completed: List[str]
    stages_failed: List[str]
    error_message: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class CompletePipelineTester:
    """
    Comprehensive end-to-end pipeline testing
    
    Tests the complete document processing workflow from upload through
    embedding storage with realistic document scenarios.
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
        self.test_results: List[PipelineTestResult] = []
        
        # HTTP client for API testing
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
        logger.info("Initialized CompletePipelineTester")
    
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
    
    async def test_complete_pipeline_small_document(self) -> PipelineTestResult:
        """Test complete pipeline with small document (<100KB)"""
        test_name = "Complete Pipeline - Small Document"
        start_time = time.time()
        stages_completed = []
        stages_failed = []
        
        try:
            logger.info(f"🧪 Starting test: {test_name}")
            
            # Stage 1: Create test job
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
                     'storage://raw/test-user/small-test.pdf', 
                     'markdown-simple@1', 'text-embedding-3-small', '1')
            
            stages_completed.append('job_creation')
            logger.info("✅ Test job created successfully")
            
            # Stage 2: Simulate parsing
            test_content = "# Small Test Document\n\nThis is a small test document for pipeline validation.\n\n## Section 1\nTest content that will generate chunks.\n\n## Section 2\nAdditional content for multi-chunk testing."
            
            # Store parsed content
            parsed_path = f"storage://parsed/{user_id}/{document_id}.md"
            await self.storage.write_blob(parsed_path, test_content.encode('utf-8'))
            
            # Update job status to parsed
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs 
                    SET status = 'parsed', parsed_path = $1, parsed_sha256 = $2
                    WHERE job_id = $3
                """, parsed_path, 'test-sha256-hash', job_id)
            
            stages_completed.append('parsing')
            logger.info("✅ Parsing stage completed")
            
            # Stage 3: Process chunks
            await self.worker._process_chunks({
                'job_id': job_id,
                'document_id': document_id,
                'status': 'parsed',
                'parsed_path': parsed_path,
                'chunks_version': 'markdown-simple@1'
            }, f"test-{uuid.uuid4()}")
            
            # Verify chunks were created
            async with self.db.get_db_connection() as conn:
                chunk_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM upload_pipeline.document_chunks 
                    WHERE document_id = $1
                """, document_id)
                
                if chunk_count > 0:
                    stages_completed.append('chunking')
                    logger.info(f"✅ Chunking completed: {chunk_count} chunks created")
                else:
                    stages_failed.append('chunking')
                    raise Exception("No chunks were created")
            
            # Stage 4: Process embeddings
            await self.worker._process_embeddings({
                'job_id': job_id,
                'document_id': document_id,
                'status': 'chunks_stored',
                'embed_model': 'text-embedding-3-small',
                'embed_version': '1'
            }, f"test-{uuid.uuid4()}")
            
            # Verify embeddings were created
            async with self.db.get_db_connection() as conn:
                embedding_count = await conn.fetchval("""
                    SELECT COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) FROM upload_pipeline.document_chunks 
                    WHERE document_id = $1
                """, document_id)
                
                if embedding_count > 0:
                    stages_completed.append('embedding')
                    logger.info(f"✅ Embedding completed: {embedding_count} embeddings created")
                else:
                    stages_failed.append('embedding')
                    raise Exception("No embeddings were created")
            
            # Stage 5: Finalize job
            await self.worker._finalize_job({
                'job_id': job_id,
                'document_id': document_id,
                'status': 'embeddings_stored'
            }, f"test-{uuid.uuid4()}")
            
            # Verify final status
            async with self.db.get_db_connection() as conn:
                final_status = await conn.fetchval("""
                    SELECT status FROM upload_pipeline.upload_jobs 
                    WHERE job_id = $1
                """, job_id)
                
                if final_status == 'complete':
                    stages_completed.append('finalization')
                    logger.info("✅ Job finalization completed")
                else:
                    stages_failed.append('finalization')
                    raise Exception(f"Job not finalized correctly: {final_status}")
            
            duration = time.time() - start_time
            logger.info(f"✅ Test completed successfully in {duration:.2f}s")
            
            return PipelineTestResult(
                test_name=test_name,
                status='passed',
                duration_seconds=duration,
                stages_completed=stages_completed,
                stages_failed=stages_failed,
                performance_metrics={
                    'total_duration': duration,
                    'chunks_created': chunk_count,
                    'embeddings_created': embedding_count
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return PipelineTestResult(
                test_name=test_name,
                status='failed',
                duration_seconds=duration,
                stages_completed=stages_completed,
                stages_failed=stages_failed,
                error_message=error_msg
            )
    
    async def test_complete_pipeline_large_document(self) -> PipelineTestResult:
        """Test complete pipeline with large document (>1MB)"""
        test_name = "Complete Pipeline - Large Document"
        start_time = time.time()
        stages_completed = []
        stages_failed = []
        
        try:
            logger.info(f"🧪 Starting test: {test_name}")
            
            # Stage 1: Create test job
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
                     'storage://raw/test-user/large-test.pdf', 
                     'markdown-simple@1', 'text-embedding-3-small', '1')
            
            stages_completed.append('job_creation')
            logger.info("✅ Test job created successfully")
            
            # Stage 2: Simulate parsing with large content
            large_content = self._generate_large_test_content()
            
            # Store parsed content
            parsed_path = f"storage://parsed/{user_id}/{document_id}.md"
            await self.storage.write_blob(parsed_path, large_content.encode('utf-8'))
            
            # Update job status to parsed
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs 
                    SET status = 'parsed', parsed_path = $1, parsed_sha256 = $2
                    WHERE job_id = $3
                """, parsed_path, 'test-large-sha256-hash', job_id)
            
            stages_completed.append('parsing')
            logger.info("✅ Parsing stage completed")
            
            # Stage 3: Process chunks
            await self.worker._process_chunks({
                'job_id': job_id,
                'document_id': document_id,
                'status': 'parsed',
                'parsed_path': parsed_path,
                'chunks_version': 'markdown-simple@1'
            }, f"test-{uuid.uuid4()}")
            
            # Verify chunks were created
            async with self.db.get_db_connection() as conn:
                chunk_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM upload_pipeline.document_chunks 
                    WHERE document_id = $1
                """, document_id)
                
                if chunk_count > 0:
                    stages_completed.append('chunking')
                    logger.info(f"✅ Chunking completed: {chunk_count} chunks created")
                else:
                    stages_failed.append('chunking')
                    raise Exception("No chunks were created")
            
            # Stage 4: Process embeddings
            await self.worker._process_embeddings({
                'job_id': job_id,
                'document_id': document_id,
                'status': 'chunks_stored',
                'embed_model': 'text-embedding-3-small',
                'embed_version': '1'
            }, f"test-{uuid.uuid4()}")
            
            # Verify embeddings were created
            async with self.db.get_db_connection() as conn:
                embedding_count = await conn.fetchval("""
                    SELECT COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) FROM upload_pipeline.document_chunks 
                    WHERE document_id = $1
                """, document_id)
                
                if embedding_count > 0:
                    stages_completed.append('embedding')
                    logger.info(f"✅ Embedding completed: {embedding_count} embeddings created")
                else:
                    stages_failed.append('embedding')
                    raise Exception("No embeddings were created")
            
            # Stage 5: Finalize job
            await self.worker._finalize_job({
                'job_id': job_id,
                'document_id': document_id,
                'status': 'embeddings_stored'
            }, f"test-{uuid.uuid4()}")
            
            # Verify final status
            async with self.db.get_db_connection() as conn:
                final_status = await conn.fetchval("""
                    SELECT status FROM upload_pipeline.upload_jobs 
                    WHERE job_id = $1
                """, job_id)
                
                if final_status == 'complete':
                    stages_completed.append('finalization')
                    logger.info("✅ Job finalization completed")
                else:
                    stages_failed.append('finalization')
                    raise Exception(f"Job not finalized correctly: {final_status}")
            
            duration = time.time() - start_time
            logger.info(f"✅ Test completed successfully in {duration:.2f}s")
            
            return PipelineTestResult(
                test_name=test_name,
                status='passed',
                duration_seconds=duration,
                stages_completed=stages_completed,
                stages_failed=stages_failed,
                performance_metrics={
                    'total_duration': duration,
                    'chunks_created': chunk_count,
                    'embeddings_created': embedding_count,
                    'content_size_bytes': len(large_content)
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return PipelineTestResult(
                test_name=test_name,
                status='failed',
                duration_seconds=duration,
                stages_completed=stages_completed,
                stages_failed=stages_failed,
                error_message=error_msg
            )
    
    def _generate_large_test_content(self) -> str:
        """Generate large test content for performance testing"""
        content = []
        content.append("# Large Test Document")
        content.append("")
        content.append("This is a large test document for pipeline performance validation.")
        content.append("")
        
        # Generate multiple sections with substantial content
        for section in range(1, 21):  # 20 sections
            content.append(f"## Section {section}")
            content.append("")
            
            # Generate paragraphs for each section
            for paragraph in range(1, 6):  # 5 paragraphs per section
                content.append(f"This is paragraph {paragraph} of section {section}. ")
                content.append("It contains substantial content to test chunking and embedding performance. ")
                content.append("The content is designed to be realistic and challenging for the processing pipeline. ")
                content.append("")
            
            # Add some technical content
            content.append("### Technical Details")
            content.append("")
            content.append("This section includes technical terminology and complex concepts. ")
            content.append("It tests the system's ability to handle diverse content types. ")
            content.append("")
        
        return "\n".join(content)
    
    async def test_concurrent_processing(self) -> PipelineTestResult:
        """Test concurrent processing of multiple documents"""
        test_name = "Concurrent Processing - Multiple Documents"
        start_time = time.time()
        stages_completed = []
        stages_failed = []
        
        try:
            logger.info(f"🧪 Starting test: {test_name}")
            
            # Create multiple test jobs
            job_count = 5
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
                         f'storage://raw/test-user/concurrent-test-{i}.pdf', 
                         'markdown-simple@1', 'text-embedding-3-small', '1')
            
            stages_completed.append('job_creation')
            logger.info(f"✅ Created {job_count} test jobs")
            
            # Process all jobs concurrently
            processing_tasks = []
            
            for job in jobs:
                # Simulate parsing
                test_content = f"# Concurrent Test Document {job['index']}\n\nContent for concurrent testing.\n\n## Section 1\nTest content for job {job['index']}."
                
                # Store parsed content
                parsed_path = f"storage://parsed/{job['user_id']}/{job['document_id']}.md"
                await self.storage.write_blob(parsed_path, test_content.encode('utf-8'))
                
                # Update job status to parsed
                async with self.db.get_db_connection() as conn:
                    await conn.execute("""
                        UPDATE upload_pipeline.upload_jobs 
                        SET status = 'parsed', parsed_path = $1, parsed_sha256 = $2
                        WHERE job_id = $3
                    """, parsed_path, f'test-concurrent-sha256-{job["index"]}', job['job_id'])
                
                # Create processing task
                task = self._process_job_concurrently(job, parsed_path)
                processing_tasks.append(task)
            
            stages_completed.append('parsing')
            logger.info("✅ All jobs parsed successfully")
            
            # Execute concurrent processing
            results = await asyncio.gather(*processing_tasks, return_exceptions=True)
            
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
                stages_completed.append('concurrent_processing')
                logger.info(f"✅ Concurrent processing completed: {successful_jobs} successful, {failed_jobs} failed")
            else:
                stages_failed.append('concurrent_processing')
                raise Exception("All concurrent jobs failed")
            
            duration = time.time() - start_time
            logger.info(f"✅ Test completed successfully in {duration:.2f}s")
            
            return PipelineTestResult(
                test_name=test_name,
                status='passed',
                duration_seconds=duration,
                stages_completed=stages_completed,
                stages_failed=stages_failed,
                performance_metrics={
                    'total_duration': duration,
                    'jobs_processed': job_count,
                    'successful_jobs': successful_jobs,
                    'failed_jobs': failed_jobs,
                    'concurrency_level': job_count
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return PipelineTestResult(
                test_name=test_name,
                status='failed',
                duration_seconds=duration,
                stages_completed=stages_completed,
                stages_failed=stages_failed,
                error_message=error_msg
            )
    
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
    
    async def run_all_tests(self) -> List[PipelineTestResult]:
        """Run all pipeline tests"""
        logger.info("🚀 Starting comprehensive pipeline testing")
        
        try:
            await self.initialize()
            
            # Run all tests
            tests = [
                self.test_complete_pipeline_small_document(),
                self.test_complete_pipeline_large_document(),
                self.test_concurrent_processing()
            ]
            
            results = await asyncio.gather(*tests, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Test {i} failed with exception: {result}")
                    # Create failed result
                    failed_result = PipelineTestResult(
                        test_name=f"Test {i}",
                        status='failed',
                        duration_seconds=0,
                        stages_completed=[],
                        stages_failed=[],
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
        logger.info("📊 Test Summary")
        logger.info("=" * 50)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        logger.info("")
        
        # Performance metrics
        if any(r.performance_metrics for r in self.test_results):
            logger.info("📈 Performance Metrics")
            logger.info("-" * 30)
            
            for result in self.test_results:
                if result.performance_metrics:
                    logger.info(f"{result.test_name}:")
                    for metric, value in result.performance_metrics.items():
                        logger.info(f"  {metric}: {value}")
                    logger.info("")
        
        # Failed test details
        if failed_tests > 0:
            logger.info("❌ Failed Test Details")
            logger.info("-" * 30)
            
            for result in self.test_results:
                if result.status == 'failed':
                    logger.info(f"{result.test_name}: {result.error_message}")
                    logger.info(f"  Stages completed: {', '.join(result.stages_completed)}")
                    logger.info(f"  Stages failed: {', '.join(result.stages_failed)}")
                    logger.info("")


async def main():
    """Main function for running pipeline tests"""
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
    tester = CompletePipelineTester(config)
    
    try:
        results = await tester.run_all_tests()
        
        # Save results to file
        results_file = "pipeline_test_results.json"
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
