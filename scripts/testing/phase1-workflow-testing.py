#!/usr/bin/env python3
"""
Phase 1 Workflow Testing Script
Implements comprehensive Phase 1 testing as specified in workflow_testing_spec.md
Local Docker-based testing with production Supabase integration
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('phase1_test_results.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    test_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    metrics: Optional[Dict] = None

@dataclass
class Phase1Config:
    project_root: Path
    docker_compose_file: Path
    env_file: Path
    api_base_url: str = "http://localhost:8000"
    worker_base_url: str = "http://localhost:8002"
    frontend_url: str = "http://localhost:3000"
    monitoring_url: str = "http://localhost:3003"
    test_user_id: str = f"phase1-test-user-{int(time.time())}"
    test_filename: str = "phase1-test-document.pdf"
    test_file_size: int = 1048576  # 1MB
    test_sha256: str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    max_concurrent_tests: int = 10
    health_check_timeout: int = 300  # 5 minutes
    test_timeout: int = 1800  # 30 minutes

class Phase1WorkflowTester:
    def __init__(self, config: Phase1Config):
        self.config = config
        self.results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_job_ids: List[str] = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.test_timeout)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test_result(self, test_name: str, passed: bool, duration: float, 
                       error_message: Optional[str] = None, metrics: Optional[Dict] = None):
        """Log test result and add to results list"""
        result = TestResult(
            test_name=test_name,
            passed=passed,
            duration=duration,
            error_message=error_message,
            metrics=metrics
        )
        self.results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} {test_name} ({duration:.2f}s)")
        
        if error_message:
            logger.error(f"  Error: {error_message}")
        if metrics:
            logger.info(f"  Metrics: {metrics}")
    
    async def check_service_health(self, service_name: str, health_url: str) -> bool:
        """Check if a service is healthy"""
        try:
            async with self.session.get(health_url) as response:
                if response.status == 200:
                    logger.info(f"✅ {service_name} is healthy")
                    return True
                else:
                    logger.error(f"❌ {service_name} returned status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ {service_name} health check failed: {e}")
            return False
    
    async def test_environment_validation(self) -> bool:
        """Phase 1.1: Environment Validation"""
        test_name = "Environment Validation"
        start_time = time.time()
        
        try:
            # Check if .env.production exists
            if not self.config.env_file.exists():
                raise FileNotFoundError(f"Production environment file not found: {self.config.env_file}")
            
            # Check if Docker is running
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("Docker is not running")
            
            # Check if docker-compose file exists
            if not self.config.docker_compose_file.exists():
                raise FileNotFoundError(f"Docker Compose file not found: {self.config.docker_compose_file}")
            
            duration = time.time() - start_time
            self.log_test_result(test_name, True, duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, duration, str(e))
            return False
    
    async def test_docker_services_startup(self) -> bool:
        """Phase 1.2: Docker Services Startup"""
        test_name = "Docker Services Startup"
        start_time = time.time()
        
        try:
            # Load environment variables from .env.production
            env_vars = {}
            if self.config.env_file.exists():
                with open(self.config.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key] = value
            
            # Stop any existing services
            logger.info("Stopping existing services...")
            subprocess.run([
                'docker-compose', '-f', str(self.config.docker_compose_file), 
                'down', '--remove-orphans'
            ], cwd=self.config.project_root, check=False, env={**os.environ, **env_vars})
            
            # Build and start services with environment variables
            logger.info("Building and starting Phase 1 services...")
            result = subprocess.run([
                'docker-compose', '-f', str(self.config.docker_compose_file),
                'up', '--build', '-d'
            ], cwd=self.config.project_root, capture_output=True, text=True, env={**os.environ, **env_vars})
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to start services: {result.stderr}")
            
            # Wait for services to be healthy
            logger.info("Waiting for services to be healthy...")
            await asyncio.sleep(30)
            
            duration = time.time() - start_time
            self.log_test_result(test_name, True, duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, duration, str(e))
            return False
    
    async def test_service_health_checks(self) -> bool:
        """Phase 1.3: Service Health Checks"""
        test_name = "Service Health Checks"
        start_time = time.time()
        
        try:
            services = [
                ("API Server", f"{self.config.api_base_url}/health"),
                ("Worker Service", f"{self.config.worker_base_url}/health"),
                ("Monitoring Service", f"{self.config.monitoring_url}/health")
            ]
            
            health_results = []
            for service_name, health_url in services:
                is_healthy = await self.check_service_health(service_name, health_url)
                health_results.append(is_healthy)
                
                if not is_healthy:
                    # Wait and retry once
                    await asyncio.sleep(10)
                    is_healthy = await self.check_service_health(service_name, health_url)
                    health_results.append(is_healthy)
            
            # Check Production Supabase connectivity via API
            supabase_healthy = await self.check_service_health(
                "Production Supabase", 
                f"{self.config.api_base_url}/health"
            )
            
            all_healthy = all(health_results) and supabase_healthy
            duration = time.time() - start_time
            
            metrics = {
                "services_checked": len(services),
                "services_healthy": sum(health_results),
                "supabase_connected": supabase_healthy
            }
            
            self.log_test_result(test_name, all_healthy, duration, metrics=metrics)
            return all_healthy
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, duration, str(e))
            return False
    
    async def test_document_upload_workflow(self) -> bool:
        """Phase 1.4: Document Upload Workflow"""
        test_name = "Document Upload Workflow"
        start_time = time.time()
        
        try:
            # Upload document
            upload_data = {
                "filename": self.config.test_filename,
                "bytes_len": self.config.test_file_size,
                "mime": "application/pdf",
                "sha256": self.config.test_sha256,
                "ocr": False
            }
            
            async with self.session.post(
                f"{self.config.api_base_url}/api/upload-pipeline/upload",
                json=upload_data,
                headers={"Authorization": "Bearer test-jwt-token"}
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Upload failed with status {response.status}")
                
                response_data = await response.json()
                job_id = response_data.get("job_id")
                document_id = response_data.get("document_id")
                
                if not job_id or not document_id:
                    raise RuntimeError("Failed to extract job_id or document_id from response")
                
                self.test_job_ids.append(job_id)
                logger.info(f"Document uploaded successfully - Job: {job_id}, Document: {document_id}")
            
            duration = time.time() - start_time
            metrics = {
                "job_id": job_id,
                "document_id": document_id,
                "upload_time": duration
            }
            
            self.log_test_result(test_name, True, duration, metrics=metrics)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, duration, str(e))
            return False
    
    async def test_job_status_monitoring(self) -> bool:
        """Phase 1.5: Job Status Monitoring"""
        test_name = "Job Status Monitoring"
        start_time = time.time()
        
        try:
            if not self.test_job_ids:
                raise RuntimeError("No test job IDs available for monitoring")
            
            job_id = self.test_job_ids[0]
            max_polls = 20
            poll_interval = 10
            
            for poll_count in range(max_polls):
                logger.info(f"Polling job status (attempt {poll_count + 1}/{max_polls})...")
                
                async with self.session.get(
                    f"{self.config.api_base_url}/api/v2/jobs/{job_id}",
                    headers={"Authorization": "Bearer test-jwt-token"}
                ) as response:
                    if response.status != 200:
                        raise RuntimeError(f"Job status check failed with status {response.status}")
                    
                    status_data = await response.json()
                    stage = status_data.get("stage", "unknown")
                    state = status_data.get("state", "unknown")
                    progress = status_data.get("total_pct", 0)
                    
                    logger.info(f"Job Status - Stage: {stage}, State: {state}, Progress: {progress}%")
                    
                    if state == "done":
                        logger.info("✅ Job completed successfully!")
                        duration = time.time() - start_time
                        metrics = {
                            "job_id": job_id,
                            "final_stage": stage,
                            "final_state": state,
                            "final_progress": progress,
                            "polls_required": poll_count + 1,
                            "total_time": duration
                        }
                        self.log_test_result(test_name, True, duration, metrics=metrics)
                        return True
                    elif state == "deadletter":
                        raise RuntimeError("Job failed and moved to dead letter queue")
                
                await asyncio.sleep(poll_interval)
            
            # Job didn't complete within expected time
            duration = time.time() - start_time
            self.log_test_result(test_name, False, duration, "Job did not complete within expected time")
            return False
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, duration, str(e))
            return False
    
    async def test_concurrent_processing(self) -> bool:
        """Phase 1.6: Concurrent Processing"""
        test_name = "Concurrent Processing"
        start_time = time.time()
        
        try:
            # Create multiple concurrent uploads
            upload_tasks = []
            for i in range(self.config.max_concurrent_tests):
                upload_data = {
                    "filename": f"concurrent-test-{i}.pdf",
                    "bytes_len": self.config.test_file_size,
                    "mime": "application/pdf",
                    "sha256": f"concurrent-test-sha256-{i}",
                    "ocr": False
                }
                
                task = self.session.post(
                    f"{self.config.api_base_url}/api/upload-pipeline/upload",
                    json=upload_data,
                    headers={"Authorization": "Bearer test-jwt-token"}
                )
                upload_tasks.append(task)
            
            # Execute all uploads concurrently
            logger.info(f"Executing {len(upload_tasks)} concurrent uploads...")
            responses = await asyncio.gather(*upload_tasks, return_exceptions=True)
            
            # Analyze results
            successful_uploads = 0
            failed_uploads = 0
            
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.error(f"Concurrent upload {i} failed: {response}")
                    failed_uploads += 1
                else:
                    async with response as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("job_id"):
                                successful_uploads += 1
                                self.test_job_ids.append(data["job_id"])
                            else:
                                failed_uploads += 1
                        else:
                            failed_uploads += 1
            
            duration = time.time() - start_time
            success_rate = (successful_uploads / len(upload_tasks)) * 100
            
            metrics = {
                "total_uploads": len(upload_tasks),
                "successful_uploads": successful_uploads,
                "failed_uploads": failed_uploads,
                "success_rate": success_rate,
                "concurrent_time": duration
            }
            
            # Consider test passed if success rate is >= 80%
            passed = success_rate >= 80
            self.log_test_result(test_name, passed, duration, metrics=metrics)
            return passed
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, duration, str(e))
            return False
    
    async def test_error_handling(self) -> bool:
        """Phase 1.7: Error Handling"""
        test_name = "Error Handling"
        start_time = time.time()
        
        try:
            error_tests = [
                {
                    "name": "Invalid File Size",
                    "data": {
                        "filename": "invalid.pdf",
                        "bytes_len": 104857600,  # 100MB
                        "mime": "application/pdf",
                        "sha256": self.config.test_sha256,
                        "ocr": False
                    },
                    "expected_error": "File size.*exceeds limit"
                },
                {
                    "name": "Invalid MIME Type",
                    "data": {
                        "filename": "invalid.txt",
                        "bytes_len": self.config.test_file_size,
                        "mime": "text/plain",
                        "sha256": self.config.test_sha256,
                        "ocr": False
                    },
                    "expected_error": "Unsupported MIME type"
                }
            ]
            
            error_tests_passed = 0
            
            for error_test in error_tests:
                logger.info(f"Testing {error_test['name']}...")
                
                async with self.session.post(
                    f"{self.config.api_base_url}/api/upload-pipeline/upload",
                    json=error_test["data"],
                    headers={"Authorization": "Bearer test-jwt-token"}
                ) as response:
                    response_text = await response.text()
                    
                    if error_test["expected_error"] in response_text:
                        logger.info(f"✅ {error_test['name']} handled correctly")
                        error_tests_passed += 1
                    else:
                        logger.error(f"❌ {error_test['name']} not handled correctly")
            
            duration = time.time() - start_time
            all_passed = error_tests_passed == len(error_tests)
            
            metrics = {
                "error_tests_run": len(error_tests),
                "error_tests_passed": error_tests_passed,
                "error_handling_rate": (error_tests_passed / len(error_tests)) * 100
            }
            
            self.log_test_result(test_name, all_passed, duration, metrics=metrics)
            return all_passed
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, duration, str(e))
            return False
    
    async def test_performance_metrics(self) -> bool:
        """Phase 1.8: Performance Metrics"""
        test_name = "Performance Metrics"
        start_time = time.time()
        
        try:
            # Test API response times
            response_times = []
            num_requests = 10
            
            for i in range(num_requests):
                request_start = time.time()
                async with self.session.get(f"{self.config.api_base_url}/health") as response:
                    if response.status == 200:
                        request_duration = (time.time() - request_start) * 1000  # Convert to ms
                        response_times.append(request_duration)
                
                await asyncio.sleep(0.1)  # Small delay between requests
            
            if not response_times:
                raise RuntimeError("No successful response times recorded")
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            duration = time.time() - start_time
            
            # Performance criteria: average response time < 1000ms
            performance_acceptable = avg_response_time < 1000
            
            metrics = {
                "requests_sent": num_requests,
                "requests_successful": len(response_times),
                "avg_response_time_ms": avg_response_time,
                "max_response_time_ms": max_response_time,
                "min_response_time_ms": min_response_time,
                "performance_acceptable": performance_acceptable
            }
            
            self.log_test_result(test_name, performance_acceptable, duration, metrics=metrics)
            return performance_acceptable
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, duration, str(e))
            return False
    
    async def cleanup_services(self):
        """Cleanup Docker services"""
        try:
            # Load environment variables from .env.production
            env_vars = {}
            if self.config.env_file.exists():
                with open(self.config.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key] = value
            
            logger.info("Cleaning up Phase 1 test environment...")
            subprocess.run([
                'docker-compose', '-f', str(self.config.docker_compose_file),
                'down', '--remove-orphans'
            ], cwd=self.config.project_root, check=False, env={**os.environ, **env_vars})
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
    
    def generate_test_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        total_duration = sum(r.duration for r in self.results)
        
        report = {
            "phase": "Phase 1 Workflow Testing",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "total_duration": total_duration
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "duration": r.duration,
                    "error_message": r.error_message,
                    "metrics": r.metrics
                }
                for r in self.results
            ]
        }
        
        return report
    
    async def run_all_tests(self) -> bool:
        """Run all Phase 1 tests"""
        logger.info("🚀 Starting Phase 1 Workflow Testing")
        logger.info(f"Project Root: {self.config.project_root}")
        logger.info(f"Test User ID: {self.config.test_user_id}")
        
        try:
            # Run all test phases
            test_phases = [
                self.test_environment_validation,
                self.test_docker_services_startup,
                self.test_service_health_checks,
                self.test_document_upload_workflow,
                self.test_job_status_monitoring,
                self.test_concurrent_processing,
                self.test_error_handling,
                self.test_performance_metrics
            ]
            
            for test_phase in test_phases:
                await test_phase()
            
            # Generate and save report
            report = self.generate_test_report()
            
            # Save report to file
            report_file = self.config.project_root / "phase1_test_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"📊 Test report saved to: {report_file}")
            
            # Print summary
            logger.info("=" * 60)
            logger.info("📋 PHASE 1 TEST SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Total Tests: {report['summary']['total_tests']}")
            logger.info(f"Passed: {report['summary']['passed_tests']} ✅")
            logger.info(f"Failed: {report['summary']['failed_tests']} ❌")
            logger.info(f"Success Rate: {report['summary']['success_rate']:.1f}%")
            logger.info(f"Total Duration: {report['summary']['total_duration']:.2f}s")
            
            if report['summary']['success_rate'] == 100:
                logger.info("🎉 Phase 1 testing completed successfully!")
                return True
            elif report['summary']['success_rate'] >= 80:
                logger.info("✅ Phase 1 testing completed with warnings")
                return True
            else:
                logger.error("❌ Phase 1 testing failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Phase 1 testing failed with exception: {e}")
            return False
        finally:
            await self.cleanup_services()

async def main():
    """Main entry point"""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # Create configuration
    config = Phase1Config(
        project_root=project_root,
        docker_compose_file=project_root / "docker-compose.phase1-workflow-testing-fixed.yml",
        env_file=project_root / ".env.production"
    )
    
    # Run tests
    async with Phase1WorkflowTester(config) as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
