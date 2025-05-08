"""
Test module for agents with Anthropic integration.

This module demonstrates how to test agents that use Anthropic models:
1. Using mocks for unit tests (fast, no API cost)
2. Using real Anthropic API calls for integration tests (realistic but costs money)
"""

import os
import sys
import unittest
import json
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the agent you want to test
from agents.prompt_security import PromptSecurityAgent
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

# Helper function to load environment variables for testing
def load_test_env():
    """Load environment variables for testing."""
    from dotenv import load_dotenv
    # Try to load from .env.test first, fall back to .env
    if os.path.exists(".env.test"):
        load_dotenv(".env.test")
    else:
        load_dotenv()
    
    # Check if we have an API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    use_mock = os.environ.get("USE_MOCK_LLM", "true").lower() == "true"
    return api_key, use_mock

class MockAnthropic:
    """Mock Anthropic model for testing."""
    
    def __init__(self, responses=None):
        """Initialize with optional predefined responses."""
        self.responses = responses or {}
        self.invoke_count = 0
        self.invoke_inputs = []
    
    def invoke(self, input_data):
        """Mock invoke method."""
        self.invoke_count += 1
        self.invoke_inputs.append(input_data)
        
        # If we have a predefined response for this input, use it
        if isinstance(input_data, str) and input_data in self.responses:
            return self.responses[input_data]
        
        # Default mock response
        ai_message = AIMessage(content=json.dumps({
            "is_safe": True,
            "threat_detected": False,
            "threat_type": None,
            "threat_severity": None,
            "sanitized_input": input_data,
            "confidence": 0.95,
            "reasoning": "This is a mock response for testing purposes."
        }))
        return ChatResult(generations=[ChatGeneration(message=ai_message)])

class TestAgentWithAnthropic(unittest.TestCase):
    """Tests for agents with Anthropic integration."""
    
    def setUp(self):
        """Set up the test environment."""
        self.api_key, self.use_mock = load_test_env()
    
    def test_agent_with_mock(self):
        """Test agent with mock Anthropic model."""
        # Create a mock Anthropic model
        mock_anthropic = MockAnthropic()
        
        # Initialize the agent with the mock model
        agent = PromptSecurityAgent(llm=mock_anthropic)
        
        # Test with a sample input
        is_safe, sanitized, result = agent.process("Test input")
        
        # Verify the mock was called
        self.assertEqual(mock_anthropic.invoke_count, 1)
        
        # Verify the results based on our default mock response
        self.assertTrue(is_safe)
        self.assertEqual(result["confidence"], 0.95)
    
    def test_agent_with_specific_mock_responses(self):
        """Test agent with specific mock responses."""
        # Create mock responses for specific inputs
        mock_responses = {
            "dangerous input": AIMessage(content=json.dumps({
                "is_safe": False,
                "threat_detected": True,
                "threat_type": "harmful_content",
                "threat_severity": 7,
                "sanitized_input": "[REDACTED]",
                "confidence": 0.9,
                "reasoning": "This input contains potentially harmful content."
            }))
        }
        
        # Create a mock Anthropic model with specific responses
        mock_anthropic = MockAnthropic(responses=mock_responses)
        
        # Initialize the agent with the mock model
        agent = PromptSecurityAgent(llm=mock_anthropic)
        
        # Patch the check_input method to use our mock directly
        # This is needed because our mock is simplified
        with patch.object(agent, 'check_input', side_effect=lambda x: {
            "is_safe": False,
            "threat_detected": True,
            "threat_type": "harmful_content",
            "threat_severity": 7,
            "sanitized_input": "[REDACTED]",
            "confidence": 0.9,
            "reasoning": "This input contains potentially harmful content."
        } if x == "dangerous input" else {
            "is_safe": True,
            "threat_detected": False,
            "threat_type": None,
            "threat_severity": None,
            "sanitized_input": x,
            "confidence": 0.95,
            "reasoning": "This is a safe input."
        }):
            # Test with a safe input
            is_safe, sanitized, result = agent.process("safe input")
            self.assertTrue(is_safe)
            
            # Test with a dangerous input
            is_safe, sanitized, result = agent.process("dangerous input")
            self.assertFalse(is_safe)
            self.assertEqual(sanitized, "[REDACTED]")
            self.assertEqual(result["threat_type"], "harmful_content")
    
    @unittest.skipIf(os.environ.get("USE_MOCK_LLM", "true").lower() == "true", 
                    "Skipping real API test when USE_MOCK_LLM=true")
    def test_agent_with_real_anthropic(self):
        """Test agent with real Anthropic API (only runs if USE_MOCK_LLM=false)."""
        # Skip this test if we don't have an API key
        if not self.api_key:
            self.skipTest("No Anthropic API key available")
        
        # Get the model name from environment or use default
        model_name = os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        
        # Initialize a real Anthropic model
        anthropic = ChatAnthropic(
            temperature=0,
            model=model_name,
            anthropic_api_key=self.api_key
        )
        
        # Initialize the agent with the real model
        agent = PromptSecurityAgent(llm=anthropic)
        
        # Test with a clearly safe input
        is_safe, sanitized, result = agent.process("What is Medicare Part A?")
        
        # We expect this to be safe, but exact values depend on the model
        print(f"Real API result: {result}")
        
        # Check that we got a reasonable result structure
        self.assertIsNotNone(result.get("is_safe"))
        self.assertIsNotNone(result.get("confidence"))
        self.assertIsNotNone(result.get("reasoning"))

def run_tests_with_real_api():
    """Run tests with real Anthropic API."""
    # Set environment variable to use real API
    os.environ["USE_MOCK_LLM"] = "false"
    
    # Run the tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == "__main__":
    # Check if we should run with real API
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-api", action="store_true", 
                        help="Run tests with real Anthropic API")
    args = parser.parse_args()
    
    if args.real_api:
        run_tests_with_real_api()
    else:
        unittest.main() 