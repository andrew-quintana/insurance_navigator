"""
Tests for the Task Requirements Agent.

These tests verify that the Task Requirements Agent correctly determines
required documentation for service requests and processes ReAct-based reasoning.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import re
from datetime import datetime

from agents.task_requirements.task_requirements import TaskRequirementsAgent
from agents.task_requirements.models.task_models import (
    DocumentStatus, ReactStep, TaskProcessingResult
)
from agents.common.exceptions import (
    TaskRequirementsException,
    TaskRequirementsProcessingError,
    DocumentValidationError,
    ReactProcessingError
)

# Test data
TEST_INPUT = {
    "meta_intent": {
        "request_type": "service_request",
        "summary": "Request for cardiology consultation",
        "emergency": False
    },
    "clinical_context": {
        "symptom": "chest pain",
        "body": {"region": "chest", "side": "left", "subpart": "center"},
        "onset": "3 days ago",
        "duration": "intermittent"
    },
    "service_intent": {
        "specialty": "cardiology",
        "service": "consultation",
        "plan_detail_type": "coverage"
    },
    "metadata": {
        "raw_user_text": "I need to see a cardiologist for chest pain",
        "user_response_created": "I'll help you with that request.",
        "timestamp": "2025-05-20T14:30:00Z"
    }
}

TEST_REACT_OUTPUT = """
**Thought 1**: I need to determine what documents are required for a cardiology consultation service request.

**Act 1**: determine_required_context[service_intent]

**Obs 1**: The required documents for a cardiology consultation are:
- Insurance ID card
- Primary care referral
- Recent medical records related to heart issues

**Thought 2**: Now I need to check if the insurance ID card is available.

**Act 2**: read_document[insurance_id_card]

**Obs 2**: Insurance ID card is available in the system. Last updated 2025-01-15.

**Thought 3**: Next, I need to check if the referral is available.

**Act 3**: read_document[primary_care_referral]

**Obs 3**: Primary care referral is not available in the system.

**Thought 4**: I need to request validation of the available documents.

**Act 4**: request_document_validation[required_context]

**Obs 4**: The insurance ID card has been validated.

**Thought 5**: I need to request the missing referral from the user.

**Act 5**: request_user[missing_context]

**Obs 5**: User has been informed of the missing primary care referral.

**Thought 6**: Now that all documents are accounted for, I can complete this task.

**Act 6**: finish[(input, required_context)]

**Obs 6**: Task completed. Required documents: insurance ID card (available), primary care referral (requested).
"""


class TestTaskRequirementsAgent(unittest.TestCase):
    """Test suite for the TaskRequirements agent."""

    def setUp(self):
        """Set up test environment."""
        # Mock LLM
        self.mock_llm = Mock()
        self.mock_llm.invoke.return_value = TEST_REACT_OUTPUT
        
        # Mock document manager
        self.mock_doc_manager = Mock()
        self.mock_doc_manager.determine_required_context.return_value = {
            "insurance_id_card": {
                "type": "document",
                "present": None,
                "source": None,
                "user_validated": False,
                "description": "Insurance identification card",
                "date_added": None,
                "document_id": None
            },
            "primary_care_referral": {
                "type": "document",
                "present": None,
                "source": None,
                "user_validated": False,
                "description": "Referral from primary care physician",
                "date_added": None,
                "document_id": None
            }
        }
        self.mock_doc_manager.read_document.side_effect = lambda doc_type: (
            {
            "type": "document",
            "present": True,
                "source": "system",
                "user_validated": False,
                "description": f"Test {doc_type}",
                "date_added": "2025-01-15",
                "document_id": f"test_{doc_type}_id"
            } if doc_type == "insurance_id_card" else 
            {
                "type": "document",
                "present": False,
                "source": None,
            "user_validated": False,
                "description": f"Test {doc_type}",
                "date_added": None,
            "document_id": None
        }
        )
        
        # Mock output agent
        self.mock_output_agent = Mock()
        
        # Mock config manager
        self.mock_config_manager = Mock()
        self.mock_config_manager.get_agent_config.return_value = {
            "model": {
                "name": "test-model",
                "temperature": 0.0
            },
            "prompt": {
                "path": "dummy_path.md"
            },
            "examples": {
                "path": "dummy_examples.md"
            },
            "test_examples": {
                "path": "dummy_test_examples.md"
            }
        }
        
        # Create agent with mocks
        with patch('os.path.exists', return_value=False):
            self.agent = TaskRequirementsAgent(
                llm=self.mock_llm,
                document_manager=self.mock_doc_manager,
                output_agent=self.mock_output_agent,
                config_manager=self.mock_config_manager
            )
            
        # Set default prompt template and examples for testing
        self.agent.prompt_template = "You are a test task requirements agent. {Examples}"
        self.agent.examples = "Example: Determine required documents"

    def test_init(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.name, "task_requirements")
        self.assertEqual(self.agent.document_manager, self.mock_doc_manager)
        self.assertEqual(self.agent.output_agent, self.mock_output_agent)
        self.assertIn("determine_required_context", self.agent.available_actions)

    def test_process_successful(self):
        """Test successful processing."""
        # Setup mock required context that will be returned
        mock_required_context = {
            "insurance_id_card": {
                "type": "document",
                "present": True,
                "source": "system",
                "user_validated": False,
                "description": "Insurance identification card",
                "date_added": "2025-01-15",
                "document_id": "test_insurance_id_card_id"
            },
            "primary_care_referral": {
                "type": "document",
                "present": False,
                "source": None,
                "user_validated": False,
                "description": "Referral from primary care physician",
                "date_added": None,
                "document_id": None
            }
        }
        
        # Update the mock to return this specific context when _process_react_steps is called
        with patch.object(self.agent, '_process_react_steps', return_value={
            "required_context": mock_required_context,
            "status": "complete",
            "input": TEST_INPUT
        }):
            # Process a task
            result = self.agent.process(TEST_INPUT)
            
            # Check that LLM was called
            self.mock_llm.invoke.assert_called_once()
            
            # Check result
            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["input"], TEST_INPUT)
            self.assertIn("required_context", result)
            self.assertIn("insurance_id_card", result["required_context"])
    
    def test_parse_react_output(self):
        """Test parsing of ReAct output."""
        # Parse test output
        steps = self.agent._parse_react_output(TEST_REACT_OUTPUT)
        
        # Check parsing results
        self.assertEqual(len(steps), 6)
        
        # Check first step
        self.assertIn("thought", steps[0])
        self.assertIn("action_name", steps[0])
        self.assertEqual(steps[0]["action_name"], "determine_required_context")
        
        # Check last step
        self.assertEqual(steps[5]["action_name"], "finish")

    def test_build_specific_prompt(self):
        """Test prompt building."""
        # Build prompt
        prompt = self.agent._build_specific_prompt(TEST_INPUT)
        
        # Check prompt structure
        self.assertIn("You are a test task requirements agent", prompt)
        self.assertIn("Example: Determine required documents", prompt)
        self.assertIn("service_request", prompt)  # From TEST_INPUT

    def test_mock_mode(self):
        """Test mock mode operation."""
        # Create agent in mock mode
        mock_agent = TaskRequirementsAgent(
            config_manager=self.mock_config_manager,
            use_mock=True
        )
        
        # Process with mock mode
        result = mock_agent.process(TEST_INPUT)
        
        # Check result
        self.assertEqual(result["status"], "complete")
        self.assertIn("mock_insurance_id", result["required_context"]["insurance_id_card"]["document_id"])

    def test_document_validation_error(self):
        """Test handling of document validation errors."""
        # Make document manager throw an exception
        self.mock_doc_manager.determine_required_context.side_effect = Exception("Document error")
        
        # Create a patched parser that will trigger the error
        def patched_parse(output):
            steps = [
                {
                    "thought": "I need to determine required documents",
                    "action_name": "determine_required_context",
                    "action_args": "service_intent"
                }
            ]
            return steps
            
        # Apply the patch
        with patch.object(self.agent, '_parse_react_output', return_value=patched_parse(TEST_REACT_OUTPUT)):
            # Check that the correct exception is raised - this now matches the actual flow
            with self.assertRaises(ReactProcessingError):
                self.agent.process(TEST_INPUT)

    def test_react_processing_error(self):
        """Test handling of ReAct processing errors."""
        # Make ReAct parsing throw an exception
        with patch.object(self.agent, '_parse_react_output', side_effect=Exception("ReAct error")):
            # Check that the correct exception is raised - this now uses TaskRequirementsProcessingError
            with self.assertRaises(TaskRequirementsProcessingError):
                self.agent.process(TEST_INPUT)

    def test_reset(self):
        """Test agent reset functionality."""
        # Set some state
        self.agent.last_input = TEST_INPUT
        self.agent.last_required_context = {"test": "context"}
        
        # Reset
        self.agent.reset()
        
        # Verify state was cleared
        self.assertIsNone(self.agent.last_input)
        self.assertIsNone(self.agent.last_required_context)


if __name__ == '__main__':
    unittest.main() 