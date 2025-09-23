#!/usr/bin/env python3
"""
Unit test runner for Insurance Navigator.

This script runs unit tests with proper Python path configuration.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Run unit tests with proper configuration."""
    # Add project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Set environment variables
    os.environ['PYTHONPATH'] = str(project_root)
    
    # Run pytest with proper configuration
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/unit/core/test_database.py',
        '-v',
        '--tb=short',
        '--asyncio-mode=auto'
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    print(f"Python path: {sys.path[0]}")
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
