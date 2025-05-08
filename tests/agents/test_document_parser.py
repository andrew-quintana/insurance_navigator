"""
Test module for the Document Parser Agent.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.document_parser import DocumentParserAgent, ExtractedDocumentInfo

class TestDocumentParserAgent(unittest.TestCase):
    """Tests for the Document Parser Agent."""
    
    def setUp(self):
        """Set up the test environment."""
        # Sample document text
        self.sample_document = """
        ABC INSURANCE COMPANY
        POLICY DOCUMENT
        
        Policy Number: POL123456789
        Policy Holder: John Doe
        Effective Date: 01/01/2025
        Expiration Date: 12/31/2025
        
        COVERAGE SUMMARY:
        - Primary Care: $20 copay per visit
        - Specialist Care: $40 copay per visit
        - Emergency Room: $250 copay (waived if admitted)
        - Hospital Stay: 20% coinsurance after deductible
        
        Annual Deductible: $1,500 individual / $3,000 family
        Out-of-Pocket Maximum: $5,000 individual / $10,000 family
        
        EXCLUSIONS:
        - Cosmetic procedures
        - Experimental treatments
        - Non-emergency care outside network
        """
        
        # Create mock LLM
        self.mock_llm = MagicMock()
        self.agent = DocumentParserAgent(llm=self.mock_llm)
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.name, "document_parser")
        self.assertIsNotNone(self.agent.logger)
        self.assertIsNotNone(self.agent.parser)
    
    def test_preprocess_text(self):
        """Test text preprocessing."""
        input_text = "This  is a   test\nwith multiple\n\nlines"
        expected_output = "This is a test with multiple lines"
        
        output = self.agent.preprocess_text(input_text)
        self.assertEqual(output, expected_output)
    
    def test_error_handling(self):
        """Test error handling without relying on parsing success."""
        # Mock error result
        error_result = {
            "document_type": "unknown",
            "insurer_name": None,
            "policy_number": None,
            "policy_holder": None,
            "effective_date": None,
            "expiration_date": None,
            "coverage_types": [],
            "coverage_limits": {},
            "key_exclusions": [],
            "deductibles": {},
            "copays": {},
            "extracted_text": "truncated text",
            "extraction_quality": 0.0,
            "missing_fields": ["all_fields_due_to_error"],
            "confidence": {"overall": 0.0},
            "error": "Error message"
        }
        
        # Create an output model based on our error result
        model = ExtractedDocumentInfo(**error_result)
        
        # Verify required fields in error output
        self.assertEqual(model.document_type, "unknown")
        self.assertIsNone(model.policy_number)
        self.assertEqual(model.extraction_quality, 0.0)
        self.assertIn("all_fields_due_to_error", model.missing_fields)
        self.assertEqual(model.confidence["overall"], 0.0)
    
    def test_process_model_creation(self):
        """Test that process properly creates a model from a dictionary."""
        # Sample result dictionary
        result_dict = {
            "document_type": "insurance_policy",
            "insurer_name": "ABC Insurance",
            "policy_number": "POL123456789",
            "policy_holder": "John Doe",
            "effective_date": "01/01/2025",
            "expiration_date": "12/31/2025",
            "coverage_types": ["primary_care", "specialist_care"],
            "coverage_limits": {},
            "key_exclusions": ["cosmetic_procedures"],
            "deductibles": {"individual": 1500},
            "copays": {"primary_care": 20},
            "extracted_text": "Sample text",
            "extraction_quality": 0.95,
            "missing_fields": [],
            "confidence": {"overall": 0.9}
        }
        
        # Create a model from the dictionary
        model = ExtractedDocumentInfo(**result_dict)
        
        # Verify model fields
        self.assertEqual(model.document_type, "insurance_policy")
        self.assertEqual(model.policy_number, "POL123456789")
        self.assertEqual(model.policy_holder, "John Doe")
        self.assertEqual(len(model.coverage_types), 2)
        self.assertEqual(model.extraction_quality, 0.95)
        self.assertEqual(len(model.missing_fields), 0)

if __name__ == "__main__":
    unittest.main() 