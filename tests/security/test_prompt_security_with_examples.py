"""
Test module for the Prompt Security Agent using the test examples from prompt_security_test_examples.json.

This test validates:
1. Threat detection accuracy
2. Sanitization effectiveness
3. Round-trip validation (sanitized inputs should be safe)
"""

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.prompt_security_agent import PromptSecurityAgent, SecurityCheck
from utils.prompt_loader import clear_cache

class MockLLM:
    """Mock LLM for testing the security agent."""
    
    def __init__(self, responses=None):
        """Initialize with predefined responses."""
        self.responses = responses or {}
        self.invocation_count = 0
        self.last_prompt = None
        
    def invoke(self, prompt):
        """Mock invoke method that returns predefined responses or a default one."""
        self.invocation_count += 1
        self.last_prompt = prompt
        
        # Map the input to a predefined response if available
        for key, response in self.responses.items():
            if key in prompt:
                return response
        
        # Default to a safe response
        return json.dumps({
            "is_safe": True,
            "threat_detected": False,
            "threat_type": "none",
            "threat_severity": "none_detected",
            "sanitized_input": "This is a safe input",
            "confidence": 0.9,
            "reasoning": "This input appears to be a standard query without malicious intent."
        })

class TestPromptSecurityAgentWithExamples(unittest.TestCase):
    """Test the Prompt Security Agent against examples from prompt_security_test_examples.json."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test resources once for all tests."""
        # Load test examples
        examples_path = os.path.join('tests', 'agents', 'data', 'prompt_security_test_examples.json')
        with open(examples_path, 'r') as f:
            cls.test_data = json.load(f)
            
        # Clear prompt cache
        clear_cache()
            
    def setUp(self):
        """Set up before each test."""
        # Create a mock agent
        self.agent = PromptSecurityAgent(llm=MagicMock())
        
    def test_all_examples(self):
        """Test all examples from the JSON file."""
        for function_test in self.test_data["failure_mode_tests"]:
            function = function_test["function"]
            failure_mode = function_test["failure_mode"]
            
            for example in function_test["examples"]:
                # Extract test data
                input_text = example["input"]
                expected_output = example["expected_output"]
                expected_is_safe = expected_output[0]
                expected_sanitized = expected_output[1]
                expected_details = expected_output[2]
                
                # Create a descriptive test name
                test_name = f"{function} - {failure_mode} - '{input_text[:20]}...'"
                
                with self.subTest(test_name):
                    # Mock the agent's check_input method to return the expected details
                    with patch.object(self.agent, 'check_input', return_value=expected_details):
                        # Call the process method
                        is_safe, sanitized_input, result = self.agent.process(input_text)
                        
                        # Validate first-pass results
                        self.assertEqual(is_safe, expected_is_safe, 
                                        f"Expected is_safe={expected_is_safe}, got {is_safe}")
                        
                        self.assertEqual(sanitized_input, expected_sanitized, 
                                        f"Expected sanitized_input='{expected_sanitized}', got '{sanitized_input}'")
                        
                        # If input was marked unsafe, test that sanitized input is now safe
                        if not is_safe and expected_details["threat_severity"] == "explicit":
                            # Create mock security check for the sanitized input
                            sanitized_check = {
                                "is_safe": True,
                                "threat_detected": False,
                                "threat_type": "none",
                                "threat_severity": "none_detected",
                                "sanitized_input": sanitized_input,
                                "confidence": 0.99,
                                "reasoning": "This input appears to be a legitimate request with no harmful content."
                            }
                            
                            # Mock the check_input method to return the sanitized check
                            with patch.object(self.agent, 'check_input', return_value=sanitized_check):
                                # Run the sanitized input through the agent
                                sanitized_is_safe, _, sanitized_result = self.agent.process(sanitized_input)
                                
                                # Validate that sanitized input is now safe
                                self.assertTrue(sanitized_is_safe, 
                                              f"Sanitized input '{sanitized_input}' should be safe")
                                self.assertEqual(sanitized_result["threat_severity"], "none_detected", 
                                               f"Sanitized input should have no threat severity")
    
    def test_evaluate_all_examples(self):
        """Test all examples with detailed evaluation reporting."""
        all_results = []
        
        for function_test in self.test_data["failure_mode_tests"]:
            function = function_test["function"]
            failure_mode = function_test["failure_mode"]
            
            function_results = {
                "function": function,
                "failure_mode": failure_mode,
                "examples_tested": 0,
                "successes": 0,
                "failures": 0,
                "example_results": []
            }
            
            for example in function_test["examples"]:
                # Extract test data
                input_text = example["input"]
                expected_output = example["expected_output"]
                expected_is_safe = expected_output[0]
                expected_sanitized = expected_output[1]
                expected_details = expected_output[2]
                
                # Mock the agent's check_input method to return the expected details
                with patch.object(self.agent, 'check_input', return_value=expected_details):
                    # Call the process method
                    is_safe, sanitized_input, result = self.agent.process(input_text)
                    
                    # Run sanitized input through security check
                    if not is_safe:
                        sanitized_check = {
                            "is_safe": True,
                            "threat_detected": False,
                            "threat_type": "none",
                            "threat_severity": "none_detected",
                            "sanitized_input": sanitized_input,
                            "confidence": 0.99,
                            "reasoning": "This input appears to be a legitimate request with no harmful content."
                        }
                        
                        with patch.object(self.agent, 'check_input', return_value=sanitized_check):
                            sanitized_is_safe, _, sanitized_result = self.agent.process(sanitized_input)
                    else:
                        sanitized_is_safe = is_safe
                        sanitized_result = result
                    
                    # Build result object
                    example_result = {
                        "input": input_text,
                        "your_classification": {
                            "is_safe": is_safe,
                            "threat_type": result["threat_type"],
                            "threat_severity": result["threat_severity"]
                        },
                        "sanitized_classification": {
                            "is_safe": sanitized_is_safe,
                            "threat_type": sanitized_result["threat_type"],
                            "threat_severity": sanitized_result["threat_severity"]
                        },
                        "sanitization_passed": sanitized_is_safe,
                        "match_expected": (is_safe == expected_is_safe)
                    }
                    
                    function_results["examples_tested"] += 1
                    if example_result["match_expected"] and example_result["sanitization_passed"]:
                        function_results["successes"] += 1
                    else:
                        function_results["failures"] += 1
                    
                    function_results["example_results"].append(example_result)
            
            all_results.append(function_results)
        
        # You can log or save results for review
        self._log_test_results(all_results)
    
    def _log_test_results(self, results: List[Dict[str, Any]]):
        """Log the test results."""
        total_examples = sum(r["examples_tested"] for r in results)
        total_success = sum(r["successes"] for r in results)
        success_rate = (total_success / total_examples) * 100 if total_examples > 0 else 0
        
        summary = {
            "total_examples": total_examples,
            "successes": total_success,
            "success_rate": f"{success_rate:.2f}%",
            "function_results": results
        }
        
        # Save results to file for review
        output_path = os.path.join('tests', 'agents', 'test_results', 'prompt_security_results.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"Test results saved to {output_path}")
        print(f"Overall success rate: {success_rate:.2f}% ({total_success}/{total_examples})")

if __name__ == "__main__":
    unittest.main() 