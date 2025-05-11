"""
Test module for the Service Provider Agent.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.service_provider import ServiceProviderAgent, Provider, ProviderSearchResult
from langchain_core.messages import AIMessage

class TestServiceProviderAgent(unittest.TestCase):
    """Tests for the Service Provider Agent."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock LLM that returns a predefined response
        self.mock_llm = MagicMock()
        self.mock_llm.invoke.return_value = AIMessage(content="""
        ```json
        {
            "providers": [
                {
                    "name": "Boston Medical Specialists",
                    "address": "123 Medical Parkway, Boston, MA 02108",
                    "city": "Boston",
                    "state": "MA",
                    "zip_code": "02108",
                    "phone": "617-555-1000",
                    "specialties": ["neurology"],
                    "in_network": true,
                    "distance": 3.2,
                    "accepts_new_patients": true,
                    "languages": ["English", "Spanish"]
                }
            ],
            "service_type": "neurology",
            "location": "Boston, MA",
            "total_results": 1,
            "search_radius": 25.0,
            "insurance_type": "Medicare",
            "confidence": 0.85
        }
        ```
        """)
        
        # Initialize the agent with the mock LLM
        self.agent = ServiceProviderAgent(llm=self.mock_llm)
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.name, "service_provider")
        self.assertIsNotNone(self.agent.logger)
        self.assertIsNotNone(self.agent.provider_db)
        self.assertIsNotNone(self.agent.location_coordinates)
    
    def test_calculate_distance(self):
        """Test the distance calculation."""
        # Boston to Cambridge, approximately 3.0 miles
        distance = self.agent._calculate_distance(42.360, -71.059, 42.373, -71.110)
        self.assertGreater(distance, 2.0)
        self.assertLess(distance, 4.0)
        
        # Same point should be 0 distance
        distance = self.agent._calculate_distance(42.360, -71.059, 42.360, -71.059)
        self.assertEqual(distance, 0.0)
    
    def test_get_location_coordinates(self):
        """Test retrieving location coordinates."""
        # Test with a known location
        coords = self.agent._get_location_coordinates("Boston, MA")
        self.assertEqual(coords["lat"], 42.360)
        self.assertEqual(coords["lng"], -71.059)
        
        # Test with an unknown location
        coords = self.agent._get_location_coordinates("Unknown Location")
        self.assertEqual(coords["lat"], 42.360)  # Should default to Boston
        self.assertEqual(coords["lng"], -71.059)
    
    def test_find_providers_database(self):
        """Test finding providers from the internal database."""
        # Test with a service type that exists in the database
        result = self.agent.find_providers("endocrinology", "Boston, MA")
        
        self.assertGreater(result["total_results"], 0)
        self.assertEqual(result["service_type"], "endocrinology")
        self.assertEqual(result["location"], "Boston, MA")
        self.assertEqual(result["insurance_type"], "Medicare")
        self.assertGreater(result["confidence"], 0.9)  # Database results should have high confidence
    
    def test_find_providers_llm(self):
        """Test finding providers using the LLM when not enough in database."""
        # Test with a service type that doesn't exist in the database
        result = self.agent.find_providers("neurology", "Boston, MA")
        
        self.assertEqual(result["total_results"], 1)
        self.assertEqual(result["service_type"], "neurology")
        self.assertEqual(result["location"], "Boston, MA")
        self.assertEqual(result["insurance_type"], "Medicare")
        self.assertEqual(result["confidence"], 0.85)
        
        # Verify the provider details
        provider = result["providers"][0]
        self.assertEqual(provider["name"], "Boston Medical Specialists")
        self.assertEqual(provider["city"], "Boston")
        self.assertTrue(provider["in_network"])
    
    def test_error_handling(self):
        """Test error handling in provider search."""
        # Make the LLM raise an exception
        self.mock_llm.invoke.side_effect = Exception("Test error")
        
        # Try to find providers for a service type that doesn't exist in the database
        result = self.agent.find_providers("nonexistent_specialty", "Boston, MA")
        
        self.assertEqual(result["total_results"], 0)
        self.assertEqual(len(result["providers"]), 0)
        self.assertEqual(result["confidence"], 0.0)
        self.assertIsNotNone(result["error"])
        self.assertIn("Test error", result["error"])
    
    def test_process_method(self):
        """Test the process method."""
        providers, result = self.agent.process("endocrinology", "Boston, MA")
        
        self.assertGreater(len(providers), 0)
        self.assertEqual(result["service_type"], "endocrinology")
        self.assertEqual(result["location"], "Boston, MA")
        
        # Verify we get Provider objects back
        for provider in providers:
            self.assertIsInstance(provider, dict)
            self.assertIn("name", provider)
            self.assertIn("specialties", provider)
            self.assertIn("in_network", provider)

if __name__ == "__main__":
    unittest.main() 