"""
Performance Testing for the Prompt Security Agent

This script uses the generic performance metrics framework to evaluate the prompt security agent.
"""

import os
import json
import sys
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from agents.prompt_security.core.prompt_security import PromptSecurityAgent
from utils.performance_metrics import PerformanceEvaluator, TestCase, estimate_tokens

def load_test_cases():
    """Load test cases from the test examples file."""
    test_cases = []
    
    try:
        examples_path = os.path.join("agents", "prompt_security", "tests", "examples", "test_examples_prompt_security.json")
        with open(examples_path, "r") as f:
            examples_data = json.load(f)
        
        # Extract test cases from the examples
        for test_group in examples_data.get("failure_mode_tests", []):
            failure_mode = test_group.get("failure_mode", "")
            for example in test_group.get("examples", []):
                input_text = example.get("input", "")
                expected_output = example.get("expected_output", [])
                
                if len(expected_output) >= 1:
                    expected_is_safe = expected_output[0]
                    
                    # Create a test case
                    test_case = TestCase(
                        input=input_text,
                        expected_output=expected_is_safe,
                        category=failure_mode,
                        metadata={"original_expected_output": expected_output}
                    )
                    
                    test_cases.append(test_case)
    
    except Exception as e:
        print(f"Error loading test cases: {str(e)}")
    
    return test_cases

def is_correct_func(actual_output, expected_output):
    """Custom function to determine if the output is correct."""
    # The actual output is a tuple (is_safe, sanitized_input, details)
    if isinstance(actual_output, tuple) and len(actual_output) >= 1:
        return actual_output[0] == expected_output
    return False

def token_counter(output):
    """Count tokens in the output."""
    if isinstance(output, tuple) and len(output) >= 2:
        # Count tokens in the sanitized input
        return estimate_tokens(str(output[1]))
    return 0

def main():
    """Run performance tests."""
    print("Starting performance testing for Prompt Security Agent...")
    
    # Load test cases
    test_cases = load_test_cases()
    print(f"Loaded {len(test_cases)} test cases")
    
    # Initialize agent in mock mode for faster testing
    agent = PromptSecurityAgent(mock_mode=True)
    
    # Create evaluator
    evaluator = PerformanceEvaluator("Prompt Security Agent")
    
    # Define the process function
    process_func = lambda input_text: agent.process(input_text)
    
    # Run the tests
    evaluator.run_test_cases(
        test_cases=test_cases,
        process_func=process_func,
        is_correct_func=is_correct_func,
        token_counter=token_counter,
        progress_interval=5
    )
    
    # Calculate and print metrics
    metrics = evaluator.calculate_metrics()
    evaluator.print_metrics_report(metrics)
    
    # Save metrics to file
    metrics_dir = os.path.join("agents", "prompt_security", "metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    metrics_file = os.path.join(metrics_dir, f"performance_metrics_{time.strftime('%Y%m%d_%H%M%S')}.json")
    metrics.save_to_file(metrics_file)
    print(f"\nMetrics saved to {metrics_file}")

if __name__ == "__main__":
    main() 