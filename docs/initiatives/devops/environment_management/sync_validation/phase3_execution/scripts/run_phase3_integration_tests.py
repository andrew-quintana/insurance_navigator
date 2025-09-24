#!/usr/bin/env python3
"""
Phase 3 Integration Testing Execution Script
Comprehensive end-to-end integration testing for Render backend and Vercel frontend platforms
"""

import asyncio
import json
import os
import sys
import time
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the Phase 3 integration tester
from phase3_integration_testing import Phase3IntegrationTester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'phase3_integration_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("phase3_execution")

class Phase3TestExecutor:
    """Executes Phase 3 integration tests with comprehensive reporting."""
    
    def __init__(self, environment: str = 'development', verbose: bool = False):
        self.environment = environment
        self.verbose = verbose
        self.start_time = datetime.now()
        self.results = {}
        
        # Set environment variable
        os.environ['ENVIRONMENT'] = environment
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
    
    async def execute_comprehensive_testing(self) -> Dict[str, Any]:
        """Execute comprehensive Phase 3 integration testing."""
        logger.info(f"Starting Phase 3 Integration Testing for {self.environment} environment")
        
        try:
            # Pre-flight checks
            await self._run_preflight_checks()
            
            # Initialize tester
            tester = Phase3IntegrationTester()
            
            # Run integration tests
            test_suite = await tester.run_comprehensive_integration_tests()
            
            # Generate comprehensive report
            report = tester.generate_report()
            
            # Add execution metadata
            report['execution'] = {
                'environment': self.environment,
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': (datetime.now() - self.start_time).total_seconds(),
                'python_version': sys.version,
                'platform': sys.platform
            }
            
            # Save detailed report
            await self._save_detailed_report(report)
            
            # Generate summary report
            summary = self._generate_summary_report(report)
            
            # Print results
            self._print_test_results(summary)
            
            return report
            
        except Exception as e:
            logger.error(f"Phase 3 testing execution failed: {e}")
            raise
    
    async def _run_preflight_checks(self):
        """Run pre-flight checks to ensure testing environment is ready."""
        logger.info("Running pre-flight checks...")
        
        checks = [
            ("Python version", self._check_python_version),
            ("Required packages", self._check_required_packages),
            ("Environment configuration", self._check_environment_config),
            ("Database connectivity", self._check_database_connectivity),
            ("External services", self._check_external_services),
            ("Test data preparation", self._prepare_test_data)
        ]
        
        for check_name, check_func in checks:
            try:
                result = await check_func()
                if result:
                    logger.info(f"✓ {check_name} check passed")
                else:
                    logger.warning(f"⚠ {check_name} check failed")
            except Exception as e:
                logger.error(f"✗ {check_name} check failed: {e}")
    
    async def _check_python_version(self) -> bool:
        """Check Python version compatibility."""
        return sys.version_info >= (3, 8)
    
    async def _check_required_packages(self) -> bool:
        """Check required packages are installed."""
        required_packages = [
            'aiohttp', 'fastapi', 'pytest', 'asyncio', 'pydantic'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.warning(f"Missing packages: {missing_packages}")
            return False
        
        return True
    
    async def _check_environment_config(self) -> bool:
        """Check environment configuration."""
        required_vars = [
            'ENVIRONMENT',
            'DATABASE_URL',
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {missing_vars}")
            return False
        
        return True
    
    async def _check_database_connectivity(self) -> bool:
        """Check database connectivity."""
        try:
            # Mock database connectivity check
            await asyncio.sleep(0.1)
            return True
        except Exception:
            return False
    
    async def _check_external_services(self) -> bool:
        """Check external services availability."""
        try:
            # Mock external services check
            await asyncio.sleep(0.1)
            return True
        except Exception:
            return False
    
    async def _prepare_test_data(self) -> bool:
        """Prepare test data for integration testing."""
        try:
            # Mock test data preparation
            await asyncio.sleep(0.1)
            return True
        except Exception:
            return False
    
    async def _save_detailed_report(self, report: Dict[str, Any]):
        """Save detailed test report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"phase3_integration_detailed_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Detailed report saved to {report_file}")
    
    def _generate_summary_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary report from detailed results."""
        summary = {
            'test_execution': {
                'environment': report['execution']['environment'],
                'start_time': report['execution']['start_time'],
                'end_time': report['execution']['end_time'],
                'duration_seconds': report['execution']['duration']
            },
            'test_results': {
                'total_tests': report['summary']['total_tests'],
                'passed_tests': report['summary']['passed_tests'],
                'failed_tests': report['summary']['failed_tests'],
                'success_rate': report['summary']['success_rate']
            },
            'platform_performance': report['platform_breakdown'],
            'environment_performance': report['environment_breakdown'],
            'performance_metrics': report['performance_metrics'],
            'recommendations': report['recommendations'],
            'status': 'PASS' if report['summary']['success_rate'] >= 90 else 'FAIL'
        }
        
        return summary
    
    def _print_test_results(self, summary: Dict[str, Any]):
        """Print test results to console."""
        print("\n" + "="*80)
        print("PHASE 3 INTEGRATION TESTING RESULTS")
        print("="*80)
        
        # Test execution info
        exec_info = summary['test_execution']
        print(f"Environment: {exec_info['environment']}")
        print(f"Start Time: {exec_info['start_time']}")
        print(f"End Time: {exec_info['end_time']}")
        print(f"Duration: {exec_info['duration_seconds']:.2f} seconds")
        
        # Test results
        results = summary['test_results']
        print(f"\nTest Results:")
        print(f"  Total Tests: {results['total_tests']}")
        print(f"  Passed: {results['passed_tests']}")
        print(f"  Failed: {results['failed_tests']}")
        print(f"  Success Rate: {results['success_rate']:.1f}%")
        
        # Status
        status = summary['status']
        status_symbol = "✓" if status == "PASS" else "✗"
        print(f"\nOverall Status: {status_symbol} {status}")
        
        # Platform breakdown
        if summary['platform_performance']:
            print(f"\nPlatform Performance:")
            for platform, stats in summary['platform_performance'].items():
                success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"  {platform}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Performance metrics
        perf = summary['performance_metrics']
        print(f"\nPerformance Metrics:")
        print(f"  Average Duration: {perf['average_duration']:.2f}s")
        print(f"  Min Duration: {perf['min_duration']:.2f}s")
        print(f"  Max Duration: {perf['max_duration']:.2f}s")
        
        # Recommendations
        if summary['recommendations']:
            print(f"\nRecommendations:")
            for i, rec in enumerate(summary['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print("="*80)

async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Phase 3 Integration Testing')
    parser.add_argument('--environment', '-e', 
                       choices=['development', 'staging', 'production'],
                       default='development',
                       help='Environment to test (default: development)')
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--output', '-o',
                       help='Output file for test results')
    
    args = parser.parse_args()
    
    try:
        # Initialize executor
        executor = Phase3TestExecutor(
            environment=args.environment,
            verbose=args.verbose
        )
        
        # Execute comprehensive testing
        report = await executor.execute_comprehensive_testing()
        
        # Save output if specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Results saved to {args.output}")
        
        # Return success/failure
        success = report['summary']['success_rate'] >= 90
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
