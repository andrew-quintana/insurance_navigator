#!/usr/bin/env python3
"""
Comprehensive Test Suite for Insurance Navigator API
Tests all major functionality on the working Render deployment
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "***REMOVED***"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"
TEST_NAME = "Test User"

class InsuranceNavigatorTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        
        # Color coding for terminal output
        color = "🟢" if status == "PASS" else "🔴" if status == "FAIL" else "🟡"
        print(f"{color} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if response_data and isinstance(response_data, dict):
            print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
        print()

    def test_health_check(self):
        """Test the health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                services = data.get("services", {})
                
                self.log_test(
                    "Health Check", 
                    "PASS", 
                    f"Status: {status}, Services: {services}",
                    data
                )
                return True
            else:
                self.log_test("Health Check", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", "FAIL", f"Exception: {str(e)}")
            return False

    def test_registration(self):
        """Test user registration"""
        try:
            payload = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": TEST_NAME
            }
            
            response = self.session.post(
                f"{self.base_url}/register",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                
                self.log_test(
                    "User Registration", 
                    "PASS", 
                    f"Token received: {self.auth_token[:20]}...",
                    {"token_type": data.get("token_type")}
                )
                return True
            elif response.status_code == 400:
                # User might already exist, try login instead
                self.log_test("User Registration", "SKIP", "User already exists, will try login")
                return self.test_login()
            else:
                self.log_test("User Registration", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Registration", "FAIL", f"Exception: {str(e)}")
            return False

    def test_login(self):
        """Test user login"""
        try:
            payload = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(
                f"{self.base_url}/login",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                
                self.log_test(
                    "User Login", 
                    "PASS", 
                    f"Token received: {self.auth_token[:20]}...",
                    {"token_type": data.get("token_type")}
                )
                return True
            else:
                self.log_test("User Login", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Login", "FAIL", f"Exception: {str(e)}")
            return False

    def test_authenticated_endpoint(self):
        """Test authenticated endpoint (/me)"""
        if not self.auth_token:
            self.log_test("Authenticated Endpoint", "SKIP", "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(
                f"{self.base_url}/me",
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Authenticated Endpoint", 
                    "PASS", 
                    f"User: {data.get('email', 'unknown')}",
                    data
                )
                return True
            else:
                self.log_test("Authenticated Endpoint", "FAIL", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Authenticated Endpoint", "FAIL", f"Exception: {str(e)}")
            return False

    def test_regulatory_document_upload(self):
        """Test regulatory document upload via URL"""
        if not self.auth_token:
            self.log_test("Regulatory Document Upload", "SKIP", "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {
                "source_url": "https://www.medicaid.gov/sites/default/files/2021-01/sho21001.pdf",
                "title": "Test Medicaid Guidance Document",
                "document_type": "regulatory_document",
                "jurisdiction": "federal",
                "program": ["medicaid"],
                "metadata": {
                    "test": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/documents/upload-regulatory",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Regulatory Document Upload", 
                    "PASS", 
                    f"Document ID: {data.get('document_id')}, Processing: {data.get('vector_processing_status')}",
                    data
                )
                return True
            else:
                self.log_test("Regulatory Document Upload", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Regulatory Document Upload", "FAIL", f"Exception: {str(e)}")
            return False

    def test_chat_endpoint(self):
        """Test chat functionality"""
        if not self.auth_token:
            self.log_test("Chat Endpoint", "SKIP", "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {
                "message": "What Medicare plans are available in my area?",
                "context": {"test": True}
            }
            
            response = self.session.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("text", "")
                
                self.log_test(
                    "Chat Endpoint", 
                    "PASS", 
                    f"Response length: {len(response_text)} chars, Conversation ID: {data.get('conversation_id')}",
                    {"response_preview": response_text[:100] + "..."}
                )
                return True
            else:
                self.log_test("Chat Endpoint", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Chat Endpoint", "FAIL", f"Exception: {str(e)}")
            return False

    def test_api_documentation(self):
        """Test API documentation endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/docs", timeout=10)
            
            if response.status_code == 200:
                self.log_test(
                    "API Documentation", 
                    "PASS", 
                    f"Docs available, content length: {len(response.content)} bytes"
                )
                return True
            else:
                self.log_test("API Documentation", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("API Documentation", "FAIL", f"Exception: {str(e)}")
            return False

    def test_conversations_endpoint(self):
        """Test conversations listing"""
        if not self.auth_token:
            self.log_test("Conversations Endpoint", "SKIP", "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(
                f"{self.base_url}/conversations",
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                conversation_count = len(data) if isinstance(data, list) else 0
                
                self.log_test(
                    "Conversations Endpoint", 
                    "PASS", 
                    f"Found {conversation_count} conversations"
                )
                return True
            else:
                self.log_test("Conversations Endpoint", "FAIL", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Conversations Endpoint", "FAIL", f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting Comprehensive Insurance Navigator API Test Suite")
        print(f"🎯 Target: {self.base_url}")
        print("=" * 70)
        
        # Core functionality tests
        self.test_health_check()
        self.test_api_documentation()
        
        # Authentication flow
        auth_success = self.test_registration()
        if not auth_success:
            auth_success = self.test_login()
            
        # Authenticated endpoints
        if auth_success:
            self.test_authenticated_endpoint()
            self.test_chat_endpoint()
            self.test_conversations_endpoint()
            self.test_regulatory_document_upload()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary report"""
        print("=" * 70)
        print("📊 TEST SUMMARY REPORT")
        print("=" * 70)
        
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped = len([r for r in self.test_results if r["status"] == "SKIP"])
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "N/A")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   ❌ {result['test']}: {result['details']}")
        
        print(f"\n📅 Test completed at: {datetime.now().isoformat()}")
        print(f"🌐 API Base URL: {self.base_url}")
        
        # Save detailed results
        with open("test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        print("💾 Detailed results saved to: test_results.json")

if __name__ == "__main__":
    tester = InsuranceNavigatorTester()
    tester.run_all_tests() 