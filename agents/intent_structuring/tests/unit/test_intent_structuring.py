"""
Test module for the Intent Structuring Agent.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.intent_structuring import IntentStructuringAgent, StructuredIntent, IntentParameter
from langchain_core.messages import AIMessage

class TestIntentStructuringAgent(unittest.TestCase):
    """Tests for the Intent Structuring Agent."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock LLM that returns predefined responses
        self.mock_llm = MagicMock()
        self.mock_llm.invoke.return_value = AIMessage(content="""
        ```json
        {
            "intent_type": "find_provider",
            "intent_category": "service",
            "parameters": [
                {
                    "name": "specialty",
                    "value": "cardiologist",
                    "required": true,
                    "confidence": 0.95,
                    "description": "Medical specialty needed"
                },
                {
                    "name": "location",
                    "value": "Boston",
                    "required": true,
                    "confidence": 0.95,
                    "description": "Geographic location"
                },
                {
                    "name": "network_status",
                    "value": "in-network",
                    "required": false,
                    "confidence": 0.8,
                    "description": "In-network or out-of-network"
                }
            ],
            "description": "User is looking for a cardiologist in Boston who accepts Medicare",
            "constraints": ["Medicare coverage"],
            "related_intents": ["check_coverage", "service_location"],
            "confidence": 0.9,
            "context_required": false,
            "followup_questions": ["Do you have a preferred hospital affiliation?"],
            "needs_clarification": false
        }
        ```
        """)
        
        # Initialize the agent with the mock LLM
        self.agent = IntentStructuringAgent(llm=self.mock_llm)
        
        # Test data
        self.test_query = "I need to find a cardiologist in Boston who accepts Medicare"
        self.test_context = {"user_profile": {"location": "Boston"}}
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.name, "intent_structuring")
        self.assertIsNotNone(self.agent.logger)
        self.assertIsNotNone(self.agent.intent_parser)
        self.assertIsNotNone(self.agent.common_intents)
        self.assertTrue("find_provider" in self.agent.common_intents)
    
    def test_structure_intent(self):
        """Test structuring an intent from a query."""
        result = self.agent.structure_intent(self.test_query)
        
        # Verify the intent was structured correctly
        self.assertEqual(result["intent_type"], "find_provider")
        self.assertEqual(result["intent_category"], "service")
        self.assertEqual(result["confidence"], 0.9)
        
        # Verify parameters were extracted
        self.assertEqual(len(result["parameters"]), 3)
        self.assertEqual(result["parameters"][0]["name"], "specialty")
        self.assertEqual(result["parameters"][0]["value"], "cardiologist")
        self.assertEqual(result["parameters"][1]["name"], "location")
        self.assertEqual(result["parameters"][1]["value"], "Boston")
        
        # Verify other fields
        self.assertEqual(len(result["constraints"]), 1)
        self.assertEqual(result["constraints"][0], "Medicare coverage")
        self.assertEqual(len(result["related_intents"]), 2)
        self.assertFalse(result["needs_clarification"])
        
        # Verify the LLM was called with the right input
        self.mock_llm.invoke.assert_called_once()
        call_args = self.mock_llm.invoke.call_args[0][0]
        self.assertIn(self.test_query, call_args.content)
    
    def test_structure_intent_with_context(self):
        """Test structuring an intent with conversation context."""
        result = self.agent.structure_intent(self.test_query, self.test_context)
        
        # Verify the intent was structured correctly
        self.assertEqual(result["intent_type"], "find_provider")
        
        # Verify the LLM was called with the context included
        self.mock_llm.invoke.assert_called_once()
        call_args = self.mock_llm.invoke.call_args[0][0]
        self.assertIn(json.dumps(self.test_context), call_args.content)
    
    def test_enrich_intent(self):
        """Test enriching a structured intent with additional information."""
        # Create a structured intent with a missing required parameter
        intent = StructuredIntent(
            intent_type="find_provider",
            intent_category="service",
            parameters=[
                IntentParameter(
                    name="specialty",
                    value="cardiologist",
                    required=True,
                    confidence=0.95
                )
                # Missing 'location' parameter, which is required
            ],
            description="Find a cardiologist",
            constraints=[],
            related_intents=[],
            confidence=0.9,
            context_required=False,
            followup_questions=[],
            needs_clarification=False
        )
        
        # Enrich the intent
        enriched = self.agent._enrich_intent(intent)
        
        # Verify the missing parameter was added
        parameters = [p.name for p in enriched.parameters]
        self.assertIn("location", parameters)
        
        # Verify needs_clarification was updated
        self.assertTrue(enriched.needs_clarification)
        
        # Verify followup_questions was updated
        self.assertTrue(any("location" in q for q in enriched.followup_questions))
    
    def test_unknown_intent_type(self):
        """Test enriching an intent with an unknown type."""
        # Create a structured intent with an unknown type
        intent = StructuredIntent(
            intent_type="unknown_type",
            intent_category="unknown",
            parameters=[],
            description="Unknown intent",
            constraints=[],
            related_intents=[],
            confidence=0.5,
            context_required=False,
            followup_questions=[],
            needs_clarification=False
        )
        
        # Enrich the intent
        enriched = self.agent._enrich_intent(intent)
        
        # Verify the intent wasn't modified
        self.assertEqual(len(enriched.parameters), 0)
        self.assertFalse(enriched.needs_clarification)
    
    def test_error_handling(self):
        """Test error handling in intent structuring."""
        # Make the LLM raise an exception
        self.mock_llm.invoke.side_effect = Exception("Test error")
        
        result = self.agent.structure_intent(self.test_query)
        
        # Verify a default intent was returned
        self.assertEqual(result["intent_type"], "unknown")
        self.assertEqual(result["confidence"], 0.0)
        self.assertTrue(result["needs_clarification"])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Test error")
    
    def test_get_missing_parameters(self):
        """Test getting missing required parameters from a structured intent."""
        # Create a structured intent with a missing required parameter
        intent = {
            "intent_type": "find_provider",
            "parameters": [
                {
                    "name": "specialty",
                    "value": "cardiologist",
                    "required": True
                },
                {
                    "name": "location",
                    "value": None,
                    "required": True,
                    "description": "Geographic location"
                },
                {
                    "name": "network_status",
                    "value": None,
                    "required": False
                }
            ]
        }
        
        missing = self.agent.get_missing_parameters(intent)
        
        # Verify the missing parameter was identified
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["name"], "location")
        self.assertEqual(missing[0]["description"], "Geographic location")
    
    def test_process_method(self):
        """Test the complete process method."""
        structured_intent, needs_clarification, followup_questions = self.agent.process(self.test_query)
        
        # Verify the result
        self.assertEqual(structured_intent["intent_type"], "find_provider")
        self.assertFalse(needs_clarification)
        self.assertEqual(len(followup_questions), 1)
        self.assertEqual(followup_questions[0], "Do you have a preferred hospital affiliation?")

if __name__ == "__main__":
    unittest.main() 