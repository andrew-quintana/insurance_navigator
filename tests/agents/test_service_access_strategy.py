"""
Test module for the Service Access Strategy Agent.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.service_access_strategy import ServiceAccessStrategyAgent, ServiceAccessStrategy
from agents.policy_compliance import PolicyComplianceAgent
from agents.service_provider import ServiceProviderAgent
from langchain_core.messages import AIMessage

class TestServiceAccessStrategyAgent(unittest.TestCase):
    """Tests for the Service Access Strategy Agent."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create mock agents
        self.mock_policy_agent = MagicMock(spec=PolicyComplianceAgent)
        self.mock_policy_agent.process.return_value = (
            True, 
            0.85, 
            {
                "is_compliant": True,
                "compliance_score": 0.85,
                "non_compliant_reasons": [],
                "rules_applied": ["Medicare Part B covers outpatient medical services"],
                "recommendations": ["Confirm referral requirements"],
                "confidence": 0.9
            }
        )
        
        self.mock_provider_agent = MagicMock(spec=ServiceProviderAgent)
        self.mock_provider_agent.process.return_value = (
            [
                {
                    "name": "Boston Diabetes Center",
                    "address": "123 Medical Parkway, Boston, MA",
                    "distance": 3.2,
                    "in_network": True,
                    "specialties": ["endocrinology"]
                }
            ],
            {"total_results": 1}
        )
        
        # Create a mock LLM that returns a predefined response
        self.mock_llm = MagicMock()
        self.mock_llm.invoke.return_value = AIMessage(content="""
        ```json
        {
            "patient_need": "endocrinology consultation for diabetes management",
            "matched_services": [
                {
                    "service_name": "Endocrinology Consultation",
                    "service_type": "Specialist Visit",
                    "service_description": "Evaluation by endocrinologist for diabetes management",
                    "is_covered": true,
                    "coverage_details": {"copay": "$40", "requires_referral": true},
                    "estimated_cost": "$40-60 copay with insurance",
                    "required_documentation": ["Insurance card", "Referral from PCP"],
                    "prerequisites": ["Updated lab work", "Blood glucose records"],
                    "alternatives": ["Telemedicine endocrinology visit", "Diabetes education program"],
                    "compliance_score": 0.85
                }
            ],
            "recommended_service": "Endocrinology Consultation",
            "action_plan": [
                {
                    "step_number": 1,
                    "step_description": "Obtain referral from primary care physician",
                    "expected_timeline": "1-2 weeks",
                    "required_resources": ["Appointment with PCP", "Medical records"],
                    "potential_obstacles": ["PCP availability", "Incomplete medical records"],
                    "contingency_plan": "Request urgent referral if needed"
                },
                {
                    "step_number": 2,
                    "step_description": "Schedule appointment with recommended endocrinologist",
                    "expected_timeline": "2-4 weeks",
                    "required_resources": ["Referral", "Insurance card", "Calendar"],
                    "potential_obstacles": ["Limited appointment availability"],
                    "contingency_plan": "Ask to be placed on cancellation list"
                }
            ],
            "estimated_timeline": "1-2 months",
            "provider_options": [
                {
                    "name": "Boston Diabetes Center",
                    "address": "123 Medical Parkway, Boston, MA",
                    "distance": 3.2,
                    "in_network": true,
                    "specialties": ["endocrinology"]
                }
            ],
            "compliance_assessment": {
                "is_compliant": true,
                "compliance_score": 0.85,
                "rules_applied": ["Medicare Part B covers specialist visits"]
            },
            "guidance_notes": [
                "Bring complete medication list to appointment",
                "Prepare questions about glucose management"
            ],
            "confidence": 0.9
        }
        ```
        """)
        
        # Initialize the agent with mocks
        self.agent = ServiceAccessStrategyAgent(
            llm=self.mock_llm,
            policy_compliance_agent=self.mock_policy_agent,
            service_provider_agent=self.mock_provider_agent
        )
        
        # Sample data for testing
        self.patient_info = {
            "name": "John Doe",
            "age": 67,
            "gender": "Male",
            "medical_conditions": ["type 2 diabetes", "hypertension"]
        }
        
        self.medical_need = "endocrinology consultation for diabetes management"
        
        self.policy_info = {
            "policy_type": "Medicare",
            "plan_name": "Medicare Advantage",
            "member_id": "MA123456789"
        }
        
        self.location = "Boston, MA"
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.name, "service_access_strategy")
        self.assertIsNotNone(self.agent.logger)
        self.assertIsNotNone(self.agent.strategy_parser)
        self.assertEqual(self.agent.policy_compliance_agent, self.mock_policy_agent)
        self.assertEqual(self.agent.service_provider_agent, self.mock_provider_agent)
    
    def test_check_compliance(self):
        """Test checking policy compliance."""
        compliance_info = self.agent.check_compliance("Medicare", "endocrinology", self.patient_info)
        
        self.assertTrue(compliance_info["is_compliant"])
        self.assertEqual(compliance_info["compliance_score"], 0.85)
        self.assertEqual(len(compliance_info["non_compliant_reasons"]), 0)
        
        # Test with no policy agent
        self.agent.policy_compliance_agent = None
        compliance_info = self.agent.check_compliance("Medicare", "endocrinology", self.patient_info)
        
        self.assertTrue(compliance_info["is_compliant"])
        self.assertEqual(compliance_info["compliance_score"], 0.8)
        self.assertIn("Assumed coverage", compliance_info["rules_applied"][0])
        
        # Test error handling
        self.agent.policy_compliance_agent = self.mock_policy_agent
        self.mock_policy_agent.process.side_effect = Exception("Test error")
        
        compliance_info = self.agent.check_compliance("Medicare", "endocrinology", self.patient_info)
        self.assertFalse(compliance_info["is_compliant"])
        self.assertEqual(compliance_info["compliance_score"], 0.0)
        self.assertIn("Error checking compliance", compliance_info["non_compliant_reasons"][0])
    
    def test_find_providers(self):
        """Test finding providers."""
        providers = self.agent.find_providers("endocrinology", "Boston, MA")
        
        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0]["name"], "Boston Diabetes Center")
        self.assertTrue(providers[0]["in_network"])
        
        # Test with no provider agent
        self.agent.service_provider_agent = None
        providers = self.agent.find_providers("endocrinology", "Boston, MA")
        
        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0]["name"], "Example Provider")
        
        # Test error handling
        self.agent.service_provider_agent = self.mock_provider_agent
        self.mock_provider_agent.process.side_effect = Exception("Test error")
        
        providers = self.agent.find_providers("endocrinology", "Boston, MA")
        self.assertEqual(len(providers), 0)
    
    def test_develop_strategy(self):
        """Test developing a service access strategy."""
        strategy = self.agent.develop_strategy(
            self.patient_info,
            self.medical_need,
            self.policy_info,
            self.location
        )
        
        self.assertEqual(strategy["patient_need"], self.medical_need)
        self.assertEqual(strategy["recommended_service"], "Endocrinology Consultation")
        self.assertEqual(len(strategy["matched_services"]), 1)
        self.assertEqual(len(strategy["action_plan"]), 2)
        self.assertEqual(strategy["action_plan"][0]["step_number"], 1)
        self.assertEqual(strategy["estimated_timeline"], "1-2 months")
        self.assertEqual(strategy["confidence"], 0.9)
    
    def test_error_handling(self):
        """Test error handling in strategy development."""
        # Make the LLM raise an exception
        self.mock_llm.invoke.side_effect = Exception("Test error")
        
        strategy = self.agent.develop_strategy(
            self.patient_info,
            self.medical_need,
            self.policy_info,
            self.location
        )
        
        self.assertEqual(strategy["patient_need"], self.medical_need)
        self.assertEqual(strategy["recommended_service"], "Unable to determine due to error")
        self.assertEqual(len(strategy["matched_services"]), 0)
        self.assertEqual(len(strategy["action_plan"]), 1)
        self.assertEqual(strategy["confidence"], 0.0)
        self.assertIn("error", strategy)
        self.assertIn("Test error", strategy["error"])
    
    def test_process_method(self):
        """Test the process method."""
        strategy, providers = self.agent.process(
            self.patient_info,
            self.medical_need,
            self.policy_info,
            self.location
        )
        
        self.assertEqual(strategy["patient_need"], self.medical_need)
        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0]["name"], "Boston Diabetes Center")

if __name__ == "__main__":
    unittest.main() 