#!/usr/bin/env python3
"""
Phase C Test Execution Script
Executes Phase C UUID standardization cloud integration tests with environment-specific configurations.

Usage:
    python run_phase_c_tests.py [--environment ENV] [--test-suite SUITE] [--verbose]

Examples:
    python run_phase_c_tests.py --environment local
    python run_phase_c_tests.py --environment cloud --test-suite c1
    python run_phase_c_tests.py --environment production --verbose
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.phase_c_test_runner import PhaseCTestRunner


class PhaseCExecutor:
    """Executes Phase C tests with environment-specific configurations."""
    
    def __init__(self, environment: str = "local", verbose: bool = False):
        self.environment = environment
        self.verbose = verbose
        self.config = self._load_environment_config()
        
    def _load_environment_config(self) -> Dict[str, Any]:
        """Load environment-specific configuration."""
        configs = {
            "local": {
                "api_base_url": "http://localhost:8000",
                "rag_service_url": "http://localhost:8001",
                "chat_service_url": "http://localhost:8002",
                "database_url": os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/accessa_dev"),
                "environment": "development",
                "log_level": "DEBUG" if self.verbose else "INFO"
            },
            "cloud": {
                "api_base_url": os.getenv("API_BASE_URL", "***REMOVED***"),
                "rag_service_url": os.getenv("RAG_SERVICE_URL", "https://rag-service.onrender.com"),
                "chat_service_url": os.getenv("CHAT_SERVICE_URL", "https://chat-service.onrender.com"),
                "database_url": os.getenv("DATABASE_URL"),
                "environment": "production",
                "log_level": "INFO"
            },
            "production": {
                "api_base_url": os.getenv("API_BASE_URL"),
                "rag_service_url": os.getenv("RAG_SERVICE_URL"),
                "chat_service_url": os.getenv("CHAT_SERVICE_URL"),
                "database_url": os.getenv("DATABASE_URL"),
                "environment": "production",
                "log_level": "WARNING"
            }
        }
        
        config = configs.get(self.environment, configs["local"])
        
        # Validate required environment variables
        if self.environment in ["cloud", "production"]:
            required_vars = ["API_BASE_URL", "DATABASE_URL"]
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
                print("Please set the required environment variables before running tests.")
                sys.exit(1)
        
        return config
    
    def _setup_environment(self):
        """Set up environment variables for testing."""
        for key, value in self.config.items():
            if value:
                os.environ[key.upper()] = str(value)
        
        if self.verbose:
            print(f"🔧 Environment: {self.environment}")
            print(f"🔧 API Base URL: {self.config['api_base_url']}")
            print(f"🔧 Database URL: {'***' if self.config['database_url'] else 'Not set'}")
            print(f"🔧 Log Level: {self.config['log_level']}")
    
    async def run_tests(self, test_suite: Optional[str] = None):
        """Run Phase C tests."""
        print(f"🚀 Starting Phase C Tests - Environment: {self.environment.upper()}")
        print("=" * 80)
        
        # Set up environment
        self._setup_environment()
        
        # Create test runner
        runner = PhaseCTestRunner()
        
        try:
            if test_suite:
                # Run specific test suite
                await self._run_specific_test_suite(runner, test_suite)
            else:
                # Run all test suites
                await runner.run_all_phase_c_tests()
            
            # Generate reports
            runner.generate_phase3_integration_report()
            
            # Print final status
            self._print_final_status(runner.results)
            
            return runner.results
            
        except Exception as e:
            print(f"❌ Test execution failed: {str(e)}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return None
    
    async def _run_specific_test_suite(self, runner: PhaseCTestRunner, test_suite: str):
        """Run a specific test suite."""
        suite_mapping = {
            "c1": "run_test_suite_c1",
            "c1.1": "run_test_suite_c1",
            "c2": "run_test_suite_c2", 
            "c2.1": "run_test_suite_c2",
            "c3": "run_test_suite_c3",
            "c3.1": "run_test_suite_c3"
        }
        
        method_name = suite_mapping.get(test_suite.lower())
        if not method_name:
            print(f"❌ Unknown test suite: {test_suite}")
            print(f"Available suites: {', '.join(suite_mapping.keys())}")
            return
        
        method = getattr(runner, method_name)
        await method()
    
    def _print_final_status(self, results: Dict[str, Any]):
        """Print final test status."""
        print("\n" + "=" * 80)
        print("📊 FINAL TEST STATUS")
        print("=" * 80)
        
        summary = results["summary"]
        phase3_status = results["phase3_integration_status"]
        cloud_readiness = results["cloud_deployment_readiness"]
        
        print(f"Test Suites: {summary['total_test_suites']} total, {summary['passed_suites']} passed, {summary['failed_suites']} failed")
        print(f"Individual Tests: {summary['total_tests']} total, {summary['passed_tests']} passed, {summary['failed_tests']} failed")
        print(f"Critical Failures: {summary['critical_failures']}")
        
        print(f"\nPhase 3 Integration Status: {phase3_status}")
        print(f"Cloud Deployment Readiness: {cloud_readiness}")
        
        if summary["critical_failures"] > 0:
            print(f"\n🚨 CRITICAL ISSUES DETECTED")
            print("Phase 3 cloud deployment is BLOCKED until issues are resolved.")
            sys.exit(1)
        elif summary["failed_tests"] > 0:
            print(f"\n⚠️ NON-CRITICAL ISSUES DETECTED")
            print("Phase 3 deployment can proceed but issues should be monitored.")
            sys.exit(2)
        else:
            print(f"\n✅ ALL TESTS PASSED")
            print("Phase C UUID standardization is ready for Phase 3 cloud deployment.")
            sys.exit(0)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Phase C UUID Standardization Cloud Integration Testing")
    
    parser.add_argument(
        "--environment", 
        choices=["local", "cloud", "production"],
        default="local",
        help="Environment to run tests against (default: local)"
    )
    
    parser.add_argument(
        "--test-suite",
        choices=["c1", "c1.1", "c2", "c2.1", "c3", "c3.1"],
        help="Specific test suite to run (default: all suites)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--config-file",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Load configuration file if provided
    if args.config_file:
        config_path = Path(args.config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Update environment variables from config
                for key, value in config.get("environment", {}).items():
                    os.environ[key] = str(value)
        else:
            print(f"❌ Configuration file not found: {args.config_file}")
            sys.exit(1)
    
    # Create executor and run tests
    executor = PhaseCExecutor(
        environment=args.environment,
        verbose=args.verbose
    )
    
    # Run tests
    asyncio.run(executor.run_tests(test_suite=args.test_suite))


if __name__ == "__main__":
    main()
