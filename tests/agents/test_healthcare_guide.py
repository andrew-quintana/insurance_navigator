"""
Test module for the Healthcare Guide Developer Agent.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
import time
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.healthcare_guide import HealthcareGuideAgent, HealthcareGuide, HealthcareGuidePrompt, GuideSection

class TestHealthcareGuideAgent(unittest.TestCase):
    """Tests for the Healthcare Guide Developer Agent."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create mock LLM
        self.mock_llm = MagicMock()
        
        # Create a mock service provider agent
        self.mock_service_provider = MagicMock()
        self.mock_service_provider.find_providers.return_value = {
            "providers": [
                {
                    "name": "Example Medical Center",
                    "address": "123 Healthcare St, Example City",
                    "phone": "555-123-4567",
                    "specialties": ["endocrinology"],
                    "in_network": True,
                    "distance": "5 miles"
                }
            ]
        }
        
        # Initialize the agent with mocks
        self.agent = HealthcareGuideAgent(
            llm=self.mock_llm, 
            service_provider_agent=self.mock_service_provider
        )
        
        # Sample data for testing
        self.user_info = {
            "name": "John Doe",
            "age": 65,
            "gender": "Male",
            "medical_conditions": ["hypertension", "type 2 diabetes"]
        }
        
        self.policy_info = {
            "insurer": "Medicare",
            "policy_type": "Medicare Advantage",
            "policy_number": "MA123456789",
            "effective_date": "2025-01-01"
        }
        
        self.service_info = {
            "service_type": "endocrinology",
            "needed_for": "diabetes management",
            "urgency": "routine",
            "frequency": "quarterly"
        }
        
        self.location = "Boston, MA"
        
        # Sample guide data for tests
        self.sample_guide_dict = {
            "title": "Diabetes Management Guide for John Doe",
            "user_name": "John Doe",
            "summary": "A personalized guide for diabetes care",
            "sections": [
                {
                    "title": "Understanding Your Coverage",
                    "content": "Coverage details here...",
                    "order": 1
                },
                {
                    "title": "Finding a Provider",
                    "content": "Provider information here...",
                    "order": 2
                }
            ],
            "action_items": ["Schedule appointment", "Prepare glucose logs"],
            "provider_details": {"primary": {"name": "Example Medical Center"}},
            "important_contacts": {"insurance": "800-MEDICARE"},
            "next_steps": ["Call to schedule appointment"],
            "last_updated": "2025-05-08 12:00:00"
        }
        
        # Sample PDF prompt data
        self.sample_prompt_dict = {
            "guide_title": "Diabetes Management Guide for John Doe",
            "guide_purpose": "To help navigate diabetes care",
            "user_info": {"name": "John Doe", "age": 65},
            "policy_info": {"insurer": "Medicare Advantage"},
            "service_info": {"service_type": "endocrinology"},
            "provider_info": {"name": "Example Medical Center"},
            "special_instructions": ["Include glucose monitoring tips"],
            "formatting_preferences": {"color_scheme": "blue"}
        }
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.name, "healthcare_guide")
        self.assertIsNotNone(self.agent.logger)
        self.assertIsNotNone(self.agent.guide_parser)
        self.assertIsNotNone(self.agent.prompt_parser)
    
    def test_get_provider_info(self):
        """Test retrieving provider information."""
        provider_info = self.agent.get_provider_info("endocrinology", "Boston, MA")
        
        self.assertIn("providers", provider_info)
        self.assertEqual(len(provider_info["providers"]), 1)
        self.assertEqual(provider_info["providers"][0]["name"], "Example Medical Center")
        
        # Test error handling
        self.mock_service_provider.find_providers.side_effect = Exception("Test error")
        error_info = self.agent.get_provider_info("endocrinology", "Boston, MA")
        
        self.assertEqual(len(error_info["providers"]), 0)
        self.assertIn("error", error_info)
    
    def test_guide_model_creation(self):
        """Test creating a guide model from dictionary data."""
        # Create a HealthcareGuide model from the sample dictionary
        guide = HealthcareGuide(**self.sample_guide_dict)
        
        # Verify the model
        self.assertEqual(guide.title, "Diabetes Management Guide for John Doe")
        self.assertEqual(guide.user_name, "John Doe")
        self.assertEqual(len(guide.sections), 2)
        self.assertEqual(guide.sections[0].title, "Understanding Your Coverage")
        self.assertEqual(len(guide.action_items), 2)
        self.assertEqual(guide.next_steps[0], "Call to schedule appointment")
    
    def test_prompt_model_creation(self):
        """Test creating a prompt model from dictionary data."""
        # Create a HealthcareGuidePrompt model from the sample dictionary
        prompt = HealthcareGuidePrompt(**self.sample_prompt_dict)
        
        # Verify the model
        self.assertEqual(prompt.guide_title, "Diabetes Management Guide for John Doe")
        self.assertEqual(prompt.guide_purpose, "To help navigate diabetes care")
        self.assertEqual(prompt.user_info["name"], "John Doe")
        self.assertEqual(prompt.user_info["age"], 65)
        self.assertEqual(prompt.policy_info["insurer"], "Medicare Advantage")
        self.assertEqual(prompt.special_instructions[0], "Include glucose monitoring tips")
    
    def test_error_handling(self):
        """Test that the agent properly handles errors."""
        # Create an error guide
        error_guide = {
            "title": "Healthcare Guide for John Doe",
            "user_name": "John Doe",
            "summary": "This guide could not be fully generated due to an error.",
            "sections": [
                {
                    "title": "Error Information",
                    "content": "We encountered an error while generating your guide: Test error. Please try again later.",
                    "order": 1
                }
            ],
            "action_items": ["Contact customer support for assistance"],
            "provider_details": {},
            "important_contacts": {"customer_support": "555-HELP-123"},
            "next_steps": ["Try again later"],
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": "Test error"
        }
        
        # Create a HealthcareGuide model from the error dictionary
        guide = HealthcareGuide(**error_guide)
        
        # Verify error handling
        self.assertEqual(guide.title, "Healthcare Guide for John Doe")
        self.assertEqual(guide.user_name, "John Doe")
        self.assertEqual(len(guide.sections), 1)
        self.assertEqual(guide.sections[0].title, "Error Information")
        self.assertIn("error", guide.sections[0].content)
        self.assertEqual(guide.action_items[0], "Contact customer support for assistance")
        
        # Test error handling for PDF prompt creation
        error_prompt = {
            "guide_title": "Healthcare Guide",
            "guide_purpose": "To assist with healthcare navigation",
            "user_info": {"name": "User"},
            "policy_info": {},
            "service_info": {},
            "provider_info": {},
            "special_instructions": ["Handle with care due to processing error"],
            "formatting_preferences": {"simple_layout": True},
            "error": "Test error"
        }
        
        # Create a HealthcareGuidePrompt model from the error dictionary
        prompt = HealthcareGuidePrompt(**error_prompt)
        
        # Verify error handling
        self.assertEqual(prompt.guide_title, "Healthcare Guide")
        self.assertEqual(prompt.guide_purpose, "To assist with healthcare navigation")
        self.assertEqual(prompt.special_instructions[0], "Handle with care due to processing error")

if __name__ == "__main__":
    unittest.main() 