import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import uuid
import json

from backend.workers.base_worker import BaseWorker, ProcessingMetrics
from backend.shared.config import WorkerConfig

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing"""
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
def base_worker(mock_config):
    """Create a BaseWorker instance for testing"""
    return BaseWorker(mock_config)

class TestBaseWorker:
    """Test cases for BaseWorker class"""
    
    def test_initialization(self, base_worker, mock_config):
        """Test BaseWorker initialization"""
        assert base_worker.worker_id is not None
        assert base_worker.config == mock_config
        assert base_worker.running is False
        assert base_worker.poll_interval == mock_config.poll_interval
        assert base_worker.max_retries == mock_config.max_retries
        assert base_worker.retry_base_delay == mock_config.retry_base_delay
        assert base_worker.circuit_open is False
        assert base_worker.failure_count == 0
    
    def test_worker_id_uniqueness(self, mock_config):
        """Test that each worker gets a unique ID"""
        worker1 = BaseWorker(mock_config)
        worker2 = BaseWorker(mock_config)
        
        assert worker1.worker_id != worker2.worker_id
        assert isinstance(worker1.worker_id, str)
        assert len(worker1.worker_id) > 0
    
    @pytest.mark.asyncio
    async def test_component_initialization(self, base_worker):
        """Test component initialization"""
        # Mock the components
        base_worker.db = AsyncMock()
        base_worker.db.initialize = AsyncMock()
        
        base_worker.storage = Mock()
        base_worker.llamaparse = Mock()
        base_worker.openai = Mock()
        
        # Test initialization
        await base_worker._initialize_components()
        
        base_worker.db.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_component_cleanup(self, base_worker):
        """Test component cleanup"""
        # Mock the components
        base_worker.db = AsyncMock()
        base_worker.db.close = AsyncMock()
        
        base_worker.storage = Mock()
        base_worker.storage.close = AsyncMock()
        
        base_worker.llamaparse = Mock()
        base_worker.llamaparse.close = AsyncMock()
        
        base_worker.openai = Mock()
        base_worker.openai.close = AsyncMock()
        
        # Test cleanup
        await base_worker._cleanup_components()
        
        base_worker.db.close.assert_called_once()
        base_worker.storage.close.assert_called_once()
        base_worker.llamaparse.close.assert_called_once()
        base_worker.openai.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_logic(self, base_worker):
        """Test circuit breaker logic"""
        # Initially closed
        assert base_worker.circuit_open is False
        
        # Open circuit
        for _ in range(5):
            await base_worker._handle_worker_error(Exception("test error"))
        assert base_worker.circuit_open is True
        assert base_worker.failure_count >= 5
        
        # Should not reset immediately
        assert base_worker._should_attempt_reset() is False
        
        # Wait for recovery timeout
        base_worker.last_failure_time = datetime.utcnow() - timedelta(seconds=70)
        assert base_worker._should_attempt_reset() is True
        
        # Reset circuit
        base_worker._reset_circuit()
        assert base_worker.circuit_open is False
        assert base_worker.failure_count == 0
    
    def test_chunk_id_generation(self, base_worker):
        """Test deterministic chunk ID generation"""
        document_id = str(uuid.uuid4())
        chunker_name = "markdown-simple"
        chunker_version = "1"
        chunk_ord = 0
        
        chunk_id1 = base_worker._generate_chunk_id(document_id, chunker_name, chunker_version, chunk_ord)
        chunk_id2 = base_worker._generate_chunk_id(document_id, chunker_name, chunker_version, chunk_ord)
        
        # Should be deterministic
        assert chunk_id1 == chunk_id2
        
        # Should be different for different inputs
        chunk_id3 = base_worker._generate_chunk_id(document_id, chunker_name, chunker_version, 1)
        assert chunk_id1 != chunk_id3
    
    def test_content_hashing(self, base_worker):
        """Test content hashing functions"""
        test_content = "Test content for hashing"
        
        # Test markdown normalization
        normalized = base_worker._normalize_markdown(test_content)
        assert normalized == test_content.strip()
        
        # Test SHA256 computation
        hash1 = base_worker._compute_sha256(test_content)
        hash2 = base_worker._compute_sha256(test_content)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
        
        # Test vector hashing
        test_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        vector_hash = base_worker._compute_vector_sha(test_vector)
        assert len(vector_hash) == 64
    
    @pytest.mark.asyncio
    async def test_markdown_chunking(self, base_worker):
        """Test markdown chunking logic"""
        test_content = """# Document Title

This is the first paragraph.

## Section 1
Content for section 1.

## Section 2
Content for section 2.

More content here.
"""
        
        chunks = await base_worker._generate_chunks(test_content, "markdown-simple@1")
        
        assert len(chunks) > 0
        
        for chunk in chunks:
            assert "ord" in chunk
            assert "text" in chunk
            assert "chunker_name" in chunk
            assert "chunker_version" in chunk
            assert "meta" in chunk
            
            assert chunk["chunker_name"] == "markdown-simple"
            assert chunk["chunker_version"] == "markdown-simple@1"
            assert chunk["text"].strip() != ""
    
    @pytest.mark.asyncio
    async def test_parse_validation_success(self, base_worker):
        """Test successful parse validation"""
        # Mock storage and database
        base_worker.storage = Mock()
        base_worker.storage.read_blob = AsyncMock(return_value="# Test Document\n\nContent here.")
        
        # Create a proper async context manager mock
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)  # No duplicate
        mock_conn.execute = AsyncMock()
        
        # Create an async context manager class
        class MockConnectionManager:
            def __init__(self, conn):
                self.conn = conn
            
            async def __aenter__(self):
                return self.conn
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        # Mock the database connection method using patch
        with patch.object(base_worker, 'db') as mock_db:
            mock_db.get_db_connection.return_value = MockConnectionManager(mock_conn)
            
            # Test validation
            job = {
                "job_id": str(uuid.uuid4()),
                "parsed_path": "storage://parsed/test/test.md"
            }
            
            await base_worker._validate_parsed(job, "test-correlation-id")
            
            # Verify storage read was called
            base_worker.storage.read_blob.assert_called_once_with(job["parsed_path"])
            
            # Verify database update was called
            mock_conn.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_parse_validation_empty_content(self, base_worker):
        """Test parse validation with empty content"""
        base_worker.storage = Mock()
        base_worker.storage.read_blob = AsyncMock(return_value="")
        
        job = {
            "job_id": str(uuid.uuid4()),
            "parsed_path": "storage://parsed/test/test.md"
        }
        
        with pytest.raises(ValueError, match="Parsed content is empty"):
            await base_worker._validate_parsed(job, "test-correlation-id")
    
    @pytest.mark.asyncio
    async def test_parse_validation_no_path(self, base_worker):
        """Test parse validation with no parsed path"""
        job = {
            "job_id": str(uuid.uuid4()),
            "parsed_path": None
        }
        
        with pytest.raises(ValueError, match="No parsed_path found"):
            await base_worker._validate_parsed(job, "test-correlation-id")
    
    @pytest.mark.asyncio
    async def test_chunk_processing_success(self, base_worker):
        """Test successful chunk processing"""
        # Mock storage and database
        base_worker.storage = Mock()
        base_worker.storage.read_blob = AsyncMock(return_value="# Test Document\n\nContent here.")
        
        # Create a proper async context manager mock
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="INSERT 0 1")  # Successful insert
        
        # Create an async context manager class
        class MockConnectionManager:
            def __init__(self, conn):
                self.conn = conn
            
            async def __aenter__(self):
                return self.conn
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        # Mock the database connection method using patch
        with patch.object(base_worker, 'db') as mock_db:
            mock_db.get_db_connection.return_value = MockConnectionManager(mock_conn)
            
            # Test chunking
            job = {
                "job_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "parsed_path": "storage://parsed/test/test.md",
                "chunks_version": "markdown-simple@1"
            }
            
            await base_worker._process_chunks(job, "test-correlation-id")
            
            # Verify storage read was called
            base_worker.storage.read_blob.assert_called_once_with(job["parsed_path"])
            
            # Verify database operations were called
            assert mock_conn.execute.call_count > 0
    
    @pytest.mark.asyncio
    async def test_embedding_processing_success(self, base_worker):
        """Test successful embedding processing"""
        # Mock database and OpenAI client
        base_worker.openai = Mock()
        base_worker.openai.generate_embeddings = AsyncMock(return_value=[[0.1] * 1536, [0.2] * 1536])
        
        # Create a proper async context manager mock
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"chunk_id": str(uuid.uuid4()), "text": "Test chunk 1", "chunk_sha": "hash1"},
            {"chunk_id": str(uuid.uuid4()), "text": "Test chunk 2", "chunk_sha": "hash2"}
        ])
        mock_conn.execute = AsyncMock()
        
        # Create an async context manager class
        class MockConnectionManager:
            def __init__(self, conn):
                self.conn = conn
            
            async def __aenter__(self):
                return self.conn
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        # Mock the database connection method using patch
        with patch.object(base_worker, 'db') as mock_db:
            mock_db.get_db_connection.return_value = MockConnectionManager(mock_conn)
            
            # Test embedding
            job = {
                "job_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "embed_model": "text-embedding-3-small",
                "embed_version": "1"
            }
            
            await base_worker._process_embeddings(job, "test-correlation-id")
            
            # Verify OpenAI was called
            base_worker.openai.generate_embeddings.assert_called_once()
            
            # Verify database operations were called
            assert mock_conn.execute.call_count > 0
    
    @pytest.mark.asyncio
    async def test_job_finalization(self, base_worker):
        """Test job finalization"""
        # Create a proper async context manager mock
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        
        # Create an async context manager class
        class MockConnectionManager:
            def __init__(self, conn):
                self.conn = conn
            
            async def __aenter__(self):
                return self.conn
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        # Mock the database connection method using patch
        with patch.object(base_worker, 'db') as mock_db:
            mock_db.get_db_connection.return_value = MockConnectionManager(mock_conn)
            
            # Test finalization
            job = {
                "job_id": str(uuid.uuid4())
            }
            
            await base_worker._finalize_job(job, "test-correlation-id")
            
            # Verify database update was called
            mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_processing_error(self, base_worker):
        """Test error handling with retry"""
        # Create a proper async context manager mock
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        
        # Create an async context manager class
        class MockConnectionManager:
            def __init__(self, conn):
                self.conn = conn
            
            async def __aenter__(self):
                return self.conn
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        # Mock the database connection method using patch
        with patch.object(base_worker, 'db') as mock_db:
            mock_db.get_db_connection.return_value = MockConnectionManager(mock_conn)
            
            # Test retry scheduling
            job = {
                "job_id": str(uuid.uuid4()),
                "retry_count": 0
            }
            
            error = ValueError("Test error")
            
            await base_worker._schedule_job_retry(job, error, "test-correlation-id")
            
            # Verify database update was called
            mock_conn.execute.assert_called_once()
            
            # Verify retry count was incremented
            call_args = mock_conn.execute.call_args
            assert call_args[0][1] == 1  # retry_count = 1
    
    @pytest.mark.asyncio
    async def test_error_handling_permanent_failure(self, base_worker):
        """Test error handling with permanent failure"""
        # Create a proper async context manager mock
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        
        # Create an async context manager class
        class MockConnectionManager:
            def __init__(self, conn):
                self.conn = conn
            
            async def __aenter__(self):
                return self.conn
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        # Mock the database connection method using patch
        with patch.object(base_worker, 'db') as mock_db:
            mock_db.get_db_connection.return_value = MockConnectionManager(mock_conn)
            
            # Test permanent failure marking
            job = {
                "job_id": str(uuid.uuid4()),
                "retry_count": 3,  # Max retries reached
                "status": "parsed"
            }
            
            error = ValueError("Test error")
            
            await base_worker._handle_processing_error(job, error, "test-correlation-id")
            
            # Verify database update was called
            mock_conn.execute.assert_called_once()
            
            # Verify the parameters contain the expected status
            call_args = mock_conn.execute.call_args
            params = call_args[0][1:]  # Skip the SQL query, get the parameters
            assert "failed_parse" in params
    
    @pytest.mark.asyncio
    async def test_health_check(self, base_worker):
        """Test worker health check"""
        # Mock components
        base_worker.db = AsyncMock()
        base_worker.db.health_check = AsyncMock(return_value={"status": "healthy"})
        
        base_worker.storage = Mock()
        base_worker.storage.health_check = AsyncMock(return_value={"status": "healthy"})
        
        base_worker.llamaparse = Mock()
        base_worker.llamaparse.health_check = AsyncMock(return_value={"status": "healthy"})
        
        base_worker.openai = Mock()
        base_worker.openai.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Test health check
        health = await base_worker.health_check()
        
        assert "status" in health
        assert "worker_id" in health
        assert "running" in health
        assert "timestamp" in health
        assert "metrics" in health
        assert "components" in health
        
        # Verify component health checks were called
        base_worker.db.health_check.assert_called_once()
        base_worker.storage.health_check.assert_called_once()
        base_worker.llamaparse.health_check.assert_called_once()
        base_worker.openai.health_check.assert_called_once()

class TestProcessingMetrics:
    """Test cases for ProcessingMetrics class"""
    
    def test_initialization(self):
        """Test ProcessingMetrics initialization"""
        metrics = ProcessingMetrics()
        
        assert metrics.jobs_processed == 0
        assert metrics.jobs_failed == 0
        assert metrics.processing_time_total == 0.0
        assert metrics.last_job_time is None
        assert metrics.stage_counts == {}
        assert metrics.error_counts == {}
    
    def test_job_completion_recording(self):
        """Test job completion recording"""
        metrics = ProcessingMetrics()
        
        # Record successful job
        metrics.record_job_completion(True, 5.0)
        assert metrics.jobs_processed == 1
        assert metrics.jobs_failed == 0
        assert metrics.processing_time_total == 5.0
        assert metrics.last_job_time is not None
        
        # Record failed job
        metrics.record_job_completion(False, 0.0)
        assert metrics.jobs_processed == 1
        assert metrics.jobs_failed == 1
        assert metrics.processing_time_total == 5.0
    
    def test_stage_completion_recording(self):
        """Test stage completion recording"""
        metrics = ProcessingMetrics()
        
        metrics.record_stage_completion("parsed")
        assert metrics.stage_counts["parsed"] == 1
        
        metrics.record_stage_completion("parsed")
        assert metrics.stage_counts["parsed"] == 2
        
        metrics.record_stage_completion("chunking")
        assert metrics.stage_counts["chunking"] == 1
    
    def test_error_recording(self):
        """Test error recording"""
        metrics = ProcessingMetrics()
        
        metrics.record_error("ValueError")
        assert metrics.error_counts["ValueError"] == 1
        
        metrics.record_error("ValueError")
        assert metrics.error_counts["ValueError"] == 2
    
    def test_metrics_summary(self):
        """Test metrics summary generation"""
        metrics = ProcessingMetrics()
        
        # Add some data
        metrics.record_job_completion(True, 10.0)
        metrics.record_job_completion(False, 0.0)
        metrics.record_stage_completion("parsed")
        metrics.record_error("ValueError")
        
        summary = metrics.get_summary()
        
        assert summary["jobs_processed"] == 1
        assert summary["jobs_failed"] == 1
        assert summary["total_jobs"] == 2
        assert summary["success_rate"] == 50.0
        assert summary["avg_processing_time"] == 5.0
        assert summary["stage_counts"]["parsed"] == 1
        assert summary["error_counts"]["ValueError"] == 1
        assert "last_job_time" in summary
    
    def test_empty_metrics_summary(self):
        """Test metrics summary with no data"""
        metrics = ProcessingMetrics()
        
        summary = metrics.get_summary()
        
        assert summary["jobs_processed"] == 0
        assert summary["jobs_failed"] == 0
        assert summary["total_jobs"] == 0
        assert summary["success_rate"] == 0
        assert summary["avg_processing_time"] == 0
        assert summary["last_job_time"] is None
