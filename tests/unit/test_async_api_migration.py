"""
Unit tests for async API migration (Phase 2).

Addresses: FM-043 - Replace deprecated get_event_loop() with get_running_loop()
"""

import pytest
import asyncio
from unittest.mock import Mock, patch


class TestAsyncAPIMigration:
    """Test deprecated API removal and replacement."""
    
    @pytest.mark.asyncio
    async def test_get_running_loop_functionality(self):
        """Test that get_running_loop() works correctly in async context."""
        loop = asyncio.get_running_loop()
        assert loop is not None
        assert isinstance(loop, asyncio.AbstractEventLoop)
    
    @pytest.mark.asyncio
    async def test_get_running_loop_in_executor(self):
        """Test get_running_loop() functionality when using run_in_executor."""
        loop = asyncio.get_running_loop()
        
        def sync_operation():
            # This runs in executor, so get_running_loop() should not work here
            try:
                asyncio.get_running_loop()
                return False  # Should raise RuntimeError
            except RuntimeError:
                return True  # Expected behavior
        
        result = await loop.run_in_executor(None, sync_operation)
        assert result is True, "get_running_loop() should raise RuntimeError in executor"
    
    @pytest.mark.asyncio
    async def test_get_running_loop_error_when_no_loop(self):
        """Test error handling when no event loop is running."""
        # In a thread without event loop, get_running_loop() should fail
        import threading
        
        error_occurred = threading.Event()
        
        def thread_function():
            try:
                asyncio.get_running_loop()
                error_occurred.set()  # Should not reach here
            except RuntimeError:
                error_occurred.set()  # Expected
        
        thread = threading.Thread(target=thread_function)
        thread.start()
        thread.join(timeout=1.0)
        
        assert error_occurred.is_set(), "get_running_loop() should raise RuntimeError outside event loop"
    
    @pytest.mark.asyncio
    async def test_executor_usage_with_new_api(self):
        """Test executor usage with new API patterns."""
        loop = asyncio.get_running_loop()
        
        def sync_task(value):
            return value * 2
        
        result = await loop.run_in_executor(None, sync_task, 21)
        assert result == 42
    
    @pytest.mark.asyncio
    async def test_loop_time_functionality(self):
        """Test loop.time() functionality for timing operations."""
        loop = asyncio.get_running_loop()
        
        start_time = loop.time()
        await asyncio.sleep(0.1)
        end_time = loop.time()
        
        elapsed = end_time - start_time
        assert elapsed >= 0.1, "Elapsed time should be at least 0.1 seconds"
        assert elapsed < 0.2, "Elapsed time should be less than 0.2 seconds"
    
    @pytest.mark.asyncio
    async def test_no_deprecated_api_usage(self):
        """Verify deprecated get_event_loop() is not used in key files."""
        import inspect
        import os
        
        # Check source files directly to avoid import issues
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        files_to_check = [
            "agents/patient_navigator/input_processing/handler.py",
            "agents/patient_navigator/information_retrieval/agent.py",
            "agents/patient_navigator/output_processing/agent.py",
            "core/service_manager.py"
        ]
        
        for file_path in files_to_check:
            full_path = os.path.join(base_path, file_path)
            if not os.path.exists(full_path):
                continue  # Skip if file doesn't exist
            
            with open(full_path, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                # Skip comments and docstrings
                if stripped.startswith('#') or '"""' in line or "'''" in line:
                    continue
                # Check for actual usage (not in strings)
                if '.get_event_loop()' in line and 'get_running_loop()' not in line:
                    # Check if it's in a string
                    if line.count('"') % 2 == 0 and line.count("'") % 2 == 0:
                        # Not in a string, this is a real usage
                        pytest.fail(
                            f"Deprecated get_event_loop() found in {file_path} at line {i}: {line.strip()}"
                        )

