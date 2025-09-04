import pytest
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from backend.workers.base_worker import BaseWorker
from backend.shared.config import WorkerConfig

@pytest.fixture
def performance_config():
    """Create configuration for performance testing"""
    return WorkerConfig(
        database_url="postgresql://test:test@localhost:5432/test",
        supabase_url="http://localhost:5000",
        supabase_anon_key="test_anon_key",
        supabase_service_role_key="test_service_key",
        llamaparse_api_url="http://localhost:8001",
        llamaparse_api_key="test_llamaparse_key",
        openai_api_url="http://localhost:8002",
        openai_api_key="test_openai_key",
        openai_model="text-embedding-3-small",
        poll_interval=0.1,  # Fast polling for performance tests
        max_retries=2,
        retry_base_delay=0.1
    )

@pytest.fixture
def performance_worker(performance_config):
    """Create BaseWorker instance for performance testing"""
    worker = BaseWorker(performance_config)
    
    # Mock all components for performance testing
    worker.db = AsyncMock()
    worker.storage = AsyncMock()
    worker.llamaparse = AsyncMock()
    worker.openai = AsyncMock()
    
    return worker

class TestBaseWorkerPerformance:
    """Performance tests for BaseWorker"""
    
    @pytest.mark.asyncio
    async def test_job_processing_throughput(self, performance_worker):
        """Test job processing throughput under load"""
        # Create multiple jobs
        num_jobs = 50
        jobs = []
        
        for i in range(num_jobs):
            job = {
                "job_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "status": "parsed",
                "parsed_path": f"storage://parsed/test/test{i}.md",
                "chunks_version": "markdown-simple@1",
                "retry_count": 0
            }
            jobs.append(job)
        
        # Mock storage responses
        performance_worker.storage.read_blob.return_value = "# Test Document\n\nContent here."
        
        # Mock database operations
        mock_conn = Mock()
        mock_conn.fetchrow.return_value = None
        mock_conn.execute.return_value = "INSERT 0 1"
        
        performance_worker.db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Process jobs and measure time
        start_time = time.time()
        
        async def process_job(job):
            correlation_id = f"perf-{uuid.uuid4()}"
            await performance_worker._validate_parsed(job, correlation_id)
            await performance_worker._process_chunks(job, correlation_id)
            return job["status"]
        
        # Process all jobs concurrently
        results = await asyncio.gather(*[process_job(job) for job in jobs])
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput
        throughput = num_jobs / total_time
        
        # Verify all jobs were processed
        assert len(results) == num_jobs
        assert all(status == "chunks_stored" for status in results)
        
        # Performance assertions
        assert total_time < 10.0  # Should complete within 10 seconds
        assert throughput > 5.0  # Should process at least 5 jobs per second
        
        print(f"Processed {num_jobs} jobs in {total_time:.2f}s")
        print(f"Throughput: {throughput:.2f} jobs/second")
    
    @pytest.mark.asyncio
    async def test_embedding_generation_performance(self, performance_worker):
        """Test embedding generation performance with large batches"""
        # Create job with many chunks
        num_chunks = 1000
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "status": "chunks_stored",
            "embed_model": "text-embedding-3-small",
            "embed_version": "1"
        }
        
        # Mock database operations
        mock_conn = Mock()
        mock_conn.fetch.return_value = [
            {
                "chunk_id": str(uuid.uuid4()),
                "text": f"Test chunk {i}",
                "chunk_sha": f"hash{i}"
            }
            for i in range(num_chunks)
        ]
        mock_conn.execute.return_value = "UPDATE 1"
        
        performance_worker.db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Mock OpenAI response
        performance_worker.openai.generate_embeddings.return_value = [[0.1] * 1536] * num_chunks
        
        # Process embeddings and measure time
        start_time = time.time()
        
        correlation_id = f"perf-{uuid.uuid4()}"
        await performance_worker._process_embeddings(job, correlation_id)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate performance metrics
        chunks_per_second = num_chunks / total_time
        
        # Verify processing completed
        assert job["status"] == "embedding_complete"
        
        # Performance assertions
        assert total_time < 30.0  # Should complete within 30 seconds
        assert chunks_per_second > 30.0  # Should process at least 30 chunks per second
        
        print(f"Processed {num_chunks} chunks in {total_time:.2f}s")
        print(f"Rate: {chunks_per_second:.2f} chunks/second")
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, performance_worker):
        """Test memory usage under sustained load"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create and process many jobs
        num_jobs = 50
        jobs = []
        
        for i in range(num_jobs):
            job = {
                "job_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "status": "parsed",
                "parsed_path": f"storage://parsed/test/test{i}.md",
                "chunks_version": "markdown-simple@1",
                "retry_count": 0
            }
            jobs.append(job)
        
        # Mock components
        performance_worker.storage.read_blob.return_value = "# Test Document\n\nContent here."
        
        mock_conn = Mock()
        mock_conn.fetchrow.return_value = None
        mock_conn.execute.return_value = "INSERT 0 1"
        
        performance_worker.db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Process jobs
        correlation_id = f"perf-{uuid.uuid4()}"
        
        for job in jobs:
            await performance_worker._validate_parsed(job, correlation_id)
            await performance_worker._process_chunks(job, correlation_id)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage assertions
        assert memory_increase < 100.0  # Should not increase by more than 100MB
        assert final_memory < 500.0  # Should not exceed 500MB total
        
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
    
    @pytest.mark.asyncio
    async def test_concurrent_worker_scaling(self, performance_config):
        """Test performance with multiple concurrent workers"""
        # Create multiple workers
        num_workers = 3
        workers = []
        
        for i in range(num_workers):
            worker = BaseWorker(performance_config)
            worker.db = Mock()
            worker.storage = Mock()
            worker.llamaparse = Mock()
            worker.openai = Mock()
            workers.append(worker)
        
        # Create jobs for each worker
        jobs_per_worker = 10
        total_jobs = num_workers * jobs_per_worker
        
        # Mock components for all workers
        for worker in workers:
            worker.storage.read_blob.return_value = "# Test Document\n\nContent here."
            
            mock_conn = Mock()
            mock_conn.fetchrow.return_value = None
            mock_conn.execute.return_value = "INSERT 0 1"
            
            worker.db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Process jobs concurrently across all workers
        start_time = time.time()
        
        async def process_worker_jobs(worker, worker_id):
            jobs = []
            for i in range(jobs_per_worker):
                job = {
                    "job_id": str(uuid.uuid4()),
                    "document_id": str(uuid.uuid4()),
                    "status": "parsed",
                    "parsed_path": f"storage://parsed/worker{worker_id}/test{i}.md",
                    "chunks_version": "markdown-simple@1",
                    "retry_count": 0
                }
                jobs.append(job)
            
            correlation_id = f"worker-{worker_id}-{uuid.uuid4()}"
            
            for job in jobs:
                await worker._validate_parsed(job, correlation_id)
                await worker._process_chunks(job, correlation_id)
            
            return len(jobs)
        
        # Process all workers concurrently
        results = await asyncio.gather(*[
            process_worker_jobs(worker, i) for i, worker in enumerate(workers)
        ])
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate performance metrics
        total_processed = sum(results)
        throughput = total_processed / total_time
        
        # Verify all jobs were processed
        assert total_processed == total_jobs
        
        # Performance assertions
        assert total_time < 15.0  # Should complete within 15 seconds
        assert throughput > 2.0  # Should process at least 2 jobs per second
        
        print(f"Processed {total_processed} jobs with {num_workers} workers in {total_time:.2f}s")
        print(f"Throughput: {throughput:.2f} jobs/second")
    
    @pytest.mark.asyncio
    async def test_large_document_processing(self, performance_worker):
        """Test processing of very large documents"""
        # Create a large document content
        large_content = ""
        for i in range(1000):  # 1000 sections
            large_content += f"# Section {i}\n\n"
            large_content += f"This is the content for section {i}. " * 10  # 10 sentences per section
            large_content += "\n\n"
        
        # Create job
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "status": "parsed",
            "parsed_path": "storage://parsed/test/large.md",
            "chunks_version": "markdown-simple@1",
            "retry_count": 0
        }
        
        # Mock storage with large content
        performance_worker.storage.read_blob.return_value = large_content
        
        # Mock database operations
        mock_conn = Mock()
        mock_conn.fetchrow.return_value = None
        mock_conn.execute.return_value = "INSERT 0 1"
        
        performance_worker.db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Process large document and measure time
        start_time = time.time()
        
        correlation_id = f"perf-{uuid.uuid4()}"
        await performance_worker._validate_parsed(job, correlation_id)
        await performance_worker._process_chunks(job, correlation_id)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate performance metrics
        content_size_mb = len(large_content.encode('utf-8')) / 1024 / 1024
        processing_rate = content_size_mb / total_time
        
        # Verify processing completed
        assert job["status"] == "chunks_stored"
        
        # Performance assertions
        assert total_time < 60.0  # Should complete within 60 seconds
        assert processing_rate > 0.1  # Should process at least 0.1 MB per second
        
        print(f"Processed {content_size_mb:.2f} MB document in {total_time:.2f}s")
        print(f"Processing rate: {processing_rate:.2f} MB/second")
    
    @pytest.mark.asyncio
    async def test_error_handling_performance(self, performance_worker):
        """Test performance under error conditions"""
        # Create job
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "status": "parsed",
            "parsed_path": "storage://parsed/test/test.md",
            "retry_count": 0
        }
        
        # Mock storage to fail
        performance_worker.storage.read_blob.side_effect = Exception("Storage error")
        
        # Mock database operations
        mock_conn = Mock()
        mock_conn.execute.return_value = "UPDATE 1"
        
        performance_worker.db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Test error handling performance
        start_time = time.time()
        
        correlation_id = f"perf-{uuid.uuid4()}"
        
        # Attempt processing multiple times to trigger retries
        for attempt in range(3):
            try:
                await performance_worker._validate_parsed(job, correlation_id)
            except Exception:
                pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertions for error handling
        assert total_time < 5.0  # Error handling should be fast
        assert job["retry_count"] > 0  # Should have attempted retries
        
        print(f"Error handling completed in {total_time:.2f}s")
        print(f"Retry attempts: {job['retry_count']}")
    
    @pytest.mark.asyncio
    async def test_metrics_collection_performance(self, performance_worker):
        """Test performance impact of metrics collection"""
        # Create many jobs
        num_jobs = 100
        jobs = []
        
        for i in range(num_jobs):
            job = {
                "job_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "status": "parsed",
                "parsed_path": f"storage://parsed/test/test{i}.md",
                "chunks_version": "markdown-simple@1",
                "retry_count": 0
            }
            jobs.append(job)
        
        # Mock components
        performance_worker.storage.read_blob.return_value = "# Test Document\n\nContent here."
        
        mock_conn = Mock()
        mock_conn.fetchrow.return_value = None
        mock_conn.execute.return_value = "INSERT 0 1"
        
        performance_worker.db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Process jobs with metrics collection
        start_time = time.time()
        
        correlation_id = f"perf-{uuid.uuid4()}"
        
        for job in jobs:
            await performance_worker._validate_parsed(job, correlation_id)
            await performance_worker._process_chunks(job, correlation_id)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Get metrics summary
        metrics_start = time.time()
        summary = performance_worker.metrics.get_summary()
        metrics_time = time.time() - metrics_start
        
        # Performance assertions
        assert total_time < 20.0  # Should complete within 20 seconds
        assert metrics_time < 0.1  # Metrics collection should be very fast
        
        # Verify metrics were collected
        assert summary["total_jobs"] >= num_jobs
        assert "stage_counts" in summary
        assert "error_counts" in summary
        
        print(f"Processed {num_jobs} jobs in {total_time:.2f}s")
        print(f"Metrics collection took {metrics_time:.4f}s")
        print(f"Metrics summary: {summary}")
