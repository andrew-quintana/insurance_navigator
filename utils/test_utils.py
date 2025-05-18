"""
Test Utilities

This module provides base test classes and utilities for testing agents and components.
All agent tests should inherit from the appropriate base test class for consistency.
"""

import os
import json
import logging
import pytest
from typing import Dict, Any, List, Optional, Type
from unittest.mock import MagicMock

from agents.base_agent import BaseAgent
from utils.error_handling import AgentError


class MockLogger:
    """Mock logger for testing."""
    
    def __init__(self):
        self.info_logs = []
        self.error_logs = []
        self.warning_logs = []
        self.debug_logs = []
    
    def info(self, message: str) -> None:
        """Log an info message."""
        self.info_logs.append(message)
    
    def error(self, message: str) -> None:
        """Log an error message."""
        self.error_logs.append(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.warning_logs.append(message)
    
    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.debug_logs.append(message)
    
    def get_logs(self, level: str = "info") -> List[str]:
        """Get logs for a specific level."""
        if level == "info":
            return self.info_logs
        elif level == "error":
            return self.error_logs
        elif level == "warning":
            return self.warning_logs
        elif level == "debug":
            return self.debug_logs
        else:
            raise ValueError(f"Invalid log level: {level}")


class MockLanguageModel:
    """Mock language model for testing."""
    
    def __init__(self, responses: Dict[str, str] = None):
        """Initialize the mock language model with optional predefined responses."""
        self.responses = responses or {}
        self.calls = []
    
    def invoke(self, messages, **kwargs) -> Any:
        """Mock invoke method that returns predefined responses or default responses."""
        prompt = "\n".join([str(m) for m in messages])
        self.calls.append({"prompt": prompt, "kwargs": kwargs})
        
        # Check if there's a predefined response for this prompt
        for key, response in self.responses.items():
            if key in prompt:
                return {'content': response}
        
        # Default mock response
        return {'content': '{"is_valid": true, "result": "mock_response"}'}


class BaseAgentTest:
    """Base test class for all agent tests."""
    
    @pytest.fixture
    def agent_class(self) -> Type[BaseAgent]:
        """Get the agent class to test. Must be overridden in subclasses."""
        raise NotImplementedError("Subclasses must implement agent_class")
    
    @pytest.fixture
    def agent_name(self) -> str:
        """Get the name of the agent being tested. Must be overridden in subclasses."""
        raise NotImplementedError("Subclasses must implement agent_name")
    
    @pytest.fixture
    def mock_config(self) -> Dict[str, Any]:
        """Provide mock configuration."""
        return {
            "active": True,
            "description": "Test agent description",
            "core_file": {
                "path": f"agents/test_agent/core/test_agent.py",
                "version": "0.1"
            },
            "prompt": {
                "version": "0.1",
                "path": f"agents/test_agent/core/prompts/prompt_test_agent_v0_1.md",
                "description": "Test prompt description"
            },
            "examples": {
                "version": "0.1",
                "path": f"agents/test_agent/core/examples/prompt_examples_test_agent_v0_1.json"
            },
            "test_examples": {
                "version": "0.1",
                "path": f"agents/test_agent/tests/data/examples/test_examples_test_agent_v0_1.json"
            },
            "model": {
                "name": "test-model",
                "temperature": 0.0
            },
            "metrics": {
                "latest_run": None
            }
        }
    
    @pytest.fixture
    def mock_logger(self) -> MockLogger:
        """Provide mock logger."""
        return MockLogger()
    
    @pytest.fixture
    def mock_llm(self) -> MockLanguageModel:
        """Provide mock language model."""
        return MockLanguageModel()
    
    @pytest.fixture
    def mock_config_manager(self, mock_config) -> MagicMock:
        """Provide mock configuration manager."""
        mock_manager = MagicMock()
        mock_manager.get_agent_config.return_value = mock_config
        return mock_manager
    
    @pytest.fixture
    def agent(self, agent_class, agent_name, mock_llm, mock_logger, mock_config_manager, monkeypatch) -> BaseAgent:
        """Create agent instance with mocks."""
        # Patch the config manager to return our mock
        monkeypatch.setattr("utils.agent_config_manager.get_config_manager", lambda: mock_config_manager)
        
        # Create the agent with our mocks
        agent = agent_class(
            name=agent_name,
            llm=mock_llm,
            logger=mock_logger
        )
        
        return agent
    
    def test_initialization(self, agent, agent_name, mock_llm, mock_logger):
        """Test that the agent initializes correctly."""
        assert agent.name == agent_name
        assert agent.llm == mock_llm
        assert agent.logger == mock_logger
    
    def test_validate_input_method_exists(self, agent):
        """Test that the _validate_input method exists."""
        assert hasattr(agent, "_validate_input")
    
    def test_process_data_method_exists(self, agent):
        """Test that the _process_data method exists."""
        assert hasattr(agent, "_process_data")
    
    def test_format_output_method_exists(self, agent):
        """Test that the _format_output method exists."""
        assert hasattr(agent, "_format_output")
    
    def test_process_method_exists(self, agent):
        """Test that the process method exists."""
        assert hasattr(agent, "process")


def load_test_examples(file_path: str) -> List[Dict[str, Any]]:
    """Load test examples from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Test examples file not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in test examples file: {file_path}")


def create_test_output_dir(agent_name: str) -> str:
    """Create a directory for test outputs."""
    output_dir = os.path.join("tests", "outputs", agent_name)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir 