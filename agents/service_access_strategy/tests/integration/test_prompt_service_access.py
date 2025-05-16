"""
Integration test for the Service Access Strategy Prompt.

This test evaluates the prompt's ability to generate valid service access strategies
based on user healthcare intents, context, and insurance information.
"""

import os
import sys
import json
import unittest
from typing import Dict, Any, List
import logging

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# Import necessary modules
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import agent_config_manager, or create a mock
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
                },
                "test_examples": {
                    "path": os.path.abspath(os.path.join(
                        os.path.dirname(__file__), 
                        '../data/examples/test_prompt_service_access_strategy.json'
                    ))
                },
                "model": {
                    "name": "gpt-4",
                    "temperature": 0.2
                }
            }
    
    def get_config_manager():
        return MockConfigManager()

class TestServiceAccessStrategyPrompt(unittest.TestCase):
    """Tests for the Service Access Strategy Prompt."""
    
    def setUp(self):
        """Set up the test environment."""
        try:
            # Get agent config
            config_manager = get_config_manager()
            self.agent_config = config_manager.get_agent_config("service_access_strategy")
            
            # Get test examples path from config
            test_examples_path = self.agent_config.get("test_examples", {}).get("path")
            
            # Check if test examples path exists in config, otherwise use default path
            if test_examples_path and os.path.exists(test_examples_path):
                self.examples_path = test_examples_path
            else:
                # Fallback to the new test examples we created
                self.examples_path = os.path.abspath(os.path.join(
                    os.path.dirname(__file__), 
                    '../data/examples/test_prompt_service_access_strategy.json'
                ))
            
            # Make sure examples file exists
            self.assertTrue(os.path.exists(self.examples_path), f"Test examples file not found: {self.examples_path}")
            
            # Get prompt path from config
            prompt_path = self.agent_config.get("prompt", {}).get("path")
            self.assertTrue(os.path.exists(prompt_path), f"Prompt file not found: {prompt_path}")
            
            # Get model config
            model_config = self.agent_config.get("model", {})
            model_name = model_config.get("name", "gpt-4")
            temperature = model_config.get("temperature", 0.2)
        except Exception as e:
            logger.warning(f"Error loading configuration: {str(e)}. Using fallback paths.")
            # Fallback paths
            self.examples_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 
                '../data/examples/test_prompt_service_access_strategy.json'
            ))
            prompt_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 
                '../../prompts/prompt_service_access_strategy_v0_2.md'
            ))
            model_name = "gpt-4"
            temperature = 0.2
        
        # Load examples
        with open(self.examples_path, 'r') as f:
            self.test_examples = json.load(f)['examples']
        
        # Load prompt
        with open(prompt_path, 'r') as f:
            self.prompt_template = f.read()
        
        # Initialize LLM (use mock for testing or actual LLM if available)
        try:
            self.llm = ChatOpenAI(
                model_name=model_name, 
                temperature=temperature,
                verbose=True
            )
            self.use_mock = False
        except Exception as e:
            logger.warning(f"Failed to initialize real LLM, using mock: {e}")
            self.use_mock = True
    
    def mock_llm_response(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock LLM response for testing purposes."""
        # This is a simplified mock response - in reality, you would want a more complex
        # mock that simulates actual LLM behavior for specific inputs
        return {
            "access_strategy": {
                "summary": {
                    "primary_approach": f"Manage {example['input']['healthcare_intent']['primary_concern']}",
                    "confidence_score": 0.85,
                    "estimated_timeline": "2-4 weeks",
                    "key_benefits": ["Convenient", "Insurance-covered", "Specialized care"]
                },
                "coverage_details": {
                    "service_type": "Specialist Consultation",
                    "is_covered": True,
                    "coverage_details": {
                        "copay": "$40",
                        "requires_referral": True,
                        "prior_authorization": False,
                        "coverage_notes": ["Must be in-network", "Limited to 4 visits per year"]
                    }
                },
                "action_plan": [
                    {
                        "step_number": 1,
                        "step_description": "Schedule appointment with primary care physician",
                        "expected_timeline": "1 week",
                        "required_resources": ["Insurance card", "Medical history"],
                        "potential_obstacles": ["Limited appointment availability"],
                        "contingency_plan": "Use urgent care if needed"
                    },
                    {
                        "step_number": 2,
                        "step_description": "Get referral to specialist",
                        "expected_timeline": "1-2 weeks",
                        "required_resources": ["PCP appointment"],
                        "potential_obstacles": ["Referral denial"],
                        "contingency_plan": "Appeal decision with insurance"
                    }
                ],
                "provider_options": [
                    {
                        "name": "Example Medical Center",
                        "address": "123 Healthcare St, City, State",
                        "distance": "5 miles",
                        "in_network": True,
                        "specialties": ["Primary Care", "Endocrinology"],
                        "availability": "Appointments available within 2 weeks"
                    }
                ],
                "preparation_guidance": {
                    "before_appointment": ["List current medications", "Bring medical records"],
                    "questions_to_ask": ["What are my treatment options?", "What are the costs?"],
                    "documents_needed": ["Insurance card", "ID", "Medical history"]
                },
                "alternative_options": [
                    {
                        "option_name": "Telehealth Consultation",
                        "brief_description": "Virtual appointment with healthcare provider",
                        "key_differences": ["No travel required", "May have limited examination"],
                        "when_to_consider": "When mobility is limited or for initial consultation"
                    }
                ],
                "support_resources": {
                    "educational_materials": ["Disease management guide", "Medication information"],
                    "support_services": ["Patient advocacy group", "Nurse hotline"],
                    "emergency_contacts": ["911", "24/7 Nurse line: 555-123-4567"]
                }
            }
        }
    
    def validate_output_structure(self, output: Dict[str, Any], expected_structure: Dict[str, Any]) -> List[str]:
        """Validate the output against the expected structure."""
        errors = []
        
        # Helper function to check structure
        def check_structure(actual, expected, path=""):
            if isinstance(expected, dict):
                if not isinstance(actual, dict):
                    errors.append(f"At {path}: Expected dictionary, got {type(actual)}")
                    return
                
                # Check for missing keys
                for key in expected:
                    if key not in actual:
                        errors.append(f"At {path}: Missing key '{key}'")
                    else:
                        check_structure(actual[key], expected[key], f"{path}.{key}" if path else key)
            
            elif isinstance(expected, list):
                if not isinstance(actual, list):
                    errors.append(f"At {path}: Expected list, got {type(actual)}")
                    return
                
                if not actual:
                    errors.append(f"At {path}: List is empty")
                    return
                
                # Check first item in list against expected structure
                if expected and actual:
                    element_type = expected[0]
                    if isinstance(element_type, (dict, list)):
                        check_structure(actual[0], element_type, f"{path}[0]")
            
            # For leaf nodes, we just check the general type (string, number, boolean)
            elif expected == "String":
                if not isinstance(actual, str):
                    errors.append(f"At {path}: Expected string, got {type(actual)}")
            
            elif expected == "Number" or "Number" in str(expected):
                if not isinstance(actual, (int, float)):
                    errors.append(f"At {path}: Expected number, got {type(actual)}")
            
            elif expected == "Boolean":
                if not isinstance(actual, bool):
                    errors.append(f"At {path}: Expected boolean, got {type(actual)}")
        
        # Start validation
        check_structure(output, expected_structure)
        return errors
    
    def validate_content_criteria(self, output: Dict[str, Any], criteria: List[str], example: Dict[str, Any]) -> List[str]:
        """Validate the output against specific content criteria."""
        errors = []
        access_strategy = output.get("access_strategy", {})
        
        for criterion in criteria:
            # Example of criterion validation - expand based on your specific needs
            if "follows the expected JSON structure" in criterion:
                # Already checked in structure validation
                continue
                
            elif "Primary approach addresses" in criterion:
                concern = example["input"]["healthcare_intent"]["primary_concern"]
                primary_approach = access_strategy.get("summary", {}).get("primary_approach", "")
                if concern.lower() not in primary_approach.lower():
                    errors.append(f"Criterion not met: {criterion}")
            
            elif "Coverage details must include" in criterion:
                coverage = access_strategy.get("coverage_details", {}).get("coverage_details", {})
                if "copay" not in coverage or "requires_referral" not in coverage:
                    errors.append(f"Criterion not met: {criterion}")
            
            elif "Action plan must include at least two steps" in criterion:
                action_plan = access_strategy.get("action_plan", [])
                if len(action_plan) < 2:
                    errors.append(f"Criterion not met: {criterion}")
            
            elif "At least one provider option must be included" in criterion:
                providers = access_strategy.get("provider_options", [])
                if len(providers) < 1:
                    errors.append(f"Criterion not met: {criterion}")
            
            elif "Alternative options should include telehealth" in criterion:
                alternatives = access_strategy.get("alternative_options", [])
                telehealth_found = False
                for alt in alternatives:
                    if "telehealth" in alt.get("option_name", "").lower():
                        telehealth_found = True
                        break
                if not telehealth_found:
                    errors.append(f"Criterion not met: {criterion}")
            
            elif "Approach reflects urgency level" in criterion:
                if example["input"]["healthcare_intent"]["urgency_level"] == "urgent":
                    timeline = access_strategy.get("summary", {}).get("estimated_timeline", "")
                    if "day" not in timeline.lower() and "immediate" not in timeline.lower():
                        errors.append(f"Criterion not met: {criterion}")
            
            elif "Provider options must include wheelchair accessibility" in criterion:
                # This would require more detailed checking in a real implementation
                # Here we're just doing a simple text search
                providers = access_strategy.get("provider_options", [])
                accessibility_found = False
                for provider in providers:
                    if "wheelchair" in json.dumps(provider).lower():
                        accessibility_found = True
                        break
                if not accessibility_found:
                    errors.append(f"Criterion not met: {criterion}")
            
            elif "Language preference" in criterion:
                # Similarly, this would need more detailed checking
                has_language_support = "language" in json.dumps(access_strategy).lower()
                if not has_language_support:
                    errors.append(f"Criterion not met: {criterion}")
            
            elif "Action plan includes immediate pain management" in criterion:
                action_plan = access_strategy.get("action_plan", [])
                pain_management_found = False
                for step in action_plan:
                    if "pain" in step.get("step_description", "").lower():
                        pain_management_found = True
                        break
                if not pain_management_found:
                    errors.append(f"Criterion not met: {criterion}")
            
            elif "Emergency contacts must be included" in criterion:
                emergency_contacts = access_strategy.get("support_resources", {}).get("emergency_contacts", [])
                if len(emergency_contacts) < 1:
                    errors.append(f"Criterion not met: {criterion}")
        
        return errors
    
    def format_input_for_prompt(self, example_input: Dict[str, Any]) -> str:
        """Format the test example input for the prompt."""
        return json.dumps(example_input, indent=2)
    
    def test_prompt_with_examples(self):
        """Test the prompt with all test examples."""
        for example in self.test_examples:
            with self.subTest(example_name=example["name"]):
                logger.info(f"Testing example: {example['name']}")
                
                # Format input
                formatted_input = self.format_input_for_prompt(example["input"])
                
                # Generate response
                if self.use_mock:
                    response = self.mock_llm_response(example)
                else:
                    # Construct the messages
                    messages = [
                        SystemMessage(content=self.prompt_template),
                        HumanMessage(content=formatted_input)
                    ]
                    
                    # Get LLM response
                    llm_response = self.llm.invoke(messages)
                    
                    # Parse JSON response
                    # Note: In a real implementation, you'd need to handle extraction of JSON from potentially
                    # non-JSON text, error handling, etc.
                    try:
                        response = json.loads(llm_response.content)
                    except json.JSONDecodeError:
                        self.fail(f"LLM response is not valid JSON: {llm_response.content}")
                
                # Validate structure
                structure_errors = self.validate_output_structure(
                    response, 
                    example["expected_output_structure"]
                )
                
                # Validate content criteria
                content_errors = self.validate_content_criteria(
                    response,
                    example["validation_criteria"],
                    example
                )
                
                # Log results
                if structure_errors or content_errors:
                    logger.error(f"Validation failed for example {example['name']}:")
                    for error in structure_errors:
                        logger.error(f"  Structure error: {error}")
                    for error in content_errors:
                        logger.error(f"  Content error: {error}")
                
                # Assert no errors
                self.assertEqual(len(structure_errors), 0, f"Structure validation errors: {structure_errors}")
                self.assertEqual(len(content_errors), 0, f"Content validation errors: {content_errors}")

if __name__ == "__main__":
    unittest.main() 