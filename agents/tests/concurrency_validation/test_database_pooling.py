# Unit Tests for Database Connection Pooling (FM-043 Fix #2)
# Tests the DatabasePoolManager and RAG core connection pooling

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch, MagicMock
from agents.tooling.rag.database_manager import DatabasePoolManager, get_pool_manager, get_db_connection, release_db_connection


class TestDatabasePoolManager:
    """Test database connection pooling implementation."""
    
    @pytest.fixture
    def pool_manager(self):
        """Create a pool manager for testing."""
        return DatabasePoolManager(min_size=2, max_size=5)
    
    @pytest.mark.asyncio
    async def test_pool_manager_initialization(self, pool_manager):
        """Test pool manager initializes correctly."""
        assert pool_manager.min_size == 2
        assert pool_manager.max_size == 5
        assert pool_manager.pool is None
        
        # Mock asyncpg to avoid actual database connection
        with patch('agents.tooling.rag.database_manager.asyncpg') as mock_asyncpg:
            mock_pool = AsyncMock()
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
            
            # Mock environment variable
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}):
                await pool_manager.initialize()
            
            assert pool_manager.pool is not None
            mock_asyncpg.create_pool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pool_manager_with_individual_params(self, pool_manager):
        """Test pool manager initialization with individual database parameters."""
        with patch('agents.tooling.rag.database_manager.asyncpg') as mock_asyncpg:
            mock_pool = AsyncMock()
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
            
            # No DATABASE_URL, use individual params
            with patch.dict(os.environ, {
                'SUPABASE_DB_HOST': 'testhost',
                'SUPABASE_DB_PORT': '5433',
                'SUPABASE_DB_USER': 'testuser',
                'SUPABASE_DB_PASSWORD': 'testpass',
                'SUPABASE_DB_NAME': 'testdb'
            }, clear=True):
                await pool_manager.initialize()
            
            # Verify called with individual parameters
            mock_asyncpg.create_pool.assert_called_once_with(
                host='testhost',
                port=5433,
                user='testuser',
                password='testpass',
                database='testdb',
                min_size=2,
                max_size=5,
                statement_cache_size=0
            )
    
    @pytest.mark.asyncio
    async def test_connection_acquire_and_release(self, pool_manager):
        """Test acquiring and releasing connections from pool."""
        with patch('agents.tooling.rag.database_manager.asyncpg') as mock_asyncpg:
            mock_pool = AsyncMock()
            mock_connection = AsyncMock()
            
            mock_pool.acquire.return_value = mock_connection
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
            
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}):
                await pool_manager.initialize()
            
            # Test acquire
            conn = await pool_manager.acquire_connection()
            assert conn == mock_connection
            mock_pool.acquire.assert_called_once()
            
            # Test release
            await pool_manager.release_connection(conn)
            mock_pool.release.assert_called_once_with(conn)
    
    @pytest.mark.asyncio
    async def test_pool_status_monitoring(self, pool_manager):
        """Test pool status reporting for monitoring."""
        with patch('agents.tooling.rag.database_manager.asyncpg') as mock_asyncpg:
            from unittest.mock import MagicMock
            mock_pool = MagicMock()
            mock_pool.get_size.return_value = 3
            mock_pool.get_min_size.return_value = 2
            mock_pool.get_max_size.return_value = 5
            mock_pool.get_idle_size.return_value = 1
            
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
            
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}):
                await pool_manager.initialize()
            
            status = await pool_manager.get_pool_status()
            
            assert status['status'] == 'active'
            assert status['size'] == 3
            assert status['min_size'] == 2  
            assert status['max_size'] == 5
            assert status['idle_size'] == 1
    
    @pytest.mark.asyncio
    async def test_pool_status_not_initialized(self, pool_manager):
        """Test pool status when pool is not initialized."""
        status = await pool_manager.get_pool_status()
        assert status['status'] == 'not_initialized'
    
    @pytest.mark.asyncio
    async def test_connection_pool_limits(self):
        """Test that connection pool respects min/max size limits."""
        with patch('agents.tooling.rag.database_manager.asyncpg') as mock_asyncpg:
            mock_pool = AsyncMock()
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
            
            pool_manager = DatabasePoolManager(min_size=3, max_size=10)
            
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}):
                await pool_manager.initialize()
            
            # Verify pool created with correct limits
            mock_asyncpg.create_pool.assert_called_once()
            call_kwargs = mock_asyncpg.create_pool.call_args[1]
            assert call_kwargs['min_size'] == 3
            assert call_kwargs['max_size'] == 10
    
    @pytest.mark.asyncio
    async def test_pool_cleanup_and_closure(self, pool_manager):
        """Test proper pool cleanup and closure."""
        with patch('agents.tooling.rag.database_manager.asyncpg') as mock_asyncpg:
            mock_pool = AsyncMock()
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
            
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}):
                await pool_manager.initialize()
            
            assert pool_manager.pool is not None
            
            # Test pool closure
            await pool_manager.close_pool()
            mock_pool.close.assert_called_once()
            assert pool_manager.pool is None
    
    @pytest.mark.asyncio
    async def test_error_handling_in_pool_operations(self, pool_manager):
        """Test error handling in pool operations."""
        with patch('agents.tooling.rag.database_manager.asyncpg') as mock_asyncpg:
            # Test initialization error
            mock_asyncpg.create_pool.side_effect = Exception("Connection failed")
            
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}):
                with pytest.raises(Exception, match="Connection failed"):
                    await pool_manager.initialize()
    
    @pytest.mark.asyncio
    async def test_global_pool_manager_singleton(self):
        """Test global pool manager singleton behavior."""
        with patch('agents.tooling.rag.database_manager.asyncpg') as mock_asyncpg:
            mock_pool = AsyncMock()
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
            
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}):
                # Get pool manager multiple times
                manager1 = await get_pool_manager()
                manager2 = await get_pool_manager()
                
                # Should be the same instance
                assert manager1 is manager2
                
                # Should only initialize once
                assert mock_asyncpg.create_pool.call_count == 1


class TestRAGCoreIntegration:
    """Test RAG core integration with connection pooling."""
    
    @pytest.mark.asyncio
    async def test_rag_core_uses_pooled_connections(self):
        """Test that RAG core uses pooled connections instead of creating new ones."""
        with patch('agents.tooling.rag.database_manager.get_db_connection') as mock_get_conn:
            with patch('agents.tooling.rag.database_manager.release_db_connection') as mock_release_conn:
                mock_connection = AsyncMock()
                mock_get_conn.return_value = mock_connection
                
                # Mock the database query results
                mock_connection.fetch.return_value = [
                    {'similarity': 0.8},
                    {'similarity': 0.7},
                    {'similarity': 0.6}
                ]
                
                # Create a minimal RAG instance to test
                from agents.tooling.rag.core import RAGTool
                
                # Mock dependencies
                with patch.object(RAGTool, '_generate_embedding', return_value=[0.1] * 1536):
                    rag = RAGTool(user_id="test-user")
                    
                    # Call the method that should use pooled connections
                    try:
                        await rag.retrieve_chunks([0.1] * 1536)
                    except Exception:
                        pass  # We expect this to fail due to mocking, but connection calls should happen
                    
                    # Verify pool connection functions were called
                    mock_get_conn.assert_called_once()
                    mock_release_conn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_release_on_exception(self):
        """Test that connections are properly released even when exceptions occur."""
        with patch('agents.tooling.rag.database_manager.get_db_connection') as mock_get_conn:
            with patch('agents.tooling.rag.database_manager.release_db_connection') as mock_release_conn:
                mock_connection = AsyncMock()
                mock_get_conn.return_value = mock_connection
                
                # Make connection fetch raise an exception
                mock_connection.fetch.side_effect = Exception("Database error")
                
                from agents.tooling.rag.core import RAGTool
                
                with patch.object(RAGTool, '_generate_embedding', return_value=[0.1] * 1536):
                    rag = RAGTool(user_id="test-user")
                    
                    # This should handle the exception and still release the connection
                    result = await rag.retrieve_chunks([0.1] * 1536)
                    
                    # Should return empty list on error
                    assert result == []
                    
                    # Verify connection was still released despite exception
                    mock_get_conn.assert_called_once()
                    mock_release_conn.assert_called_once_with(mock_connection)


class TestConnectionPoolPerformance:
    """Test connection pool performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_concurrent_connection_usage(self):
        """Test pool handles concurrent connection requests efficiently."""
        with patch('agents.tooling.rag.database_manager.asyncpg') as mock_asyncpg:
            mock_pool = AsyncMock()
            mock_connections = [AsyncMock() for _ in range(5)]
            
            # Mock pool to return different connections
            connection_index = 0
            async def get_connection():
                nonlocal connection_index
                conn = mock_connections[connection_index % len(mock_connections)]
                connection_index += 1
                return conn
            
            mock_pool.acquire.side_effect = get_connection
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
            
            pool_manager = DatabasePoolManager(min_size=2, max_size=5)
            
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}):
                await pool_manager.initialize()
            
            # Simulate concurrent connection requests
            async def use_connection():
                conn = await pool_manager.acquire_connection()
                await asyncio.sleep(0.01)  # Simulate work
                await pool_manager.release_connection(conn)
                return conn
            
            # Run 20 concurrent operations with pool of max 5 connections
            tasks = [use_connection() for _ in range(20)]
            results = await asyncio.gather(*tasks)
            
            # All operations should complete successfully
            assert len(results) == 20
            
            # Pool should have been used efficiently
            assert mock_pool.acquire.call_count == 20
            assert mock_pool.release.call_count == 20
    
    @pytest.mark.asyncio
    async def test_pool_connection_reuse(self):
        """Test that pool properly reuses connections."""
        with patch('agents.tooling.rag.database_manager.asyncpg') as mock_asyncpg:
            mock_pool = AsyncMock()
            mock_connection = AsyncMock()
            
            # Always return the same connection (reuse)
            mock_pool.acquire.return_value = mock_connection
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
            
            pool_manager = DatabasePoolManager(min_size=1, max_size=1)
            
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}):
                await pool_manager.initialize()
            
            # Use connection multiple times
            for _ in range(10):
                conn = await pool_manager.acquire_connection()
                await pool_manager.release_connection(conn)
                assert conn is mock_connection  # Same connection reused
            
            # Should have acquired/released same connection 10 times
            assert mock_pool.acquire.call_count == 10
            assert mock_pool.release.call_count == 10