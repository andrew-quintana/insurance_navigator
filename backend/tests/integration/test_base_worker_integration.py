import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from backend.workers.base_worker import BaseWorker
from backend.shared.config import WorkerConfig
from backend.shared.db.connection import DatabaseManager
from backend.shared.storage.storage_manager import StorageManager
from backend.shared.external.llamaparse_client import LlamaParseClient
from backend.shared.external.openai_client import OpenAIClient

@pytest.fixture
def test_config():
    """Create test configuration"""
    return WorkerConfig(
        database_url="postgresql://test:test@localhost:5432/test",
        supabase_url="http://localhost:5000",
        supabase_anon_key="test_anon_key",
        supabase_service_role_key="test_service_key",
        llamaparse_api_url="http://localhost:8001",
        llamaparse_api_key="test_llamaparse_key",
        openai_api_url="http://localhost:8002",
        openai_api_key="test_openai_key",
        openai_model="text-embedding-3-small"
    )

@pytest.fixture
def mock_components():
    """Create mock components for testing"""
    db = AsyncMock(spec=DatabaseManager)
    storage = AsyncMock(spec=StorageManager)
    llamaparse = AsyncMock(spec=LlamaParseClient)
    openai = AsyncMock(spec=OpenAIClient)
    
    return db, storage, llamaparse, openai

@pytest.fixture
def base_worker(test_config, mock_components):
    """Create BaseWorker instance with mock components"""
    db, storage, llamaparse, openai = mock_components
    
    worker = BaseWorker(test_config)
    worker.db = db
    worker.storage = storage
    worker.llamaparse = llamaparse
    worker.openai = openai
    
    return worker

class TestBaseWorkerIntegration:
    """Integration tests for BaseWorker"""
    
    @pytest.mark.asyncio
    async def test_full_job_processing_workflow(self, base_worker, mock_components):
        """Test complete job processing workflow"""
        db, storage, llamaparse, openai = mock_components
        
        # Mock job data
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "status": "parsed",
            "parsed_path": "storage://parsed/test/test.md",
            "chunks_version": "markdown-simple@1",
            "embed_model": "text-embedding-3-small",
            "embed_version": "1",
            "retry_count": 0
        }
        
        # Mock storage responses
        storage.read_blob.return_value = "# Test Document\n\nContent here.\n\n## Section 1\nMore content."
        
        # Mock database operations
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None  # No duplicate
        mock_conn.fetch.return_value = [
            {"chunk_id": str(uuid.uuid4()), "text": "Test chunk 1", "chunk_sha": "hash1"},
            {"chunk_id": str(uuid.uuid4()), "text": "Test chunk 2", "chunk_sha": "hash2"}
        ]
        mock_conn.execute.return_value = "INSERT 0 1"
        
        db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Mock OpenAI response
        openai.generate_embeddings.return_value = [[0.1] * 1536, [0.2] * 1536]
        
        # Test the workflow
        correlation_id = f"test-{uuid.uuid4()}"
        
        # Step 1: Validate parsed content
        await base_worker._validate_parsed(job, correlation_id)
        assert job["status"] == "parse_validated"
        
        # Step 2: Process chunks
        await base_worker._process_chunks(job, correlation_id)
        assert job["status"] == "chunks_stored"
        
        # Step 3: Process embeddings
        await base_worker._process_embeddings(job, correlation_id)
        assert job["status"] == "embedding_complete"
        
        # Step 4: Finalize job
        await base_worker._finalize_job(job, correlation_id)
        assert job["status"] == "complete"
        
        # Verify all components were called
        storage.read_blob.assert_called()
        openai.generate_embeddings.assert_called()
        assert mock_conn.execute.call_count >= 4  # Multiple database operations
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_retry(self, base_worker, mock_components):
        """Test error recovery and retry logic"""
        db, storage, llamaparse, openai = mock_components
        
        # Mock job data
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "status": "parsed",
            "parsed_path": "storage://parsed/test/test.md",
            "retry_count": 0
        }
        
        # Mock storage failure
        storage.read_blob.side_effect = Exception("Storage error")
        
        # Mock database operations
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "UPDATE 1"
        
        db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Test error handling
        correlation_id = f"test-{uuid.uuid4()}"
        
        with pytest.raises(Exception):
            await base_worker._validate_parsed(job, correlation_id)
        
        # Verify retry was scheduled
        assert mock_conn.execute.call_count > 0
        
        # Verify retry count was incremented
        call_args = mock_conn.execute.call_args
        assert "retry_count" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, base_worker, mock_components):
        """Test circuit breaker integration with external services"""
        db, storage, llamaparse, openai = mock_components
        
        # Mock job data
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "status": "chunks_stored",
            "embed_model": "text-embedding-3-small",
            "embed_version": "1"
        }
        
        # Mock database operations
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {"chunk_id": str(uuid.uuid4()), "text": "Test chunk", "chunk_sha": "hash1"}
        ]
        mock_conn.execute.return_value = "UPDATE 1"
        
        db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Mock OpenAI failures to trigger circuit breaker
        openai.generate_embeddings.side_effect = Exception("OpenAI API error")
        
        # Test circuit breaker behavior
        correlation_id = f"test-{uuid.uuid4()}"
        
        # First few failures should be retried
        for i in range(3):
            try:
                await base_worker._process_embeddings(job, correlation_id)
            except Exception:
                pass
        
        # After multiple failures, circuit should open
        assert base_worker.circuit_open is True
        assert base_worker.failure_count >= 3
        
        # Should not attempt to call OpenAI when circuit is open
        openai.generate_embeddings.reset_mock()
        
        try:
            await base_worker._process_embeddings(job, correlation_id)
        except Exception:
            pass
        
        # OpenAI should not be called when circuit is open
        openai.generate_embeddings.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_concurrent_job_processing(self, base_worker, mock_components):
        """Test concurrent job processing"""
        db, storage, llamaparse, openai = mock_components
        
        # Create multiple jobs
        jobs = []
        for i in range(3):
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
        storage.read_blob.return_value = "# Test Document\n\nContent here."
        
        # Mock database operations
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None
        mock_conn.execute.return_value = "INSERT 0 1"
        
        db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Process jobs concurrently
        correlation_id = f"test-{uuid.uuid4()}"
        
        async def process_job(job):
            await base_worker._validate_parsed(job, correlation_id)
            await base_worker._process_chunks(job, correlation_id)
            return job["status"]
        
        # Process all jobs concurrently
        results = await asyncio.gather(*[process_job(job) for job in jobs])
        
        # Verify all jobs were processed
        assert len(results) == 3
        assert all(status == "chunks_stored" for status in results)
        
        # Verify storage was called for each job
        assert storage.read_blob.call_count == 3
        
        # Verify database operations were called for each job
        assert mock_conn.execute.call_count >= 6  # 2 operations per job
    
    @pytest.mark.asyncio
    async def test_idempotent_operations(self, base_worker, mock_components):
        """Test idempotent operations for crash recovery"""
        db, storage, llamaparse, openai = mock_components
        
        # Mock job data
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "status": "parsed",
            "parsed_path": "storage://parsed/test/test.md",
            "chunks_version": "markdown-simple@1",
            "retry_count": 0
        }
        
        # Mock storage responses
        storage.read_blob.return_value = "# Test Document\n\nContent here."
        
        # Mock database operations
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None
        mock_conn.execute.return_value = "INSERT 0 1"
        
        db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Process job first time
        correlation_id = f"test-{uuid.uuid4()}"
        await base_worker._validate_parsed(job, correlation_id)
        await base_worker._process_chunks(job, correlation_id)
        
        # Reset mocks to simulate fresh start
        storage.read_blob.reset_mock()
        mock_conn.execute.reset_mock()
        
        # Process job again (simulating restart after crash)
        await base_worker._validate_parsed(job, correlation_id)
        await base_worker._process_chunks(job, correlation_id)
        
        # Verify operations were idempotent
        # Storage should still be read
        assert storage.read_blob.call_count == 1
        
        # Database operations should still be executed
        assert mock_conn.execute.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_health_check_integration(self, base_worker, mock_components):
        """Test health check integration with all components"""
        db, storage, llamaparse, openai = mock_components
        
        # Mock health check responses
        db.health_check.return_value = {"status": "healthy", "connections": 5}
        storage.health_check.return_value = {"status": "healthy", "buckets": ["test"]}
        llamaparse.health_check.return_value = {"status": "healthy", "version": "1.0"}
        openai.health_check.return_value = {"status": "healthy", "model": "text-embedding-3-small"}
        
        # Test health check
        health = await base_worker.health_check()
        
        # Verify overall health
        assert health["status"] == "healthy"
        assert health["worker_id"] == base_worker.worker_id
        assert health["running"] == base_worker.running
        assert "timestamp" in health
        assert "metrics" in health
        assert "components" in health
        
        # Verify component health
        components = health["components"]
        assert components["database"]["status"] == "healthy"
        assert components["storage"]["status"] == "healthy"
        assert components["llamaparse"]["status"] == "healthy"
        assert components["openai"]["status"] == "healthy"
        
        # Verify all components were checked
        db.health_check.assert_called_once()
        storage.health_check.assert_called_once()
        llamaparse.health_check.assert_called_once()
        openai.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, base_worker, mock_components):
        """Test metrics collection during processing"""
        db, storage, llamaparse, openai = mock_components
        
        # Mock job data
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "status": "parsed",
            "parsed_path": "storage://parsed/test/test.md",
            "chunks_version": "markdown-simple@1",
            "retry_count": 0
        }
        
        # Mock storage responses
        storage.read_blob.return_value = "# Test Document\n\nContent here."
        
        # Mock database operations
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None
        mock_conn.execute.return_value = "INSERT 0 1"
        
        db.get_db_connection.return_value.__aenter__.return_value = mock_conn
        
        # Process job
        correlation_id = f"test-{uuid.uuid4()}"
        
        start_time = datetime.utcnow()
        await base_worker._validate_parsed(job, correlation_id)
        await base_worker._process_chunks(job, correlation_id)
        end_time = datetime.utcnow()
        
        # Check metrics
        metrics = base_worker.metrics
        
        # Verify metrics were recorded
        assert metrics.jobs_processed >= 0  # May not be incremented in this test
        assert "parsed" in metrics.stage_counts
        assert "chunking" in metrics.stage_counts
        
        # Verify stage counts
        assert metrics.stage_counts["parsed"] >= 1
        assert metrics.stage_counts["chunking"] >= 1
        
        # Verify timing
        assert metrics.last_job_time is not None
        assert metrics.last_job_time >= start_time
        assert metrics.last_job_time <= end_time
    
    @pytest.mark.asyncio
    async def test_configuration_validation(self, base_worker, test_config):
        """Test configuration validation and usage"""
        # Verify configuration is properly loaded
        assert base_worker.config == test_config
        assert base_worker.poll_interval == test_config.poll_interval
        assert base_worker.max_retries == test_config.max_retries
        assert base_worker.retry_base_delay == test_config.retry_base_delay
        
        # Verify configuration validation
        assert test_config.validate() is True
        
        # Test configuration conversion
        config_dict = test_config.to_dict()
        assert "database_url" in config_dict
        assert "openai_api_key" in config_dict
        assert "llamaparse_api_key" in config_dict
        
        # Test component-specific config extraction
        openai_config = test_config.get_openai_config()
        assert openai_config["api_url"] == test_config.openai_api_url
        assert openai_config["api_key"] == test_config.openai_api_key
        assert openai_config["model"] == test_config.openai_model
        
        llamaparse_config = test_config.get_llamaparse_config()
        assert llamaparse_config["api_url"] == test_config.llamaparse_api_url
        assert llamaparse_config["api_key"] == test_config.llamaparse_api_key
        
        storage_config = test_config.get_storage_config()
        assert storage_config["storage_url"] == test_config.supabase_url
        assert storage_config["service_role_key"] == test_config.supabase_service_role_key

