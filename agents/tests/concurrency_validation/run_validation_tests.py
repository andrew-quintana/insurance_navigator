#!/usr/bin/env python3
"""
Test runner for Phase 1 Concurrency Validation
Addresses: FM-043 - Validate Phase 1 emergency stabilization fixes

This script runs comprehensive tests to validate that all Phase 1 concurrency
fixes are working correctly and meet the success criteria.
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def main():
    """Run Phase 1 validation tests."""
    print("🔍 Phase 1 Concurrency Validation - FM-043")
    print("=" * 60)
    
    # Get the test directory
    test_dir = Path(__file__).parent
    project_root = test_dir.parent.parent.parent
    
    print(f"Test directory: {test_dir}")
    print(f"Project root: {project_root}")
    
    # Ensure we're in the right location
    os.chdir(project_root)
    
    # Add project to Python path
    sys.path.insert(0, str(project_root))
    
    test_files = [
        "test_semaphore_controls.py",
        "test_database_pooling.py", 
        "test_async_timeout_patterns.py",
        "test_concurrency_monitoring.py"
    ]
    
    print("\n🧪 Running Phase 1 Validation Tests...")
    print("-" * 40)
    
    all_passed = True
    results = {}
    
    for test_file in test_files:
        test_path = test_dir / test_file
        component = test_file.replace("test_", "").replace(".py", "")
        
        print(f"\n📋 Testing {component}...")
        
        try:
            # Run pytest on the specific test file
            cmd = [
                sys.executable, 
                "-m", "pytest", 
                str(test_path),
                "-v",  # verbose
                "-s",  # don't capture output
                "--tb=short",  # shorter tracebacks
                "-x"  # stop on first failure
            ]
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout per test file
            )
            end_time = time.time()
            duration = end_time - start_time
            
            if result.returncode == 0:
                print(f"✅ {component} tests PASSED ({duration:.1f}s)")
                results[component] = "PASSED"
            else:
                print(f"❌ {component} tests FAILED ({duration:.1f}s)")
                print(f"STDOUT:\n{result.stdout}")
                print(f"STDERR:\n{result.stderr}")
                results[component] = "FAILED"
                all_passed = False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {component} tests TIMED OUT (>60s)")
            results[component] = "TIMEOUT"
            all_passed = False
        except Exception as e:
            print(f"💥 {component} tests ERROR: {e}")
            results[component] = "ERROR"
            all_passed = False
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 PHASE 1 VALIDATION RESULTS")
    print("=" * 60)
    
    for component, status in results.items():
        status_icon = {
            "PASSED": "✅",
            "FAILED": "❌", 
            "TIMEOUT": "⏰",
            "ERROR": "💥"
        }.get(status, "❓")
        
        print(f"{status_icon} {component:<25} {status}")
    
    print("-" * 60)
    
    if all_passed:
        print("🎉 ALL PHASE 1 VALIDATION TESTS PASSED!")
        print("\n✅ Phase 1 Success Criteria Validation:")
        print("   ✅ Semaphore controls limit concurrent operations")
        print("   ✅ Database connections use pooling within limits") 
        print("   ✅ No daemon threads - proper async patterns implemented")
        print("   ✅ Basic concurrency monitoring active with alerts")
        print("   ✅ All changes include proper error handling")
        print("\n🚀 Phase 1 emergency stabilization is COMPLETE and VALIDATED!")
        print("Ready to proceed to Phase 2 - Pattern Modernization")
        return 0
    else:
        print("🚨 SOME PHASE 1 VALIDATION TESTS FAILED!")
        print("\n❌ Phase 1 requires fixes before proceeding to Phase 2")
        print("Review the failed tests and fix the issues before continuing.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)