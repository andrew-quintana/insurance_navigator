"""
Test module for the Quality Assurance Agent.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.quality_assurance import QualityAssuranceAgent, QualityAssessment, ContentIssue
from langchain_core.messages import AIMessage

class TestQualityAssuranceAgent(unittest.TestCase):
    """Tests for the Quality Assurance Agent."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock LLM that returns predefined responses
        self.mock_llm = MagicMock()
        self.mock_llm.invoke.return_value = AIMessage(content="""
        ```json
        {
            "content_id": "guide_12345",
            "content_type": "guide",
            "overall_quality": 0.85,
            "passed_qa": true,
            "factual_assessment": {
                "is_accurate": true,
                "confidence": 0.9,
                "factual_issues": [
                    {
                        "issue_type": "factual",
                        "severity": 3,
                        "location": "costs section",
                        "description": "Premium amount is slightly outdated",
                        "recommendation": "Update premium to $174.70 for 2023",
                        "requires_human_review": false
                    }
                ],
                "citations": ["Medicare.gov/costs"],
                "uncertain_claims": []
            },
            "structural_assessment": {
                "is_well_structured": true,
                "confidence": 0.95,
                "structural_issues": [],
                "missing_sections": [],
                "invalid_formats": []
            },
            "readability_score": 0.88,
            "clarity_score": 0.9,
            "completeness_score": 0.85,
            "consistency_score": 0.92,
            "requires_escalation": false,
            "escalation_reason": null,
            "confidence_threshold_applied": 0.8,
            "qa_decision": "pass",
            "qa_timestamp": "2024-05-15 10:30:00"
        }
        ```
        """)
        
        # Initialize the agent with the mock LLM
        self.agent = QualityAssuranceAgent(llm=self.mock_llm)
        
        # Test data
        self.test_guide = {
            "title": "Medicare Part B Enrollment Guide",
            "introduction": "This guide helps you understand how to enroll in Medicare Part B.",
            "steps": [
                "Step 1: Check your eligibility",
                "Step 2: Complete Form CMS-40B",
                "Step 3: Submit your application",
                "Step 4: Wait for confirmation"
            ],
            "requirements": [
                "Social Security card",
                "Government-issued ID",
                "Proof of eligibility"
            ],
            "timeline": "Process typically takes 2-4 weeks",
            "contacts": "1-800-MEDICARE",
            "costs": "Standard premium is $170.10 (2022)"
        }
        
        self.test_context = {
            "content_id": "guide_12345",
            "author": "Medicare Navigator System",
            "created_at": "2024-05-15 10:00:00"
        }
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.name, "quality_assurance")
        self.assertIsNotNone(self.agent.logger)
        self.assertIsNotNone(self.agent.parser)
        self.assertTrue("guide" in self.agent.structure_templates)
        self.assertTrue("provider_list" in self.agent.structure_templates)
        self.assertTrue("strategy" in self.agent.structure_templates)
    
    def test_get_structure_template(self):
        """Test getting structure templates for different content types."""
        # Get template for a known content type
        guide_template = self.agent._get_structure_template("guide")
        self.assertTrue("Medicare guide" in guide_template)
        
        # Unknown content type should return default message
        unknown_template = self.agent._get_structure_template("unknown_type")
        self.assertTrue("No specific structure template" in unknown_template)
    
    def test_get_confidence_threshold(self):
        """Test getting confidence thresholds for different content types."""
        # Get threshold for a known content type
        guide_threshold = self.agent._get_confidence_threshold("guide")
        self.assertEqual(guide_threshold, 0.85)
        
        # Unknown content type should return general threshold
        unknown_threshold = self.agent._get_confidence_threshold("unknown_type")
        self.assertEqual(unknown_threshold, 0.75)
    
    def test_assess_quality(self):
        """Test quality assessment of content."""
        result = self.agent.assess_quality(self.test_guide, "guide", self.test_context)
        
        # Verify the quality assessment result
        self.assertEqual(result["content_id"], "guide_12345")
        self.assertEqual(result["content_type"], "guide")
        self.assertEqual(result["overall_quality"], 0.85)
        self.assertTrue(result["passed_qa"])
        self.assertTrue(result["factual_assessment"]["is_accurate"])
        self.assertEqual(len(result["factual_assessment"]["factual_issues"]), 1)
        self.assertTrue(result["structural_assessment"]["is_well_structured"])
        self.assertEqual(result["qa_decision"], "pass")
        
        # Verify the LLM was called with the right input
        self.mock_llm.invoke.assert_called_once()
        call_args = self.mock_llm.invoke.call_args[0][0]
        self.assertIn("guide", call_args.content)
        self.assertIn(json.dumps(self.test_guide, indent=2), call_args.content)
        self.assertIn(json.dumps(self.test_context, indent=2), call_args.content)
    
    def test_validate_structure_guide(self):
        """Test validating guide structure."""
        # Test with valid guide structure
        valid_guide = {
            "title": "Test Guide",
            "introduction": "Introduction text",
            "steps": ["Step 1", "Step 2"],
            "requirements": ["Req 1", "Req 2"],
            "timeline": "2-4 weeks",
            "contacts": "1-800-TEST"
        }
        
        is_valid, issues = self.agent.validate_structure(valid_guide, "guide")
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)
        
        # Test with missing required section
        invalid_guide = valid_guide.copy()
        del invalid_guide["requirements"]
        
        is_valid, issues = self.agent.validate_structure(invalid_guide, "guide")
        self.assertFalse(is_valid)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["issue_type"], "structure")
        self.assertTrue("requirements" in issues[0]["description"])
    
    def test_validate_structure_provider_list(self):
        """Test validating provider list structure."""
        # Test with valid provider list structure
        valid_provider_list = {
            "providers": [
                {
                    "name": "Dr. Smith",
                    "specialty": "Cardiology",
                    "location": "Boston",
                    "contact": "555-1234",
                    "network_status": "In-network"
                }
            ]
        }
        
        is_valid, issues = self.agent.validate_structure(valid_provider_list, "provider_list")
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)
        
        # Test with missing providers array
        invalid_provider_list = {}
        
        is_valid, issues = self.agent.validate_structure(invalid_provider_list, "provider_list")
        self.assertFalse(is_valid)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["issue_type"], "structure")
        self.assertTrue("providers" in issues[0]["description"])
        
        # Test with missing required field
        invalid_provider_list = {
            "providers": [
                {
                    "name": "Dr. Smith",
                    "specialty": "Cardiology",
                    "contact": "555-1234",
                    "network_status": "In-network"
                    # Missing location
                }
            ]
        }
        
        is_valid, issues = self.agent.validate_structure(invalid_provider_list, "provider_list")
        self.assertFalse(is_valid)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["issue_type"], "structure")
        self.assertTrue("location" in issues[0]["description"])
    
    def test_escalate_if_needed_no_issues(self):
        """Test escalation with no issues."""
        assessment = {
            "overall_quality": 0.9,
            "factual_assessment": {"factual_issues": []},
            "structural_assessment": {"structural_issues": []}
        }
        
        result = self.agent.escalate_if_needed(assessment)
        self.assertFalse(result["requires_escalation"])
        self.assertIsNone(result["escalation_reason"])
    
    def test_escalate_if_needed_with_critical_issues(self):
        """Test escalation with critical issues."""
        assessment = {
            "overall_quality": 0.8,
            "factual_assessment": {
                "factual_issues": [
                    {
                        "issue_type": "factual",
                        "severity": 8,
                        "description": "Serious factual error",
                        "requires_human_review": True
                    }
                ]
            },
            "structural_assessment": {"structural_issues": []}
        }
        
        result = self.agent.escalate_if_needed(assessment)
        self.assertTrue(result["requires_escalation"])
        self.assertTrue("Critical issues detected" in result["escalation_reason"])
    
    def test_escalate_if_needed_low_quality(self):
        """Test escalation with low overall quality."""
        assessment = {
            "overall_quality": 0.4,  # Below threshold
            "factual_assessment": {"factual_issues": []},
            "structural_assessment": {"structural_issues": []}
        }
        
        result = self.agent.escalate_if_needed(assessment)
        self.assertTrue(result["requires_escalation"])
        self.assertTrue("quality score" in result["escalation_reason"])
    
    def test_error_handling(self):
        """Test error handling in quality assessment."""
        # Make the LLM raise an exception
        self.mock_llm.invoke.side_effect = Exception("Test error")
        
        result = self.agent.assess_quality(self.test_guide, "guide")
        
        # Verify error handling
        self.assertFalse(result["passed_qa"])
        self.assertEqual(result["overall_quality"], 0.0)
        self.assertTrue(result["requires_escalation"])
        self.assertTrue("QA assessment failed with error" in result["escalation_reason"])
        self.assertEqual(result["qa_decision"], "needs_human_review")
        self.assertTrue("error" in result)
        self.assertEqual(result["error"], "Test error")
    
    def test_process_method(self):
        """Test the complete process method."""
        result = self.agent.process(self.test_guide, "guide", self.test_context)
        
        # Verify the process result
        self.assertEqual(result["content_id"], "guide_12345")
        self.assertTrue(result["passed_qa"])
        self.assertEqual(result["qa_decision"], "pass")

if __name__ == "__main__":
    unittest.main() 