#!/usr/bin/env python3
"""
Comprehensive unit test runner for Insurance Navigator.

This script executes all unit tests and generates coverage reports.
"""

import sys
import os
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

def run_tests():
    """Run comprehensive unit tests."""
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    os.environ['PYTHONPATH'] = str(project_root)
    
    print("=" * 80)
    print("INSURANCE NAVIGATOR - COMPREHENSIVE UNIT TESTING")
    print("=" * 80)
    print(f"Project Root: {project_root}")
    print(f"Python Path: {sys.path[0]}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Test results storage
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "environment": "development",
        "tests": {},
        "coverage": {},
        "summary": {}
    }
    
    # Define test modules
    test_modules = [
        {
            "name": "core_database",
            "file": "tests/unit/core/test_database.py",
            "description": "Core Database Module Tests"
        },
        {
            "name": "core_service_manager", 
            "file": "tests/unit/core/test_service_manager.py",
            "description": "Core Service Manager Tests"
        },
        {
            "name": "core_agent_integration",
            "file": "tests/unit/core/test_agent_integration.py", 
            "description": "Core Agent Integration Tests"
        }
    ]
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    # Run individual test modules
    for module in test_modules:
        print(f"\n🧪 Running {module['description']}...")
        print("-" * 60)
        
        # Run pytest with coverage for this module
        cmd = [
            sys.executable, '-m', 'pytest',
            module['file'],
            '-v',
            '--tb=short',
            '--asyncio-mode=auto',
            '--cov=core',
            '--cov-report=json',
            '--cov-report=term-missing',
            f'--junitxml=test-results/{module["name"]}_results.xml'
        ]
        
        try:
            # Create test-results directory
            os.makedirs('test-results', exist_ok=True)
            
            result = subprocess.run(
                cmd, 
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per module
            )
            
            # Parse results
            module_result = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": "N/A"  # Would need to parse from pytest output
            }
            
            if result.returncode == 0:
                print(f"✅ {module['description']} - PASSED")
                total_passed += 1
            else:
                print(f"❌ {module['description']} - FAILED")
                print(f"Error output: {result.stderr}")
                total_failed += 1
            
            test_results["tests"][module['name']] = module_result
            total_tests += 1
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {module['description']} - TIMEOUT")
            test_results["tests"][module['name']] = {
                "returncode": -1,
                "stdout": "",
                "stderr": "Test timeout after 5 minutes",
                "duration": "300s+"
            }
            total_failed += 1
            total_tests += 1
            
        except Exception as e:
            print(f"💥 {module['description']} - ERROR: {e}")
            test_results["tests"][module['name']] = {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": "N/A"
            }
            total_failed += 1
            total_tests += 1
    
    # Generate overall coverage report
    print(f"\n📊 Generating Overall Coverage Report...")
    print("-" * 60)
    
    try:
        coverage_cmd = [
            sys.executable, '-m', 'pytest',
            'tests/unit/',
            '--cov=core',
            '--cov-report=json:test-results/coverage.json',
            '--cov-report=html:test-results/coverage_html',
            '--cov-report=term-missing'
        ]
        
        coverage_result = subprocess.run(
            coverage_cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for full coverage
        )
        
        if coverage_result.returncode == 0:
            print("✅ Coverage report generated successfully")
            # Try to load coverage data
            try:
                with open('test-results/coverage.json', 'r') as f:
                    coverage_data = json.load(f)
                    test_results["coverage"] = coverage_data
            except Exception as e:
                print(f"⚠️  Could not load coverage data: {e}")
        else:
            print(f"❌ Coverage report failed: {coverage_result.stderr}")
            
    except Exception as e:
        print(f"💥 Coverage report error: {e}")
    
    # Summary
    test_results["summary"] = {
        "total_tests": total_tests,
        "passed": total_passed,
        "failed": total_failed,
        "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
    }
    
    print("\n" + "=" * 80)
    print("TEST EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Test Modules: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {test_results['summary']['success_rate']:.1f}%")
    print("=" * 80)
    
    # Save results
    with open('test-results/test_execution_report.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: test-results/test_execution_report.json")
    print(f"📊 Coverage report available at: test-results/coverage_html/index.html")
    
    return test_results

if __name__ == "__main__":
    results = run_tests()
    sys.exit(0 if results['summary']['failed'] == 0 else 1)
