#!/usr/bin/env python3
"""
Phase 2 Component Testing Framework
Comprehensive testing for Render backend and Vercel frontend platforms
"""

import asyncio
import unittest
import json
import os
import sys
import time
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, List, Any, Optional
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("component_testing")

class ComponentTestResult:
    """Container for component test results."""
    
    def __init__(self, component: str, platform: str, environment: str):
        self.component = component
        self.platform = platform
        self.environment = environment
        self.tests = []
        self.start_time = datetime.now()
        self.end_time = None
        self.success = False
        self.error_count = 0
        self.failure_count = 0
        
    def add_test_result(self, test_name: str, passed: bool, details: str = "", error: str = ""):
        """Add a test result to this component."""
        self.tests.append({
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
        if not passed:
            if error:
                self.error_count += 1
            else:
                self.failure_count += 1
    
    def finalize(self):
        """Mark the component test as complete."""
        self.end_time = datetime.now()
        self.success = self.error_count == 0 and self.failure_count == 0
        
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "component": self.component,
            "platform": self.platform,
            "environment": self.environment,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else None,
            "success": self.success,
            "total_tests": len(self.tests),
            "passed_tests": len([t for t in self.tests if t["passed"]]),
            "failed_tests": self.failure_count,
            "error_tests": self.error_count,
            "success_rate": (len([t for t in self.tests if t["passed"]]) / len(self.tests) * 100) if self.tests else 0,
            "tests": self.tests
        }

class RenderAPITester:
    """Test Render Web Service API endpoints and functionality."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.base_url = self._get_render_url()
        self.session = requests.Session()
        self.session.timeout = 30
        
    def _get_render_url(self) -> str:
        """Get Render URL based on environment."""
        if self.environment == "production":
            return "***REMOVED***"
        elif self.environment == "staging":
            return "https://insurance-navigator-api-staging.onrender.com"
        else:  # development
            return "http://localhost:8000"
    
    async def test_health_endpoints(self, result: ComponentTestResult):
        """Test health check endpoints."""
        try:
            # Test /health endpoint
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                result.add_test_result("health_endpoint", True, f"Health check passed: {health_data}")
            else:
                result.add_test_result("health_endpoint", False, f"Health check failed: {response.status_code}")
                
            # Test /status endpoint
            response = self.session.get(f"{self.base_url}/status")
            if response.status_code == 200:
                status_data = response.json()
                result.add_test_result("status_endpoint", True, f"Status check passed: {status_data}")
            else:
                result.add_test_result("status_endpoint", False, f"Status check failed: {response.status_code}")
                
        except Exception as e:
            result.add_test_result("health_endpoints", False, error=str(e))
    
    async def test_authentication_endpoints(self, result: ComponentTestResult):
        """Test authentication endpoints."""
        try:
            # Test login endpoint
            login_data = {
                "email": "test@example.com",
                "password": "testpassword"
            }
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            
            if response.status_code in [200, 401]:  # 401 is expected for invalid credentials
                result.add_test_result("login_endpoint", True, f"Login endpoint accessible: {response.status_code}")
            else:
                result.add_test_result("login_endpoint", False, f"Login endpoint failed: {response.status_code}")
                
            # Test registration endpoint
            register_data = {
                "email": "newuser@example.com",
                "password": "newpassword",
                "full_name": "Test User"
            }
            response = self.session.post(f"{self.base_url}/auth/register", json=register_data)
            
            if response.status_code in [200, 201, 400, 409]:  # Various expected responses
                result.add_test_result("register_endpoint", True, f"Register endpoint accessible: {response.status_code}")
            else:
                result.add_test_result("register_endpoint", False, f"Register endpoint failed: {response.status_code}")
                
        except Exception as e:
            result.add_test_result("authentication_endpoints", False, error=str(e))
    
    async def test_document_endpoints(self, result: ComponentTestResult):
        """Test document upload and retrieval endpoints."""
        try:
            # Test document upload endpoint
            files = {'file': ('test.pdf', b'fake pdf content', 'application/pdf')}
            response = self.session.post(f"{self.base_url}/documents/upload", files=files)
            
            if response.status_code in [200, 201, 401, 422]:  # Various expected responses
                result.add_test_result("document_upload", True, f"Document upload endpoint accessible: {response.status_code}")
            else:
                result.add_test_result("document_upload", False, f"Document upload failed: {response.status_code}")
                
            # Test document list endpoint
            response = self.session.get(f"{self.base_url}/documents")
            
            if response.status_code in [200, 401]:  # 401 expected without auth
                result.add_test_result("document_list", True, f"Document list endpoint accessible: {response.status_code}")
            else:
                result.add_test_result("document_list", False, f"Document list failed: {response.status_code}")
                
        except Exception as e:
            result.add_test_result("document_endpoints", False, error=str(e))
    
    async def test_ai_chat_endpoints(self, result: ComponentTestResult):
        """Test AI chat interface endpoints."""
        try:
            # Test chat endpoint
            chat_data = {
                "message": "Hello, how can you help me?",
                "conversation_id": "test_conv_123"
            }
            response = self.session.post(f"{self.base_url}/chat", json=chat_data)
            
            if response.status_code in [200, 401, 422]:  # Various expected responses
                result.add_test_result("ai_chat", True, f"AI chat endpoint accessible: {response.status_code}")
            else:
                result.add_test_result("ai_chat", False, f"AI chat failed: {response.status_code}")
                
        except Exception as e:
            result.add_test_result("ai_chat_endpoints", False, error=str(e))
    
    async def test_error_handling(self, result: ComponentTestResult):
        """Test error response handling."""
        try:
            # Test 404 endpoint
            response = self.session.get(f"{self.base_url}/nonexistent")
            if response.status_code == 404:
                result.add_test_result("error_404", True, "404 error handling works correctly")
            else:
                result.add_test_result("error_404", False, f"Expected 404, got {response.status_code}")
                
            # Test invalid JSON
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       data="invalid json", 
                                       headers={"Content-Type": "application/json"})
            if response.status_code in [400, 422]:
                result.add_test_result("error_invalid_json", True, "Invalid JSON error handling works")
            else:
                result.add_test_result("error_invalid_json", False, f"Invalid JSON handling failed: {response.status_code}")
                
        except Exception as e:
            result.add_test_result("error_handling", False, error=str(e))

class RenderWorkersTester:
    """Test Render Workers background processes and job handling."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.worker_url = self._get_worker_url()
        
    def _get_worker_url(self) -> str:
        """Get Render Worker URL based on environment."""
        if self.environment == "production":
            return "https://insurance-navigator-worker.onrender.com"
        elif self.environment == "staging":
            return "https://insurance-navigator-worker-staging.onrender.com"
        else:  # development
            return "http://localhost:8001"
    
    async def test_worker_initialization(self, result: ComponentTestResult):
        """Test worker initialization and startup."""
        try:
            # Test worker health check
            response = requests.get(f"{self.worker_url}/health", timeout=10)
            if response.status_code == 200:
                result.add_test_result("worker_health", True, f"Worker health check passed: {response.json()}")
            else:
                result.add_test_result("worker_health", False, f"Worker health check failed: {response.status_code}")
                
        except Exception as e:
            result.add_test_result("worker_initialization", False, error=str(e))
    
    async def test_job_processing(self, result: ComponentTestResult):
        """Test job processing capabilities."""
        try:
            # Test job submission
            job_data = {
                "job_type": "document_processing",
                "document_id": "test_doc_123",
                "parameters": {"extract_text": True}
            }
            response = requests.post(f"{self.worker_url}/jobs", json=job_data, timeout=10)
            
            if response.status_code in [200, 201, 202]:
                result.add_test_result("job_submission", True, f"Job submission successful: {response.status_code}")
            else:
                result.add_test_result("job_submission", False, f"Job submission failed: {response.status_code}")
                
        except Exception as e:
            result.add_test_result("job_processing", False, error=str(e))

class DatabaseIntegrationTester:
    """Test database integration and external API connectivity."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        
    async def test_supabase_connection(self, result: ComponentTestResult):
        """Test Supabase connection establishment."""
        try:
            from supabase import create_client, Client
            import os
            
            # Load environment variables
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                result.add_test_result("supabase_connection", False, "Missing Supabase credentials")
                return
                
            # Test connection
            supabase: Client = create_client(supabase_url, supabase_key)
            
            # Test basic query
            response = supabase.table("users").select("*").limit(1).execute()
            
            if response.data is not None:
                result.add_test_result("supabase_connection", True, f"Supabase connection successful: {len(response.data)} records")
            else:
                result.add_test_result("supabase_connection", False, "Supabase query returned no data")
                
        except Exception as e:
            result.add_test_result("supabase_connection", False, error=str(e))
    
    async def test_database_schema(self, result: ComponentTestResult):
        """Test database schema validation."""
        try:
            from supabase import create_client, Client
            import os
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                result.add_test_result("database_schema", False, "Missing Supabase credentials")
                return
                
            supabase: Client = create_client(supabase_url, supabase_key)
            
            # Test key tables exist
            tables_to_test = ["users", "documents", "conversations"]
            
            for table in tables_to_test:
                try:
                    response = supabase.table(table).select("*").limit(1).execute()
                    result.add_test_result(f"table_{table}", True, f"Table {table} accessible")
                except Exception as e:
                    result.add_test_result(f"table_{table}", False, f"Table {table} error: {str(e)}")
                    
        except Exception as e:
            result.add_test_result("database_schema", False, error=str(e))

class VercelFrontendTester:
    """Test Vercel frontend integration and React/Next.js functionality."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.frontend_url = self._get_frontend_url()
        
    def _get_frontend_url(self) -> str:
        """Get Vercel frontend URL based on environment."""
        if self.environment == "production":
            return "https://insurance-navigator.vercel.app"
        elif self.environment == "staging":
            return "https://insurance-navigator-staging.vercel.app"
        else:  # development
            return "http://localhost:3000"
    
    async def test_frontend_startup(self, result: ComponentTestResult):
        """Test frontend application startup."""
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                result.add_test_result("frontend_startup", True, f"Frontend accessible: {response.status_code}")
            else:
                result.add_test_result("frontend_startup", False, f"Frontend startup failed: {response.status_code}")
                
        except Exception as e:
            result.add_test_result("frontend_startup", False, error=str(e))
    
    async def test_vercel_cli_setup(self, result: ComponentTestResult):
        """Test Vercel CLI setup and configuration."""
        try:
            # Check if Vercel CLI is installed
            result_vercel = subprocess.run(["vercel", "--version"], capture_output=True, text=True)
            if result_vercel.returncode == 0:
                result.add_test_result("vercel_cli_installed", True, f"Vercel CLI version: {result_vercel.stdout.strip()}")
            else:
                result.add_test_result("vercel_cli_installed", False, "Vercel CLI not installed")
                
            # Check Vercel project configuration
            if os.path.exists("vercel.json"):
                result.add_test_result("vercel_config", True, "Vercel configuration file exists")
            else:
                result.add_test_result("vercel_config", False, "Vercel configuration file missing")
                
        except Exception as e:
            result.add_test_result("vercel_cli_setup", False, error=str(e))

class CrossPlatformCommunicationTester:
    """Test cross-platform communication between Vercel and Render."""
    
    def __init__(self, frontend_url: str, backend_url: str):
        self.frontend_url = frontend_url
        self.backend_url = backend_url
        
    async def test_api_connectivity(self, result: ComponentTestResult):
        """Test API connectivity between frontend and backend."""
        try:
            # Test if frontend can reach backend API
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                result.add_test_result("api_connectivity", True, f"Backend API reachable: {response.status_code}")
            else:
                result.add_test_result("api_connectivity", False, f"Backend API unreachable: {response.status_code}")
                
        except Exception as e:
            result.add_test_result("api_connectivity", False, error=str(e))
    
    async def test_cors_configuration(self, result: ComponentTestResult):
        """Test CORS configuration for cross-platform communication."""
        try:
            # Test CORS preflight request
            headers = {
                "Origin": self.frontend_url,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
            response = requests.options(f"{self.backend_url}/auth/login", headers=headers, timeout=10)
            
            if response.status_code in [200, 204]:
                result.add_test_result("cors_configuration", True, f"CORS preflight successful: {response.status_code}")
            else:
                result.add_test_result("cors_configuration", False, f"CORS preflight failed: {response.status_code}")
                
        except Exception as e:
            result.add_test_result("cors_configuration", False, error=str(e))

class ComponentTestSuite:
    """Main component test suite orchestrator."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.results = []
        
    async def run_all_tests(self):
        """Run all component tests for the specified environment."""
        logger.info(f"Starting component testing for {self.environment} environment")
        
        # Test Render API
        api_result = ComponentTestResult("render_api", "render", self.environment)
        api_tester = RenderAPITester(self.environment)
        
        await api_tester.test_health_endpoints(api_result)
        await api_tester.test_authentication_endpoints(api_result)
        await api_tester.test_document_endpoints(api_result)
        await api_tester.test_ai_chat_endpoints(api_result)
        await api_tester.test_error_handling(api_result)
        api_result.finalize()
        self.results.append(api_result)
        
        # Test Render Workers
        workers_result = ComponentTestResult("render_workers", "render", self.environment)
        workers_tester = RenderWorkersTester(self.environment)
        
        await workers_tester.test_worker_initialization(workers_result)
        await workers_tester.test_job_processing(workers_result)
        workers_result.finalize()
        self.results.append(workers_result)
        
        # Test Database Integration
        db_result = ComponentTestResult("database_integration", "render", self.environment)
        db_tester = DatabaseIntegrationTester(self.environment)
        
        await db_tester.test_supabase_connection(db_result)
        await db_tester.test_database_schema(db_result)
        db_result.finalize()
        self.results.append(db_result)
        
        # Test Vercel Frontend
        frontend_result = ComponentTestResult("vercel_frontend", "vercel", self.environment)
        frontend_tester = VercelFrontendTester(self.environment)
        
        await frontend_tester.test_frontend_startup(frontend_result)
        await frontend_tester.test_vercel_cli_setup(frontend_result)
        frontend_result.finalize()
        self.results.append(frontend_result)
        
        # Test Cross-Platform Communication
        comm_result = ComponentTestResult("cross_platform_communication", "both", self.environment)
        comm_tester = CrossPlatformCommunicationTester(
            frontend_tester.frontend_url,
            api_tester.base_url
        )
        
        await comm_tester.test_api_connectivity(comm_result)
        await comm_tester.test_cors_configuration(comm_result)
        comm_result.finalize()
        self.results.append(comm_result)
        
        # Generate summary report
        self._generate_report()
        
    def _generate_report(self):
        """Generate comprehensive test report."""
        total_tests = sum(len(result.tests) for result in self.results)
        passed_tests = sum(len([t for t in result.tests if t["passed"]]) for result in self.results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "summary": {
                "total_components": len(self.results),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": success_rate
            },
            "components": [result.to_dict() for result in self.results]
        }
        
        # Save report
        os.makedirs("test-results", exist_ok=True)
        report_path = f"test-results/component_test_report_{self.environment}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Component testing completed for {self.environment}")
        logger.info(f"Success rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests)")
        logger.info(f"Report saved to: {report_path}")
        
        return report

async def main():
    """Main execution function."""
    print("=" * 80)
    print("INSURANCE NAVIGATOR - PHASE 2 COMPONENT TESTING")
    print("=" * 80)
    print(f"Project Root: {project_root}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Test development environment
    dev_suite = ComponentTestSuite("development")
    await dev_suite.run_all_tests()
    
    # Test staging environment
    staging_suite = ComponentTestSuite("staging")
    await staging_suite.run_all_tests()
    
    print("\n" + "=" * 80)
    print("PHASE 2 COMPONENT TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
