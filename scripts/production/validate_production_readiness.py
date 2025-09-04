#!/usr/bin/env python3
"""
Phase 4 Production Readiness Validation Script

This script executes comprehensive production readiness validation including
monitoring setup, alerting systems, backup procedures, scaling functionality,
CI/CD integration, deployment procedures, and performance baselines.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.testing.cloud_deployment.phase4_production_validator import ProductionReadinessValidator
from backend.monitoring.alert_configuration import ProductionAlertConfiguration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionReadinessTestRunner:
    """Runs comprehensive production readiness validation"""
    
    def __init__(self):
        self.config = self._load_config()
        self.results = {}
        self.start_time = None
    
    def _load_config(self) -> Dict[str, str]:
        """Load configuration from environment variables"""
        config = {
            'vercel_url': os.getenv('VERCEL_URL', 'https://insurance-navigator.vercel.app'),
            'api_url': os.getenv('API_URL', 'https://insurance-navigator-api.onrender.com'),
            'worker_url': os.getenv('WORKER_URL', 'https://insurance-navigator-worker.onrender.com'),
            'supabase_url': os.getenv('SUPABASE_URL', 'https://znvwzkdblknkkztqyfnu.supabase.co'),
            'supabase_key': os.getenv('SUPABASE_ANON_KEY', ''),
            'render_token': os.getenv('RENDER_CLI_API_KEY', ''),
            'vercel_token': os.getenv('VERCEL_TOKEN', '')
        }
        
        logger.info("Configuration loaded:")
        for key, value in config.items():
            if 'key' in key.lower() or 'token' in key.lower():
                logger.info(f"  {key}: {'*' * 8 if value else 'NOT SET'}")
            else:
                logger.info(f"  {key}: {value}")
        
        return config
    
    async def run_alert_system_test(self) -> Dict[str, Any]:
        """Test alert system configuration and functionality"""
        logger.info("Testing alert system...")
        
        try:
            alert_config = ProductionAlertConfiguration()
            test_results = await alert_config.test_alert_system()
            
            logger.info(f"Alert system test completed: {test_results['alerts_triggered']} alerts triggered")
            return {
                'status': 'pass',
                'results': test_results,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Alert system test failed: {str(e)}")
            return {
                'status': 'fail',
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    async def run_production_readiness_validation(self) -> Dict[str, Any]:
        """Run comprehensive production readiness validation"""
        logger.info("Running production readiness validation...")
        
        try:
            async with ProductionReadinessValidator(self.config) as validator:
                results = await validator.run_comprehensive_validation()
                
                logger.info(f"Production readiness validation completed: {results['summary']['overall_status']}")
                return results
                
        except Exception as e:
            logger.error(f"Production readiness validation failed: {str(e)}")
            return {
                'error': str(e),
                'summary': {
                    'overall_status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now()
                }
            }
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete production readiness test suite"""
        logger.info("Starting comprehensive production readiness test suite...")
        self.start_time = time.time()
        
        try:
            # Test 1: Alert System Configuration
            logger.info("=" * 60)
            logger.info("TEST 1: Alert System Configuration")
            logger.info("=" * 60)
            self.results['alert_system_test'] = await self.run_alert_system_test()
            
            # Test 2: Production Readiness Validation
            logger.info("=" * 60)
            logger.info("TEST 2: Production Readiness Validation")
            logger.info("=" * 60)
            self.results['production_readiness'] = await self.run_production_readiness_validation()
            
            # Calculate overall results
            total_execution_time = time.time() - self.start_time
            
            # Determine overall status
            overall_status = "pass"
            total_tests = 0
            passed_tests = 0
            
            for test_name, test_result in self.results.items():
                total_tests += 1
                if test_result.get('status') == 'pass' or test_result.get('summary', {}).get('overall_status') == 'pass':
                    passed_tests += 1
                elif test_result.get('status') == 'fail' or test_result.get('summary', {}).get('overall_status') == 'fail':
                    overall_status = "fail"
            
            # Compile final summary
            final_summary = {
                'overall_status': overall_status,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                'total_execution_time': total_execution_time,
                'timestamp': datetime.now(),
                'test_results': self.results
            }
            
            self.results['final_summary'] = final_summary
            
            logger.info("=" * 60)
            logger.info("PRODUCTION READINESS TEST SUITE COMPLETED")
            logger.info("=" * 60)
            logger.info(f"Overall Status: {overall_status}")
            logger.info(f"Tests Passed: {passed_tests}/{total_tests} ({final_summary['success_rate']:.1f}%)")
            logger.info(f"Total Execution Time: {total_execution_time:.2f} seconds")
            
            return final_summary
            
        except Exception as e:
            logger.error(f"Comprehensive test suite failed: {str(e)}")
            return {
                'overall_status': 'error',
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def save_results(self, output_file: str = None):
        """Save test results to file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"phase4_production_readiness_results_{timestamp}.json"
        
        output_path = Path(project_root) / "scripts" / "cloud_deployment" / output_file
        
        try:
            with open(output_path, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")
            return None
    
    def print_summary(self):
        """Print a summary of test results"""
        if 'final_summary' not in self.results:
            logger.error("No test results available")
            return
        
        summary = self.results['final_summary']
        
        print("\n" + "=" * 80)
        print("PHASE 4 PRODUCTION READINESS VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"Tests Passed: {summary['passed_tests']}/{summary['total_tests']} ({summary['success_rate']:.1f}%)")
        print(f"Total Execution Time: {summary['total_execution_time']:.2f} seconds")
        print(f"Timestamp: {summary['timestamp']}")
        
        print("\n" + "-" * 80)
        print("DETAILED RESULTS:")
        print("-" * 80)
        
        for test_name, test_result in self.results.items():
            if test_name == 'final_summary':
                continue
            
            print(f"\n{test_name.upper().replace('_', ' ')}:")
            
            if 'status' in test_result:
                print(f"  Status: {test_result['status']}")
            elif 'summary' in test_result:
                print(f"  Status: {test_result['summary'].get('overall_status', 'unknown')}")
            
            if 'error' in test_result:
                print(f"  Error: {test_result['error']}")
            
            if 'results' in test_result:
                results = test_result['results']
                if 'alerts_triggered' in results:
                    print(f"  Alerts Triggered: {results['alerts_triggered']}")
                if 'active_alerts' in results:
                    print(f"  Active Alerts: {results['active_alerts']}")
        
        print("\n" + "=" * 80)

async def main():
    """Main execution function"""
    logger.info("Starting Phase 4 Production Readiness Validation")
    
    # Check if running in production environment
    if not os.getenv('SUPABASE_ANON_KEY'):
        logger.warning("SUPABASE_ANON_KEY not set - some tests may fail")
    
    # Initialize test runner
    test_runner = ProductionReadinessTestRunner()
    
    try:
        # Run comprehensive test suite
        summary = await test_runner.run_comprehensive_test_suite()
        
        # Save results
        output_file = test_runner.save_results()
        
        # Print summary
        test_runner.print_summary()
        
        # Exit with appropriate code
        if summary['overall_status'] == 'pass':
            logger.info("All tests passed - Production readiness validation successful")
            sys.exit(0)
        else:
            logger.error("Some tests failed - Production readiness validation unsuccessful")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
