#!/usr/bin/env python3
"""
Multi-Environment Test Runner for Insurance Navigator.

This script runs comprehensive unit tests across all environments
(development, staging, production) to ensure consistency.
"""

import sys
import os
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_tests_in_environment(environment: str) -> Dict[str, Any]:
    """Run comprehensive tests in a specific environment."""
    print(f"\n{'='*80}")
    print(f"RUNNING TESTS IN {environment.upper()} ENVIRONMENT")
    print(f"{'='*80}")
    
    # Set environment variables
    env_vars = os.environ.copy()
    env_vars['PYTHONPATH'] = str(project_root)
    env_vars['ENVIRONMENT'] = environment
    
    # Run comprehensive unit tests
    cmd = [sys.executable, 'comprehensive_unit_tests.py']
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            env=env_vars,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Parse results
        test_results = {
            "environment": environment,
            "timestamp": datetime.now().isoformat(),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
        # Try to extract test statistics from output
        if "Total Tests:" in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if "Total Tests:" in line:
                    test_results["total_tests"] = int(line.split(":")[1].strip())
                elif "Success Rate:" in line:
                    test_results["success_rate"] = float(line.split(":")[1].strip().replace('%', ''))
        
        return test_results
        
    except subprocess.TimeoutExpired:
        return {
            "environment": environment,
            "timestamp": datetime.now().isoformat(),
            "returncode": -1,
            "stdout": "",
            "stderr": "Test execution timeout after 5 minutes",
            "success": False,
            "error": "timeout"
        }
    except Exception as e:
        return {
            "environment": environment,
            "timestamp": datetime.now().isoformat(),
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
            "error": str(e)
        }

def run_coverage_analysis() -> Dict[str, Any]:
    """Run coverage analysis across all environments."""
    print(f"\n{'='*80}")
    print("RUNNING COVERAGE ANALYSIS")
    print(f"{'='*80}")
    
    cmd = [sys.executable, 'coverage_analysis.py']
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
            "error": str(e)
        }

def generate_environment_comparison_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate comparison report across environments."""
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "environments_tested": len(results),
        "environments": {},
        "summary": {
            "total_environments": len(results),
            "successful_environments": 0,
            "failed_environments": 0,
            "consistency_score": 0.0
        }
    }
    
    successful_envs = 0
    total_tests = 0
    success_rates = []
    
    for result in results:
        env_name = result["environment"]
        comparison["environments"][env_name] = {
            "success": result["success"],
            "total_tests": result.get("total_tests", 0),
            "success_rate": result.get("success_rate", 0.0),
            "returncode": result["returncode"],
            "has_errors": bool(result.get("stderr", "").strip())
        }
        
        if result["success"]:
            successful_envs += 1
            total_tests += result.get("total_tests", 0)
            success_rates.append(result.get("success_rate", 0.0))
    
    comparison["summary"]["successful_environments"] = successful_envs
    comparison["summary"]["failed_environments"] = len(results) - successful_envs
    comparison["summary"]["consistency_score"] = (successful_envs / len(results)) * 100 if results else 0
    comparison["summary"]["average_success_rate"] = sum(success_rates) / len(success_rates) if success_rates else 0
    comparison["summary"]["total_tests_across_environments"] = total_tests
    
    return comparison

def main():
    """Main execution function."""
    print("=" * 80)
    print("INSURANCE NAVIGATOR - MULTI-ENVIRONMENT TESTING")
    print("=" * 80)
    print(f"Project Root: {project_root}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Define environments to test
    environments = ["development", "staging", "production"]
    
    # Run tests in each environment
    all_results = []
    
    for env in environments:
        print(f"\n🧪 Testing {env} environment...")
        result = run_tests_in_environment(env)
        all_results.append(result)
        
        if result["success"]:
            print(f"✅ {env.upper()} - Tests passed successfully")
            if "total_tests" in result:
                print(f"   Tests: {result['total_tests']}, Success Rate: {result.get('success_rate', 0):.1f}%")
        else:
            print(f"❌ {env.upper()} - Tests failed")
            if result.get("stderr"):
                print(f"   Error: {result['stderr'][:200]}...")
    
    # Run coverage analysis
    print(f"\n📊 Running coverage analysis...")
    coverage_result = run_coverage_analysis()
    
    # Generate comparison report
    print(f"\n📈 Generating environment comparison report...")
    comparison_report = generate_environment_comparison_report(all_results)
    
    # Print summary
    print(f"\n{'='*80}")
    print("MULTI-ENVIRONMENT TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Environments Tested: {comparison_report['summary']['total_environments']}")
    print(f"Successful: {comparison_report['summary']['successful_environments']}")
    print(f"Failed: {comparison_report['summary']['failed_environments']}")
    print(f"Consistency Score: {comparison_report['summary']['consistency_score']:.1f}%")
    print(f"Average Success Rate: {comparison_report['summary']['average_success_rate']:.1f}%")
    print(f"Total Tests: {comparison_report['summary']['total_tests_across_environments']}")
    
    # Print detailed results by environment
    print(f"\n📋 DETAILED RESULTS BY ENVIRONMENT")
    print("-" * 60)
    for env_name, env_data in comparison_report["environments"].items():
        status = "✅ PASS" if env_data["success"] else "❌ FAIL"
        print(f"{status} {env_name.upper()}")
        print(f"   Tests: {env_data['total_tests']}")
        print(f"   Success Rate: {env_data['success_rate']:.1f}%")
        print(f"   Has Errors: {'Yes' if env_data['has_errors'] else 'No'}")
        print()
    
    # Save comprehensive results
    os.makedirs('test-results', exist_ok=True)
    
    # Save individual environment results
    with open('test-results/multi_environment_test_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "test_results": all_results,
            "coverage_analysis": coverage_result,
            "comparison_report": comparison_report
        }, f, indent=2)
    
    # Save comparison report
    with open('test-results/environment_comparison_report.json', 'w') as f:
        json.dump(comparison_report, f, indent=2)
    
    print(f"📄 Results saved to:")
    print(f"   - test-results/multi_environment_test_results.json")
    print(f"   - test-results/environment_comparison_report.json")
    
    # Determine overall success
    overall_success = comparison_report['summary']['consistency_score'] >= 80.0
    
    print(f"\n{'='*80}")
    if overall_success:
        print("🎉 MULTI-ENVIRONMENT TESTING COMPLETED SUCCESSFULLY")
        print("All environments are consistent and tests are passing!")
    else:
        print("⚠️  MULTI-ENVIRONMENT TESTING COMPLETED WITH ISSUES")
        print("Some environments have inconsistencies that need attention.")
    print(f"{'='*80}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
