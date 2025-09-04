#!/usr/bin/env python3
"""
Test runner for BaseWorker tests
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type, verbose=False, coverage=False):
    """Run tests of specified type"""
    
    # Get the backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    # Set up test command
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=backend", "--cov-report=html", "--cov-report=term"])
    
    # Add test directory based on type
    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "integration":
        cmd.append("tests/integration/")
    elif test_type == "performance":
        cmd.append("tests/performance/")
    elif test_type == "all":
        cmd.append("tests/")
    else:
        print(f"Unknown test type: {test_type}")
        return False
    
    # Run tests
    print(f"Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✅ {test_type.title()} tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {test_type.title()} tests failed with exit code {e.returncode}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run BaseWorker tests")
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "performance", "all"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path("tests/").exists():
        print("Error: tests/ directory not found. Please run from backend directory.")
        sys.exit(1)
    
    # Run tests
    success = run_tests(args.test_type, args.verbose, args.coverage)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

