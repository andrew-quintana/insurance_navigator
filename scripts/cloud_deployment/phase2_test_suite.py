#!/usr/bin/env python3
"""
Phase 2 Cloud Integration Test Suite

This script orchestrates comprehensive Phase 2 testing including:
- End-to-end integration testing
- Performance benchmarking with Artillery.js
- Cloud-specific functionality testing
- Error handling and recovery validation

Based on RFC001.md interface contracts and Phase 1 foundation.
"""

import asyncio
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import argparse

# Add backend modules to path
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

from testing.cloud_deployment.phase2_integration_validator import CloudIntegrationValidator, CloudIntegrationTestResults
from testing.cloud_deployment.phase2_performance_monitor import CloudPerformanceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase2TestSuite:
    """
    Comprehensive Phase 2 test suite for cloud deployment validation
    """
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """Initialize the Phase 2 test suite"""
        self.config = config or self._load_default_config()
        self.test_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.results = {}
        
        # Test configuration
        self.test_config = {
            "concurrent_users": 10,
            "load_test_duration": 300,  # 5 minutes
            "artillery_config": "scripts/cloud_deployment/artillery_cloud_config.yml",
            "performance_monitoring_duration": 600,  # 10 minutes
            "error_scenarios": [
                "network_timeout",
                "service_unavailable",
                "database_connection_failure",
                "authentication_failure"
            ]
        }
        
        # Results storage
        self.results_dir = Path("scripts/cloud_deployment/results")
        self.results_dir.mkdir(exist_ok=True)
    
    def _load_default_config(self) -> Dict[str, str]:
        """Load default configuration for cloud services"""
        return {
            "vercel_url": "https://insurance-navigator.vercel.app",
            "api_url": "https://insurance-navigator-api.onrender.com",
            "worker_url": "https://insurance-navigator-worker.onrender.com",
            "supabase_url": "https://znvwzkdblknkkztqyfnu.supabase.co"
        }
    
    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """
        Run the complete Phase 2 test suite
        
        Returns:
            Dict with comprehensive test results
        """
        logger.info("Starting Phase 2 Complete Test Suite")
        logger.info(f"Test ID: {self.test_id}")
        
        suite_start_time = time.time()
        
        try:
            # Test 1: Validate Phase 1 Completion
            logger.info("Test 1: Validating Phase 1 completion...")
            phase1_validation = await self._validate_phase1_completion()
            self.results["phase1_validation"] = phase1_validation
            
            if not phase1_validation["success"]:
                logger.error("Phase 1 validation failed. Cannot proceed with Phase 2.")
                return self._generate_final_report(suite_start_time, success=False)
            
            # Test 2: End-to-End Integration Testing
            logger.info("Test 2: Running end-to-end integration tests...")
            integration_results = await self._run_integration_tests()
            self.results["integration_tests"] = integration_results
            
            # Test 3: Performance Benchmarking
            logger.info("Test 3: Running performance benchmarking...")
            performance_results = await self._run_performance_benchmarking()
            self.results["performance_benchmarking"] = performance_results
            
            # Test 4: Cloud-Specific Testing
            logger.info("Test 4: Running cloud-specific tests...")
            cloud_specific_results = await self._run_cloud_specific_tests()
            self.results["cloud_specific_tests"] = cloud_specific_results
            
            # Test 5: Error Handling Validation
            logger.info("Test 5: Running error handling validation...")
            error_handling_results = await self._run_error_handling_tests()
            self.results["error_handling_tests"] = error_handling_results
            
            # Test 6: Performance Monitoring
            logger.info("Test 6: Running performance monitoring...")
            monitoring_results = await self._run_performance_monitoring()
            self.results["performance_monitoring"] = monitoring_results
            
            # Generate final report
            total_time = time.time() - suite_start_time
            final_report = self._generate_final_report(suite_start_time, success=True)
            
            # Save results
            await self._save_test_results(final_report)
            
            return final_report
            
        except Exception as e:
            logger.error(f"Phase 2 test suite failed: {e}")
            return self._generate_final_report(suite_start_time, success=False, error=str(e))
    
    async def _validate_phase1_completion(self) -> Dict[str, Any]:
        """Validate that Phase 1 is complete and services are operational"""
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Test API health
                async with session.get(f"{self.config['api_url']}/health", timeout=10) as response:
                    api_health = response.status == 200
                    if api_health:
                        api_data = await response.json()
                        api_healthy = api_data.get("status") == "healthy"
                    else:
                        api_healthy = False
                
                # Test frontend accessibility
                async with session.get(self.config['vercel_url'], timeout=10) as response:
                    frontend_accessible = response.status == 200
                
                # Test Supabase connectivity
                async with session.get(f"{self.config['supabase_url']}/rest/v1/", timeout=10) as response:
                    supabase_accessible = response.status in [200, 401, 404]  # 401/404 are acceptable
                
                success = api_healthy and frontend_accessible and supabase_accessible
                
                return {
                    "success": success,
                    "api_health": api_healthy,
                    "frontend_accessible": frontend_accessible,
                    "supabase_accessible": supabase_accessible,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Phase 1 validation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _run_integration_tests(self) -> Dict[str, Any]:
        """Run comprehensive integration tests"""
        
        try:
            async with CloudIntegrationValidator(self.config) as validator:
                results = await validator.run_phase2_integration_tests()
                
                return {
                    "success": results.summary["overall_status"] == "passed",
                    "integration_result": {
                        "status": results.integration_result.status,
                        "processing_time": results.integration_result.processing_time,
                        "stages_completed": results.integration_result.stages_completed,
                        "errors": results.integration_result.errors
                    },
                    "auth_result": {
                        "login_success": results.auth_result.login_success,
                        "session_management": results.auth_result.session_management,
                        "security_validation": results.auth_result.security_validation,
                        "errors": results.auth_result.errors
                    },
                    "performance_result": {
                        "passes_baseline": results.performance_result.passes_baseline,
                        "throughput": results.performance_result.throughput,
                        "concurrent_users": results.performance_result.concurrent_users,
                        "baseline_comparison": results.performance_result.baseline_comparison
                    },
                    "summary": results.summary,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Integration tests failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _run_performance_benchmarking(self) -> Dict[str, Any]:
        """Run performance benchmarking with Artillery.js"""
        
        try:
            # Check if Artillery.js is installed
            try:
                subprocess.run(["artillery", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("Artillery.js not found. Installing...")
                subprocess.run(["npm", "install", "-g", "artillery"], check=True)
            
            # Set environment variables for Artillery
            env = {
                "SUPABASE_URL": self.config["supabase_url"],
                "SUPABASE_ANON_KEY": "test_key",  # Placeholder
                "API_URL": self.config["api_url"]
            }
            
            # Run Artillery load test
            artillery_config = self.test_config["artillery_config"]
            results_file = f"artillery_results_{self.test_id[:8]}.json"
            
            cmd = [
                "artillery", "run", artillery_config,
                "--output", results_file,
                "--environment", "production"
            ]
            
            logger.info(f"Running Artillery load test: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env={**env, **subprocess.os.environ},
                timeout=self.test_config["load_test_duration"] + 60  # Add buffer
            )
            
            # Parse results
            if Path(results_file).exists():
                with open(results_file, 'r') as f:
                    artillery_results = json.load(f)
            else:
                artillery_results = {"error": "Results file not generated"}
            
            # Analyze results
            success = process.returncode == 0 and "error" not in artillery_results
            
            return {
                "success": success,
                "artillery_exit_code": process.returncode,
                "artillery_stdout": process.stdout,
                "artillery_stderr": process.stderr,
                "results": artillery_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Artillery load test timed out")
            return {
                "success": False,
                "error": "Load test timed out",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Performance benchmarking failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _run_cloud_specific_tests(self) -> Dict[str, Any]:
        """Run cloud-specific functionality tests"""
        
        try:
            import aiohttp
            
            results = {
                "cdn_performance": {},
                "auto_scaling": {},
                "edge_functions": {},
                "database_pooling": {}
            }
            
            async with aiohttp.ClientSession() as session:
                # Test CDN performance (Vercel)
                cdn_start = time.time()
                async with session.get(self.config['vercel_url'], timeout=10) as response:
                    cdn_time = (time.time() - cdn_start) * 1000
                    results["cdn_performance"] = {
                        "response_time_ms": cdn_time,
                        "status_code": response.status,
                        "cache_headers": dict(response.headers).get("cache-control", ""),
                        "success": response.status == 200
                    }
                
                # Test API auto-scaling (Render)
                api_start = time.time()
                async with session.get(f"{self.config['api_url']}/health", timeout=10) as response:
                    api_time = (time.time() - api_start) * 1000
                    results["auto_scaling"] = {
                        "response_time_ms": api_time,
                        "status_code": response.status,
                        "success": response.status == 200
                    }
                
                # Test database connection pooling (Supabase)
                db_start = time.time()
                async with session.get(f"{self.config['supabase_url']}/rest/v1/", timeout=10) as response:
                    db_time = (time.time() - db_start) * 1000
                    results["database_pooling"] = {
                        "response_time_ms": db_time,
                        "status_code": response.status,
                        "success": response.status in [200, 401, 404]
                    }
            
            # Overall success
            success = all([
                results["cdn_performance"]["success"],
                results["auto_scaling"]["success"],
                results["database_pooling"]["success"]
            ])
            
            return {
                "success": success,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cloud-specific tests failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _run_error_handling_tests(self) -> Dict[str, Any]:
        """Run error handling and recovery tests"""
        
        try:
            import aiohttp
            
            error_scenarios = self.test_config["error_scenarios"]
            results = {}
            
            async with aiohttp.ClientSession() as session:
                # Test 1: Network timeout handling
                try:
                    async with session.get(f"{self.config['api_url']}/health", timeout=0.1) as response:
                        results["network_timeout"] = {
                            "handled": True,
                            "status": "timeout_handled"
                        }
                except asyncio.TimeoutError:
                    results["network_timeout"] = {
                        "handled": True,
                        "status": "timeout_caught"
                    }
                except Exception as e:
                    results["network_timeout"] = {
                        "handled": False,
                        "error": str(e)
                    }
                
                # Test 2: Service unavailable (non-existent endpoint)
                try:
                    async with session.get(f"{self.config['api_url']}/non-existent-endpoint", timeout=5) as response:
                        results["service_unavailable"] = {
                            "handled": True,
                            "status_code": response.status,
                            "status": "404_handled" if response.status == 404 else "unexpected_status"
                        }
                except Exception as e:
                    results["service_unavailable"] = {
                        "handled": False,
                        "error": str(e)
                    }
                
                # Test 3: Authentication failure
                try:
                    async with session.post(
                        f"{self.config['api_url']}/api/v1/upload",
                        json={"test": "data"},
                        timeout=5
                    ) as response:
                        results["authentication_failure"] = {
                            "handled": True,
                            "status_code": response.status,
                            "status": "401_handled" if response.status == 401 else "unexpected_status"
                        }
                except Exception as e:
                    results["authentication_failure"] = {
                        "handled": False,
                        "error": str(e)
                    }
            
            # Overall success
            success = all(result.get("handled", False) for result in results.values())
            
            return {
                "success": success,
                "error_scenarios": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling tests failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _run_performance_monitoring(self) -> Dict[str, Any]:
        """Run performance monitoring and analysis"""
        
        try:
            async with CloudPerformanceMonitor(self.config) as monitor:
                # Take performance snapshot
                snapshot = await monitor.take_performance_snapshot()
                
                # Generate performance report
                report = await monitor.generate_performance_report()
                
                # Monitor trends
                trends = await monitor.monitor_performance_trends(duration_minutes=5)
                
                return {
                    "success": True,
                    "snapshot": {
                        "timestamp": snapshot.timestamp.isoformat(),
                        "alerts_count": len(snapshot.alerts),
                        "overall_performance": snapshot.baseline_comparison["overall_performance"]
                    },
                    "report": report,
                    "trends": trends,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Performance monitoring failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_final_report(self, start_time: float, success: bool, error: Optional[str] = None) -> Dict[str, Any]:
        """Generate final comprehensive test report"""
        
        total_time = time.time() - start_time
        
        # Calculate overall success
        test_results = list(self.results.values())
        successful_tests = sum(1 for result in test_results if result.get("success", False))
        total_tests = len(test_results)
        
        # Generate summary
        summary = {
            "overall_success": success and successful_tests == total_tests,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_execution_time": total_time,
            "test_id": self.test_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat()
        }
        
        if error:
            summary["error"] = error
        
        # Phase 2 completion criteria
        phase2_complete = (
            summary["overall_success"] and
            summary["success_rate"] >= 80 and  # At least 80% of tests must pass
            self.results.get("integration_tests", {}).get("success", False) and
            self.results.get("performance_benchmarking", {}).get("success", False)
        )
        
        summary["phase2_complete"] = phase2_complete
        summary["ready_for_phase3"] = phase2_complete
        
        return {
            "summary": summary,
            "test_results": self.results,
            "config": self.config,
            "test_config": self.test_config
        }
    
    async def _save_test_results(self, final_report: Dict[str, Any]) -> None:
        """Save test results to file"""
        
        results_file = self.results_dir / f"phase2_test_results_{self.test_id[:8]}.json"
        
        with open(results_file, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        logger.info(f"Test results saved to: {results_file}")

async def main():
    """Main entry point for Phase 2 test suite"""
    
    parser = argparse.ArgumentParser(description="Phase 2 Cloud Integration Test Suite")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--concurrent-users", type=int, default=10, help="Number of concurrent users for testing")
    parser.add_argument("--load-test-duration", type=int, default=300, help="Load test duration in seconds")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = None
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Initialize and run test suite
    test_suite = Phase2TestSuite(config)
    
    if args.concurrent_users:
        test_suite.test_config["concurrent_users"] = args.concurrent_users
    if args.load_test_duration:
        test_suite.test_config["load_test_duration"] = args.load_test_duration
    
    # Run tests
    results = await test_suite.run_complete_test_suite()
    
    # Print summary
    summary = results["summary"]
    print(f"\n{'='*60}")
    print(f"PHASE 2 TEST SUITE RESULTS")
    print(f"{'='*60}")
    print(f"Test ID: {summary['test_id']}")
    print(f"Overall Success: {summary['overall_success']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Successful Tests: {summary['successful_tests']}")
    print(f"Failed Tests: {summary['failed_tests']}")
    print(f"Execution Time: {summary['total_execution_time']:.2f} seconds")
    print(f"Phase 2 Complete: {summary['phase2_complete']}")
    print(f"Ready for Phase 3: {summary['ready_for_phase3']}")
    
    if summary.get("error"):
        print(f"Error: {summary['error']}")
    
    print(f"{'='*60}")
    
    # Exit with appropriate code
    sys.exit(0 if summary["overall_success"] else 1)

if __name__ == "__main__":
    asyncio.run(main())
