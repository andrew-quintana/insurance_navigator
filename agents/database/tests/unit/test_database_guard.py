"""
Test module for the Database Guard Agent.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.database_guard import DatabaseGuardAgent, SecurityValidation, DatabaseOperation
from langchain_core.messages import AIMessage

class TestDatabaseGuardAgent(unittest.TestCase):
    """Tests for the Database Guard Agent."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock LLM that returns predefined responses
        self.mock_llm = MagicMock()
        self.mock_llm.invoke.return_value = AIMessage(content="""
        ```json
        {
            "is_valid": true,
            "contains_pii": true,
            "contains_phi": false,
            "redacted_fields": ["email", "phone"],
            "original_hash": "abc123",
            "redacted_hash": "def456",
            "confidence": 0.85,
            "reasoning": "The payload contains PII (email and phone) that should be redacted. No PHI detected."
        }
        ```
        """)
        
        # Initialize the agent with the mock LLM
        self.agent = DatabaseGuardAgent(llm=self.mock_llm)
        
        # Test data
        self.test_data = {
            "user_id": "12345",
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "phone": "555-123-4567",
            "address": {
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip": "02108"
            }
        }
        
        self.test_schema = {
            "required_fields": ["user_id", "name"],
            "field_types": {
                "user_id": "str",
                "name": "str",
                "email": "str",
                "phone": "str",
                "address": "dict"
            }
        }
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.name, "database_guard")
        self.assertIsNotNone(self.agent.logger)
        self.assertIsNotNone(self.agent.parser)
        self.assertTrue(hasattr(self.agent, "sensitive_patterns"))
        self.assertEqual(self.agent.max_retries, 3)
    
    def test_compute_hash(self):
        """Test hash computation for data."""
        test_data = {"name": "Test", "value": 123}
        hash1 = self.agent._compute_hash(test_data)
        
        # Same data should produce the same hash
        hash2 = self.agent._compute_hash(test_data)
        self.assertEqual(hash1, hash2)
        
        # Different data should produce different hashes
        test_data2 = {"name": "Test", "value": 456}
        hash3 = self.agent._compute_hash(test_data2)
        self.assertNotEqual(hash1, hash3)
    
    def test_validate_structure_success(self):
        """Test structure validation with valid data."""
        is_valid, message = self.agent._validate_structure(self.test_data, self.test_schema)
        self.assertTrue(is_valid)
        self.assertEqual(message, "Structure validation passed")
    
    def test_validate_structure_missing_field(self):
        """Test structure validation with missing required field."""
        data = self.test_data.copy()
        del data["name"]  # Remove a required field
        
        is_valid, message = self.agent._validate_structure(data, self.test_schema)
        self.assertFalse(is_valid)
        self.assertTrue("Missing required field" in message)
    
    def test_validate_structure_wrong_type(self):
        """Test structure validation with wrong field type."""
        data = self.test_data.copy()
        data["user_id"] = 12345  # Should be string, not int
        
        is_valid, message = self.agent._validate_structure(data, self.test_schema)
        self.assertFalse(is_valid)
        self.assertTrue("incorrect type" in message)
    
    def test_validate_security(self):
        """Test security validation of data."""
        result = self.agent.validate_security(self.test_data)
        
        # Verify the security validation result
        self.assertTrue(result["is_valid"])
        self.assertTrue(result["contains_pii"])
        self.assertFalse(result["contains_phi"])
        self.assertEqual(len(result["redacted_fields"]), 2)
        self.assertEqual(result["confidence"], 0.85)
        
        # Verify the LLM was called with the right input
        self.mock_llm.invoke.assert_called_once()
        call_args = self.mock_llm.invoke.call_args[0][0]
        self.assertIn(json.dumps(self.test_data, indent=2), call_args.content)
    
    def test_store_data_success(self):
        """Test storing data successfully."""
        # Mock the simulate_db_write method to return a fixed ID
        with patch.object(self.agent, '_simulate_db_write', return_value="test_collection_12345"):
            result = self.agent.store_data(self.test_data, "test_collection", self.test_schema)
            
            # Verify the store result
            self.assertTrue(result["success"])
            self.assertEqual(result["operation_type"], "insert")
            self.assertEqual(result["record_id"], "test_collection_12345")
            self.assertEqual(result["retry_count"], 0)
    
    def test_store_data_invalid_structure(self):
        """Test storing data with invalid structure."""
        data = self.test_data.copy()
        del data["name"]  # Remove a required field
        
        result = self.agent.store_data(data, "test_collection", self.test_schema)
        
        # Verify the store failed due to structure validation
        self.assertFalse(result["success"])
        self.assertIn("Missing required field", result["error_message"])
    
    def test_store_data_security_failure(self):
        """Test storing data that fails security validation."""
        # Change the mock LLM to return a security failure
        self.mock_llm.invoke.return_value = AIMessage(content="""
        ```json
        {
            "is_valid": false,
            "contains_pii": true,
            "contains_phi": true,
            "redacted_fields": [],
            "original_hash": "abc123",
            "redacted_hash": "",
            "confidence": 0.9,
            "reasoning": "The payload contains unredacted PHI which violates HIPAA regulations."
        }
        ```
        """)
        
        result = self.agent.store_data(self.test_data, "test_collection", self.test_schema)
        
        # Verify the store failed due to security validation
        self.assertFalse(result["success"])
        self.assertIn("security validation failed", result["error_message"].lower())
    
    def test_redaction(self):
        """Test redaction of sensitive fields."""
        fields_to_redact = ["email", "phone", "address.street"]
        redacted_data = self.agent._simulate_redaction(self.test_data, fields_to_redact)
        
        # Check top-level fields were redacted
        self.assertEqual(redacted_data["email"], "[REDACTED]")
        self.assertEqual(redacted_data["phone"], "[REDACTED]")
        
        # Check nested field was redacted
        self.assertEqual(redacted_data["address"]["street"], "[REDACTED]")
        
        # Check other fields were preserved
        self.assertEqual(redacted_data["name"], self.test_data["name"])
        self.assertEqual(redacted_data["address"]["city"], self.test_data["address"]["city"])
    
    def test_process_method(self):
        """Test the complete process method."""
        # Mock the simulate_db_write method to return a fixed ID
        with patch.object(self.agent, '_simulate_db_write', return_value="test_collection_12345"):
            result = self.agent.process(self.test_data, "test_collection", self.test_schema)
            
            # Verify the process result
            self.assertTrue(result["success"])
            self.assertEqual(result["operation_type"], "insert")
            self.assertEqual(result["record_id"], "test_collection_12345")
    
    def test_error_handling(self):
        """Test error handling in security validation."""
        # Make the LLM raise an exception
        self.mock_llm.invoke.side_effect = Exception("Test error")
        
        result = self.agent.validate_security(self.test_data)
        
        # Verify error handling
        self.assertFalse(result["is_valid"])
        self.assertTrue(result["contains_pii"])  # Conservative assumption
        self.assertTrue(result["contains_phi"])  # Conservative assumption
        self.assertEqual(result["confidence"], 0.0)
        self.assertIn("Error during validation", result["reasoning"])

if __name__ == "__main__":
    unittest.main() 