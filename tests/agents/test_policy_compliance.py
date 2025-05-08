"""
Test module for the Policy Compliance Evaluator Agent.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.policy_compliance import PolicyComplianceAgent, ComplianceAnalysis
from langchain_core.messages import AIMessage

class TestPolicyComplianceAgent(unittest.TestCase):
    """Tests for the Policy Compliance Evaluator Agent."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock LLM that returns a predefined response
        self.mock_llm = MagicMock()
        self.mock_llm.invoke.return_value = AIMessage(content="""
        ```json
        {
            "is_compliant": true,
            "compliance_score": 0.85,
            "non_compliant_reasons": [],
            "rules_applied": ["Medicare Part B covers outpatient medical services"],
            "recommendations": ["Ensure proper documentation for the visit"],
            "confidence": 0.9,
            "reasoning": "Annual wellness visits are covered under Medicare Part B as preventive care."
        }
        ```
        """)
        
        # Create a mock retriever
        self.mock_retriever = MagicMock()
        self.mock_retriever.get_relevant_documents.return_value = [
            MagicMock(page_content="Annual wellness visits are covered under Medicare Part B.")
        ]
        
        # Initialize the agent with the mock LLM and retriever
        self.agent = PolicyComplianceAgent(llm=self.mock_llm, retriever=self.mock_retriever)
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.name, "policy_compliance")
        self.assertIsNotNone(self.agent.logger)
        self.assertIsNotNone(self.agent.policy_rules)
    
    def test_get_policy_info(self):
        """Test retrieving policy information."""
        # Test with a known policy type
        medicare_info = self.agent.get_policy_info("medicare")
        self.assertIn("Medicare Part A", medicare_info)
        self.assertIn("Medicare Part B", medicare_info)
        
        # Test with an unknown policy type
        unknown_info = self.agent.get_policy_info("unknown")
        self.assertIn("not found", unknown_info)
    
    def test_retrieve_context(self):
        """Test retrieving context using the RAG retriever."""
        context = self.agent.retrieve_context("medicare annual wellness visit")
        self.assertIn("Annual wellness visits", context)
        
        # Test when the retriever raises an exception
        self.mock_retriever.get_relevant_documents.side_effect = Exception("Test error")
        error_context = self.agent.retrieve_context("medicare annual wellness visit")
        self.assertIn("Error retrieving context", error_context)
    
    def test_evaluate_compliance(self):
        """Test evaluating compliance."""
        result = self.agent.evaluate_compliance(
            policy_type="medicare",
            service_request="Annual wellness visit",
            user_context={"age": 67, "has_part_b": True}
        )
        
        self.assertTrue(result["is_compliant"])
        self.assertEqual(result["compliance_score"], 0.85)
        self.assertEqual(len(result["non_compliant_reasons"]), 0)
        self.assertEqual(len(result["rules_applied"]), 1)
        self.assertIn("Annual wellness visits", result["reasoning"])
    
    def test_evaluate_compliance_error(self):
        """Test error handling in compliance evaluation."""
        # Make the LLM raise an exception
        self.mock_llm.invoke.side_effect = Exception("Test error")
        
        result = self.agent.evaluate_compliance(
            policy_type="medicare",
            service_request="Annual wellness visit"
        )
        
        self.assertFalse(result["is_compliant"])
        self.assertEqual(result["compliance_score"], 0.0)
        self.assertIn("Processing error", result["non_compliant_reasons"][0])
    
    def test_process(self):
        """Test the process method."""
        is_compliant, score, result = self.agent.process(
            policy_type="medicare",
            service_request="Annual wellness visit"
        )
        
        self.assertTrue(is_compliant)
        self.assertEqual(score, 0.85)
        self.assertTrue(isinstance(result, dict))
        self.assertIn("reasoning", result)

if __name__ == "__main__":
    unittest.main() 