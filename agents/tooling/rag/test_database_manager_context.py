"""
Collocated unit tests for DatabasePoolManager async context managers.

Addresses: FM-043 - Phase 2 Pattern Modernization
Tests async context manager implementation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from .database_manager import DatabasePoolManager


class TestAsyncContextManagers:
    """Test async context manager implementation."""
    
    @pytest.mark.asyncio
    async def test_database_pool_context_manager(self):
        """Test DatabasePoolManager as async context manager."""
        # Mock asyncpg.create_pool
        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock()
        mock_pool.get_size = MagicMock(return_value=5)
        mock_pool.get_min_size = MagicMock(return_value=5)
        mock_pool.get_max_size = MagicMock(return_value=20)
        mock_pool.get_idle_size = MagicMock(return_value=2)
        
        with patch('agents.tooling.rag.database_manager.asyncpg.create_pool', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_pool
            
            manager = DatabasePoolManager(min_size=5, max_size=20)
            
            async with manager:
                # Pool should be initialized
                assert manager.pool is not None
                assert manager.pool == mock_pool
            
            # Pool should be closed after context exit
            assert manager.pool is None
            mock_pool.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_cleanup_on_exception(self):
        """Test context manager cleans up even on exceptions."""
        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock()
        
        with patch('agents.tooling.rag.database_manager.asyncpg.create_pool', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_pool
            
            manager = DatabasePoolManager()
            
            with pytest.raises(ValueError):
                async with manager:
                    raise ValueError("Test exception")
            
            # Pool should still be closed
            assert manager.pool is None
            mock_pool.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_does_not_suppress_exceptions(self):
        """Test context manager doesn't suppress exceptions."""
        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock()
        
        with patch('agents.tooling.rag.database_manager.asyncpg.create_pool', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_pool
            
            manager = DatabasePoolManager()
            
            # Exception should propagate
            with pytest.raises(RuntimeError):
                async with manager:
                    raise RuntimeError("Test exception")
            
            # Pool should still be closed
            mock_pool.close.assert_called_once()

