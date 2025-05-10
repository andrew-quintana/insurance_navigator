#!/usr/bin/env python3
"""
Compare performance of different versions of the prompt security agent.
This script runs the evaluation on both V0.1 and V0.2 versions and
generates a comparison report with key metrics and differences.
"""

import os
import sys
import csv
import subprocess
from typing import Dict, List, Any

def read_csv_file(filepath: str) -> List[Dict[str, Any]]:
    """Read data from a CSV file."""
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found")
        return []
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def generate_comparison_report(v1_results: List[Dict[str, Any]], v2_results: List[Dict[str, Any]]) -> None:
    """Generate a comparison report between two versions."""
    print("\n=== PROMPT SECURITY AGENT VERSION COMPARISON ===\n")
    
    # Create a table for metrics comparison
    print("METRICS COMPARISON:")
    print(f"{'Metric':<15} | {'V0.1 Accuracy':<15} | {'V0.2 Accuracy':<15} | {'Difference':<15}")
    print("-" * 65)
    
    for v1_row in v1_results:
        for v2_row in v2_results:
            if v1_row["Field"] == v2_row["Field"]:
                field = v1_row["Field"]
                v1_accuracy = v1_row["Accuracy"] 
                v2_accuracy = v2_row["Accuracy"]
                
                # Extract numeric values from percentage strings
                v1_value = float(v1_accuracy.strip("%")) / 100
                v2_value = float(v2_accuracy.strip("%")) / 100
                diff = v2_value - v1_value
                diff_str = f"{diff:.2%}"
                
                # Add a +/- sign to show improvement/regression
                if diff > 0:
                    diff_str = f"+{diff_str}"
                
                print(f"{field:<15} | {v1_accuracy:<15} | {v2_accuracy:<15} | {diff_str:<15}")

def compare_by_field(test_file: str) -> None:
    """Compare performance of V0.1 and V0.2 on a specific test file."""
    # Create results directories if they don't exist
    os.makedirs("results/V0_1", exist_ok=True)
    os.makedirs("results/V0_2", exist_ok=True)
    
    # Run evaluations for both versions
    print("Running evaluation with V0.1...")
    subprocess.run([sys.executable, "evaluate_security_predictions.py", test_file, "V0.1"])
    
    print("\nRunning evaluation with V0.2...")
    subprocess.run([sys.executable, "evaluate_security_predictions.py", test_file, "V0.2"])
    
    # Read the results
    v1_results = read_csv_file("results/V0_1/summary_metrics.csv")
    v2_results = read_csv_file("results/V0_2/summary_metrics.csv")
    
    # Generate comparison report
    generate_comparison_report(v1_results, v2_results)
    
    # Write comparison results to a file
    with open("results/version_comparison.txt", "w") as f:
        f.write("PROMPT SECURITY AGENT VERSION COMPARISON\n\n")
        f.write(f"{'Metric':<15} | {'V0.1 Accuracy':<15} | {'V0.2 Accuracy':<15} | {'Difference':<15}\n")
        f.write("-" * 65 + "\n")
        
        for v1_row in v1_results:
            for v2_row in v2_results:
                if v1_row["Field"] == v2_row["Field"]:
                    field = v1_row["Field"]
                    v1_accuracy = v1_row["Accuracy"] 
                    v2_accuracy = v2_row["Accuracy"]
                    
                    # Extract numeric values from percentage strings
                    v1_value = float(v1_accuracy.strip("%")) / 100
                    v2_value = float(v2_accuracy.strip("%")) / 100
                    diff = v2_value - v1_value
                    diff_str = f"{diff:.2%}"
                    
                    # Add a +/- sign to show improvement/regression
                    if diff > 0:
                        diff_str = f"+{diff_str}"
                    
                    f.write(f"{field:<15} | {v1_accuracy:<15} | {v2_accuracy:<15} | {diff_str:<15}\n")
        
        # Add recommendations
        f.write("\n\nRECOMMENDATIONS:\n")
        
        # Compare is_safe accuracy
        v1_is_safe = float(next(row["Accuracy"].strip("%") for row in v1_results if row["Field"] == "is_safe")) / 100
        v2_is_safe = float(next(row["Accuracy"].strip("%") for row in v2_results if row["Field"] == "is_safe")) / 100
        
        # Compare threat_type accuracy
        v1_threat_type = float(next(row["Accuracy"].strip("%") for row in v1_results if row["Field"] == "threat_type")) / 100
        v2_threat_type = float(next(row["Accuracy"].strip("%") for row in v2_results if row["Field"] == "threat_type")) / 100
        
        if v2_is_safe > v1_is_safe and v2_threat_type > v1_threat_type:
            f.write("- V0.2 performs better on both safety and threat type classification.\n")
            f.write("- Recommended to use V0.2 for production.\n")
        elif v2_is_safe > v1_is_safe:
            f.write("- V0.2 performs better on safety classification but not on threat type.\n")
            f.write("- Consider using a hybrid approach combining V0.2's safety detection with improved threat type classification.\n")
        elif v2_threat_type > v1_threat_type:
            f.write("- V0.2 performs better on threat type classification but worse on safety.\n")
            f.write("- Consider tuning V0.2 to reduce false positives while maintaining improved threat type detection.\n")
        else:
            f.write("- V0.1 outperforms V0.2 on key metrics.\n")
            f.write("- Recommend investigating why the self-consistency approach in V0.2 is not improving performance.\n")
            f.write("- Consider reverting to V0.1 for now and exploring different improvements.\n")
    
    print(f"\nComparison report saved to results/version_comparison.txt")

def main():
    """Run the comparison with command line arguments."""
    # Set default test file
    test_file = "tests/agents/data/prompt_security_test_examples.json"
    
    # Allow overriding test file from command line
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    
    compare_by_field(test_file)

if __name__ == "__main__":
    main() 