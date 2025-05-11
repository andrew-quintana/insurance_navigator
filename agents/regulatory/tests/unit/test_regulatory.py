"""
Test module for the Regulatory Agent.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
import hashlib
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.regulatory import RegulatoryAgent, RegulatoryAssessment, SensitiveEntity, RedactionResult
from langchain_core.messages import AIMessage

class TestRegulatoryAgent(unittest.TestCase):
    """Tests for the Regulatory Agent."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock LLM for the assessment chain
        self.mock_assessment_llm = MagicMock()
        self.mock_assessment_llm.invoke.return_value = AIMessage(content="""
        ```json
        {
            "content_id": "guide_12345",
            "content_type": "guide",
            "hipaa_compliant": false,
            "cms_compliant": true,
            "contains_phi": true,
            "contains_pii": true,
            "sensitive_entities": [
                {
                    "entity_type": "PHI",
                    "entity_subtype": "medicare_id",
                    "content": "123-45-6789A",
                    "location": "paragraph 2",
                    "confidence": 0.95,
                    "redaction_recommended": true,
                    "context": "Medicare ID: 123-45-6789A"
                },
                {
                    "entity_type": "PII",
                    "entity_subtype": "name",
                    "content": "John Smith",
                    "location": "header",
                    "confidence": 0.98,
                    "redaction_recommended": true,
                    "context": "Guide for John Smith"
                },
                {
                    "entity_type": "PII",
                    "entity_subtype": "email",
                    "content": "john.smith@example.com",
                    "location": "contact section",
                    "confidence": 0.99,
                    "redaction_recommended": true,
                    "context": "Email: john.smith@example.com"
                }
            ],
            "compliance_issues": [
                {
                    "issue_type": "HIPAA",
                    "severity": 8,
                    "description": "Unredacted PHI present in document",
                    "recommendation": "Redact all PHI including Medicare ID and personal identifiers",
                    "reference": "45 CFR § 164.514",
                    "location": "multiple locations",
                    "requires_immediate_action": true
                }
            ],
            "advisories_needed": ["medical", "general"],
            "disclaimers_needed": ["general", "medical"],
            "confidence": 0.95,
            "overall_risk_level": "high",
            "assessment_timestamp": "2024-05-15 10:30:00",
            "references": ["45 CFR § 164.514", "42 CFR § 482.13"],
            "recommendations": ["Redact all PHI", "Add medical and general disclaimers"]
        }
        ```
        """)
        
        # Create a mock LLM for the redaction chain
        self.mock_redaction_llm = MagicMock()
        self.mock_redaction_llm.invoke.return_value = AIMessage(content="""
        ```json
        {
            "original_content_hash": "abc123",
            "redacted_content": "Medicare Benefit Guide for [NAME]\\n\\nDear [NAME],\\n\\nBased on your enrollment in Medicare Part B (Medicare ID: [ID NUMBER]) and your diagnosis of Type 2 Diabetes on [DATE], you are eligible for the following benefits:\\n\\n1. Diabetes self-management training\\n2. Blood glucose monitors and supplies\\n3. Therapeutic shoes and inserts (with a doctor's certification)\\n\\nTo access these benefits, please contact Dr. [NAME] at [LOCATION] ([CONTACT INFO]) to schedule an appointment.\\n\\nFor questions about your coverage, please call 1-800-MEDICARE or email us at [CONTACT INFO].\\n\\nSincerely,\\nMedicare Benefits Coordinator",
            "entities_redacted": [
                {
                    "entity_type": "PII",
                    "entity_subtype": "name",
                    "content": "John Smith",
                    "location": "header",
                    "confidence": 0.98,
                    "redaction_recommended": true,
                    "context": "Guide for John Smith"
                },
                {
                    "entity_type": "PHI",
                    "entity_subtype": "medicare_id",
                    "content": "123-45-6789A",
                    "location": "paragraph 2",
                    "confidence": 0.95,
                    "redaction_recommended": true,
                    "context": "Medicare ID: 123-45-6789A"
                },
                {
                    "entity_type": "PII",
                    "entity_subtype": "email",
                    "content": "john.smith@example.com",
                    "location": "contact section",
                    "confidence": 0.99,
                    "redaction_recommended": true,
                    "context": "Email: john.smith@example.com"
                }
            ],
            "redaction_count": 5,
            "confidence": 0.95
        }
        ```
        """)
        
        # Initialize the agent with the mock LLMs
        self.agent = RegulatoryAgent(llm=self.mock_assessment_llm)
        # Replace the redaction chain's LLM with our mock
        self.agent.redaction_chain.middle = self.mock_redaction_llm
        
        # Test data
        self.test_content = """
        Medicare Benefit Guide for John Smith
        
        Dear Mr. Smith,
        
        Based on your enrollment in Medicare Part B (Medicare ID: 123-45-6789A) and your diagnosis 
        of Type 2 Diabetes on 01/15/2022, you are eligible for the following benefits:
        
        1. Diabetes self-management training
        2. Blood glucose monitors and supplies
        3. Therapeutic shoes and inserts (with a doctor's certification)
        
        To access these benefits, please contact Dr. Jane Johnson at Boston Medical Center 
        (555-123-4567) to schedule an appointment.
        
        For questions about your coverage, please call 1-800-MEDICARE or email us at 
        john.smith@example.com.
        
        Sincerely,
        Medicare Benefits Coordinator
        """
        
        self.test_context = {
            "content_id": "guide_12345",
            "user_id": "user_987",
            "created_at": "2024-05-15 10:00:00"
        }
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.name, "regulatory")
        self.assertIsNotNone(self.agent.logger)
        self.assertIsNotNone(self.agent.assessment_parser)
        self.assertIsNotNone(self.agent.redaction_parser)
        self.assertTrue(hasattr(self.agent, "phi_patterns"))
        self.assertTrue(hasattr(self.agent, "standard_disclaimers"))
    
    def test_quick_scan_for_phi(self):
        """Test quick scan for PHI/PII."""
        results = self.agent._quick_scan_for_phi(self.test_content)
        
        # Verify results
        self.assertTrue(len(results) > 0)
        
        # Check if we found the Medicare ID
        medicare_id_found = False
        for entity in results:
            if entity["entity_subtype"] == "medicare_id" and "123-45-6789A" in entity["content"]:
                medicare_id_found = True
                break
        self.assertTrue(medicare_id_found)
        
        # Check if we found the email
        email_found = False
        for entity in results:
            if entity["entity_subtype"] == "email" and "john.smith@example.com" in entity["content"]:
                email_found = True
                break
        self.assertTrue(email_found)
    
    def test_assess_regulatory_compliance(self):
        """Test regulatory compliance assessment."""
        result = self.agent.assess_regulatory_compliance(self.test_content, "guide", self.test_context)
        
        # Verify the assessment result
        self.assertEqual(result["content_id"], "guide_12345")
        self.assertEqual(result["content_type"], "guide")
        self.assertFalse(result["hipaa_compliant"])
        self.assertTrue(result["cms_compliant"])
        self.assertTrue(result["contains_phi"])
        self.assertTrue(result["contains_pii"])
        self.assertEqual(len(result["sensitive_entities"]), 3)
        self.assertEqual(len(result["compliance_issues"]), 1)
        self.assertEqual(len(result["advisories_needed"]), 2)
        self.assertEqual(result["overall_risk_level"], "high")
        
        # Verify the LLM was called with the right input
        self.mock_assessment_llm.invoke.assert_called_once()
        call_args = self.mock_assessment_llm.invoke.call_args[0][0]
        self.assertIn(self.test_content, call_args.content)
        self.assertIn(json.dumps(self.test_context, indent=2), call_args.content)
    
    def test_redact_sensitive_information(self):
        """Test redaction of sensitive information."""
        sensitive_entities = [
            {
                "entity_type": "PII",
                "entity_subtype": "name",
                "content": "John Smith",
                "location": "header",
                "confidence": 0.98,
                "redaction_recommended": True
            },
            {
                "entity_type": "PHI",
                "entity_subtype": "medicare_id",
                "content": "123-45-6789A",
                "location": "paragraph 2",
                "confidence": 0.95,
                "redaction_recommended": True
            }
        ]
        
        result = self.agent.redact_sensitive_information(self.test_content, sensitive_entities)
        
        # Verify the redaction result
        self.assertTrue("[NAME]" in result["redacted_content"])
        self.assertTrue("[ID NUMBER]" in result["redacted_content"])
        self.assertEqual(result["redaction_count"], 5)
        self.assertEqual(result["confidence"], 0.95)
        
        # Verify the LLM was called with the right input
        self.mock_redaction_llm.invoke.assert_called_once()
        call_args = self.mock_redaction_llm.invoke.call_args[0][0]
        self.assertIn(self.test_content, call_args.content)
        self.assertIn(json.dumps(sensitive_entities, indent=2), call_args.content)
    
    def test_get_standard_disclaimer(self):
        """Test getting standard disclaimers."""
        # Get a known disclaimer
        medical_disclaimer = self.agent.get_standard_disclaimer("medical")
        self.assertTrue("medical advice" in medical_disclaimer)
        
        # Get a non-existent disclaimer (should return default)
        unknown_disclaimer = self.agent.get_standard_disclaimer("nonexistent")
        self.assertTrue("guidance only" in unknown_disclaimer)
    
    def test_add_disclaimers_to_string(self):
        """Test adding disclaimers to string content."""
        disclaimers = ["medical", "general"]
        result = self.agent.add_disclaimers("Test content", disclaimers)
        
        # Verify disclaimers were added
        self.assertTrue("DISCLAIMERS:" in result)
        self.assertTrue("medical advice" in result)
        self.assertTrue("educational purposes only" in result)
    
    def test_add_disclaimers_to_dict(self):
        """Test adding disclaimers to dictionary content."""
        content = {"title": "Test Guide", "body": "Test content"}
        disclaimers = ["medical", "general"]
        
        result = self.agent.add_disclaimers(content, disclaimers)
        
        # Verify disclaimers were added
        self.assertTrue("disclaimers" in result)
        self.assertEqual(len(result["disclaimers"]), 2)
    
    def test_process_method(self):
        """Test the complete process method."""
        result = self.agent.process(self.test_content, "guide", self.test_context)
        
        # Verify process result
        self.assertIn("assessment", result)
        self.assertIn("content", result)
        self.assertIn("redacted_content", result)
        self.assertIn("content_with_disclaimers", result)
        
        # Check assessment results
        self.assertEqual(result["assessment"]["content_id"], "guide_12345")
        self.assertTrue(result["assessment"]["contains_phi"])
        
        # Check redaction
        self.assertTrue("[NAME]" in result["redacted_content"])
        
        # Check disclaimers
        self.assertTrue("DISCLAIMERS:" in result["content_with_disclaimers"])
    
    def test_error_handling_assessment(self):
        """Test error handling in regulatory assessment."""
        # Make the assessment LLM raise an exception
        self.mock_assessment_llm.invoke.side_effect = Exception("Test error")
        
        result = self.agent.assess_regulatory_compliance(self.test_content, "guide")
        
        # Verify conservative error handling
        self.assertFalse(result["hipaa_compliant"])
        self.assertFalse(result["cms_compliant"])
        self.assertTrue(result["contains_phi"])
        self.assertTrue(result["contains_pii"])
        self.assertEqual(result["overall_risk_level"], "critical")
        self.assertEqual(len(result["compliance_issues"]), 1)
        self.assertTrue("failed with error" in result["compliance_issues"][0]["description"])
        self.assertTrue("error" in result)
        self.assertEqual(result["error"], "Test error")
    
    def test_error_handling_redaction(self):
        """Test error handling in redaction."""
        # Make the redaction LLM raise an exception
        self.mock_redaction_llm.invoke.side_effect = Exception("Test error")
        
        sensitive_entities = [
            {
                "entity_type": "PII",
                "entity_subtype": "name",
                "content": "John Smith",
                "location": "header",
                "confidence": 0.98,
                "redaction_recommended": True
            }
        ]
        
        result = self.agent.redact_sensitive_information(self.test_content, sensitive_entities)
        
        # Verify conservative error handling
        self.assertEqual(result["redacted_content"], "[CONTENT REDACTED DUE TO PROCESSING ERROR]")
        self.assertEqual(result["redaction_count"], 1)
        self.assertEqual(result["confidence"], 0.0)
        self.assertTrue("error" in result)
        self.assertEqual(result["error"], "Test error")

if __name__ == "__main__":
    unittest.main() 