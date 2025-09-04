"""
Test runner for agent tests.

This script discovers and runs all tests in the agents test directory.
"""

import os
import sys
import unittest
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Disable logging for tests
logging.disable(logging.CRITICAL)

def run_agent_tests():
    """Run all agent tests."""
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests/agents', pattern='test_*.py')
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_agent_tests()) 