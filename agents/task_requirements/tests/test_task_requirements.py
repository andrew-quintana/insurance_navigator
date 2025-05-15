"""
Unit tests for the Task Requirements Agent.

This file contains tests to verify that the TaskRequirementsAgent
properly processes input from the patient navigator, combines the prompt template
with examples, and produces the expected output.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
import time
from datetime import datetime
import sys
import re
from typing import Dict, Any, List, Tuple

# Add the root directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from agents.task_requirements.core.task_requirements import TaskRequirementsAgent

# For SBERT similarity comparison
try:
    from sentence_transformers import SentenceTransformer, util
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False

class MockLLM:
    """Mock LLM for testing."""
    
    def __init__(self, response_text=None, prompt_tokens=100, completion_tokens=50):
        self.response_text = response_text
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.last_prompt = None
    
    def generate(self, prompt):
        """Generate a response from the mock LLM."""
        self.last_prompt = prompt
        
        # If no response text is provided, generate a default one
        if self.response_text is None:
            self.response_text = self._generate_default_response()
        
        # Create a response object with the same interface as the real LLM
        response = MagicMock()
        response.text = self.response_text
        response.prompt_tokens = self.prompt_tokens
        response.completion_tokens = self.completion_tokens
        
        return response
    
    def _generate_default_response(self):
        """Generate a default response for testing."""
        return """
**Thought 1**: I need to determine what documentation or plan rules are required for this request.
**Act 1**: determine_required_context[service_intent]
**Obs 1**: {
  "insurance_id_card": {
    "type": "document",
    "present": null,
    "source": null,
    "user_validated": false,
    "description": "Photo or scan of the user's active insurance card",
    "date_added": null,
    "document_id": null
  },
  "insurance_plan": {
    "type": "document",
    "present": null,
    "source": null,
    "user_validated": false,
    "description": "System must confirm services are covered under user plan",
    "date_added": null,
    "document_id": null
  }
}

**Thought 2**: I need to check the insurance card to confirm coverage.
**Act 2**: read_document[insurance_id_card]
**Obs 2**: {
  "type": "document",
  "present": true,
  "user_validated": false,
  "source": "user_documents_database",
  "description": "Active insurance card valid through 2026",
  "date_added": "2025-05-10",
  "document_id": null
}

**Thought 3**: I need to check the plan coverage info.
**Act 3**: read_document[insurance_plan]
**Obs 3**: {
  "type": "document",
  "present": true,
  "user_validated": false,
  "source": "user_documents_database",
  "description": "Plan covers requested service",
  "date_added": "2025-05-13",
  "document_id": null
}

**Thought 4**: I need to validate the documents with the user.
**Act 4**: request_user[required_context]
**Obs 4**: {
  "insurance_id_card": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Active insurance card valid through 2026",
    "date_added": "2025-05-10",
    "document_id": null
  },
  "insurance_plan": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Plan covers requested service",
    "date_added": "2025-05-13",
    "document_id": null
  }
}

**Thought 5**: I need to add unique IDs to the documents.
**Act 5**: add_doc_unique_ids[required_context]
**Obs 5**: {
  "insurance_id_card": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Active insurance card valid through 2026",
    "date_added": "2025-05-10",
    "document_id": "doc_123"
  },
  "insurance_plan": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Plan covers requested service",
    "date_added": "2025-05-13",
    "document_id": "plan_456"
  }
}

**Thought 6**: I have all the required documentation. I can now finish the task.
**Act 6**: finish[(input, required_context)]
"""

class MockDocumentManager:
    """Mock Document Manager for testing."""
    
    def determine_required_context(self, service_intent):
        """Determine the required context based on the service intent."""
        return {
            "insurance_id_card": {
                "type": "document",
                "present": None,
                "source": None,
                "user_validated": False,
                "description": "Photo or scan of the user's active insurance card",
                "date_added": None,
                "document_id": None
            },
            "insurance_plan": {
                "type": "document",
                "present": None,
                "source": None,
                "user_validated": False,
                "description": "System must confirm services are covered under user plan",
                "date_added": None,
                "document_id": None
            }
        }
    
    def read_document(self, document_type):
        """Read a document from the document manager."""
        return {
            "type": "document",
            "present": True,
            "user_validated": False,
            "source": "user_documents_database",
            "description": f"Mock {document_type} document",
            "date_added": datetime.now().strftime("%Y-%m-%d"),
            "document_id": None
        }
    
    def validate_documents(self, required_context):
        """Validate documents."""
        updated_context = required_context.copy()
        for key in updated_context:
            updated_context[key]["user_validated"] = True
        return updated_context
    
    def validate_information(self, required_context):
        """Validate information."""
        return required_context
    
    def add_unique_ids(self, required_context):
        """Add unique IDs to documents."""
        updated_context = required_context.copy()
        for key in updated_context:
            updated_context[key]["document_id"] = f"mock_id_{key}"
        return updated_context

class MockOutputAgent:
    """Mock Output Agent for testing."""
    
    def __init__(self):
        self.last_request = None
        self.last_task = None
    
    def request_user_information(self, missing_context):
        """Request information from the user."""
        self.last_request = missing_context
        
        # Return validated context
        updated_context = missing_context.copy()
        for key in updated_context:
            updated_context[key]["user_validated"] = True
        
        return updated_context
    
    def process_task(self, task):
        """Process a completed task."""
        self.last_task = task
        return {"status": "success"}

class TestTaskRequirementsAgent(unittest.TestCase):
    """Test case for the TaskRequirementsAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use test versions of the prompt files
        self.prompt_path = "agents/task_requirements/prompts/prompt_task_requirements_v0_1.md"
        self.examples_path = "agents/task_requirements/prompts/examples/prompt_examples_task_requirements_v0_1.md"
        
        # Create mock components
        self.mock_llm = MockLLM()
        self.mock_document_manager = MockDocumentManager()
        self.mock_output_agent = MockOutputAgent()
        
        # Initialize the agent with mock components
        self.agent = TaskRequirementsAgent(
            llm=self.mock_llm,
            document_manager=self.mock_document_manager,
            output_agent=self.mock_output_agent,
            prompt_path=self.prompt_path,
            examples_path=self.examples_path,
            use_mock=False
        )
        
        # Create test input data
        self.test_input = {
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
        }
        
        # Load test examples
        self.test_examples_path = "agents/task_requirements/tests/data/examples/test_examples_task_requirements_v0_1.md"
        with open(self.test_examples_path, 'r') as f:
            self.test_examples_content = f.read()
        
        # Initialize SBERT model if available
        if SBERT_AVAILABLE:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.prompt_path, self.prompt_path)
        self.assertEqual(self.agent.examples_path, self.examples_path)
        self.assertFalse(self.agent.use_mock)
        self.assertIsNotNone(self.agent.prompt_template)
        self.assertIsNotNone(self.agent.examples)
    
    def test_build_prompt(self):
        """Test that the prompt is built correctly."""
        prompt = self.agent._build_prompt(self.test_input)
        
        # Verify that the prompt includes the examples
        self.assertIn("# Example 1:", prompt)
        
        # Verify that the prompt includes the input
        self.assertIn(json.dumps(self.test_input, indent=2), prompt)
    
    def test_determine_required_context(self):
        """Test the determine_required_context action."""
        service_intent = self.test_input["service_intent"]
        result = self.agent._determine_required_context(service_intent)
        
        # Verify the result structure
        self.assertIn("insurance_id_card", result)
        self.assertIn("insurance_plan", result)
        
        # Verify the result content
        self.assertEqual(result["insurance_id_card"]["present"], None)
        self.assertEqual(result["insurance_id_card"]["user_validated"], False)
    
    def test_read_document(self):
        """Test the read_document action."""
        result = self.agent._read_document("insurance_id_card")
        
        # Verify the result structure
        self.assertEqual(result["type"], "document")
        self.assertEqual(result["present"], True)
        self.assertEqual(result["user_validated"], False)
        self.assertIn("description", result)
    
    def test_request_document_validation(self):
        """Test the request_document_validation action."""
        required_context = {
            "insurance_id_card": {
                "type": "document",
                "present": True,
                "user_validated": False,
                "source": "user_documents_database",
                "description": "Mock insurance_id_card document",
                "date_added": datetime.now().strftime("%Y-%m-%d"),
                "document_id": None
            }
        }
        
        result = self.agent._request_document_validation(required_context)
        
        # Verify the result
        self.assertEqual(result["insurance_id_card"]["user_validated"], True)
    
    def test_request_user(self):
        """Test the request_user action."""
        required_context = {
            "insurance_id_card": {
                "type": "document",
                "present": True,
                "user_validated": False,
                "source": "user_documents_database",
                "description": "Mock insurance_id_card document",
                "date_added": datetime.now().strftime("%Y-%m-%d"),
                "document_id": None
            }
        }
        
        result = self.agent._request_user(required_context)
        
        # Verify the result
        self.assertEqual(result["insurance_id_card"]["user_validated"], True)
        
        # Verify that the output agent was called
        self.assertEqual(self.mock_output_agent.last_request, required_context)
    
    def test_add_doc_unique_ids(self):
        """Test the add_doc_unique_ids action."""
        required_context = {
            "insurance_id_card": {
                "type": "document",
                "present": True,
                "user_validated": True,
                "source": "user_documents_database",
                "description": "Mock insurance_id_card document",
                "date_added": datetime.now().strftime("%Y-%m-%d"),
                "document_id": None
            }
        }
        
        result = self.agent._add_doc_unique_ids(required_context)
        
        # Verify the result
        self.assertIsNotNone(result["insurance_id_card"]["document_id"])
        self.assertEqual(result["insurance_id_card"]["document_id"], "mock_id_insurance_id_card")
    
    def test_finish(self):
        """Test the finish action."""
        input_data = self.test_input
        required_context = {
            "insurance_id_card": {
                "type": "document",
                "present": True,
                "user_validated": True,
                "source": "user_documents_database",
                "description": "Mock insurance_id_card document",
                "date_added": datetime.now().strftime("%Y-%m-%d"),
                "document_id": "mock_id_insurance_id_card"
            }
        }
        
        result = self.agent._finish((input_data, required_context))
        
        # Verify the result structure
        self.assertIn("input", result)
        self.assertIn("required_context", result)
        self.assertIn("status", result)
        self.assertIn("timestamp", result)
        
        # Verify the result content
        self.assertEqual(result["input"], input_data)
        self.assertEqual(result["required_context"], required_context)
        self.assertEqual(result["status"], "complete")
        
        # Verify that the output agent was called
        self.assertEqual(self.mock_output_agent.last_task, result)
    
    def test_parse_react_output(self):
        """Test parsing the ReAct output."""
        llm_output = self.mock_llm._generate_default_response()
        steps = self.agent._parse_react_output(llm_output)
        
        # Verify the steps
        self.assertEqual(len(steps), 6)
        self.assertIn("thought", steps[0])
        self.assertIn("act", steps[0])
        self.assertIn("action_name", steps[0])
        self.assertIn("action_args", steps[0])
        self.assertIn("observation", steps[0])
        
        # Verify the first step
        self.assertEqual(steps[0]["action_name"], "determine_required_context")
        self.assertEqual(steps[0]["action_args"], "service_intent")
    
    def test_process_react_steps(self):
        """Test processing the ReAct steps."""
        # Create mock steps
        steps = [
            {
                "thought": "I need to determine what documentation or plan rules are required for this request.",
                "act": "determine_required_context[service_intent]",
                "action_name": "determine_required_context",
                "action_args": "service_intent",
                "observation": "..."
            },
            {
                "thought": "I need to check the insurance card to confirm coverage.",
                "act": "read_document[insurance_id_card]",
                "action_name": "read_document",
                "action_args": "insurance_id_card",
                "observation": "..."
            },
            {
                "thought": "I need to validate the documents with the user.",
                "act": "request_user[required_context]",
                "action_name": "request_user",
                "action_args": "required_context",
                "observation": "..."
            },
            {
                "thought": "I need to add unique IDs to the documents.",
                "act": "add_doc_unique_ids[required_context]",
                "action_name": "add_doc_unique_ids",
                "action_args": "required_context",
                "observation": "..."
            },
            {
                "thought": "I have all the required documentation. I can now finish the task.",
                "act": "finish[(input, required_context)]",
                "action_name": "finish",
                "action_args": "(input, required_context)",
                "observation": "..."
            }
        ]
        
        # Set the last input
        self.agent.last_input = self.test_input
        
        # Process the steps
        result = self.agent._process_react_steps(steps)
        
        # Verify the result
        self.assertIn("required_context", result)
        self.assertIn("status", result)
    
    def test_process_with_mock_llm(self):
        """Test processing with a mock LLM."""
        result = self.agent.process(self.test_input)
        
        # Verify the result
        self.assertIn("required_context", result)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "complete")
        
        # Verify metrics were updated
        self.assertEqual(self.agent.metrics["total_requests"], 1)
        self.assertEqual(self.agent.metrics["successful_requests"], 1)
        self.assertGreater(self.agent.metrics["avg_response_time"], 0)
    
    def test_process_with_mock_mode(self):
        """Test processing with mock mode enabled."""
        # Create a new agent with mock mode enabled
        mock_agent = TaskRequirementsAgent(
            prompt_path=self.prompt_path,
            examples_path=self.examples_path,
            use_mock=True
        )
        
        result = mock_agent.process(self.test_input)
        
        # Verify the result
        self.assertIn("required_context", result)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "complete")
        
        # Verify the required context
        self.assertIn("insurance_id_card", result["required_context"])
        self.assertEqual(result["required_context"]["insurance_id_card"]["present"], True)
        self.assertEqual(result["required_context"]["insurance_id_card"]["user_validated"], True)
    
    def test_process_without_llm(self):
        """Test processing without an LLM."""
        # Create a new agent without an LLM
        no_llm_agent = TaskRequirementsAgent(
            document_manager=self.mock_document_manager,
            output_agent=self.mock_output_agent,
            prompt_path=self.prompt_path,
            examples_path=self.examples_path,
            use_mock=False
        )
        
        result = no_llm_agent.process(self.test_input)
        
        # Verify the result
        self.assertIn("error", result)
        self.assertEqual(result["status"], "failed")
    
    def test_metrics(self):
        """Test metrics collection and reporting."""
        # Process a request to generate metrics
        self.agent.process(self.test_input)
        
        # Get the metrics
        metrics = self.agent.get_metrics()
        
        # Verify the metrics structure
        self.assertIn("total_requests", metrics)
        self.assertIn("successful_requests", metrics)
        self.assertIn("failed_requests", metrics)
        self.assertIn("avg_response_time", metrics)
        self.assertIn("token_usage", metrics)
        self.assertIn("by_category", metrics)
        self.assertIn("success_rate", metrics)
        
        # Verify the metrics content
        self.assertEqual(metrics["total_requests"], 1)
        self.assertEqual(metrics["successful_requests"], 1)
        self.assertEqual(metrics["success_rate"], 1.0)
        
        # Test saving metrics
        metrics_file = self.agent.save_metrics()
        self.assertTrue(os.path.exists(metrics_file))
        
        # Clean up
        if os.path.exists(metrics_file):
            os.remove(metrics_file)
    
    def test_against_examples(self):
        """Test the agent against the test examples."""
        # Skip if SBERT is not available
        if not SBERT_AVAILABLE:
            self.skipTest("SBERT is not available")
        
        # Extract examples from the test examples file
        examples = self._extract_examples_from_md(self.test_examples_content)
        
        for i, example in enumerate(examples):
            # Create a custom LLM response based on the example
            llm_response = self._create_llm_response_from_example(example)
            mock_llm = MockLLM(response_text=llm_response)
            
            # Create a new agent with the mock LLM
            test_agent = TaskRequirementsAgent(
                llm=mock_llm,
                document_manager=self.mock_document_manager,
                output_agent=self.mock_output_agent,
                prompt_path=self.prompt_path,
                examples_path=self.examples_path,
                use_mock=False
            )
            
            # Process the input
            result = test_agent.process(example["input"])
            
            # Compare the result with the expected output
            similarity_score = self._compare_outputs(result, example["expected_output"])
            
            # Verify the similarity score
            self.assertGreaterEqual(similarity_score, 0.7, f"Example {i+1} failed with similarity score {similarity_score}")
            
            # Print the result
            print(f"Example {i+1}: Similarity score = {similarity_score:.2f} - {'PASS' if similarity_score >= 0.7 else 'FAIL'}")
    
    def _extract_examples_from_md(self, md_content: str) -> List[Dict[str, Any]]:
        """Extract examples from the markdown content."""
        examples = []
        
        # Split the content by example sections
        example_sections = re.split(r'# Example \d+:', md_content)[1:]
        
        for section in example_sections:
            # Extract the input JSON
            input_match = re.search(r'```json\n(.*?)\n```', section, re.DOTALL)
            if not input_match:
                continue
            
            input_json = json.loads(input_match.group(1))
            
            # Extract the expected output (final required_context)
            output_match = re.search(r'\*\*Obs \d+ \(uid added required_context\)\*\*:\s*```json\n(.*?)\n```', section, re.DOTALL)
            if not output_match:
                continue
            
            expected_output = json.loads(output_match.group(1))
            
            # Create the example
            examples.append({
                "input": input_json,
                "expected_output": expected_output
            })
        
        return examples
    
    def _create_llm_response_from_example(self, example: Dict[str, Any]) -> str:
        """Create an LLM response from an example."""
        # Extract the input and expected output
        input_json = example["input"]
        expected_output = example["expected_output"]
        
        # Create a response with the expected steps
        response = """
**Thought 1**: I need to determine what documentation or plan rules are required for this request.
**Act 1**: determine_required_context[service_intent]
**Obs 1**: {
  "insurance_id_card": {
    "type": "document",
    "present": null,
    "source": null,
    "user_validated": false,
    "description": "Photo or scan of the user's active insurance card",
    "date_added": null,
    "document_id": null
  },
  "insurance_plan": {
    "type": "document",
    "present": null,
    "source": null,
    "user_validated": false,
    "description": "System must confirm services are covered under user plan",
    "date_added": null,
    "document_id": null
  }
}

**Thought 2**: I need to check the insurance card to confirm coverage.
**Act 2**: read_document[insurance_id_card]
**Obs 2**: {
  "type": "document",
  "present": true,
  "user_validated": false,
  "source": "user_documents_database",
  "description": "Active insurance card valid through 2026",
  "date_added": "2025-05-10",
  "document_id": null
}

**Thought 3**: I need to check the plan coverage info.
**Act 3**: read_document[insurance_plan]
**Obs 3**: {
  "type": "document",
  "present": true,
  "user_validated": false,
  "source": "user_documents_database",
  "description": "Plan covers requested service",
  "date_added": "2025-05-13",
  "document_id": null
}

**Thought 4**: I need to validate the documents with the user.
**Act 4**: request_user[required_context]
**Obs 4**: {
  "insurance_id_card": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Active insurance card valid through 2026",
    "date_added": "2025-05-10",
    "document_id": null
  },
  "insurance_plan": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Plan covers requested service",
    "date_added": "2025-05-13",
    "document_id": null
  }
}

**Thought 5**: I need to add unique IDs to the documents.
**Act 5**: add_doc_unique_ids[required_context]
**Obs 5**: """ + json.dumps(expected_output, indent=2) + """

**Thought 6**: I have all the required documentation. I can now finish the task.
**Act 6**: finish[(input, required_context)]
"""
        
        return response
    
    def _compare_outputs(self, actual_output: Dict[str, Any], expected_output: Dict[str, Any]) -> float:
        """Compare the actual output with the expected output using SBERT."""
        # Convert the outputs to strings
        actual_str = json.dumps(actual_output.get("required_context", {}), sort_keys=True)
        expected_str = json.dumps(expected_output, sort_keys=True)
        
        # Compute embeddings
        actual_embedding = self.model.encode(actual_str, convert_to_tensor=True)
        expected_embedding = self.model.encode(expected_str, convert_to_tensor=True)
        
        # Compute cosine similarity
        similarity = util.pytorch_cos_sim(actual_embedding, expected_embedding).item()
        
        return similarity

if __name__ == "__main__":
    unittest.main() 