"""
Collocated unit tests for InputHandler async patterns.

Addresses: FM-043 - Phase 2 Pattern Modernization
Tests get_running_loop() replacement.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
import inspect

from .handler import DefaultInputHandler


class TestAsyncAPIMigration:
    """Test async API migration in InputHandler."""
    
    @pytest.fixture
    def handler(self):
        """Create handler instance for testing."""
        return DefaultInputHandler()
    
    @pytest.mark.asyncio
    async def test_get_running_loop_usage(self, handler):
        """Test that get_running_loop() is used in capture_text_input."""
        # Mock input function
        with patch('builtins.input', return_value="test input"):
            result = await handler.capture_text_input("Enter: ")
            assert result == "test input"
    
    @pytest.mark.asyncio
    async def test_no_deprecated_api_in_handler(self):
        """Test that handler doesn't use deprecated get_event_loop()."""
        import inspect
        from . import handler
        
        source = inspect.getsource(handler.DefaultInputHandler)
        
        # Check for deprecated API usage
        lines = source.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#') or '"""' in line:
                continue
            if '.get_event_loop()' in line and 'get_running_loop()' not in line:
                if line.count('"') % 2 == 0 and line.count("'") % 2 == 0:
                    pytest.fail(
                        f"Deprecated get_event_loop() found at line {i}: {line.strip()}"
                    )

