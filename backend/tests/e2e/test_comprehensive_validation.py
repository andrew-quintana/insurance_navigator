#!/usr/bin/env python3
"""
Comprehensive Validation Test Runner

This module orchestrates all Phase 4 testing modules and provides a unified
interface for running the complete comprehensive testing suite.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pytest
from dataclasses import dataclass, asdict

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.shared.config import WorkerConfig
from backend.shared.db.connection import DatabaseManager
from backend.shared.storage.storage_manager import StorageManager
from backend.shared.external.llamaparse_client import LlamaParseClient
from backend.shared.external.openai_client import OpenAIClient
from backend.workers.base_worker import BaseWorker

# Import test modules
from .test_complete_pipeline import PipelineValidator
from .test_failure_scenarios import FailureScenarioValidator
from .test_performance_validation import PerformanceValidator
from .test_security_validation import SecurityValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ComprehensiveTestResult:
    """Result of comprehensive testing"""
    test_suite: str
    status: str  # 'passed', 'failed', 'skipped'
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    success_rate: float
    duration_seconds: float
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class ComprehensiveValidator:
    """
    Comprehensive validation orchestrator
    
    Runs all Phase 4 testing modules and provides unified results.
    """
    
    def __init__(self, config: WorkerConfig):
        """Initialize validator with configuration"""
        self.config = config
        self.db = DatabaseManager(config.database_url)
        self.storage = StorageManager(config.supabase_url, config.supabase_service_role_key)
        self.llamaparse = LlamaParseClient(config.llamaparse_api_url, config.llamaparse_api_key)
        self.openai = OpenAIClient(config.openai_api_url, config.openai_api_key)
        self.worker = BaseWorker(config)
        
        # Test results tracking
        self.test_results: List[ComprehensiveTestResult] = []
        
        # Test validators
        self.pipeline_validator = PipelineValidator(config)
        self.failure_validator = FailureScenarioValidator(config)
        self.performance_validator = PerformanceValidator(config)
        self.security_validator = SecurityValidator(config)
        
        logger.info("Initialized ComprehensiveValidator")
    
    async def initialize(self):
        """Initialize all components for testing"""
        try:
            await self.db.initialize()
            await self.storage.initialize()
            await self.llamaparse.initialize()
            await self.openai.initialize()
            await self.worker._initialize_components()
            logger.info("✅ All components initialized successfully")
        except Exception as e:
            logger.error(f"❌ Component initialization failed: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup all components after testing"""
        try:
            await self.db.close()
            await self.storage.close()
            await self.llamaparse.close()
            await self.openai.close()
            await self.worker._cleanup_components()
            logger.info("✅ All components cleaned up successfully")
        except Exception as e:
            logger.error(f"❌ Component cleanup failed: {e}")
    
    async def run_pipeline_validation(self) -> ComprehensiveTestResult:
        """Run complete pipeline validation tests"""
        test_suite = "Complete Pipeline Validation"
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Starting {test_suite}")
            
            # Run pipeline tests
            results = await self.pipeline_validator.run_all_tests()
            
            # Calculate metrics
            total_tests = len(results)
            passed_tests = len([r for r in results if r.status == 'passed'])
            failed_tests = len([r for r in results if r.status == 'failed'])
            skipped_tests = len([r for r in results if r.status == 'skipped'])
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            duration = time.time() - start_time
            
            # Create result
            result = ComprehensiveTestResult(
                test_suite=test_suite,
                status='passed' if failed_tests == 0 else 'failed',
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                skipped_tests=skipped_tests,
                success_rate=success_rate,
                duration_seconds=duration,
                details={
                    'pipeline_results': [r.to_dict() for r in results],
                    'pipeline_summary': {
                        'total_jobs_processed': sum(1 for r in results if r.status == 'passed'),
                        'processing_stages_validated': ['upload', 'parsing', 'chunking', 'embedding', 'storage'],
                        'data_integrity_verified': True if failed_tests == 0 else False
                    }
                }
            )
            
            logger.info(f"✅ {test_suite} completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ {test_suite} failed: {e}")
            
            return ComprehensiveTestResult(
                test_suite=test_suite,
                status='failed',
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                success_rate=0.0,
                duration_seconds=duration,
                details={'error': str(e)}
            )
    
    async def run_failure_scenario_validation(self) -> ComprehensiveTestResult:
        """Run failure scenario validation tests"""
        test_suite = "Failure Scenario Validation"
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Starting {test_suite}")
            
            # Run failure scenario tests
            results = await self.failure_validator.run_all_tests()
            
            # Calculate metrics
            total_tests = len(results)
            passed_tests = len([r for r in results if r.status == 'passed'])
            failed_tests = len([r for r in results if r.status == 'failed'])
            skipped_tests = len([r for r in results if r.status == 'skipped'])
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            duration = time.time() - start_time
            
            # Create result
            result = ComprehensiveTestResult(
                test_suite=test_suite,
                status='passed' if failed_tests == 0 else 'failed',
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                skipped_tests=skipped_tests,
                success_rate=success_rate,
                duration_seconds=duration,
                details={
                    'failure_scenario_results': [r.to_dict() for r in results],
                    'failure_scenario_summary': {
                        'resilience_tests_passed': passed_tests,
                        'error_recovery_validated': True if failed_tests == 0 else False,
                        'failure_modes_covered': ['network', 'database', 'storage', 'processing', 'timeout']
                    }
                }
            )
            
            logger.info(f"✅ {test_suite} completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ {test_suite} failed: {e}")
            
            return ComprehensiveTestResult(
                test_suite=test_suite,
                status='failed',
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                success_rate=0.0,
                duration_seconds=duration,
                details={'error': str(e)}
            )
    
    async def run_performance_validation(self) -> ComprehensiveTestResult:
        """Run performance validation tests"""
        test_suite = "Performance Validation"
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Starting {test_suite}")
            
            # Run performance tests
            results = await self.performance_validator.run_all_tests()
            
            # Calculate metrics
            total_tests = len(results)
            passed_tests = len([r for r in results if r.status == 'passed'])
            failed_tests = len([r for r in results if r.status == 'failed'])
            skipped_tests = len([r for r in results if r.status == 'skipped'])
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            duration = time.time() - start_time
            
            # Calculate performance metrics
            if passed_tests > 0:
                avg_throughput = sum(r.throughput for r in results if r.status == 'passed') / passed_tests
                avg_latency = sum(r.latency_p50 for r in results if r.status == 'passed') / passed_tests
                scalability_factor = sum(r.scalability_factor for r in results if r.status == 'passed' and r.scalability_factor) / passed_tests
            else:
                avg_throughput = 0.0
                avg_latency = 0.0
                scalability_factor = 0.0
            
            # Create result
            result = ComprehensiveTestResult(
                test_suite=test_suite,
                status='passed' if failed_tests == 0 else 'failed',
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                skipped_tests=skipped_tests,
                success_rate=success_rate,
                duration_seconds=duration,
                details={
                    'performance_results': [r.to_dict() for r in results],
                    'performance_summary': {
                        'average_throughput': avg_throughput,
                        'average_latency': avg_latency,
                        'scalability_factor': scalability_factor,
                        'performance_targets_met': True if failed_tests == 0 else False
                    }
                }
            )
            
            logger.info(f"✅ {test_suite} completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            logger.info(f"  Average Throughput: {avg_throughput:.2f} docs/sec")
            logger.info(f"  Average Latency: {avg_latency:.2f}s")
            logger.info(f"  Scalability Factor: {scalability_factor:.2f}x")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ {test_suite} failed: {e}")
            
            return ComprehensiveTestResult(
                test_suite=test_suite,
                status='failed',
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                success_rate=0.0,
                duration_seconds=duration,
                details={'error': str(e)}
            )
    
    async def run_security_validation(self) -> ComprehensiveTestResult:
        """Run security validation tests"""
        test_suite = "Security Validation"
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Starting {test_suite}")
            
            # Run security tests
            results = await self.security_validator.run_all_tests()
            
            # Calculate metrics
            total_tests = len(results)
            passed_tests = len([r for r in results if r.status == 'passed'])
            failed_tests = len([r for r in results if r.status == 'failed'])
            skipped_tests = len([r for r in results if r.status == 'skipped'])
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            duration = time.time() - start_time
            
            # Calculate security metrics
            if failed_tests > 0:
                critical_vulnerabilities = len([r for r in results if r.status == 'failed' and r.severity == 'critical'])
                high_vulnerabilities = len([r for r in results if r.status == 'failed' and r.severity == 'high'])
                medium_vulnerabilities = len([r for r in results if r.status == 'failed' and r.severity == 'medium'])
                low_vulnerabilities = len([r for r in results if r.status == 'failed' and r.severity == 'low'])
            else:
                critical_vulnerabilities = 0
                high_vulnerabilities = 0
                medium_vulnerabilities = 0
                low_vulnerabilities = 0
            
            # Create result
            result = ComprehensiveTestResult(
                test_suite=test_suite,
                status='passed' if failed_tests == 0 else 'failed',
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                skipped_tests=skipped_tests,
                success_rate=success_rate,
                duration_seconds=duration,
                details={
                    'security_results': [r.to_dict() for r in results],
                    'security_summary': {
                        'critical_vulnerabilities': critical_vulnerabilities,
                        'high_vulnerabilities': high_vulnerabilities,
                        'medium_vulnerabilities': medium_vulnerabilities,
                        'low_vulnerabilities': low_vulnerabilities,
                        'security_posture': 'secure' if failed_tests == 0 else 'vulnerable'
                    }
                }
            )
            
            logger.info(f"✅ {test_suite} completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            if failed_tests > 0:
                logger.info(f"  Critical: {critical_vulnerabilities}, High: {high_vulnerabilities}")
                logger.info(f"  Medium: {medium_vulnerabilities}, Low: {low_vulnerabilities}")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ {test_suite} failed: {e}")
            
            return ComprehensiveTestResult(
                test_suite=test_suite,
                status='failed',
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                success_rate=0.0,
                duration_seconds=duration,
                details={'error': str(e)}
            )
    
    async def run_all_validations(self) -> List[ComprehensiveTestResult]:
        """Run all validation test suites"""
        logger.info("🚀 Starting comprehensive Phase 4 validation")
        logger.info("=" * 60)
        
        try:
            await self.initialize()
            
            # Run all test suites
            test_suites = [
                self.run_pipeline_validation(),
                self.run_failure_scenario_validation(),
                self.run_performance_validation(),
                self.run_security_validation()
            ]
            
            results = await asyncio.gather(*test_suites, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Test suite {i} failed with exception: {result}")
                    # Create failed result
                    failed_result = ComprehensiveTestResult(
                        test_suite=f"Test Suite {i}",
                        status='failed',
                        total_tests=0,
                        passed_tests=0,
                        failed_tests=1,
                        skipped_tests=0,
                        success_rate=0.0,
                        duration_seconds=0,
                        details={'error': str(result)}
                    )
                    self.test_results.append(failed_result)
                else:
                    self.test_results.append(result)
            
            # Generate comprehensive summary
            await self._generate_comprehensive_summary()
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"Comprehensive validation failed: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def _generate_comprehensive_summary(self):
        """Generate comprehensive test summary"""
        total_suites = len(self.test_results)
        passed_suites = len([r for r in self.test_results if r.status == 'passed'])
        failed_suites = len([r for r in self.test_results if r.status == 'failed'])
        
        total_tests = sum(r.total_tests for r in self.test_results)
        total_passed = sum(r.passed_tests for r in self.test_results)
        total_failed = sum(r.failed_tests for r in self.test_results)
        total_skipped = sum(r.skipped_tests for r in self.test_results)
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        suite_success_rate = (passed_suites / total_suites * 100) if total_suites > 0 else 0
        
        total_duration = sum(r.duration_seconds for r in self.test_results)
        
        logger.info("")
        logger.info("🎯 Comprehensive Phase 4 Validation Summary")
        logger.info("=" * 60)
        logger.info(f"Test Suites: {total_suites}")
        logger.info(f"  Passed: {passed_suites}")
        logger.info(f"  Failed: {failed_suites}")
        logger.info(f"  Suite Success Rate: {suite_success_rate:.1f}%")
        logger.info("")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"  Passed: {total_passed}")
        logger.info(f"  Failed: {total_failed}")
        logger.info(f"  Skipped: {total_skipped}")
        logger.info(f"  Overall Success Rate: {overall_success_rate:.1f}%")
        logger.info("")
        logger.info(f"Total Duration: {total_duration:.2f}s")
        logger.info("")
        
        # Test suite details
        logger.info("📊 Test Suite Details")
        logger.info("-" * 40)
        
        for result in self.test_results:
            status_icon = "✅" if result.status == 'passed' else "❌"
            logger.info(f"{status_icon} {result.test_suite}")
            logger.info(f"    Status: {result.status}")
            logger.info(f"    Tests: {result.passed_tests}/{result.total_tests} passed ({result.success_rate:.1f}%)")
            logger.info(f"    Duration: {result.duration_seconds:.2f}s")
            
            # Add specific details based on test suite
            if result.details:
                if 'pipeline_summary' in result.details:
                    summary = result.details['pipeline_summary']
                    logger.info(f"    Pipeline: {summary['total_jobs_processed']} jobs processed")
                    logger.info(f"    Data Integrity: {'✅' if summary['data_integrity_verified'] else '❌'}")
                
                elif 'failure_scenario_summary' in result.details:
                    summary = result.details['failure_scenario_summary']
                    logger.info(f"    Resilience: {summary['resilience_tests_passed']} tests passed")
                    logger.info(f"    Error Recovery: {'✅' if summary['error_recovery_validated'] else '❌'}")
                
                elif 'performance_summary' in result.details:
                    summary = result.details['performance_summary']
                    logger.info(f"    Throughput: {summary['average_throughput']:.2f} docs/sec")
                    logger.info(f"    Latency: {summary['average_latency']:.2f}s")
                    logger.info(f"    Scalability: {summary['scalability_factor']:.2f}x")
                
                elif 'security_summary' in result.details:
                    summary = result.details['security_summary']
                    logger.info(f"    Security Posture: {summary['security_posture']}")
                    if summary['critical_vulnerabilities'] > 0 or summary['high_vulnerabilities'] > 0:
                        logger.info(f"    Critical: {summary['critical_vulnerabilities']}, High: {summary['high_vulnerabilities']}")
            
            logger.info("")
        
        # Overall assessment
        logger.info("🎯 Overall Assessment")
        logger.info("-" * 40)
        
        if overall_success_rate >= 95:
            logger.info("🟢 EXCELLENT: System ready for deployment")
        elif overall_success_rate >= 90:
            logger.info("🟡 GOOD: Minor issues to address before deployment")
        elif overall_success_rate >= 80:
            logger.info("🟠 FAIR: Significant issues to resolve before deployment")
        else:
            logger.info("🔴 POOR: Major issues must be resolved before deployment")
        
        if failed_suites > 0:
            logger.info(f"⚠️  {failed_suites} test suite(s) failed - review required")
        
        if total_failed > 0:
            logger.info(f"⚠️  {total_failed} individual test(s) failed - investigation required")
        
        logger.info("")
        logger.info("📋 Next Steps:")
        if overall_success_rate >= 95:
            logger.info("  ✅ Proceed to Phase 5: Deployment Preparation")
        else:
            logger.info("  🔧 Address failed tests before proceeding")
            logger.info("  📝 Review test results and implement fixes")
            logger.info("  🔄 Re-run validation after fixes")
        
        logger.info("")


async def main():
    """Main function for running comprehensive validation"""
    # Load configuration
    config = WorkerConfig(
        database_url="postgresql://postgres:postgres@localhost:5432/accessa_dev",
        supabase_url="http://localhost:5000",
        supabase_anon_key="***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
        supabase_service_role_key="***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nk0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
        llamaparse_api_url="http://localhost:8001",
        llamaparse_api_key="test_key",
        openai_api_url="http://localhost:8002",
        openai_api_key="test_key",
        openai_model="text-embedding-3-small"
    )
    
    # Create validator and run tests
    validator = ComprehensiveValidator(config)
    
    try:
        results = await validator.run_all_validations()
        
        # Save results to file
        results_file = "comprehensive_validation_results.json"
        with open(results_file, 'w') as f:
            json.dump([r.to_dict() for r in results], f, indent=2)
        
        logger.info(f"Comprehensive validation results saved to {results_file}")
        
        # Exit with appropriate code
        failed_suites = len([r for r in results if r.status == 'failed'])
        if failed_suites > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Comprehensive validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
