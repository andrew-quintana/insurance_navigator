"""
Tests for the Policy Compliance Agent.
"""

import unittest
from unittest.mock import MagicMock, patch
from agents.policy_compliance.core.logic import PolicyComplianceAgent
from tests.agents.test_base import BaseAgentTest

class TestPolicyComplianceAgent(BaseAgentTest):
    """Test cases for the Policy Compliance Agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.agent = self.assert_agent_initialization(PolicyComplianceAgent)
        
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertIsInstance(self.agent, PolicyComplianceAgent)
        
    def test_check_compliance(self):
        """Test compliance checking."""
        test_data = {
            "patient_id": "12345",
            "action": "share_data",
            "recipient": "external_provider",
            "data_type": "medical_history"
        }
        expected_result = {
            "is_compliant": True,
            "policy_references": ["HIPAA §164.502", "HITECH Act §13405"],
            "requirements_met": ["patient_consent", "minimum_necessary"],
            "restrictions": ["no_marketing_use", "secure_transmission_required"]
        }
        
        # Mock the LLM response
        self.mock_llm.generate.return_value = expected_result
        
        result = self.agent.check_compliance(test_data)
        
        self.assertEqual(result, expected_result)
        self.mock_llm.generate.assert_called_once()
        
    def test_validate_action(self):
        """Test action validation."""
        test_action = {
            "type": "data_access",
            "user_role": "physician",
            "resource": "patient_records",
            "purpose": "treatment"
        }
        expected_result = {
            "is_valid": True,
            "authorization_level": "full_access",
            "required_documentation": ["patient_consent", "treatment_relationship"],
            "audit_trail": True
        }
        
        # Mock the LLM response
        self.mock_llm.generate.return_value = expected_result
        
        result = self.agent.validate_action(test_action)
        
        self.assertEqual(result, expected_result)
        self.mock_llm.generate.assert_called_once()
        
    def test_get_policy_requirements(self):
        """Test retrieving policy requirements."""
        test_scenario = "data_sharing_external"
        expected_result = {
            "required_policies": ["privacy", "security", "consent"],
            "compliance_steps": [
                "verify_patient_consent",
                "check_recipient_credentials",
                "encrypt_data",
                "log_transfer"
            ],
            "documentation_needed": ["consent_form", "recipient_agreement"]
        }
        
        # Mock the LLM response
        self.mock_llm.generate.return_value = expected_result
        
        result = self.agent.get_policy_requirements(test_scenario)
        
        self.assertEqual(result, expected_result)
        self.mock_llm.generate.assert_called_once()

if __name__ == '__main__':
    unittest.main() 