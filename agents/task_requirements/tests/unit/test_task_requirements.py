"""
Test module for the Task Requirements Agent.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.task_requirements import TaskRequirementsAgent, TaskRequirements
from langchain_core.messages import AIMessage

class TestTaskRequirementsAgent(unittest.TestCase):
    """Tests for the Task Requirements Agent."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock LLM that returns predefined responses
        self.mock_llm = MagicMock()
        self.mock_llm.invoke.return_value = AIMessage(content="""
        ```json
        {
            "task_id": "enrollment_12345",
            "task_name": "Medicare Part B Enrollment",
            "task_description": "Enrolling in Medicare Part B for someone turning 65 next month",
            "category": "enrollment",
            "required_inputs": [
                {
                    "name": "Social Security card",
                    "description": "Original or certified copy of Social Security card",
                    "input_type": "document",
                    "required": true,
                    "source": "Social Security Administration",
                    "alternatives": ["Social Security Number verification letter"],
                    "validation_rules": ["Must be original or certified copy"]
                },
                {
                    "name": "Proof of identity",
                    "description": "Government-issued photo ID",
                    "input_type": "document",
                    "required": true,
                    "source": null,
                    "alternatives": ["Passport", "Driver's license"],
                    "validation_rules": ["Must be unexpired"]
                }
            ],
            "expected_outputs": [
                {
                    "name": "Medicare card",
                    "description": "Official Medicare card showing Parts A and B enrollment",
                    "output_type": "document",
                    "format": "Physical card",
                    "recipients": ["Beneficiary"],
                    "dependencies": [],
                    "success_criteria": ["Shows correct name", "Shows correct Medicare number", "Shows Part B enrollment"]
                },
                {
                    "name": "Enrollment confirmation letter",
                    "description": "Letter confirming successful enrollment in Medicare Part B",
                    "output_type": "document",
                    "format": "Paper letter",
                    "recipients": ["Beneficiary"],
                    "dependencies": [],
                    "success_criteria": ["Shows effective date", "Shows premium amount"]
                }
            ],
            "policy_references": [
                {
                    "policy_name": "Initial Enrollment Period",
                    "policy_section": "42 CFR § 407.14",
                    "requirement": "A 7-month period beginning 3 months before the month an individual first meets the requirements",
                    "authority": "Centers for Medicare & Medicaid Services",
                    "last_updated": "2023-01-15",
                    "impact": "Determines when the beneficiary can enroll without penalties",
                    "uri": "https://www.medicare.gov/basics/get-started-with-medicare/sign-up/when-can-i-sign-up-for-medicare"
                }
            ],
            "estimated_complexity": 4,
            "prerequisites": ["U.S. citizenship or legal residency for at least 5 years"],
            "time_sensitivity": "Must apply during Initial Enrollment Period to avoid penalties",
            "confidence": 0.95
        }
        ```
        """)
        
        # Initialize the agent with the mock LLM
        self.agent = TaskRequirementsAgent(llm=self.mock_llm)
        
        # Test data
        self.test_task_description = "I need to enroll in Medicare Part B because I'm turning 65 next month"
        self.test_context = {
            "user_age": 64,
            "current_insurance": "Employer group health plan",
            "employment_status": "Retiring next month"
        }
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.name, "task_requirements")
        self.assertIsNotNone(self.agent.logger)
        self.assertIsNotNone(self.agent.parser)
        self.assertTrue("enrollment" in self.agent.task_categories)
        self.assertTrue("claims" in self.agent.task_categories)
        self.assertTrue("benefits" in self.agent.task_categories)
    
    def test_check_policy_freshness(self):
        """Test the policy freshness check."""
        today = datetime.now().strftime("%Y-%m-%d")
        old_date = "2000-01-01"
        
        # Current date should be fresh
        self.assertTrue(self.agent._check_policy_freshness(today))
        
        # Old date should not be fresh
        self.assertFalse(self.agent._check_policy_freshness(old_date))
        
        # Invalid date format should return False
        self.assertFalse(self.agent._check_policy_freshness("not a date"))
    
    def test_get_base_requirements(self):
        """Test getting base requirements for a task category."""
        # Get base requirements for a known category
        base_reqs = self.agent._get_base_requirements("enrollment")
        
        # Verify the base requirements are returned correctly
        self.assertEqual(base_reqs["category"], "enrollment")
        self.assertTrue(len(base_reqs["required_inputs"]) > 0)
        self.assertTrue(len(base_reqs["expected_outputs"]) > 0)
        
        # Unknown category should return empty dict
        self.assertEqual(self.agent._get_base_requirements("unknown_category"), {})
    
    def test_identify_requirements(self):
        """Test identifying requirements for a task."""
        result = self.agent.identify_requirements(self.test_task_description, self.test_context)
        
        # Verify the requirements
        self.assertEqual(result["task_name"], "Medicare Part B Enrollment")
        self.assertEqual(result["category"], "enrollment")
        self.assertEqual(len(result["required_inputs"]), 2)
        self.assertEqual(len(result["expected_outputs"]), 2)
        self.assertEqual(len(result["policy_references"]), 1)
        self.assertEqual(result["estimated_complexity"], 4)
        self.assertEqual(result["confidence"], 0.95)
        
        # Verify the LLM was called with the right input
        self.mock_llm.invoke.assert_called_once()
        call_args = self.mock_llm.invoke.call_args[0][0]
        self.assertIn(self.test_task_description, call_args.content)
        self.assertIn(json.dumps(self.test_context, indent=2), call_args.content)
    
    def test_identify_requirements_with_outdated_policy(self):
        """Test identifying requirements with outdated policy references."""
        # Modify the mock LLM to return outdated policy date
        original_return = self.mock_llm.invoke.return_value
        modified_content = original_return.content.replace('"last_updated": "2023-01-15"', '"last_updated": "1999-01-15"')
        self.mock_llm.invoke.return_value = AIMessage(content=modified_content)
        
        # This should trigger warning about outdated policy
        with self.assertLogs(self.agent.logger, level='WARNING') as cm:
            result = self.agent.identify_requirements(self.test_task_description, self.test_context)
            
            # Check that outdated policy warning was logged
            self.assertTrue(any("Outdated policies referenced" in msg for msg in cm.output))
    
    def test_error_handling(self):
        """Test error handling in requirements identification."""
        # Make the LLM raise an exception
        self.mock_llm.invoke.side_effect = Exception("Test error")
        
        result = self.agent.identify_requirements(self.test_task_description)
        
        # Verify error handling
        self.assertEqual(result["task_name"], "Error in task processing")
        self.assertEqual(result["category"], "unknown")
        self.assertEqual(len(result["required_inputs"]), 0)
        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(result["error"], "Test error")
    
    def test_process_method(self):
        """Test the complete process method."""
        result = self.agent.process(self.test_task_description, self.test_context)
        
        # Verify the process result
        self.assertEqual(result["task_name"], "Medicare Part B Enrollment")
        self.assertEqual(result["category"], "enrollment")
        self.assertEqual(result["confidence"], 0.95)

if __name__ == "__main__":
    unittest.main() 