"""
Tests for the Task Requirements ReAct Agent.

This file contains tests to verify that the TaskRequirementsReactAgent
properly processes input from the patient navigator, combines the prompt template
with examples, and produces the expected output.
"""

import json
import os
import unittest
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from agents.task_requirements.core.task_requirements import TaskRequirementsReactAgent

class TestTaskRequirementsReactAgent(unittest.TestCase):
    """Test case for the TaskRequirementsReactAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use test versions of the prompt files
        self.prompt_template_path = "agents/task_requirements/prompts/prompt_v0.1.md"
        self.examples_path = "agents/task_requirements/prompts/examples/prompt_examples_v0_1.md"
        
        # Create a mock patient navigator agent
        self.mock_patient_navigator = MagicMock()
        self.mock_patient_navigator.process_request.return_value = {"status": "success"}
        
        # Initialize the agent with mock database
        self.agent = TaskRequirementsReactAgent(
            prompt_template_path=self.prompt_template_path,
            examples_path=self.examples_path,
            use_mock_db=True,
            patient_navigator_agent=self.mock_patient_navigator
        )
        
        # Create test input data manually
        self.test_inputs = [
            # Example 3: Service Request — Allergy Test (PPO, No Referral Required)
            {
                "meta_intent": {
                    "request_type": "service_request",
                    "summary": "User wants to get an allergy test.",
                    "emergency": False
                },
                "clinical_context": {
                    "symptom": None,
                    "body": {
                        "region": None,
                        "side": None,
                        "subpart": None
                    },
                    "onset": None,
                    "duration": None
                },
                "service_intent": {
                    "specialty": "allergy",
                    "service": "allergy test",
                    "plan_detail_type": None
                },
                "metadata": {
                    "raw_user_text": "I want to get an allergy test.",
                    "user_response_created": "Got it — I'll check your plan and try to help you access an allergy test near you.",
                    "timestamp": "2025-05-13T15:41:00Z"
                }
            },
            # Example 4: Policy Question — PT Visit Limit
            {
                "meta_intent": {
                    "request_type": "policy_question",
                    "summary": "User asking about physical therapy visit limit.",
                    "emergency": False
                },
                "clinical_context": {
                    "symptom": None,
                    "body": {
                        "region": None,
                        "side": None,
                        "subpart": None
                    },
                    "onset": None,
                    "duration": None
                },
                "service_intent": {
                    "specialty": "physical therapy",
                    "service": "physical therapy",
                    "plan_detail_type": "visit_limit"
                },
                "metadata": {
                    "raw_user_text": "How many physical therapy appointments can I get with my plan?",
                    "user_response_created": "I'll check your plan to see how many physical therapy visits you're allowed each year.",
                    "timestamp": "2025-05-13T15:43:00Z"
                }
            },
            # Example with missing documents (for testing patient navigator requests)
            {
                "meta_intent": {
                    "request_type": "expert_request",
                    "summary": "User is requesting to see a podiatrist.",
                    "emergency": False
                },
                "clinical_context": {
                    "symptom": None,
                    "body": {
                        "region": "foot",
                        "side": None,
                        "subpart": None
                    },
                    "onset": None,
                    "duration": None
                },
                "service_intent": {
                    "specialty": "podiatry",
                    "service": None,
                    "plan_detail_type": None
                },
                "metadata": {
                    "raw_user_text": "Can I book an appointment with a podiatrist?",
                    "user_response_created": "Sure! I'll help you figure out how to get support from a podiatrist based on your insurance.",
                    "timestamp": "2025-05-13T15:51:00Z"
                }
            }
        ]
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.prompt_template_path, self.prompt_template_path)
        self.assertEqual(self.agent.examples_path, self.examples_path)
        self.assertTrue(self.agent.use_mock_db)
        self.assertIsNotNone(self.agent.prompt_template)
        self.assertIsNotNone(self.agent.examples)
        self.assertIsNotNone(self.agent.mock_document_db)
        self.assertEqual(self.agent.patient_navigator_agent, self.mock_patient_navigator)
    
    def test_build_prompt(self):
        """Test that the prompt is built correctly."""
        # Test with a simple input
        test_input = {"test": "input"}
        prompt = self.agent._build_prompt(test_input)
        
        # Verify that the prompt includes the examples
        self.assertIn("# Example 1: Expert Request", prompt)
        
        # Verify that the prompt includes the input
        self.assertIn(json.dumps(test_input, indent=2), prompt)
    
    def test_simulate_document_action(self):
        """Test the document action simulation."""
        # Test with an existing document
        result = self.agent._simulate_document_action("read_document", "insurance_id_card")
        self.assertEqual(result["present"], True)
        self.assertEqual(result["validated"], True)
        self.assertIn("document_id", result)
        
        # Test with a non-existent document
        result = self.agent._simulate_document_action("read_document", "non_existent_document")
        self.assertEqual(result["present"], False)
        self.assertEqual(result["validated"], False)
        self.assertIsNone(result["document_id"])
        
        # Test with an unsupported action
        result = self.agent._simulate_document_action("unsupported_action", "insurance_id_card")
        self.assertIn("error", result)
    
    def test_process_with_allergy_test_input(self):
        """Test processing an allergy test input."""
        # Get the allergy test input
        allergy_test_input = self.test_inputs[0]
        
        # Process the input
        result = self.agent.process(allergy_test_input)
        
        # Verify the result structure
        self.assertIn("required_context", result)
        required_context = result["required_context"]
        
        # Verify the insurance card
        self.assertIn("insurance_id_card", required_context)
        insurance_card = required_context["insurance_id_card"]
        self.assertEqual(insurance_card["present"], True)
        self.assertEqual(insurance_card["validated"], True)
        self.assertIn("document_id", insurance_card)
        
        # Verify the plan coverage info
        self.assertIn("plan_coverage_info", required_context)
        plan_coverage = required_context["plan_coverage_info"]
        self.assertEqual(plan_coverage["present"], True)
        self.assertEqual(plan_coverage["validated"], True)
        self.assertIn("document_id", plan_coverage)
    
    def test_process_with_pt_question_input(self):
        """Test processing a physical therapy policy question input."""
        # Get the PT policy question input
        pt_question_input = self.test_inputs[1]
        
        # Process the input
        result = self.agent.process(pt_question_input)
        
        # Verify the result structure
        self.assertIn("required_context", result)
        required_context = result["required_context"]
        
        # Verify the insurance card
        self.assertIn("insurance_id_card", required_context)
        insurance_card = required_context["insurance_id_card"]
        self.assertEqual(insurance_card["present"], True)
        self.assertEqual(insurance_card["validated"], True)
        self.assertIn("document_id", insurance_card)
        
        # Verify the plan coverage info
        self.assertIn("plan_coverage_info", required_context)
        plan_coverage = required_context["plan_coverage_info"]
        self.assertEqual(plan_coverage["present"], True)
        self.assertEqual(plan_coverage["validated"], True)
        self.assertIn("document_id", plan_coverage)
        self.assertIn("physical therapy visits", plan_coverage["description"])
    
    def test_check_for_missing_documents(self):
        """Test checking for missing documents."""
        # Create a required context with missing documents
        required_context = {
            "insurance_id_card": {
                "type": "document",
                "present": True,
                "validated": True,
                "source": "user_documents_database",
                "description": "Insurance card",
                "document_id": "doc_123"
            },
            "referral_note": {
                "type": "document",
                "present": None,
                "validated": False,
                "source": None,
                "description": "Referral from primary care doctor",
                "document_id": None
            },
            "plan_coverage_info": {
                "type": "document",
                "present": False,
                "validated": False,
                "source": None,
                "description": "Plan coverage information",
                "document_id": None
            }
        }
        
        # Check for missing documents
        missing_docs = self.agent._check_for_missing_documents(required_context)
        
        # Verify that we found the missing documents
        self.assertEqual(len(missing_docs), 2)
        self.assertEqual(missing_docs[0]["type"], "referral_note")
        self.assertEqual(missing_docs[1]["type"], "plan_coverage_info")
    
    def test_request_from_patient_navigator(self):
        """Test requesting documents from the patient navigator."""
        # Create a list of missing documents
        missing_docs = [
            {
                "type": "referral_note",
                "description": "Referral from primary care doctor"
            },
            {
                "type": "plan_coverage_info",
                "description": "Plan coverage information"
            }
        ]
        
        # Set the last input
        self.agent.last_input = self.test_inputs[2]  # Podiatrist example
        
        # Request from the patient navigator
        request = self.agent.request_from_patient_navigator(missing_docs)
        
        # Verify the request
        self.assertEqual(request["request_type"], "document_request")
        self.assertEqual(len(request["missing_documents"]), 2)
        self.assertEqual(request["missing_documents"][0]["type"], "referral_note")
        self.assertEqual(request["context"]["service_intent"]["specialty"], "podiatry")
        
        # Verify that the patient navigator was called
        self.mock_patient_navigator.process_request.assert_called_once()
    
    def test_simulate_document_update(self):
        """Test simulating document updates."""
        # Create a required context with missing documents
        required_context = {
            "insurance_id_card": {
                "type": "document",
                "present": True,
                "validated": True,
                "source": "user_documents_database",
                "description": "Insurance card",
                "document_id": "doc_123"
            },
            "referral_note": {
                "type": "document",
                "present": None,
                "validated": False,
                "source": None,
                "description": "Referral from primary care doctor",
                "document_id": None
            }
        }
        
        # Simulate document update
        updated_context = self.agent._simulate_document_update(required_context)
        
        # Verify that the documents were updated
        self.assertEqual(updated_context["insurance_id_card"]["present"], True)  # Unchanged
        self.assertEqual(updated_context["referral_note"]["present"], True)  # Updated
        self.assertEqual(updated_context["referral_note"]["validated"], True)  # Updated
        self.assertIsNotNone(updated_context["referral_note"]["document_id"])  # Updated
    
    @patch('agents.task_requirements.core.task_requirements.logger')
    def test_process_with_real_llm_not_provided(self, mock_logger):
        """Test processing with a real LLM client not provided."""
        # Get the first test input
        test_input = self.test_inputs[0]
        
        # Process the input with no LLM client
        result = self.agent.process(test_input, llm_client=None)
        
        # Verify the logger was called
        mock_logger.info.assert_any_call("No LLM client provided. In production, this would use a real LLM.")
        
        # Verify that we still get a simulated result
        self.assertIn("required_context", result)
    
    def test_process_with_missing_documents(self):
        """Test processing an input with missing documents."""
        # Get the podiatrist input (which will have a missing referral)
        podiatrist_input = self.test_inputs[2]
        
        # Process the input
        result = self.agent.process(podiatrist_input)
        
        # Verify that a request was sent to the patient navigator
        self.mock_patient_navigator.process_request.assert_called_once()
        
        # Verify the result structure
        self.assertIn("required_context", result)
        self.assertIn("patient_navigator_request", result)
        
        # Verify the request
        request = result["patient_navigator_request"]
        self.assertEqual(request["request_type"], "document_request")
        
        # Verify that the documents were updated after the request
        required_context = result["required_context"]
        self.assertEqual(required_context["referral_note"]["present"], True)
        self.assertEqual(required_context["referral_note"]["validated"], True)
        self.assertIsNotNone(required_context["referral_note"]["document_id"])
    
    def test_parse_react_output(self):
        """Test parsing ReAct output."""
        # Sample ReAct output
        react_output = """
**Thought 1**: I need to determine what documentation is required for allergy testing.
**Act 1**: determine_required_context[service_context]
**Obs 1**: 
```json
{
  "insurance_id_card": {
    "present": null,
    "source": "user_documents",
    "description": "Photo or scan of the user's active insurance card",
    "date_added": null,
    "document_id": null
  },
  "plan_coverage_info": {
    "present": null,
    "source": "CMS policy lookup",
    "description": "System must confirm allergy testing is covered under user plan",
    "date_added": null,
    "document_id": null
  }
}
```

**Thought 2**: I need to check the insurance card to confirm coverage and plan type.
**Act 2**: read_document[insurance_id_card]
**Obs 2**: Card found. It's an Anthem PPO, valid through 2026.

**Thought 3**: Now I need to check plan coverage for allergy testing.
**Act 3**: read_document[plan_coverage_info]
"""
        
        # Parse the output
        steps = self.agent._parse_react_output(react_output)
        
        # Verify the steps
        self.assertEqual(len(steps), 3)
        
        # Check step 1
        self.assertEqual(steps[0]["step"], 1)
        self.assertEqual(steps[0]["action"], "determine_required_context")
        self.assertEqual(steps[0]["action_args"], "service_context")
        self.assertIn("insurance_id_card", steps[0]["observation"])
        
        # Check step 2
        self.assertEqual(steps[1]["step"], 2)
        self.assertEqual(steps[1]["action"], "read_document")
        self.assertEqual(steps[1]["action_args"], "insurance_id_card")
        self.assertIn("Anthem PPO", steps[1]["observation"])
        
        # Check step 3
        self.assertEqual(steps[2]["step"], 3)
        self.assertEqual(steps[2]["action"], "read_document")
        self.assertEqual(steps[2]["action_args"], "plan_coverage_info")
        self.assertNotIn("observation", steps[2])  # No observation for the last step

if __name__ == "__main__":
    unittest.main() 