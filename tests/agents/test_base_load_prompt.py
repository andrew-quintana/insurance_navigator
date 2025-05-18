"""
Test module for the BaseAgent _load_prompt and _load_examples methods.

This module validates that:
1. The _load_prompt method works correctly with different scenarios
2. The _load_examples method loads examples properly
3. Both methods handle errors and fallbacks appropriately
"""

import os
import sys
import pytest
import tempfile
import json
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.base_agent import BaseAgent
from utils.error_handling import ConfigurationError

class TestBaseAgentPromptLoading:
    """Test class for validating BaseAgent's prompt loading functionality."""
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return MagicMock()
    
    @pytest.fixture
    def agent(self, mock_logger):
        """Create a BaseAgent instance for testing."""
        return BaseAgent(
            name="test_agent",
            logger=mock_logger,
            use_mock=True
        )
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_load_prompt_with_valid_path(self, agent, temp_dir):
        """Test loading a prompt from a valid file path."""
        # Create a test prompt file
        prompt_content = "This is a test prompt for the BaseAgent"
        prompt_path = os.path.join(temp_dir, "test_prompt.md")
        
        with open(prompt_path, 'w') as f:
            f.write(prompt_content)
        
        # Load the prompt
        result = agent._load_prompt(prompt_path)
        
        # Verify the result
        assert result == prompt_content
        agent.logger.info.assert_called_with(f"Successfully loaded prompt from {prompt_path}")
    
    def test_load_prompt_with_invalid_path(self, agent):
        """Test loading a prompt from an invalid path."""
        # Use a path that doesn't exist
        invalid_path = "/non/existent/path/prompt.md"
        default_prompt = "Default prompt for testing"
        
        # Load the prompt with a default value
        result = agent._load_prompt(invalid_path, default_prompt=default_prompt)
        
        # Verify the result
        assert result == default_prompt
        agent.logger.warning.assert_called_with(f"Prompt file not found at {invalid_path}, using default prompt")
    
    def test_load_prompt_no_path_no_default(self, agent):
        """Test loading a prompt with no path and no default."""
        # Set the agent's prompt_path to None
        agent.prompt_path = None
        
        # Try to load the prompt without a default
        with pytest.raises(ConfigurationError) as excinfo:
            agent._load_prompt()
        
        # Verify the exception
        assert "No prompt path specified and no default prompt provided" in str(excinfo.value)
    
    def test_load_prompt_no_path_with_default(self, agent):
        """Test loading a prompt with no path but with a default value."""
        # Set the agent's prompt_path to None
        agent.prompt_path = None
        default_prompt = "Default prompt for testing"
        
        # Load the prompt with a default value
        result = agent._load_prompt(default_prompt=default_prompt)
        
        # Verify the result
        assert result == default_prompt
        agent.logger.warning.assert_called_with("No prompt path specified, using default prompt")
    
    def test_load_examples_with_valid_json(self, agent, temp_dir):
        """Test loading examples from a valid JSON file."""
        # Create a test examples file
        examples = [
            {"input": "Example 1 input", "output": "Example 1 output"},
            {"input": "Example 2 input", "output": "Example 2 output"}
        ]
        examples_path = os.path.join(temp_dir, "test_examples.json")
        
        with open(examples_path, 'w') as f:
            json.dump(examples, f)
        
        # Load the examples
        result = agent._load_examples(examples_path)
        
        # Verify the result
        assert result == examples
        assert len(result) == 2
        assert result[0]["input"] == "Example 1 input"
        agent.logger.info.assert_called_with(f"Successfully loaded 2 examples from {examples_path}")
    
    def test_load_examples_with_invalid_path(self, agent):
        """Test loading examples from an invalid path."""
        # Use a path that doesn't exist
        invalid_path = "/non/existent/path/examples.json"
        default_examples = [{"input": "Default input", "output": "Default output"}]
        
        # Load the examples with default values
        result = agent._load_examples(invalid_path, default_examples=default_examples)
        
        # Verify the result
        assert result == default_examples
        agent.logger.warning.assert_called_with(f"Examples file not found at {invalid_path}, using default examples")
    
    def test_load_examples_no_path_no_default(self, agent):
        """Test loading examples with no path and no default."""
        # Set the agent's examples_path to None
        agent.examples_path = None
        
        # Load the examples without a default
        result = agent._load_examples()
        
        # Verify the result
        assert result == []
        agent.logger.info.assert_called_with("No examples path specified and no default examples provided")
    
    def test_load_examples_invalid_json(self, agent, temp_dir):
        """Test loading examples from an invalid JSON file."""
        # Create an invalid JSON file
        examples_path = os.path.join(temp_dir, "invalid_examples.json")
        
        with open(examples_path, 'w') as f:
            f.write("This is not valid JSON")
        
        # Load the examples with default values
        default_examples = [{"input": "Default input", "output": "Default output"}]
        result = agent._load_examples(examples_path, default_examples=default_examples)
        
        # Verify the result
        assert result == default_examples
        agent.logger.warning.assert_called_with(f"Invalid JSON in examples file {examples_path}: Expecting value: line 1 column 1 (char 0), using default examples") 