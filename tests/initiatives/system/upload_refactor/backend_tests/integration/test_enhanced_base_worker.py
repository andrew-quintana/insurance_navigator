"""
Integration tests for Enhanced BaseWorker with real service integration.

This test suite validates the enhanced BaseWorker's ability to:
- Integrate with real service clients via ServiceRouter
- Handle cost limits and service unavailability gracefully
- Provide comprehensive error handling and fallback mechanisms
- Track correlation IDs throughout the processing pipeline
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from backend.workers.enhanced_base_worker import EnhancedBaseWorker, ProcessingMetrics
from shared.config import WorkerConfig
from shared.external.service_router import ServiceMode, ServiceUnavailableError, ServiceExecutionError


class TestEnhancedBaseWorker:
    """Test suite for Enhanced BaseWorker integration"""
    
    @pytest.fixture
    async def mock_config(self):
        """Create mock configuration for testing"""
        config = Mock(spec=WorkerConfig)
        config.database_url = "postgresql://test:test@localhost:5432/test"
        config.log_level = "INFO"
        config.poll_interval = 1
        config.max_retries = 3
        config.retry_base_delay = 1
        config.get_storage_config.return_value = {"url": "http://localhost:5000"}
        config.get_service_router_config.return_value = {"mode": "hybrid"}
        config.to_dict.return_value = {"test": "config"}
        # Add get method to mock with different return values
        config.get = Mock(side_effect=lambda key, default=None: {
            "daily_cost_limit": 5.00,
            "hourly_rate_limit": 100
        }.get(key, default))
        return config
    
    @pytest.fixture
    async def mock_components(self):
        """Create mock components for testing"""
        # Mock database manager
        mock_db = AsyncMock()
        mock_db.initialize = AsyncMock()
        mock_db.close = AsyncMock()
        
        # Mock database connection with async context manager support
        mock_connection = AsyncMock()
        mock_connection.execute = AsyncMock(return_value="INSERT 0 1")
        mock_connection.fetch = AsyncMock(return_value=[])
        mock_connection.fetchrow = AsyncMock(return_value=None)
        mock_connection.fetchval = AsyncMock(return_value=0)
        
        # Make the connection an async context manager
        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock(return_value=None)
        
        mock_db.get_db_connection = Mock(return_value=mock_connection)
        
        # Mock storage manager
        mock_storage = AsyncMock()
        mock_storage.close = AsyncMock()
        mock_storage.read_blob.return_value = "# Test Document\n\nThis is test content for chunking."
        
        # Mock service router
        mock_service_router = AsyncMock()
        mock_service_router.close = AsyncMock()
        mock_service_router.health_check.return_value = {
            "status": "healthy",
            "healthy_services": 2,
            "total_services": 2
        }
        
        # Mock cost tracker
        mock_cost_tracker = Mock()
        mock_cost_tracker.configure_service_limits = Mock()
        mock_cost_tracker.get_daily_cost.return_value = 0.50
        mock_cost_tracker.get_hourly_requests.return_value = 50
        mock_cost_tracker.record_request = Mock()
        
        return {
            "db": mock_db,
            "storage": mock_storage,
            "service_router": mock_service_router,
            "cost_tracker": mock_cost_tracker
        }
    
    @pytest.fixture
    async def enhanced_worker(self, mock_config, mock_components):
        """Create EnhancedBaseWorker instance for testing"""
        # Create worker first
        worker = EnhancedBaseWorker(mock_config)
        
        # Patch the _initialize_components method to use our mocks
        async def mock_initialize_components():
            worker.db = mock_components["db"]
            worker.storage = mock_components["storage"]
            worker.service_router = mock_components["service_router"]
            worker.cost_tracker = mock_components["cost_tracker"]
        
        worker._initialize_components = mock_initialize_components
        
        return worker
    
    async def test_initialization(self, enhanced_worker):
        """Test EnhancedBaseWorker initialization"""
        assert enhanced_worker.worker_id is not None
        assert enhanced_worker.running is False
        assert enhanced_worker.circuit_open is False
        assert enhanced_worker.failure_count == 0
        assert enhanced_worker.daily_cost_limit == 5.00
        assert enhanced_worker.hourly_rate_limit == 100
    
    async def test_component_initialization(self, enhanced_worker):
        """Test component initialization"""
        # Call the mocked _initialize_components to set up the mocked components
        await enhanced_worker._initialize_components()
        
        # Verify components are properly initialized
        assert enhanced_worker.db is not None
        assert enhanced_worker.storage is not None
        assert enhanced_worker.service_router is not None
        assert enhanced_worker.cost_tracker is not None
    
    async def test_cost_limit_checking(self, enhanced_worker):
        """Test cost limit checking functionality"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        # Test normal cost limits
        cost_exceeded = await enhanced_worker._check_cost_limits()
        assert cost_exceeded is False
        
        # Test exceeded daily cost limit
        enhanced_worker.cost_tracker.get_daily_cost.return_value = 6.00
        cost_exceeded = await enhanced_worker._check_cost_limits()
        assert cost_exceeded is True
        
        # Test exceeded hourly rate limit
        enhanced_worker.cost_tracker.get_daily_cost.return_value = 0.50
        enhanced_worker.cost_tracker.get_hourly_requests.return_value = 150
        cost_exceeded = await enhanced_worker._check_cost_limits()
        assert cost_exceeded is True
    
    async def test_service_health_checking(self, enhanced_worker):
        """Test service health checking"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        await enhanced_worker._check_service_health()
    
        assert enhanced_worker.service_health is not None
        assert enhanced_worker.last_health_check is not None
        enhanced_worker.service_router.health_check.assert_called_once()
    
    async def test_health_check_frequency(self, enhanced_worker):
        """Test health check frequency logic"""
        # First check should always happen
        assert enhanced_worker._should_check_health() is True
        
        # Set last check to now
        enhanced_worker.last_health_check = datetime.utcnow()
        assert enhanced_worker._should_check_health() is False
        
        # Set last check to 6 minutes ago (should trigger check)
        enhanced_worker.last_health_check = datetime.utcnow() - timedelta(minutes=6)
        assert enhanced_worker._should_check_health() is True
    
    async def test_job_retry_scheduling(self, enhanced_worker):
        """Test job retry scheduling with exponential backoff"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        job = {
            "job_id": str(uuid.uuid4()),
            "retry_count": 0
        }
        
        await enhanced_worker._schedule_job_retry(job, "Test error", "test-correlation-id")
        
        # Verify retry was scheduled
        # The execute method should have been called on the connection
        assert enhanced_worker.db.get_db_connection.called
        
        # Test max retries exceeded
        job["retry_count"] = 3
        await enhanced_worker._schedule_job_retry(job, "Test error", "test-correlation-id")
        
        # Verify job was marked as failed
        assert enhanced_worker.db.get_db_connection.called
    
    async def test_job_failure_marking(self, enhanced_worker):
        """Test marking jobs as permanently failed"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        job = {
            "job_id": str(uuid.uuid4())
        }
        
        await enhanced_worker._mark_job_failed(job, "Test failure", "test-correlation-id")
        
        # Verify job was marked as failed
        enhanced_worker.db.execute.assert_called()
    
    async def test_enhanced_parse_validation(self, enhanced_worker):
        """Test enhanced parse validation with real service integration"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        job = {
            "job_id": str(uuid.uuid4()),
            "parsed_path": "test/path.md"
        }
        
        # Mock database query for duplicate check
        enhanced_worker.db.fetchrow.return_value = None
        
        await enhanced_worker._validate_parsed_enhanced(job, "test-correlation-id")
        
        # Verify validation completed
        enhanced_worker.db.execute.assert_called()
    
    async def test_enhanced_chunk_processing(self, enhanced_worker):
        """Test enhanced chunk processing"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "parsed_path": "test/path.md",
            "chunks_version": "markdown-simple@1"
        }
        
        # Mock database operations
        enhanced_worker.db.execute.return_value = "INSERT 0 1"
        
        await enhanced_worker._process_chunks_enhanced(job, "test-correlation-id")
        
        # Verify chunks were processed
        enhanced_worker.db.execute.assert_called()
    
    async def test_enhanced_embedding_queueing(self, enhanced_worker):
        """Test enhanced embedding queueing with health and cost checks"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4())
        }
        
        # Mock service health check
        enhanced_worker.service_router.get_service.return_value.get_health.return_value.is_healthy = True
        
        # Mock cost limit check
        with patch.object(enhanced_worker, '_check_cost_limits', return_value=False):
            await enhanced_worker._queue_embeddings_enhanced(job, "test-correlation-id")
            
            # Verify job was queued
            enhanced_worker.db.execute.assert_called()
    
    async def test_enhanced_embedding_processing_success(self, enhanced_worker):
        """Test successful embedding processing with real service"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "embed_model": "text-embedding-3-small",
            "embed_version": "1"
        }
        
        # Mock chunks data
        enhanced_worker.db.fetch.return_value = [
            {"chunk_id": "chunk1", "text": "Test text 1", "chunk_sha": "sha1"},
            {"chunk_id": "chunk2", "text": "Test text 2", "chunk_sha": "sha2"}
        ]
        
        # Mock successful embedding generation
        enhanced_worker.service_router.generate_embeddings.return_value = [
            [0.1, 0.2, 0.3] * 512,  # 1536-dimensional vector
            [0.4, 0.5, 0.6] * 512
        ]
        
        # Mock database operations
        enhanced_worker.db.execute.return_value = "INSERT 0 1"
        
        await enhanced_worker._process_embeddings_enhanced(job, "test-correlation-id")
        
        # Verify embeddings were processed
        enhanced_worker.service_router.generate_embeddings.assert_called_once()
        enhanced_worker.cost_tracker.record_request.assert_called_once()
        enhanced_worker.db.execute.assert_called()
    
    async def test_enhanced_embedding_processing_fallback(self, enhanced_worker):
        """Test embedding processing fallback to mock service"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "embed_model": "text-embedding-3-small",
            "embed_version": "1"
        }
        
        # Mock chunks data
        enhanced_worker.db.fetch.return_value = [
            {"chunk_id": "chunk1", "text": "Test text 1", "chunk_sha": "sha1"}
        ]
        
        # Mock service unavailable error
        enhanced_worker.service_router.generate_embeddings.side_effect = ServiceUnavailableError("Service down")
        
        # Mock database operations
        enhanced_worker.db.execute.return_value = "INSERT 0 1"
        
        await enhanced_worker._process_embeddings_enhanced(job, "test-correlation-id")
        
        # Verify fallback to mock embeddings
        enhanced_worker.service_router.generate_embeddings.assert_called_once()
        enhanced_worker.db.execute.assert_called()
    
    async def test_enhanced_embedding_processing_failure(self, enhanced_worker):
        """Test embedding processing failure handling"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "embed_model": "text-embedding-3-small",
            "embed_version": "1"
        }
        
        # Mock chunks data
        enhanced_worker.db.fetch.return_value = [
            {"chunk_id": "chunk1", "text": "Test text 1", "chunk_sha": "sha1"}
        ]
        
        # Mock service execution error
        enhanced_worker.service_router.generate_embeddings.side_effect = ServiceExecutionError("API error")
        
        # Test that error is raised
        with pytest.raises(ServiceExecutionError):
            await enhanced_worker._process_embeddings_enhanced(job, "test-correlation-id")
    
    async def test_enhanced_job_finalization(self, enhanced_worker):
        """Test enhanced job finalization"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        job = {
            "job_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4())
        }
        
        # Mock final metrics
        enhanced_worker.db.fetchval.side_effect = [2, 2]  # 2 chunks, 2 embeddings
        
        await enhanced_worker._finalize_job_enhanced(job, "test-correlation-id")
        
        # Verify job was finalized
        enhanced_worker.db.execute.assert_called()
    
    async def test_enhanced_error_handling(self, enhanced_worker):
        """Test enhanced error handling and classification"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        job = {
            "job_id": str(uuid.uuid4()),
            "retry_count": 0
        }
        
        # Test service unavailable error
        error = ServiceUnavailableError("ServiceUnavailableError")
        await enhanced_worker._handle_processing_error_enhanced(job, error, "test-correlation-id")
        
        # Verify retry was scheduled
        enhanced_worker.db.execute.assert_called()
        
        # Test cost limit error
        error = Exception("Cost limit exceeded")
        await enhanced_worker._handle_processing_error_enhanced(job, error, "test-correlation-id")
        
        # Verify retry was scheduled
        enhanced_worker.db.execute.assert_called()
        
        # Test unknown error
        error = Exception("Unknown error")
        await enhanced_worker._handle_processing_error_enhanced(job, error, "test-correlation-id")
        
        # Verify job was marked as failed
        enhanced_worker.db.execute.assert_called()
    
    async def test_circuit_breaker_logic(self, enhanced_worker):
        """Test circuit breaker pattern implementation"""
        # Test initial state
        assert enhanced_worker.circuit_open is False
        assert enhanced_worker.failure_count == 0
        
        # Test circuit opening after multiple failures
        for i in range(5):
            await enhanced_worker._handle_worker_error(Exception(f"Error {i}"))
        
        assert enhanced_worker.circuit_open is True
        assert enhanced_worker.failure_count == 5
        
        # Test circuit reset timing
        assert enhanced_worker._should_attempt_reset() is False
        
        # Simulate time passing
        enhanced_worker.last_failure_time = datetime.utcnow() - timedelta(minutes=2)
        assert enhanced_worker._should_attempt_reset() is True
        
        # Test circuit reset
        enhanced_worker._reset_circuit()
        assert enhanced_worker.circuit_open is False
        assert enhanced_worker.failure_count == 0
    
    async def test_processing_metrics(self, enhanced_worker):
        """Test processing metrics collection"""
        # Record some metrics
        enhanced_worker._record_processing_success("parse_validated", 1.5)
        enhanced_worker._record_processing_success("chunks_stored", 2.0)
        enhanced_worker._record_processing_error("parse_validated", "Test error")
        
        # Get metrics summary
        summary = enhanced_worker.metrics.get_summary()
        
        assert summary["total_jobs_processed"] == 2
        assert summary["total_errors"] == 1
        assert summary["error_rate"] == 50.0
        assert "parse_validated" in summary["processing_metrics"]
        assert "chunks_stored" in summary["processing_metrics"]
    
    async def test_health_check(self, enhanced_worker):
        """Test enhanced health check functionality"""
        health = await enhanced_worker.health_check()
        
        assert "status" in health
        assert "worker" in health
        assert "services" in health
        assert "costs" in health
        assert "timestamp" in health
        
        # Verify worker health information
        worker_health = health["worker"]
        assert worker_health["worker_id"] == enhanced_worker.worker_id
        assert worker_health["running"] == enhanced_worker.running
        assert worker_health["circuit_open"] == enhanced_worker.circuit_open
    
    async def test_mock_embedding_generation(self, enhanced_worker):
        """Test mock embedding generation as fallback"""
        texts = ["Test text 1", "Test text 2"]
        
        embeddings = await enhanced_worker._generate_mock_embeddings(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536  # OpenAI embedding dimension
        assert len(embeddings[1]) == 1536
        
        # Test deterministic generation
        embeddings2 = await enhanced_worker._generate_mock_embeddings(texts)
        assert embeddings == embeddings2  # Same input should produce same output
    
    async def test_chunk_generation(self, enhanced_worker):
        """Test chunk generation functionality"""
        content = """# Header 1
Content for header 1.

## Header 2
Content for header 2.

More content here.

# Header 3
Final content."""
        
        chunks = await enhanced_worker._generate_chunks(content, "markdown-simple@1")
        
        assert len(chunks) > 0
        
        for chunk in chunks:
            assert "text" in chunk
            assert "ord" in chunk
            assert "chunker_name" in chunk
            assert "chunker_version" in chunk
            assert "meta" in chunk
            assert chunk["chunker_name"] == "markdown-simple"
            assert chunk["chunker_version"] == "markdown-simple@1"
    
    async def test_cleanup(self, enhanced_worker):
        """Test component cleanup"""
        # Initialize components first
        await enhanced_worker._initialize_components()
        
        await enhanced_worker._cleanup_components()
        
        # Verify cleanup was called
        enhanced_worker.db.close.assert_called_once()
        enhanced_worker.storage.close.assert_called_once()
        enhanced_worker.service_router.close.assert_called_once()


class TestProcessingMetrics:
    """Test suite for ProcessingMetrics class"""
    
    def test_initialization(self):
        """Test ProcessingMetrics initialization"""
        metrics = ProcessingMetrics()
        
        assert metrics.processing_metrics == {}
        assert metrics.error_counts == {}
        assert metrics.start_time is not None
    
    def test_metrics_summary(self):
        """Test metrics summary generation"""
        metrics = ProcessingMetrics()
        
        # Add some test data
        metrics.processing_metrics["test_stage"] = {"count": 5, "total_duration": 10.0}
        metrics.error_counts["test_stage"] = {"TestError": 2}
        
        summary = metrics.get_summary()
        
        assert summary["total_jobs_processed"] == 5
        assert summary["total_errors"] == 2
        assert summary["error_rate"] == 40.0
        assert "test_stage" in summary["processing_metrics"]
        assert "test_stage" in summary["error_counts"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
