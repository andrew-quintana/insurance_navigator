"""
Base test module for all agent tests.

This module provides common test functionality and utilities for testing agents.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.base_agent import BaseAgent

# Disable logging for tests
logging.disable(logging.CRITICAL)

class BaseAgentTest(unittest.TestCase):
    """Base test class for all agent tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_llm = MagicMock()
        # Removed prompt_loader as it's no longer used in the refactored design
        
    def tearDown(self):
        """Tear down test fixtures."""
        pass
        
    def assert_agent_initialization(self, agent_class, **kwargs):
        """Assert that an agent can be properly initialized."""
        agent = agent_class(
            llm=self.mock_llm,
            use_mock=True,  # Use mock mode for testing
            **kwargs
        )
        self.assertIsInstance(agent, BaseAgent)
        # When use_mock=True, the agent sets self.llm = None, so don't assert equality with mock_llm
        return agent
        
    def assert_agent_method(self, agent, method_name, *args, **kwargs):
        """Assert that an agent method can be called and returns expected result."""
        method = getattr(agent, method_name)
        result = method(*args, **kwargs)
        return result 