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
        self.mock_prompt_loader = MagicMock()
        
    def tearDown(self):
        """Tear down test fixtures."""
        pass
        
    def assert_agent_initialization(self, agent_class, **kwargs):
        """Assert that an agent can be properly initialized."""
        agent = agent_class(
            llm=self.mock_llm,
            prompt_loader=self.mock_prompt_loader,
            **kwargs
        )
        self.assertIsInstance(agent, BaseAgent)
        self.assertEqual(agent.llm, self.mock_llm)
        self.assertEqual(agent.prompt_loader, self.mock_prompt_loader)
        return agent
        
    def assert_agent_method(self, agent, method_name, *args, **kwargs):
        """Assert that an agent method can be called and returns expected result."""
        method = getattr(agent, method_name)
        result = method(*args, **kwargs)
        return result 