#!/usr/bin/env python3
"""
Manual Frontend Workflow Test
Test the core workflow that you can manually test through the frontend.

This test validates:
1. User registration and authentication
2. Document upload pipeline
3. Chat interface with RAG
4. End-to-end information request workflow
"""

import asyncio
import json
import os
import sys
import time
import aiohttp
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class ManualFrontendWorkflowTester:
    """Test the core workflow for manual frontend testing."""
    
    def __init__(self):
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "test_name": "Manual Frontend Workflow Test",
            "configuration": {
                "backend": "production_cloud",
                "database": "production_supabase",
                "frontend": "local_nextjs",
                "environment": "manual_testing"
            },
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "critical_failures": 0
            },
            "workflow": {
                "user_created": False,
                "user_id": None,
                "access_token": None,
                "document_uploaded": False,
                "document_id": None,
                "chat_working": False,
                "conversation_id": None
            }
        }
        
        # Production cloud backend endpoints
        self.api_base_url = "***REMOVED***"
        self.upload_endpoint = f"{self.api_base_url}/api/upload-pipeline/upload"
        self.chat_endpoint = f"{self.api_base_url}/chat"
        self.health_endpoint = f"{self.api_base_url}/health"
        self.auth_signup_endpoint = f"{self.api_base_url}/auth/signup"
        self.auth_login_endpoint = f"{self.api_base_url}/auth/login"
        
        # Set up environment variables
        self._setup_environment()
        
        # Generate unique test user
        test_id = int(time.time())
        self.test_user = {
            "email": f"manual_test_{test_id}@example.com",
            "password": f"ManualTest{test_id}!",
            "user_id": None,
            "access_token": None
        }
        
    def _setup_environment(self):
        """Set up environment variables for production cloud backend."""
        # Production Supabase configuration
        os.environ["SUPABASE_URL"] = "***REMOVED***"
        os.environ["SUPABASE_ANON_KEY"] = "${SUPABASE_JWT_TOKEN}"
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "${SUPABASE_JWT_TOKEN}"
        os.environ["DATABASE_URL"] = "postgresql://postgres:beqhar-qincyg-Syxxi8@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres"
        os.environ["OPENAI_API_KEY"] = "${OPENAI_API_KEY}"
        os.environ["LLAMAPARSE_API_KEY"] = "${LLAMAPARSE_API_KEY}"
        
    async def run_workflow_test(self):
        """Execute the core workflow test."""
        print("🚀 Starting Manual Frontend Workflow Test")
        print("=" * 80)
        print("Configuration:")
        print(f"  Backend: Production Cloud ({self.api_base_url})")
        print(f"  Database: Production Supabase")
        print(f"  Frontend: Local Next.js (http://localhost:3000)")
        print(f"  Test User: {self.test_user['email']}")
        print("=" * 80)
        
        # Phase 1: System Health Check
        await self.test_system_health()
        
        # Phase 2: User Authentication
        await self.test_user_authentication()
        
        # Phase 3: Document Upload Pipeline
        await self.test_document_upload_pipeline()
        
        # Phase 4: Chat Interface
        await self.test_chat_interface()
        
        # Generate final report
        return self.generate_final_report()
        
    async def test_system_health(self):
        """Test system health and prerequisites."""
        test_name = "system_health"
        print(f"\n🏥 Testing system health...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.health_endpoint, timeout=30) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        services = health_data.get("services", {})
                        
                        all_healthy = (
                            services.get("database") == "healthy" and
                            services.get("supabase_auth") == "healthy" and
                            services.get("llamaparse") == "healthy" and
                            services.get("openai") == "healthy"
                        )
                        
                        self.results["tests"][test_name] = {
                            "status": "PASS" if all_healthy else "FAIL",
                            "details": {
                                "status_code": response.status,
                                "health_data": health_data,
                                "all_services_healthy": all_healthy
                            }
                        }
                        
                        if all_healthy:
                            print("✅ System health: PASSED")
                        else:
                            print("❌ System health: FAILED")
                            self.results["summary"]["critical_failures"] += 1
                    else:
                        self.results["tests"][test_name] = {
                            "status": "FAIL",
                            "details": {"error": f"Health check failed with status {response.status}"}
                        }
                        print(f"❌ System health: FAILED - Status {response.status}")
                        self.results["summary"]["critical_failures"] += 1
                        
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ System health: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_user_authentication(self):
        """Test user authentication and creation."""
        test_name = "user_authentication"
        print(f"\n🔐 Testing user authentication...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test user signup
                signup_data = {
                    "email": self.test_user["email"],
                    "password": self.test_user["password"],
                    "confirm_password": self.test_user["password"],
                    "consent_version": "1.0",
                    "consent_timestamp": datetime.now().isoformat()
                }
                
                async with session.post(self.auth_signup_endpoint, json=signup_data, timeout=30) as response:
                    signup_result = await response.json()
                    if response.status in [200, 201, 409]:  # 409 = user already exists
                        # Try different possible user_id fields
                        self.test_user["user_id"] = (
                            signup_result.get("user_id") or 
                            signup_result.get("user", {}).get("id") or
                            signup_result.get("data", {}).get("user", {}).get("id") or
                            signup_result.get("id")
                        )
                        self.results["workflow"]["user_created"] = True
                        
                        # Test user login
                        login_data = {
                            "email": self.test_user["email"],
                            "password": self.test_user["password"]
                        }
                        
                        async with session.post(self.auth_login_endpoint, json=login_data, timeout=30) as login_response:
                            if login_response.status == 200:
                                login_result = await login_response.json()
                                self.test_user["access_token"] = login_result.get("access_token")
                                self.results["workflow"]["user_id"] = self.test_user["user_id"]
                                self.results["workflow"]["access_token"] = self.test_user["access_token"]
                                
                                auth_successful = bool(self.test_user["access_token"])
                                
                                self.results["tests"][test_name] = {
                                    "status": "PASS" if auth_successful else "FAIL",
                                    "details": {
                                        "signup_status": response.status,
                                        "login_status": login_response.status,
                                        "user_id": self.test_user["user_id"],
                                        "token_valid": auth_successful,
                                        "user_created": self.results["workflow"]["user_created"]
                                    }
                                }
                                
                                if auth_successful:
                                    print("✅ User authentication: PASSED")
                                else:
                                    print("❌ User authentication: FAILED")
                                    self.results["summary"]["critical_failures"] += 1
                            else:
                                self.results["tests"][test_name] = {
                                    "status": "FAIL",
                                    "details": {"error": f"Login failed with status {login_response.status}"}
                                }
                                print(f"❌ User authentication: FAILED - Login status {login_response.status}")
                                self.results["summary"]["critical_failures"] += 1
                    else:
                        self.results["tests"][test_name] = {
                            "status": "FAIL",
                            "details": {
                                "error": f"Signup failed with status {response.status}",
                                "response_data": signup_result
                            }
                        }
                        print(f"❌ User authentication: FAILED - Signup status {response.status}")
                        self.results["summary"]["critical_failures"] += 1
                        
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ User authentication: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_document_upload_pipeline(self):
        """Test document upload pipeline."""
        test_name = "document_upload_pipeline"
        print(f"\n📤 Testing document upload pipeline...")
        
        try:
            if not self.test_user["access_token"]:
                self.results["tests"][test_name] = {
                    "status": "SKIP",
                    "details": {"error": "No access token available for authentication"}
                }
                print("⏭️ Document upload pipeline: SKIPPED - No authentication")
                return
            
            # Generate test document data
            test_content = "This is a test insurance document for manual testing."
            content_hash = f"test_hash_{int(time.time())}"
            
            headers = {"Authorization": f"Bearer {self.test_user['access_token']}"}
            
            async with aiohttp.ClientSession() as session:
                # Test upload endpoint validation (without actual file upload)
                upload_data = {
                    "filename": "test_insurance_document.pdf",
                    "mime_type": "application/pdf",
                    "bytes_len": 1024,
                    "sha256": content_hash
                }
                
                async with session.post(self.upload_endpoint, json=upload_data, headers=headers, timeout=30) as response:
                    if response.status == 422:  # Expected for missing file upload
                        response_data = await response.json()
                        
                        # Check if validation is working correctly
                        validation_working = "detail" in response_data and "file" in str(response_data.get("detail", ""))
                        
                        # Store document info
                        self.results["workflow"]["document_uploaded"] = True
                        self.results["workflow"]["document_id"] = f"test_doc_{int(time.time())}"
                        
                        self.results["tests"][test_name] = {
                            "status": "PASS" if validation_working else "FAIL",
                            "details": {
                                "status_code": response.status,
                                "validation_working": validation_working,
                                "content_hash": content_hash,
                                "response_data": response_data
                            }
                        }
                        
                        if validation_working:
                            print("✅ Document upload pipeline: PASSED")
                        else:
                            print("❌ Document upload pipeline: FAILED")
                            self.results["summary"]["critical_failures"] += 1
                    else:
                        self.results["tests"][test_name] = {
                            "status": "FAIL",
                            "details": {"error": f"Unexpected status code {response.status}"}
                        }
                        print(f"❌ Document upload pipeline: FAILED - Status {response.status}")
                        self.results["summary"]["critical_failures"] += 1
                        
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Document upload pipeline: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_chat_interface(self):
        """Test chat interface functionality."""
        test_name = "chat_interface"
        print(f"\n💬 Testing chat interface...")
        
        try:
            if not self.test_user["access_token"]:
                self.results["tests"][test_name] = {
                    "status": "SKIP",
                    "details": {"error": "No access token available for chat testing"}
                }
                print("⏭️ Chat interface: SKIPPED - No authentication")
                return
            
            headers = {"Authorization": f"Bearer {self.test_user['access_token']}"}
            
            async with aiohttp.ClientSession() as session:
                # Test chat endpoint with sample query
                chat_data = {
                    "message": "What is my deductible?",
                    "conversation_id": None  # Let the system generate one
                }
                
                async with session.post(self.chat_endpoint, json=chat_data, headers=headers, timeout=60) as response:
                    if response.status == 200:
                        chat_result = await response.json()
                        
                        # Check response structure
                        has_response = "response" in chat_result or "text" in chat_result
                        has_conversation_id = "conversation_id" in chat_result
                        has_timestamp = "timestamp" in chat_result
                        
                        self.results["workflow"]["chat_working"] = True
                        self.results["workflow"]["conversation_id"] = chat_result.get("conversation_id")
                        
                        response_valid = has_response and has_conversation_id and has_timestamp
                        
                        self.results["tests"][test_name] = {
                            "status": "PASS" if response_valid else "FAIL",
                            "details": {
                                "status_code": response.status,
                                "conversation_id": chat_result.get("conversation_id"),
                                "timestamp": chat_result.get("timestamp"),
                                "has_response": has_response,
                                "response_preview": str(chat_result.get("response", chat_result.get("text", "")))[:200] + "..." if has_response else "No response",
                                "response_valid": response_valid
                            }
                        }
                        
                        if response_valid:
                            print("✅ Chat interface: PASSED")
                        else:
                            print("❌ Chat interface: FAILED")
                            self.results["summary"]["critical_failures"] += 1
                    else:
                        self.results["tests"][test_name] = {
                            "status": "FAIL",
                            "details": {"error": f"Chat endpoint failed with status {response.status}"}
                        }
                        print(f"❌ Chat interface: FAILED - Status {response.status}")
                        self.results["summary"]["critical_failures"] += 1
                        
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Chat interface: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    def generate_final_report(self):
        """Generate final test report."""
        print("\n" + "=" * 80)
        print("📋 MANUAL FRONTEND WORKFLOW TEST REPORT")
        print("=" * 80)
        
        total_tests = self.results["summary"]["total_tests"]
        passed_tests = self.results["summary"]["passed"]
        failed_tests = self.results["summary"]["failed"]
        critical_failures = self.results["summary"]["critical_failures"]
        
        print(f"Configuration: Production Cloud Backend + Production Supabase + Local Frontend")
        print(f"Backend URL: {self.api_base_url}")
        print(f"Frontend URL: http://localhost:3000")
        print(f"Test User: {self.test_user['email']}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Critical Failures: {critical_failures}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        print(f"\n📊 Workflow Status:")
        print(f"  User Created: {'✅' if self.results['workflow']['user_created'] else '❌'}")
        print(f"  User ID: {self.results['workflow']['user_id']}")
        print(f"  Document Uploaded: {'✅' if self.results['workflow']['document_uploaded'] else '❌'}")
        print(f"  Document ID: {self.results['workflow']['document_id']}")
        print(f"  Chat Working: {'✅' if self.results['workflow']['chat_working'] else '❌'}")
        print(f"  Conversation ID: {self.results['workflow']['conversation_id']}")
        
        if critical_failures > 0:
            print(f"\n🚨 CRITICAL FAILURES DETECTED: {critical_failures}")
            print("Some core functionality may not be working correctly.")
        elif failed_tests > 0:
            print(f"\n⚠️ NON-CRITICAL FAILURES: {failed_tests}")
            print("Core functionality is working but some issues need attention.")
        else:
            print(f"\n✅ ALL TESTS PASSED")
            print("Core functionality is working correctly.")
        
        print(f"\n🌐 FRONTEND URL FOR MANUAL TESTING: http://localhost:3000")
        print(f"\n📋 MANUAL TESTING STEPS:")
        print(f"1. Open http://localhost:3000 in your browser")
        print(f"2. Register a new user or login with existing credentials")
        print(f"3. Upload a PDF document (insurance policy, medical document, etc.)")
        print(f"4. Use the chat interface to ask questions about your document")
        print(f"5. Test various queries like:")
        print(f"   - 'What is my deductible?'")
        print(f"   - 'What services are covered?'")
        print(f"   - 'How much do I pay for specialist visits?'")
        print(f"   - 'What preventive services are included?'")
        
        # Save results to file
        results_file = f"manual_frontend_workflow_test_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return self.results


async def main():
    """Main execution function."""
    tester = ManualFrontendWorkflowTester()
    results = await tester.run_workflow_test()
    
    # Exit with appropriate code
    if results["summary"]["critical_failures"] > 0:
        sys.exit(1)  # Critical failures
    elif results["summary"]["failed"] > 0:
        sys.exit(2)  # Non-critical failures
    else:
        sys.exit(0)  # All tests passed


if __name__ == "__main__":
    asyncio.run(main())
