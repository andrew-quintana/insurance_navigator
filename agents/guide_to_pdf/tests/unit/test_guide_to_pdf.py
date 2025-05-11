"""
Test module for the Guide to PDF Agent.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
import tempfile
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.guide_to_pdf import GuideToPDFAgent, GuideContent, PDFStyle, PDFGenerationResult
from langchain_core.messages import AIMessage

class TestGuideToPDFAgent(unittest.TestCase):
    """Tests for the Guide to PDF Agent."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock LLM that returns a predefined response
        self.mock_llm = MagicMock()
        self.mock_llm.invoke.return_value = AIMessage(content="""
        ```json
        {
            "success": true,
            "file_path": "output/guides/test_guide.pdf",
            "file_size": 1024,
            "generation_time": 0.5,
            "quality_score": 0.9,
            "error": null,
            "performance_metrics": {
                "rendering_time": 0.2,
                "conversion_time": 0.3
            },
            "improvement_suggestions": [
                "Add more visual elements",
                "Include a table of contents"
            ]
        }
        ```
        """)
        
        # Initialize the agent with the mock LLM
        self.agent = GuideToPDFAgent(llm=self.mock_llm)
        
        # Sample guide content for testing
        self.guide_content = {
            "title": "Test Guide",
            "user_name": "Test User",
            "summary": "This is a test guide summary.",
            "sections": [
                {
                    "title": "Section 1",
                    "content": "<p>This is section 1 content.</p>",
                    "order": 1
                },
                {
                    "title": "Section 2",
                    "content": "<p>This is section 2 content.</p>",
                    "order": 2
                }
            ],
            "action_items": ["Action 1", "Action 2"],
            "provider_details": {
                "providers": [
                    {
                        "name": "Provider 1",
                        "address": "123 Test St",
                        "phone": "555-1234",
                        "specialties": ["specialty1", "specialty2"]
                    }
                ]
            },
            "contact_info": {
                "Support": "555-HELP",
                "Emergency": "911"
            },
            "date_generated": "2025-05-10"
        }
        
        # Create a temporary output directory for tests
        self.test_output_dir = os.path.join(tempfile.gettempdir(), "test_guides")
        os.makedirs(self.test_output_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up any test files
        for file in os.listdir(self.test_output_dir):
            file_path = os.path.join(self.test_output_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
    
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.name, "guide_to_pdf")
        self.assertIsNotNone(self.agent.logger)
        self.assertIsNotNone(self.agent.result_parser)
        self.assertIsNotNone(self.agent.html_template)
        self.assertIsNotNone(self.agent.default_style)
    
    def test_render_html(self):
        """Test rendering HTML from guide content."""
        content_model = GuideContent(**self.guide_content)
        style_model = self.agent.default_style
        
        html = self.agent._render_html(content_model, style_model)
        
        # Verify HTML content
        self.assertIn("<title>Test Guide</title>", html)
        self.assertIn("Test User", html)
        self.assertIn("This is a test guide summary.", html)
        self.assertIn("Section 1", html)
        self.assertIn("Section 2", html)
        self.assertIn("Action 1", html)
        self.assertIn("Provider 1", html)
        self.assertIn("555-HELP", html)
    
    def test_convert_html_to_pdf(self):
        """Test converting HTML to PDF (simulation)."""
        # Simple HTML for testing
        html = "<html><body><h1>Test</h1></body></html>"
        output_path = os.path.join(self.test_output_dir, "test_guide.pdf")
        
        success, file_path, file_size = self.agent._convert_html_to_pdf(html, output_path)
        
        self.assertTrue(success)
        self.assertEqual(file_path, output_path)
        self.assertTrue(os.path.exists(file_path))
        self.assertGreater(file_size, 0)
        
        # Check the HTML file was also created
        html_path = output_path.replace(".pdf", ".html")
        self.assertTrue(os.path.exists(html_path))
    
    def test_evaluate_pdf_quality(self):
        """Test evaluating PDF quality."""
        # Sample generation results
        generation_results = {
            "success": True,
            "file_path": "test_path.pdf",
            "file_size": 1024,
            "generation_time": 0.5,
            "quality_score": 0.0
        }
        
        result = self.agent._evaluate_pdf_quality(self.guide_content, generation_results)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["quality_score"], 0.9)
        self.assertEqual(len(result["improvement_suggestions"]), 2)
        self.assertEqual(result["file_path"], "output/guides/test_guide.pdf")
    
    def test_evaluate_pdf_quality_error(self):
        """Test error handling in PDF quality evaluation."""
        # Make the LLM raise an exception
        self.mock_llm.invoke.side_effect = Exception("Test error")
        
        generation_results = {
            "success": True,
            "file_path": "test_path.pdf",
            "file_size": 1024,
            "generation_time": 0.5,
            "quality_score": 0.0
        }
        
        result = self.agent._evaluate_pdf_quality(self.guide_content, generation_results)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["quality_score"], 0.5)  # Default quality score
        self.assertIn("error", result)
        self.assertTrue(len(result["improvement_suggestions"]) > 0)
    
    def test_generate_pdf(self):
        """Test generating a PDF."""
        output_path = os.path.join(self.test_output_dir, "test_guide.pdf")
        
        result = self.agent.generate_pdf(self.guide_content, output_path)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["quality_score"], 0.9)
        self.assertEqual(len(result["improvement_suggestions"]), 2)
        
        # Check that the PDF file was created
        self.assertTrue(os.path.exists(output_path))
    
    def test_generate_pdf_error(self):
        """Test error handling in PDF generation."""
        # Create a situation where PDF generation will fail
        with patch.object(self.agent, '_render_html', side_effect=Exception("Test error")):
            output_path = os.path.join(self.test_output_dir, "error_guide.pdf")
            
            result = self.agent.generate_pdf(self.guide_content, output_path)
            
            self.assertFalse(result["success"])
            self.assertEqual(result["quality_score"], 0.0)
            self.assertIn("error", result)
            self.assertIn("Test error", result["error"])
    
    def test_process_method(self):
        """Test the process method."""
        output_path = os.path.join(self.test_output_dir, "process_guide.pdf")
        
        success, file_path, result = self.agent.process(self.guide_content, output_path)
        
        self.assertTrue(success)
        self.assertEqual(file_path, "output/guides/test_guide.pdf")  # This comes from the mock LLM
        self.assertEqual(result["quality_score"], 0.9)
        self.assertEqual(len(result["improvement_suggestions"]), 2)

if __name__ == "__main__":
    unittest.main() 