#!/usr/bin/env python
"""
Script to run prompt security tests against the examples in prompt_security_test_examples.json

This script:
1. Runs all test cases from the examples file
2. Reports results in the requested format
3. Validates round-trip sanitization
"""

import os
import sys
import json
from typing import Dict, Any, List, Tuple
import argparse

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from agents.prompt_security_agent import PromptSecurityAgent
from utils.prompt_loader import clear_cache

def load_test_examples(file_path: str) -> Dict[str, Any]:
    """Load test examples from the specified JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def evaluate_example(agent: PromptSecurityAgent, example: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a single test example.
    
    Args:
        agent: The PromptSecurityAgent instance
        example: The test example
        
    Returns:
        A dictionary with the evaluation results
    """
    input_text = example["input"]
    expected_output = example["expected_output"]
    expected_is_safe = expected_output[0]
    expected_sanitized = expected_output[1]
    expected_details = expected_output[2]
    
    # Process the input
    is_safe, sanitized_input, result = agent.process(input_text)
    
    # If input was unsafe, check that sanitized input is now safe
    if not is_safe:
        # Process the sanitized input
        sanitized_is_safe, _, sanitized_result = agent.process(sanitized_input)
    else:
        sanitized_is_safe = is_safe
        sanitized_result = result
    
    # Build the evaluation result
    return {
        "input": input_text,
        "your_classification": {
            "is_safe": is_safe,
            "threat_type": result.get("threat_type", "none"),
            "threat_severity": result.get("threat_severity", "none_detected")
        },
        "sanitized_classification": {
            "is_safe": sanitized_is_safe,
            "threat_type": sanitized_result.get("threat_type", "none"),
            "threat_severity": sanitized_result.get("threat_severity", "none_detected")
        },
        "sanitization_passed": sanitized_is_safe,
        "match_expected": (is_safe == expected_is_safe)
    }

def evaluate_all_examples(agent: PromptSecurityAgent, test_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluate all test examples and return detailed results.
    
    Args:
        agent: The PromptSecurityAgent instance
        test_data: The test data containing all examples
        
    Returns:
        A list of dictionaries with evaluation results
    """
    all_results = []
    
    for function_test in test_data["failure_mode_tests"]:
        function = function_test["function"]
        failure_mode = function_test["failure_mode"]
        
        function_results = {
            "function": function,
            "failure_mode": failure_mode,
            "examples": []
        }
        
        for example in function_test["examples"]:
            try:
                result = evaluate_example(agent, example)
                function_results["examples"].append(result)
            except Exception as e:
                print(f"Error evaluating example: {example['input'][:30]}... - {str(e)}")
                # Add a failed result
                function_results["examples"].append({
                    "input": example["input"],
                    "error": str(e),
                    "match_expected": False,
                    "sanitization_passed": False
                })
        
        all_results.append(function_results)
    
    return all_results

def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Summarize the evaluation results.
    
    Args:
        results: The list of evaluation results
        
    Returns:
        A dictionary with summary statistics
    """
    total_examples = 0
    successes = 0
    
    for function_result in results:
        for example in function_result["examples"]:
            total_examples += 1
            if example.get("match_expected", False) and example.get("sanitization_passed", False):
                successes += 1
    
    success_rate = (successes / total_examples) * 100 if total_examples > 0 else 0
    
    return {
        "total_examples": total_examples,
        "successes": successes,
        "failures": total_examples - successes,
        "success_rate": f"{success_rate:.2f}%"
    }

def main():
    """Run the prompt security tests and generate a report."""
    parser = argparse.ArgumentParser(description="Run prompt security tests")
    parser.add_argument('--output', '-o', default='tests/agents/test_results/prompt_security_results.json',
                      help='Output file for test results')
    parser.add_argument('--examples', '-e', default='tests/agents/data/prompt_security_test_examples.json',
                      help='Path to the test examples JSON file')
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Clear the prompt cache
    clear_cache()
    
    # Create the agent
    agent = PromptSecurityAgent()
    
    # Load test examples
    test_data = load_test_examples(args.examples)
    
    print(f"Running tests on {sum(len(f['examples']) for f in test_data['failure_mode_tests'])} examples...")
    
    # Evaluate all examples
    results = evaluate_all_examples(agent, test_data)
    
    # Summarize results
    summary = summarize_results(results)
    
    # Create final report
    report = {
        "summary": summary,
        "results": results
    }
    
    # Save report to file
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Test results saved to {args.output}")
    print(f"Overall success rate: {summary['success_rate']} ({summary['successes']}/{summary['total_examples']})")

if __name__ == "__main__":
    main() 