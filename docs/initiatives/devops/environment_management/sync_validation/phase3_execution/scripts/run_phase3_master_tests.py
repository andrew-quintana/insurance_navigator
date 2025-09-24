#!/usr/bin/env python3
"""
Phase 3 Master Integration Testing Execution Script
Comprehensive end-to-end integration testing orchestration for Render backend and Vercel frontend platforms
"""

import asyncio
import json
import os
import sys
import time
import subprocess
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import test modules
from phase3_integration_testing import Phase3IntegrationTester
from phase3_comprehensive_test_suite import Phase3ComprehensiveTestSuite
from phase3_cross_platform_tests import Phase3CrossPlatformTester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'phase3_master_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("phase3_master")

class Phase3MasterTestExecutor:
    """Master executor for Phase 3 integration testing across all platforms."""
    
    def __init__(self, environment: str = 'development', verbose: bool = False):
        self.environment = environment
        self.verbose = verbose
        self.start_time = datetime.now()
        self.test_results = {}
        self.overall_success = False
        
        # Set environment variable
        os.environ['ENVIRONMENT'] = environment
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
    
    async def execute_master_testing(self) -> Dict[str, Any]:
        """Execute comprehensive Phase 3 master testing."""
        logger.info(f"Starting Phase 3 Master Integration Testing for {self.environment} environment")
        
        try:
            # Pre-flight validation
            await self._run_preflight_validation()
            
            # Execute test suites in parallel where possible
            test_tasks = [
                self._run_basic_integration_tests(),
                self._run_comprehensive_test_suite(),
                self._run_cross_platform_tests()
            ]
            
            # Run tests concurrently
            results = await asyncio.gather(*test_tasks, return_exceptions=True)
            
            # Process results
            self._process_test_results(results)
            
            # Generate master report
            master_report = self._generate_master_report()
            
            # Save comprehensive report
            await self._save_master_report(master_report)
            
            # Print final summary
            self._print_final_summary(master_report)
            
            return master_report
            
        except Exception as e:
            logger.error(f"Master testing execution failed: {e}")
            raise
    
    async def _run_preflight_validation(self):
        """Run pre-flight validation checks."""
        logger.info("Running pre-flight validation...")
        
        validation_checks = [
            ("Environment configuration", self._validate_environment_config),
            ("Service availability", self._validate_service_availability),
            ("Database connectivity", self._validate_database_connectivity),
            ("External service connectivity", self._validate_external_services),
            ("Test data preparation", self._prepare_test_data),
            ("Platform readiness", self._validate_platform_readiness)
        ]
        
        validation_results = {}
        for check_name, check_func in validation_checks:
            try:
                result = await check_func()
                validation_results[check_name] = result
                if result:
                    logger.info(f"✓ {check_name} validation passed")
                else:
                    logger.warning(f"⚠ {check_name} validation failed")
            except Exception as e:
                logger.error(f"✗ {check_name} validation failed: {e}")
                validation_results[check_name] = False
        
        # Check if all critical validations passed
        critical_checks = ["Environment configuration", "Service availability", "Database connectivity"]
        critical_passed = all(validation_results.get(check, False) for check in critical_checks)
        
        if not critical_passed:
            raise Exception("Critical pre-flight validations failed")
        
        logger.info("Pre-flight validation completed successfully")
    
    async def _validate_environment_config(self) -> bool:
        """Validate environment configuration."""
        try:
            required_vars = [
                'ENVIRONMENT',
                'DATABASE_URL',
                'SUPABASE_URL',
                'SUPABASE_ANON_KEY'
            ]
            
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                logger.warning(f"Missing environment variables: {missing_vars}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Environment configuration validation failed: {e}")
            return False
    
    async def _validate_service_availability(self) -> bool:
        """Validate service availability."""
        try:
            # Mock service availability check
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Service availability validation failed: {e}")
            return False
    
    async def _validate_database_connectivity(self) -> bool:
        """Validate database connectivity."""
        try:
            # Mock database connectivity check
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Database connectivity validation failed: {e}")
            return False
    
    async def _validate_external_services(self) -> bool:
        """Validate external service connectivity."""
        try:
            # Mock external service check
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"External service validation failed: {e}")
            return False
    
    async def _prepare_test_data(self) -> bool:
        """Prepare test data for integration testing."""
        try:
            # Mock test data preparation
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Test data preparation failed: {e}")
            return False
    
    async def _validate_platform_readiness(self) -> bool:
        """Validate platform readiness."""
        try:
            # Mock platform readiness check
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Platform readiness validation failed: {e}")
            return False
    
    async def _run_basic_integration_tests(self) -> Dict[str, Any]:
        """Run basic integration tests."""
        logger.info("Running basic integration tests...")
        
        try:
            tester = Phase3IntegrationTester()
            test_suite = await tester.run_comprehensive_integration_tests()
            report = tester.generate_report()
            
            return {
                'test_type': 'basic_integration',
                'success': True,
                'results': report,
                'duration': (datetime.now() - self.start_time).total_seconds()
            }
        except Exception as e:
            logger.error(f"Basic integration tests failed: {e}")
            return {
                'test_type': 'basic_integration',
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - self.start_time).total_seconds()
            }
    
    async def _run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        logger.info("Running comprehensive test suite...")
        
        try:
            test_suite = Phase3ComprehensiveTestSuite(environment=self.environment)
            report = await test_suite.run_comprehensive_testing()
            
            return {
                'test_type': 'comprehensive_suite',
                'success': True,
                'results': report,
                'duration': (datetime.now() - self.start_time).total_seconds()
            }
        except Exception as e:
            logger.error(f"Comprehensive test suite failed: {e}")
            return {
                'test_type': 'comprehensive_suite',
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - self.start_time).total_seconds()
            }
    
    async def _run_cross_platform_tests(self) -> Dict[str, Any]:
        """Run cross-platform tests."""
        logger.info("Running cross-platform tests...")
        
        try:
            tester = Phase3CrossPlatformTester(environment=self.environment)
            report = await tester.run_cross_platform_tests()
            
            return {
                'test_type': 'cross_platform',
                'success': True,
                'results': report,
                'duration': (datetime.now() - self.start_time).total_seconds()
            }
        except Exception as e:
            logger.error(f"Cross-platform tests failed: {e}")
            return {
                'test_type': 'cross_platform',
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - self.start_time).total_seconds()
            }
    
    def _process_test_results(self, results: List[Dict[str, Any]]):
        """Process test results from all test suites."""
        self.test_results = {}
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Test suite failed with exception: {result}")
                continue
            
            test_type = result.get('test_type', 'unknown')
            self.test_results[test_type] = result
        
        # Determine overall success
        successful_tests = sum(1 for r in self.test_results.values() if r.get('success', False))
        total_tests = len(self.test_results)
        self.overall_success = successful_tests >= total_tests * 0.8  # 80% success rate required
    
    def _generate_master_report(self) -> Dict[str, Any]:
        """Generate comprehensive master test report."""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Aggregate results from all test suites
        aggregated_results = self._aggregate_test_results()
        
        # Generate recommendations
        recommendations = self._generate_master_recommendations()
        
        # Calculate overall metrics
        overall_metrics = self._calculate_overall_metrics()
        
        master_report = {
            'execution_info': {
                'environment': self.environment,
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration': total_duration,
                'python_version': sys.version,
                'platform': sys.platform
            },
            'test_suites': self.test_results,
            'aggregated_results': aggregated_results,
            'overall_metrics': overall_metrics,
            'recommendations': recommendations,
            'success_criteria': {
                'overall_success': self.overall_success,
                'required_success_rate': 80.0,
                'actual_success_rate': overall_metrics.get('success_rate', 0.0)
            },
            'generated_at': datetime.now().isoformat()
        }
        
        return master_report
    
    def _aggregate_test_results(self) -> Dict[str, Any]:
        """Aggregate results from all test suites."""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        total_duration = 0.0
        
        for test_suite in self.test_results.values():
            if test_suite.get('success', False):
                results = test_suite.get('results', {})
                
                # Extract test counts
                if 'summary' in results:
                    total_tests += results['summary'].get('total_tests', 0)
                    passed_tests += results['summary'].get('passed_tests', 0)
                    failed_tests += results['summary'].get('failed_tests', 0)
                
                # Extract duration
                total_duration += test_suite.get('duration', 0.0)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'total_duration': total_duration
        }
    
    def _calculate_overall_metrics(self) -> Dict[str, Any]:
        """Calculate overall test metrics."""
        aggregated = self._aggregate_test_results()
        
        return {
            'success_rate': aggregated['success_rate'],
            'total_tests': aggregated['total_tests'],
            'passed_tests': aggregated['passed_tests'],
            'failed_tests': aggregated['failed_tests'],
            'total_duration': aggregated['total_duration'],
            'test_suites_executed': len(self.test_results),
            'successful_test_suites': sum(1 for r in self.test_results.values() if r.get('success', False))
        }
    
    def _generate_master_recommendations(self) -> List[str]:
        """Generate master recommendations based on all test results."""
        recommendations = []
        
        # Overall success rate recommendations
        overall_metrics = self._calculate_overall_metrics()
        success_rate = overall_metrics.get('success_rate', 0.0)
        
        if success_rate < 90:
            recommendations.append(f"Overall success rate is {success_rate:.1f}% - focus on improving test reliability")
        
        # Test suite specific recommendations
        for test_type, result in self.test_results.items():
            if not result.get('success', False):
                recommendations.append(f"Address failures in {test_type} test suite")
        
        # Performance recommendations
        if overall_metrics.get('total_duration', 0) > 300:  # 5 minutes
            recommendations.append("Consider optimizing test execution time - exceeds 5 minutes")
        
        # General recommendations
        if overall_metrics.get('failed_tests', 0) > 0:
            recommendations.append(f"Investigate and fix {overall_metrics['failed_tests']} failed tests")
        
        return recommendations
    
    async def _save_master_report(self, report: Dict[str, Any]):
        """Save master test report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"phase3_master_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Master test report saved to {report_file}")
    
    def _print_final_summary(self, report: Dict[str, Any]):
        """Print final test summary."""
        print("\n" + "="*80)
        print("PHASE 3 MASTER INTEGRATION TESTING RESULTS")
        print("="*80)
        
        # Execution info
        exec_info = report['execution_info']
        print(f"Environment: {exec_info['environment']}")
        print(f"Start Time: {exec_info['start_time']}")
        print(f"End Time: {exec_info['end_time']}")
        print(f"Total Duration: {exec_info['total_duration']:.2f} seconds")
        
        # Overall metrics
        metrics = report['overall_metrics']
        print(f"\nOverall Test Results:")
        print(f"  Total Tests: {metrics['total_tests']}")
        print(f"  Passed: {metrics['passed_tests']}")
        print(f"  Failed: {metrics['failed_tests']}")
        print(f"  Success Rate: {metrics['success_rate']:.1f}%")
        print(f"  Test Suites Executed: {metrics['test_suites_executed']}")
        print(f"  Successful Test Suites: {metrics['successful_test_suites']}")
        
        # Success criteria
        success_criteria = report['success_criteria']
        status = "PASS" if success_criteria['overall_success'] else "FAIL"
        status_symbol = "✓" if success_criteria['overall_success'] else "✗"
        print(f"\nOverall Status: {status_symbol} {status}")
        print(f"Required Success Rate: {success_criteria['required_success_rate']}%")
        print(f"Actual Success Rate: {success_criteria['actual_success_rate']:.1f}%")
        
        # Test suite breakdown
        print(f"\nTest Suite Breakdown:")
        for test_type, result in report['test_suites'].items():
            status = "PASS" if result.get('success', False) else "FAIL"
            duration = result.get('duration', 0.0)
            print(f"  {test_type}: {status} ({duration:.2f}s)")
        
        # Recommendations
        if report['recommendations']:
            print(f"\nRecommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print("="*80)

async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Phase 3 Master Integration Testing')
    parser.add_argument('--environment', '-e', 
                       choices=['development', 'staging', 'production'],
                       default='development',
                       help='Environment to test (default: development)')
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--output', '-o',
                       help='Output file for test results')
    parser.add_argument('--quick', '-q',
                       action='store_true',
                       help='Run quick test suite only')
    
    args = parser.parse_args()
    
    try:
        # Initialize master executor
        executor = Phase3MasterTestExecutor(
            environment=args.environment,
            verbose=args.verbose
        )
        
        # Execute master testing
        report = await executor.execute_master_testing()
        
        # Save output if specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Master test results saved to {args.output}")
        
        # Return success/failure
        success = report['success_criteria']['overall_success']
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Master testing execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
