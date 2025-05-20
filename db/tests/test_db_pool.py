import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from datetime import datetime

from db.services.db_pool import DatabasePool

class MockConnection:
    def __init__(self):
        self.execute = AsyncMock()
        self.fetch = AsyncMock()

class MockPool:
    def __init__(self):
        self._holders = []
        self._free = []
        self._max_size = 50
        self.acquire = AsyncMock()
        self.close = AsyncMock()

    async def __aenter__(self):
        return MockConnection()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.fixture
def mock_pool():
    return MockPool()

@pytest.fixture
async def db_pool():
    pool = DatabasePool(
        dsn="postgresql://user:password@localhost:5432/testdb",
        min_size=5,
        max_size=20
    )
    pool._pool = mock_pool()
    return pool

class TestDatabasePool:
    async def test_initialization(self):
        """Test pool initialization with custom parameters."""
        pool = DatabasePool(
            dsn="postgresql://user:password@localhost:5432/testdb",
            min_size=5,
            max_size=20,
            max_queries=1000,
            setup_queries=["SET statement_timeout = '30s'"]
        )
        assert pool.min_size == 5
        assert pool.max_size == 20
        assert pool.max_queries == 1000
        assert len(pool.setup_queries) == 1

    @patch('asyncpg.create_pool')
    async def test_initialize_success(self, mock_create_pool, db_pool):
        """Test successful pool initialization."""
        mock_create_pool.return_value = mock_pool()
        await db_pool.initialize()
        mock_create_pool.assert_called_once()

    @patch('asyncpg.create_pool')
    async def test_initialize_failure(self, mock_create_pool):
        """Test pool initialization failure."""
        mock_create_pool.side_effect = Exception("Connection failed")
        pool = DatabasePool("postgresql://invalid")
        
        with pytest.raises(Exception):
            await pool.initialize()

    async def test_connection_acquisition(self, db_pool):
        """Test connection acquisition from pool."""
        async with db_pool.acquire() as conn:
            assert isinstance(conn, MockConnection)
        assert db_pool._stats['active_connections'] == 0

    async def test_execute_with_retry(self, db_pool):
        """Test query execution with retry logic."""
        query = "INSERT INTO test_table (column) VALUES ($1)"
        args = ("test_value",)
        
        result = await db_pool.execute_with_retry(query, *args)
        assert db_pool._stats['queries_executed'] == 1

    async def test_fetch_with_retry(self, db_pool):
        """Test query fetch with retry logic."""
        query = "SELECT * FROM test_table"
        mock_result = [{"id": 1, "name": "test"}]
        
        db_pool._pool.acquire().__aenter__().fetch.return_value = mock_result
        result = await db_pool.fetch_with_retry(query)
        assert db_pool._stats['queries_executed'] == 1

    async def test_error_handling(self, db_pool):
        """Test error handling and statistics updates."""
        error_msg = "Query failed"
        with pytest.raises(Exception):
            db_pool._pool.acquire().__aenter__().execute.side_effect = Exception(error_msg)
            await db_pool.execute_with_retry("SELECT 1")
        
        assert db_pool._stats['error_count'] == 1
        assert db_pool._stats['last_error']['error'] == error_msg

    async def test_health_check_healthy(self, db_pool):
        """Test health check when database is healthy."""
        result = await db_pool.health_check()
        assert result['status'] == 'healthy'
        assert 'response_time_seconds' in result
        assert 'pool_stats' in result

    async def test_health_check_unhealthy(self, db_pool):
        """Test health check when database is unhealthy."""
        db_pool._pool.acquire().__aenter__().execute.side_effect = Exception("Connection lost")
        result = await db_pool.health_check()
        assert result['status'] == 'unhealthy'
        assert 'error' in result

    async def test_get_stats(self, db_pool):
        """Test retrieving pool statistics."""
        stats = await db_pool.get_stats()
        assert 'total_connections' in stats
        assert 'active_connections' in stats
        assert 'queries_executed' in stats
        assert 'error_count' in stats

    async def test_close_pool(self, db_pool):
        """Test pool closure."""
        await db_pool.close()
        db_pool._pool.close.assert_called_once()

    async def test_connection_setup(self, db_pool):
        """Test connection setup with custom queries."""
        mock_conn = MockConnection()
        await db_pool._connection_setup(mock_conn)
        assert mock_conn.execute.call_count >= 2  # Application name and timezone

    async def test_retry_mechanism(self, db_pool):
        """Test retry mechanism for failed queries."""
        db_pool._pool.acquire().__aenter__().execute.side_effect = [
            Exception("Temporary failure"),
            Exception("Temporary failure"),
            "Success"
        ]
        
        result = await db_pool.execute_with_retry("SELECT 1")
        assert result == "Success"
        assert db_pool._stats['error_count'] == 2 