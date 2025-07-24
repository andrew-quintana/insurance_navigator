"""
Unit test for validating the Service Access Strategy prompt structure.

This test verifies that the prompt follows the required formatting and contains
all necessary sections without running actual LLM evaluations.
"""

import os
import sys
import unittest
import re

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

try:
    from utils.agent_config_manager import get_config_manager
except ImportError:
    # If the import fails, we'll create a simple mock for testing
    class MockConfigManager:
        def get_agent_config(self, agent_name):
            return {
                "prompt": {
                    "version": "0.2",
                    "path": os.path.abspath(os.path.join(
                        os.path.dirname(__file__), 
                        '../../prompts/prompt_service_access_strategy_v0_2.md'
                    ))
                }
            }
    
    def get_config_manager():
        return MockConfigManager()

class TestPromptValidation(unittest.TestCase):
    """Tests for validating the Service Access Strategy prompt structure."""
    
    def setUp(self):
        """Set up the test environment."""
        try:
            # Load the prompt template using agent config
            config_manager = get_config_manager()
            agent_config = config_manager.get_agent_config("service_access_strategy")
            prompt_path = agent_config.get("prompt", {}).get("path")
            
            # Make sure prompt path exists
            self.assertIsNotNone(prompt_path, "Prompt path not configured in agent_config.json")
            self.assertTrue(os.path.exists(prompt_path), f"Prompt file does not exist: {prompt_path}")
        except Exception as e:
            # Fallback to direct path if config loading fails
            prompt_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 
                '../../prompts/prompt_service_access_strategy_v0_2.md'
            ))
            print(f"Warning: Using fallback prompt path due to error: {str(e)}")
        
        with open(prompt_path, 'r') as f:
            self.prompt_content = f.read()
    
    def test_prompt_structure(self):
        """Test that the prompt contains all required sections."""
        required_sections = [
            "Service Access Strategy Prompt",
            "Tree of Thoughts Problem Solver",
            "Expected Input Format",
            "Tree of Thoughts Framework",
            "PROBLEM ANALYSIS",
            "GREEDY SOLUTION BRANCHING",
            "PATH EVALUATION",
            "SOLUTION SELECTION AND DELIVERY",
            "LANGUAGE & COMPLIANCE FINALIZATION",
            "Task Context",
            "Requirements",
            "Constraints",
            "Success Criteria",
            "Output Format"
        ]
        
        for section in required_sections:
            self.assertIn(section, self.prompt_content, f"Missing required section: {section}")
    
    def test_input_format_description(self):
        """Test that the input format is properly described."""
        input_sections = [
            "Healthcare Intent",
            "User Context",
            "Insurance Information"
        ]
        
        # Find the Expected Input Format section
        input_format_match = re.search(r"## Expected Input Format(.*?)---", self.prompt_content, re.DOTALL)
        self.assertIsNotNone(input_format_match, "Expected Input Format section not found")
        
        input_format_section = input_format_match.group(1)
        for section in input_sections:
            self.assertIn(section, input_format_section, f"Missing input section: {section}")
    
    def test_output_format_validity(self):
        """Test that the output format is valid JSON."""
        # Find the Output Format section - now uses ```json format
        output_format_match = re.search(r'## Output Format\s*```json\s*(\{.*?\})\s*```', self.prompt_content, re.DOTALL)
        self.assertIsNotNone(output_format_match, "Output Format section not found")
        
        output_format = output_format_match.group(1)
        
        # Check for balanced braces - a simple approach to validate JSON-like structure
        open_braces = output_format.count("{")
        close_braces = output_format.count("}")
        self.assertEqual(open_braces, close_braces, "Unbalanced braces in output format")
        
        open_brackets = output_format.count("[")
        close_brackets = output_format.count("]")
        self.assertEqual(open_brackets, close_brackets, "Unbalanced brackets in output format")
    
    def test_tree_of_thoughts_components(self):
        """Test that all Tree of Thoughts components are present."""
        tot_components = [
            "PROBLEM ANALYSIS",
            "GREEDY SOLUTION BRANCHING",
            "PATH EVALUATION",
            "SOLUTION SELECTION AND DELIVERY",
            "LANGUAGE & COMPLIANCE FINALIZATION"
        ]
        
        # Find the Tree of Thoughts Framework section
        tot_framework_match = re.search(r"## Tree of Thoughts Framework(.*?)^## Task Context", 
                                       self.prompt_content, re.DOTALL | re.MULTILINE)
        self.assertIsNotNone(tot_framework_match, "Tree of Thoughts Framework section not found")
        
        tot_framework_section = tot_framework_match.group(1)
        for component in tot_components:
            self.assertIn(component, tot_framework_section, f"Missing Tree of Thoughts component: {component}")
    
    def test_required_output_fields(self):
        """Test that all required output fields are defined."""
        required_fields = [
            "access_strategy",
            "summary",
            "coverage_details",
            "action_plan",
            "provider_options",
            "preparation_guidance",
            "alternative_options",
            "support_resources"
        ]
        
        for field in required_fields:
            self.assertIn(field, self.prompt_content, f"Missing required output field: {field}")
    
    def test_prompt_version(self):
        """Test that the prompt version is correctly specified."""
        try:
            # Get expected version from config
            config_manager = get_config_manager()
            agent_config = config_manager.get_agent_config("service_access_strategy")
            expected_version = agent_config.get("prompt", {}).get("version", "0.2")
        except Exception:
            # Fallback version
            expected_version = "0.2"
        
        # Check version in prompt content
        version_match = re.search(r"Service Access Strategy Prompt v(\d+\.\d+)", self.prompt_content)
        self.assertIsNotNone(version_match, "Prompt version not found")
        
        version = version_match.group(1)
        self.assertEqual(version, expected_version, f"Incorrect prompt version. Expected {expected_version}, got {version}")

if __name__ == "__main__":
    unittest.main() 