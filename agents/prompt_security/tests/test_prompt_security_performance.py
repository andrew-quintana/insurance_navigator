"""
Performance Testing for the Prompt Security Agent

This script measures:
1. Response time for different input types
2. Accuracy against known test cases
3. Memory usage
"""

import os
import json
import sys
import time
import tracemalloc
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from agents.prompt_security.prompt_security import PromptSecurityAgent

def load_test_cases() -> List[Dict[str, Any]]:
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
                    
                    test_cases.append({
                        "input": input_text,
                        "expected_is_safe": expected_is_safe,
                        "failure_mode": failure_mode
                    })
    
    except Exception as e:
        print(f"Error loading test cases: {str(e)}")
    
    return test_cases

def measure_performance(agent: PromptSecurityAgent, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Measure performance metrics for the agent."""
    results = {
        "total_cases": len(test_cases),
        "correct_predictions": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "total_time": 0,
        "avg_time": 0,
        "max_time": 0,
        "min_time": float('inf'),
        "memory_peak": 0,
        "by_failure_mode": {}
    }
    
    # Start memory tracking
    tracemalloc.start()
    
    # Process each test case
    for i, case in enumerate(test_cases):
        input_text = case["input"]
        expected_is_safe = case["expected_is_safe"]
        failure_mode = case["failure_mode"]
        
        # Initialize failure mode stats if not present
        if failure_mode not in results["by_failure_mode"]:
            results["by_failure_mode"][failure_mode] = {
                "total": 0,
                "correct": 0,
                "avg_time": 0,
                "total_time": 0
            }
        
        results["by_failure_mode"][failure_mode]["total"] += 1
        
        # Measure processing time
        start_time = time.time()
        is_safe, sanitized_input, details = agent.process(input_text)
        end_time = time.time()
        
        # Calculate processing time
        processing_time = end_time - start_time
        results["total_time"] += processing_time
        results["by_failure_mode"][failure_mode]["total_time"] += processing_time
        
        # Update min/max times
        results["max_time"] = max(results["max_time"], processing_time)
        results["min_time"] = min(results["min_time"], processing_time)
        
        # Check accuracy
        if is_safe == expected_is_safe:
            results["correct_predictions"] += 1
            results["by_failure_mode"][failure_mode]["correct"] += 1
        else:
            if is_safe and not expected_is_safe:
                results["false_negatives"] += 1
            elif not is_safe and expected_is_safe:
                results["false_positives"] += 1
        
        # Print progress
        if (i + 1) % 5 == 0 or i == len(test_cases) - 1:
            print(f"Processed {i + 1}/{len(test_cases)} test cases")
    
    # Calculate averages
    if results["total_cases"] > 0:
        results["avg_time"] = results["total_time"] / results["total_cases"]
        
        for mode, stats in results["by_failure_mode"].items():
            if stats["total"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["total"]
    
    # Get memory peak
    current, peak = tracemalloc.get_traced_memory()
    results["memory_peak"] = peak / 1024 / 1024  # Convert to MB
    tracemalloc.stop()
    
    return results

def print_performance_report(results: Dict[str, Any]) -> None:
    """Print a formatted performance report."""
    print("\n" + "=" * 50)
    print("PROMPT SECURITY AGENT PERFORMANCE REPORT")
    print("=" * 50)
    
    # Overall metrics
    print("\n--- OVERALL METRICS ---")
    print(f"Total test cases: {results['total_cases']}")
    print(f"Correct predictions: {results['correct_predictions']} ({results['correct_predictions']/results['total_cases']*100:.2f}%)")
    print(f"False positives: {results['false_positives']}")
    print(f"False negatives: {results['false_negatives']}")
    print(f"Average processing time: {results['avg_time']:.4f} seconds")
    print(f"Min processing time: {results['min_time']:.4f} seconds")
    print(f"Max processing time: {results['max_time']:.4f} seconds")
    print(f"Memory peak usage: {results['memory_peak']:.2f} MB")
    
    # Metrics by failure mode
    print("\n--- METRICS BY FAILURE MODE ---")
    for mode, stats in results["by_failure_mode"].items():
        accuracy = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"\n{mode}:")
        print(f"  Total cases: {stats['total']}")
        print(f"  Accuracy: {accuracy:.2f}%")
        print(f"  Average time: {stats['avg_time']:.4f} seconds")

def main():
    """Run performance tests."""
    print("Starting performance testing for Prompt Security Agent...")
    
    # Load test cases
    test_cases = load_test_cases()
    print(f"Loaded {len(test_cases)} test cases")
    
    # Initialize agent in mock mode for faster testing
    agent = PromptSecurityAgent(mock_mode=True)
    
    # Measure performance
    results = measure_performance(agent, test_cases)
    
    # Print report
    print_performance_report(results)
    
    print("\nPerformance testing completed!")

if __name__ == "__main__":
    main() 