"""
Tests for the Patient Navigator Agent.

These tests verify that the Patient Navigator Agent correctly processes user queries,
formats outputs, and handles errors.
"""

import os
import unittest
from unittest.mock import Mock, patch
import json
from datetime import datetime

from agents.patient_navigator.patient_navigator import PatientNavigatorAgent
from agents.patient_navigator.models.navigator_models import (
    NavigatorOutput, MetaIntent, ClinicalContext, ServiceIntent, Metadata, BodyLocation
)
from agents.common.exceptions import (
    PatientNavigatorException,
    PatientNavigatorProcessingError,
    PatientNavigatorOutputParsingError
)

# Test data
TEST_QUERY = "Does Medicare cover a visit to the cardiologist?"
TEST_USER_ID = "test_user_123"
TEST_SESSION_ID = "test_session_456"

TEST_MODEL_RESPONSE = """
{
  "meta_intent": {
    "request_type": "policy_question",
    "summary": "Inquiry about Medicare coverage for cardiologist visits",
    "emergency": false
  },
  "clinical_context": {
    "symptom": null,
    "body": {
      "region": null,
      "side": null,
      "subpart": null
    },
    "onset": null,
    "duration": null
  },
  "service_intent": {
    "specialty": "cardiology",
    "service": "office_visit",
    "plan_detail_type": "coverage"
  },
  "metadata": {
    "raw_user_text": "Does Medicare cover a visit to the cardiologist?",
    "user_response_created": "Yes, Medicare Part B generally covers visits to cardiologists when they're medically necessary. You'll typically pay 20% of the Medicare-approved amount after you've met your Part B deductible. The visit would need to be with a cardiologist who accepts Medicare assignment for the best coverage.",
    "timestamp": "2025-05-20T14:30:00Z"
  }
}
"""


class TestPatientNavigatorAgent(unittest.TestCase):
    """Test suite for the PatientNavigator agent."""

    def setUp(self):
        """Set up test environment."""
        # Mock LLM
        self.mock_llm = Mock()
        self.mock_llm.invoke.return_value = TEST_MODEL_RESPONSE
        
        # Mock prompt security agent
        self.mock_security_agent = Mock()
        self.mock_security_agent.validate_prompt.return_value = (True, 0.95, [])
        
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
            }
        }
        
        # Create agent with mocks
        with patch('os.path.exists', return_value=False):
            self.agent = PatientNavigatorAgent(
                llm=self.mock_llm,
                prompt_security_agent=self.mock_security_agent,
                config_manager=self.mock_config_manager
            )
            
        # Set a default system prompt for testing
        self.agent.system_prompt = "You are a test navigator agent."

    def test_init(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.name, "patient_navigator")
        self.assertEqual(self.agent.system_prompt, "You are a test navigator agent.")
        self.assertEqual(self.agent.llm, self.mock_llm)
        self.assertEqual(self.agent.prompt_security_agent, self.mock_security_agent)

    def test_process_successful(self):
        """Test successful query processing."""
        # Process a query
        response_text, result = self.agent.process(TEST_QUERY, TEST_USER_ID, TEST_SESSION_ID)
        
        # Check that LLM was called
        self.mock_llm.invoke.assert_called_once()
        
        # Check security agent was called
        self.mock_security_agent.validate_prompt.assert_called_once_with(TEST_QUERY)
        
        # Check response
        self.assertIn("Medicare Part B generally covers visits to cardiologists", response_text)
        self.assertEqual(result["meta_intent"]["request_type"], "policy_question")
        self.assertEqual(result["service_intent"]["specialty"], "cardiology")

    def test_security_check_failed(self):
        """Test handling of failed security check."""
        # Make security check fail
        self.mock_security_agent.validate_prompt.return_value = (False, 0.1, ["Potential prompt injection"])
        
        # Process a query
        response_text, result = self.agent.process(TEST_QUERY, TEST_USER_ID, TEST_SESSION_ID)
        
        # Check response
        self.assertIn("I apologize, but I cannot process this request", response_text)
        self.assertEqual(result["meta_intent"]["request_type"], "security_issue")

    def test_conversation_management(self):
        """Test conversation management features."""
        # Process a query to create a conversation
        self.agent.process(TEST_QUERY, TEST_USER_ID, TEST_SESSION_ID)
        
        # Check that conversation was saved
        conversation_key = f"{TEST_USER_ID}:{TEST_SESSION_ID}"
        self.assertIn(conversation_key, self.agent.active_conversations)
        
        # Get history
        history = self.agent.get_conversation_history(TEST_USER_ID, TEST_SESSION_ID)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["raw_user_text"], TEST_QUERY)
        
        # End conversation
        self.agent.end_conversation(TEST_USER_ID, TEST_SESSION_ID)
        
        # Verify conversation was removed
        self.assertNotIn(conversation_key, self.agent.active_conversations)
        
        # Verify exception on getting nonexistent conversation
        with self.assertRaises(PatientNavigatorException):
            self.agent.get_conversation_history(TEST_USER_ID, TEST_SESSION_ID)

    @patch('langchain_core.output_parsers.PydanticOutputParser.parse')
    def test_parsing_error(self, mock_parse):
        """Test handling of parsing errors."""
        # Make parser throw an exception
        mock_parse.side_effect = ValueError("Invalid format")
        
        # Check that the correct exception is raised
        with self.assertRaises(PatientNavigatorOutputParsingError):
            self.agent.process(TEST_QUERY, TEST_USER_ID, TEST_SESSION_ID)

    def test_reset(self):
        """Test agent reset functionality."""
        # Create some conversations
        self.agent.process(TEST_QUERY, TEST_USER_ID, TEST_SESSION_ID)
        self.agent.process(TEST_QUERY, "other_user", "other_session")
        
        # Verify conversations exist
        self.assertEqual(len(self.agent.active_conversations), 2)
        
        # Reset
        self.agent.reset()
        
        # Verify conversations were cleared
        self.assertEqual(len(self.agent.active_conversations), 0)


if __name__ == '__main__':
    unittest.main() 