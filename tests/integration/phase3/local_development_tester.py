#!/usr/bin/env python3
"""
Local Development Environment Testing
Test local development setup with Vercel CLI and local backend
"""

import asyncio
import subprocess
import time
import requests
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("local_dev_tester")

class LocalDevelopmentTester:
    """Test local development environment setup and functionality."""
    
    def __init__(self):
        self.results = []
        self.backend_process = None
        self.frontend_process = None
        
    async def test_environment_setup(self) -> Dict[str, Any]:
        """Test local environment setup and dependencies."""
        result = {
            "test_name": "environment_setup",
            "platform": "local_development",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            setup_tests = []
            
            # Check Python version
            python_version = sys.version_info
            setup_tests.append({
                "test": "python_version",
                "success": python_version >= (3, 8),
                "details": f"Python {python_version.major}.{python_version.minor}.{python_version.micro}"
            })
            
            # Check if required packages are installed
            required_packages = ["fastapi", "uvicorn", "requests", "pytest"]
            for package in required_packages:
                try:
                    __import__(package)
                    setup_tests.append({
                        "test": f"package_{package}",
                        "success": True,
                        "details": f"Package {package} is installed"
                    })
                except ImportError:
                    setup_tests.append({
                        "test": f"package_{package}",
                        "success": False,
                        "details": f"Package {package} is not installed"
                    })
            
            # Check if Vercel CLI is available
            try:
                vercel_result = subprocess.run(["vercel", "--version"], capture_output=True, text=True, timeout=5)
                setup_tests.append({
                    "test": "vercel_cli",
                    "success": vercel_result.returncode == 0,
                    "details": f"Vercel CLI: {vercel_result.stdout.strip()}" if vercel_result.returncode == 0 else "Vercel CLI not available"
                })
            except Exception as e:
                setup_tests.append({
                    "test": "vercel_cli",
                    "success": False,
                    "details": f"Vercel CLI error: {str(e)}"
                })
            
            # Check environment files
            env_files = [".env.development", ".env.local", ".env"]
            for env_file in env_files:
                file_exists = os.path.exists(env_file)
                setup_tests.append({
                    "test": f"env_file_{env_file.replace('.', '_')}",
                    "success": file_exists,
                    "details": f"Environment file {env_file} exists" if file_exists else f"Environment file {env_file} missing"
                })
            
            passed_tests = sum(1 for test in setup_tests if test["success"])
            total_tests = len(setup_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Environment setup: {passed_tests}/{total_tests} tests passed",
                "test_results": setup_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Environment setup error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def start_backend_server(self) -> bool:
        """Start the local backend server."""
        try:
            logger.info("Starting local backend server...")
            self.backend_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            max_wait = 120  # 2 minutes
            for i in range(max_wait):
                try:
                    response = requests.get("http://localhost:8000/health", timeout=5)
                    if response.status_code == 200:
                        logger.info("Backend server started successfully")
                        return True
                except:
                    pass
                if i % 10 == 0 and i > 0:
                    logger.info(f"Still waiting for backend server... ({i}/{max_wait} seconds)")
                time.sleep(1)
            
            logger.error("Backend server failed to start within 120 seconds")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start backend server: {e}")
            return False
    
    async def start_frontend_server(self) -> bool:
        """Start the local frontend server using Vercel CLI."""
        try:
            logger.info("Starting local frontend server with Vercel CLI...")
            
            # Check if we're in a Vercel project
            if not os.path.exists("vercel.json") and not os.path.exists(".vercel"):
                logger.info("Not a Vercel project, trying npm start instead...")
                self.frontend_process = subprocess.Popen(
                    ["npm", "start"],
                    cwd=project_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                # Use Vercel CLI for local development
                self.frontend_process = subprocess.Popen(
                    ["vercel", "dev", "--port", "3000"],
                    cwd=project_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Wait for server to start
            max_wait = 120  # 2 minutes
            for i in range(max_wait):
                try:
                    response = requests.get("http://localhost:3000", timeout=5)
                    if response.status_code == 200:
                        logger.info("Frontend server started successfully")
                        return True
                except:
                    pass
                if i % 10 == 0 and i > 0:
                    logger.info(f"Still waiting for frontend server... ({i}/{max_wait} seconds)")
                time.sleep(1)
            
            logger.error("Frontend server failed to start within 120 seconds")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start frontend server: {e}")
            return False
    
    async def test_backend_functionality(self) -> Dict[str, Any]:
        """Test backend functionality when running locally."""
        result = {
            "test_name": "backend_functionality",
            "platform": "local_development",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            backend_tests = []
            
            # Test health endpoint
            try:
                health_response = requests.get("http://localhost:8000/health", timeout=10)
                backend_tests.append({
                    "test": "health_endpoint",
                    "success": health_response.status_code == 200,
                    "status_code": health_response.status_code,
                    "response_time_ms": health_response.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                backend_tests.append({
                    "test": "health_endpoint",
                    "success": False,
                    "error": str(e)
                })
            
            # Test root endpoint
            try:
                root_response = requests.get("http://localhost:8000/", timeout=10)
                backend_tests.append({
                    "test": "root_endpoint",
                    "success": root_response.status_code == 200,
                    "status_code": root_response.status_code,
                    "response_time_ms": root_response.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                backend_tests.append({
                    "test": "root_endpoint",
                    "success": False,
                    "error": str(e)
                })
            
            # Test API documentation
            try:
                docs_response = requests.get("http://localhost:8000/docs", timeout=10)
                backend_tests.append({
                    "test": "api_docs",
                    "success": docs_response.status_code == 200,
                    "status_code": docs_response.status_code,
                    "response_time_ms": docs_response.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                backend_tests.append({
                    "test": "api_docs",
                    "success": False,
                    "error": str(e)
                })
            
            # Test authentication endpoint
            try:
                auth_response = requests.post("http://localhost:8000/auth/login", 
                                           json={"email": "test@example.com", "password": "test"}, 
                                           timeout=10)
                backend_tests.append({
                    "test": "auth_endpoint",
                    "success": auth_response.status_code in [200, 401, 422],
                    "status_code": auth_response.status_code,
                    "response_time_ms": auth_response.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                backend_tests.append({
                    "test": "auth_endpoint",
                    "success": False,
                    "error": str(e)
                })
            
            passed_tests = sum(1 for test in backend_tests if test["success"])
            total_tests = len(backend_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Backend functionality: {passed_tests}/{total_tests} tests passed",
                "test_results": backend_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Backend functionality error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_frontend_functionality(self) -> Dict[str, Any]:
        """Test frontend functionality when running locally."""
        result = {
            "test_name": "frontend_functionality",
            "platform": "local_development",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            frontend_tests = []
            
            # Test frontend accessibility
            try:
                frontend_response = requests.get("http://localhost:3000", timeout=10)
                frontend_tests.append({
                    "test": "frontend_accessibility",
                    "success": frontend_response.status_code == 200,
                    "status_code": frontend_response.status_code,
                    "response_time_ms": frontend_response.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                frontend_tests.append({
                    "test": "frontend_accessibility",
                    "success": False,
                    "error": str(e)
                })
            
            # Test API proxy (if configured)
            try:
                api_proxy_response = requests.get("http://localhost:3000/api/health", timeout=10)
                frontend_tests.append({
                    "test": "api_proxy",
                    "success": api_proxy_response.status_code in [200, 404],  # 404 if no proxy
                    "status_code": api_proxy_response.status_code,
                    "response_time_ms": api_proxy_response.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                frontend_tests.append({
                    "test": "api_proxy",
                    "success": False,
                    "error": str(e)
                })
            
            passed_tests = sum(1 for test in frontend_tests if test["success"])
            total_tests = len(frontend_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Frontend functionality: {passed_tests}/{total_tests} tests passed",
                "test_results": frontend_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Frontend functionality error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_cross_platform_communication(self) -> Dict[str, Any]:
        """Test communication between local frontend and backend."""
        result = {
            "test_name": "cross_platform_communication",
            "platform": "local_development",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            comm_tests = []
            
            # Test CORS configuration
            try:
                cors_response = requests.options("http://localhost:8000/auth/login",
                                               headers={"Origin": "http://localhost:3000",
                                                       "Access-Control-Request-Method": "POST"},
                                               timeout=10)
                comm_tests.append({
                    "test": "cors_configuration",
                    "success": cors_response.status_code in [200, 204],
                    "status_code": cors_response.status_code,
                    "has_cors_headers": "Access-Control-Allow-Origin" in cors_response.headers
                })
            except Exception as e:
                comm_tests.append({
                    "test": "cors_configuration",
                    "success": False,
                    "error": str(e)
                })
            
            # Test actual API call from frontend to backend
            try:
                api_response = requests.post("http://localhost:8000/auth/login",
                                          json={"email": "test@example.com", "password": "test"},
                                          headers={"Origin": "http://localhost:3000"},
                                          timeout=10)
                comm_tests.append({
                    "test": "api_communication",
                    "success": api_response.status_code in [200, 401, 422],
                    "status_code": api_response.status_code,
                    "response_time_ms": api_response.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                comm_tests.append({
                    "test": "api_communication",
                    "success": False,
                    "error": str(e)
                })
            
            passed_tests = sum(1 for test in comm_tests if test["success"])
            total_tests = len(comm_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Cross-platform communication: {passed_tests}/{total_tests} tests passed",
                "test_results": comm_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Cross-platform communication error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    def stop_servers(self):
        """Stop the local servers."""
        if self.backend_process:
            logger.info("Stopping backend server...")
            self.backend_process.terminate()
            self.backend_process.wait()
        
        if self.frontend_process:
            logger.info("Stopping frontend server...")
            self.frontend_process.terminate()
            self.frontend_process.wait()
    
    async def run_all_tests(self):
        """Run all local development tests."""
        print("=" * 80)
        print("LOCAL DEVELOPMENT ENVIRONMENT TESTING")
        print("=" * 80)
        print(f"Project Root: {project_root}")
        print(f"Start Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        try:
            # Test environment setup
            print("\n🔧 Testing Environment Setup...")
            await self.test_environment_setup()
            
            # Start backend server
            print("\n🚀 Starting Backend Server...")
            backend_started = await self.start_backend_server()
            if not backend_started:
                print("❌ Failed to start backend server. Some tests will be skipped.")
            
            # Start frontend server
            print("\n🎨 Starting Frontend Server...")
            frontend_started = await self.start_frontend_server()
            if not frontend_started:
                print("❌ Failed to start frontend server. Some tests will be skipped.")
            
            # Test backend functionality
            if backend_started:
                print("\n🔧 Testing Backend Functionality...")
                await self.test_backend_functionality()
            
            # Test frontend functionality
            if frontend_started:
                print("\n🎨 Testing Frontend Functionality...")
                await self.test_frontend_functionality()
            
            # Test cross-platform communication
            if backend_started and frontend_started:
                print("\n🔗 Testing Cross-Platform Communication...")
                await self.test_cross_platform_communication()
            
            # Generate report
            self._generate_report()
            
        finally:
            # Always stop servers
            self.stop_servers()
    
    def _generate_report(self):
        """Generate local development test report."""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.get("status") == "passed"])
        partial_tests = len([r for r in self.results if r.get("status") == "partial"])
        error_tests = len([r for r in self.results if r.get("status") == "error"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": "local_development",
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "partial_tests": partial_tests,
                "error_tests": error_tests,
                "success_rate": success_rate
            },
            "test_results": self.results
        }
        
        # Save report
        os.makedirs("test-results", exist_ok=True)
        report_path = "test-results/local_development_test_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print("\n" + "="*80)
        print("LOCAL DEVELOPMENT TESTING SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Partial: {partial_tests}")
        print(f"Errors: {error_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Report saved to: {report_path}")
        print("="*80)
        
        return report

async def main():
    """Main execution function."""
    tester = LocalDevelopmentTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
