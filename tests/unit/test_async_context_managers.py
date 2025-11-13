"""
Unit tests for async context managers (Phase 2).

Addresses: FM-043 - Implement async context managers for resource cleanup
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestAsyncContextManagers:
    """Test async context manager implementation."""
    
    @pytest.mark.asyncio
    async def test_aenter_aexit_implementation(self):
        """Test __aenter__ and __aexit__ method implementation."""
        class TestResource:
            def __init__(self):
                self.initialized = False
                self.cleaned_up = False
            
            async def __aenter__(self):
                self.initialized = True
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                self.cleaned_up = True
                return False
        
        async with TestResource() as resource:
            assert resource.initialized is True
            assert resource.cleaned_up is False
        
        assert resource.cleaned_up is True
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_on_success(self):
        """Test resource cleanup on successful operations."""
        cleanup_called = []
        
        class TestResource:
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                cleanup_called.append("cleanup")
                return False
        
        async with TestResource():
            pass  # Successful operation
        
        assert len(cleanup_called) == 1
        assert cleanup_called[0] == "cleanup"
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_during_exceptions(self):
        """Test resource cleanup during exception scenarios."""
        cleanup_called = []
        exception_handled = []
        
        class TestResource:
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                cleanup_called.append("cleanup")
                if exc_type is not None:
                    exception_handled.append(exc_type.__name__)
                return False  # Don't suppress exceptions
        
        with pytest.raises(ValueError):
            async with TestResource():
                raise ValueError("Test exception")
        
        assert len(cleanup_called) == 1
        assert len(exception_handled) == 1
        assert exception_handled[0] == "ValueError"
    
    @pytest.mark.asyncio
    async def test_nested_context_managers(self):
        """Test nested context managers and proper cleanup ordering."""
        cleanup_order = []
        
        class InnerResource:
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                cleanup_order.append("inner")
                return False
        
        class OuterResource:
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                cleanup_order.append("outer")
                return False
        
        async with OuterResource():
            async with InnerResource():
                pass
        
        # Cleanup should happen in reverse order (inner first, then outer)
        assert cleanup_order == ["inner", "outer"]
    
    @pytest.mark.asyncio
    async def test_database_pool_context_manager(self):
        """Test DatabasePoolManager async context manager."""
        from agents.tooling.rag.database_manager import DatabasePoolManager
        
        # Mock the asyncpg.create_pool to avoid actual database connection
        with patch('agents.tooling.rag.database_manager.asyncpg.create_pool') as mock_pool:
            mock_pool_instance = AsyncMock()
            mock_pool_instance.close = AsyncMock()
            mock_pool_instance.get_size = MagicMock(return_value=5)
            mock_pool_instance.get_min_size = MagicMock(return_value=5)
            mock_pool_instance.get_max_size = MagicMock(return_value=20)
            mock_pool_instance.get_idle_size = MagicMock(return_value=2)
            mock_pool.return_value = mock_pool_instance
            
            manager = DatabasePoolManager(min_size=5, max_size=20)
            
            async with manager:
                assert manager.pool is not None
                # Pool should be initialized
            
            # Pool should be closed after context exit
            assert manager.pool is None
            mock_pool_instance.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_httpx_async_client_context_manager(self):
        """Test httpx.AsyncClient as async context manager."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            assert client is not None
            # Client should be open
        
        # Client should be closed after context exit
        # (httpx handles this automatically)
    
    @pytest.mark.asyncio
    async def test_concurrent_access_to_context_managed_resources(self):
        """Test concurrent access to context-managed resources."""
        access_count = []
        
        class SharedResource:
            def __init__(self):
                self.lock = asyncio.Lock()
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return False
            
            async def access(self, identifier):
                async with self.lock:
                    access_count.append(identifier)
                    await asyncio.sleep(0.01)
        
        async def use_resource(resource, identifier):
            async with resource:
                await resource.access(identifier)
        
        resource = SharedResource()
        
        # Concurrent access
        tasks = [use_resource(resource, i) for i in range(5)]
        await asyncio.gather(*tasks)
        
        assert len(access_count) == 5
        assert set(access_count) == {0, 1, 2, 3, 4}
    
    @pytest.mark.asyncio
    async def test_performance_impact_measurement(self):
        """Performance impact measurement and validation."""
        import time
        
        class SimpleResource:
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return False
        
        # Measure overhead of context manager
        iterations = 1000
        start = time.time()
        
        for _ in range(iterations):
            async with SimpleResource():
                pass
        
        elapsed = time.time() - start
        overhead_per_iteration = elapsed / iterations
        
        # Context manager overhead should be minimal (< 1ms per iteration)
        assert overhead_per_iteration < 0.001, \
            f"Context manager overhead too high: {overhead_per_iteration*1000:.2f}ms per iteration"

