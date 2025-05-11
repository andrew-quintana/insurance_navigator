"""
Tests for the Prompt Security Agent.
"""

import unittest
from unittest.mock import MagicMock, patch
from agents.prompt_security.core.prompt_security import PromptSecurityAgent, SecurityCheck
from tests.agents.test_base import BaseAgentTest

class TestPromptSecurityAgent(BaseAgentTest):
    """Test cases for the Prompt Security Agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.agent = self.assert_agent_initialization(PromptSecurityAgent)
        
        # Create a mock response as a dictionary
        self.mock_response = {
            "is_safe": True,
            "threat_detected": False,
            "threat_type": "none",
            "threat_severity": "none_detected",
            "sanitized_input": "Test prompt content",
            "confidence": 0.95,
            "reasoning": "This input appears to be a standard test prompt with no malicious intent."
        }
        
        # Mock the base_chain
        self.agent.base_chain = MagicMock()
        self.agent.base_chain.invoke.return_value = SecurityCheck(**self.mock_response)
        
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertIsInstance(self.agent, PromptSecurityAgent)
        
    def test_quick_check(self):
        """Test the quick_check method."""
        test_input = "Test prompt content"
        result = self.agent.quick_check(test_input)
        self.assertIsInstance(result, bool)
        
    def test_check_input(self):
        """Test the check_input method."""
        test_input = "Test prompt content"
        
        result = self.agent.check_input(test_input)
        
        self.assertEqual(result["is_safe"], True)
        self.assertEqual(result["threat_detected"], False)
        self.assertEqual(result["threat_type"], "none")
        self.assertEqual(result["threat_severity"], "none_detected")
        self.assertEqual(result["sanitized_input"], "Test prompt content")
        self.assertEqual(result["confidence"], 0.95)
        self.assertEqual(result["reasoning"], "This input appears to be a standard test prompt with no malicious intent.")
        self.agent.base_chain.invoke.assert_called_once_with(test_input)
        
    def test_process(self):
        """Test the process method."""
        test_input = "Test prompt content"
        
        result = self.agent.process(test_input)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        self.assertTrue(result[0])  # is_safe
        self.assertEqual(result[1], "Test prompt content")  # sanitized_input
        self.assertEqual(result[2]["is_safe"], True)
        self.assertEqual(result[2]["threat_detected"], False)
        self.assertEqual(result[2]["threat_type"], "none")
        self.assertEqual(result[2]["threat_severity"], "none_detected")
        self.assertEqual(result[2]["sanitized_input"], "Test prompt content")
        self.assertEqual(result[2]["confidence"], 0.95)
        self.assertEqual(result[2]["reasoning"], "This input appears to be a standard test prompt with no malicious intent.")
        self.agent.base_chain.invoke.assert_called_once_with(test_input)

if __name__ == '__main__':
    unittest.main() 