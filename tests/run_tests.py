#!/usr/bin/env python3
import pytest
import sys
import os
from typing import List, Dict
import subprocess
import json
from datetime import datetime

class TestRunner:
    def __init__(self):
        self.test_levels = {
            'unit': ['tests/agents', 'tests/config'],
            'integration': ['tests/process_steps'],
            'system': ['tests/system'],
            'security': ['tests/security']
        }
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_tests(self, level: str = None) -> bool:
        """Run tests for specified level or all levels if none specified."""
        self.start_time = datetime.now()
        
        if level and level not in self.test_levels:
            print(f"Invalid test level: {level}")
            return False

        levels_to_run = [level] if level else self.test_levels.keys()
        all_passed = True

        for test_level in levels_to_run:
            print(f"\n=== Running {test_level.upper()} Tests ===")
            for test_dir in self.test_levels[test_level]:
                if not os.path.exists(test_dir):
                    print(f"Warning: Test directory {test_dir} does not exist")
                    continue
                
                result = self._run_pytest(test_dir)
                self.results[test_dir] = result
                if not result['passed']:
                    all_passed = False

        self.end_time = datetime.now()
        self._print_summary()
        return all_passed

    def _run_pytest(self, test_dir: str) -> Dict:
        """Run pytest for a specific directory and return results."""
        try:
            result = subprocess.run(
                ['pytest', test_dir, '-v', '--json-report'],
                capture_output=True,
                text=True
            )
            
            # Parse pytest results
            passed = result.returncode == 0
            output = result.stdout
            
            return {
                'passed': passed,
                'output': output,
                'return_code': result.returncode
            }
        except Exception as e:
            return {
                'passed': False,
                'output': str(e),
                'return_code': -1
            }

    def _print_summary(self):
        """Print test execution summary."""
        print("\n=== Test Execution Summary ===")
        print(f"Start Time: {self.start_time}")
        print(f"End Time: {self.end_time}")
        print(f"Duration: {self.end_time - self.start_time}")
        print("\nResults by Directory:")
        
        for test_dir, result in self.results.items():
            status = "PASSED" if result['passed'] else "FAILED"
            print(f"{test_dir}: {status}")

def main():
    runner = TestRunner()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        level = sys.argv[1]
        success = runner.run_tests(level)
    else:
        success = runner.run_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 