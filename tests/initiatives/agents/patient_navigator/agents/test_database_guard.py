"""
Tests for the Database Guard Agent.
"""

import unittest
from unittest.mock import MagicMock, patch
from agents.database_guard.logic import DatabaseGuardAgent
from tests.agents.test_base import BaseAgentTest

class TestDatabaseGuardAgent(BaseAgentTest):
    """Test cases for the Database Guard Agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.agent = self.assert_agent_initialization(DatabaseGuardAgent)
        
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertIsInstance(self.agent, DatabaseGuardAgent)
        
    def test_validate_query(self):
        """Test query validation."""
        test_query = "SELECT * FROM patients WHERE id = 1"
        expected_result = {
            "is_valid": True,
            "risk_level": "low",
            "issues": [],
            "sanitized_query": "SELECT * FROM patients WHERE id = ?"
        }
        
        # Mock the LLM response
        self.mock_llm.generate.return_value = expected_result
        
        result = self.agent.validate_query(test_query)
        
        self.assertEqual(result, expected_result)
        self.mock_llm.generate.assert_called_once()
        
    def test_check_data_access(self):
        """Test data access permission checking."""
        test_request = {
            "user_id": "test_user",
            "table": "patients",
            "operation": "SELECT",
            "conditions": {"id": 1}
        }
        expected_result = {
            "has_access": True,
            "reason": "User has required permissions"
        }
        
        # Mock the LLM response
        self.mock_llm.generate.return_value = expected_result
        
        result = self.agent.check_data_access(test_request)
        
        self.assertEqual(result, expected_result)
        self.mock_llm.generate.assert_called_once()
        
    def test_audit_query(self):
        """Test query auditing."""
        test_query = "UPDATE patients SET status = 'active' WHERE id = 1"
        expected_result = {
            "is_compliant": True,
            "audit_log": {
                "timestamp": "2025-05-10T13:30:00Z",
                "operation": "UPDATE",
                "table": "patients",
                "affected_rows": 1
            }
        }
        
        # Mock the LLM response
        self.mock_llm.generate.return_value = expected_result
        
        result = self.agent.audit_query(test_query)
        
        self.assertEqual(result, expected_result)
        self.mock_llm.generate.assert_called_once()

if __name__ == '__main__':
    unittest.main() 