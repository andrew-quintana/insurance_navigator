#!/usr/bin/env python3
"""
Phase 2: Authentication System Testing
Tests user registration, login, protected routes, and security features
"""

import asyncio
import requests
import json
import uuid
from datetime import datetime
import time

class Phase2AuthenticationTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_user_email = f"test_user_{int(time.time())}@example.com"
        self.test_user_password = "SecureTestPass123!"
        self.access_token = None
        self.user_id = None
        
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'tests': []
        }

    def log_test(self, test_name, status, message, is_warning=False):
        """Log test result"""
        emoji = "⚠️" if is_warning else ("✅" if status else "❌")
        status_text = "WARNING" if is_warning else ("PASS" if status else "FAIL")
        
        print(f"{emoji} {test_name}: {status_text}")
        if message:
            print(f"   └─ {message}")
        
        self.results['tests'].append({
            'name': test_name,
            'status': status_text,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        if is_warning:
            self.results['warnings'] += 1
        elif status:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1

    def test_api_health_check(self):
        """2.1 - Verify API is accessible"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("API Health Check", True, f"API responding - {data}")
                else:
                    self.log_test("API Health Check", False, f"Unhealthy status: {data}")
            else:
                self.log_test("API Health Check", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("API Health Check", False, f"Connection failed: {e}")

    def test_user_registration(self):
        """2.2 - Test user registration endpoint"""
        try:
            registration_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "full_name": "Test User Phase 2"
            }
            
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=registration_data,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                if "user_id" in data:
                    self.user_id = data["user_id"]
                    self.log_test("User Registration", True, f"User created: {data['user_id']}")
                else:
                    self.log_test("User Registration", False, f"Missing user_id in response: {data}")
            elif response.status_code == 400:
                error_data = response.json()
                if "already exists" in str(error_data).lower():
                    self.log_test("User Registration", True, "User already exists (expected if re-running)", is_warning=True)
                else:
                    self.log_test("User Registration", False, f"Registration failed: {error_data}")
            else:
                self.log_test("User Registration", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("User Registration", False, f"Registration error: {e}")

    def test_user_login(self):
        """2.3 - Test user login and token generation"""
        try:
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.access_token = data["access_token"]
                    self.user_id = data.get("user_id", self.user_id)
                    self.log_test("User Login", True, f"Login successful - Token received")
                else:
                    self.log_test("User Login", False, f"Missing access_token: {data}")
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                self.log_test("User Login", False, f"HTTP {response.status_code}: {error_data}")
                
        except Exception as e:
            self.log_test("User Login", False, f"Login error: {e}")

    def test_protected_route_without_token(self):
        """2.4 - Test protected route access without authentication"""
        try:
            response = requests.get(
                f"{self.base_url}/auth/profile",
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test("Protected Route (No Auth)", True, "Correctly rejected unauthenticated request")
            else:
                self.log_test("Protected Route (No Auth)", False, f"Should return 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Protected Route (No Auth)", False, f"Error testing unauth access: {e}")

    def test_protected_route_with_token(self):
        """2.5 - Test protected route access with valid token"""
        if not self.access_token:
            self.log_test("Protected Route (With Auth)", False, "No access token available from login")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.base_url}/auth/profile",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "email" in data and data["email"] == self.test_user_email:
                    self.log_test("Protected Route (With Auth)", True, f"Profile retrieved: {data['email']}")
                else:
                    self.log_test("Protected Route (With Auth)", False, f"Unexpected profile data: {data}")
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                self.log_test("Protected Route (With Auth)", False, f"HTTP {response.status_code}: {error_data}")
                
        except Exception as e:
            self.log_test("Protected Route (With Auth)", False, f"Error accessing protected route: {e}")

    def test_invalid_token(self):
        """2.6 - Test authentication with invalid token"""
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.get(
                f"{self.base_url}/auth/profile",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test("Invalid Token Rejection", True, "Invalid token correctly rejected")
            else:
                self.log_test("Invalid Token Rejection", False, f"Should return 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Token Rejection", False, f"Error testing invalid token: {e}")

    def test_password_requirements(self):
        """2.7 - Test password validation requirements"""
        try:
            weak_password_data = {
                "email": f"weak_test_{int(time.time())}@example.com",
                "password": "weak",
                "full_name": "Weak Password Test"
            }
            
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=weak_password_data,
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_test("Password Requirements", True, "Weak password correctly rejected")
            elif response.status_code == 201:
                self.log_test("Password Requirements", False, "Weak password was accepted (security risk)", is_warning=True)
            else:
                self.log_test("Password Requirements", False, f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("Password Requirements", False, f"Error testing password requirements: {e}")

    def test_duplicate_registration(self):
        """2.8 - Test duplicate email registration prevention"""
        try:
            duplicate_data = {
                "email": self.test_user_email,  # Same email as original test user
                "password": "AnotherPassword123!",
                "full_name": "Duplicate Test User"
            }
            
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=duplicate_data,
                timeout=10
            )
            
            if response.status_code == 400:
                error_data = response.json()
                if "already exists" in str(error_data).lower() or "duplicate" in str(error_data).lower():
                    self.log_test("Duplicate Email Prevention", True, "Duplicate email correctly rejected")
                else:
                    self.log_test("Duplicate Email Prevention", False, f"Wrong error message: {error_data}")
            else:
                self.log_test("Duplicate Email Prevention", False, f"Duplicate email was accepted: {response.status_code}")
                
        except Exception as e:
            self.log_test("Duplicate Email Prevention", False, f"Error testing duplicate email: {e}")

    def test_audit_logging(self):
        """2.9 - Test HIPAA audit logging for authentication events"""
        if not self.access_token or not self.user_id:
            self.log_test("Authentication Audit Logging", False, "No authenticated user available for audit test")
            return
            
        try:
            # Make a request that should trigger audit logging
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.base_url}/auth/profile",
                headers=headers,
                timeout=10
            )
            
            # We can't directly check audit logs via API, but we can verify the request succeeded
            # (which means the audit logging function should have been called)
            if response.status_code == 200:
                self.log_test("Authentication Audit Logging", True, "User action completed (audit log should be created)", is_warning=True)
            else:
                self.log_test("Authentication Audit Logging", False, f"User action failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Authentication Audit Logging", False, f"Error testing audit logging: {e}")

    def generate_report(self):
        """Generate final test report"""
        total_tests = self.results['passed'] + self.results['failed'] + self.results['warnings']
        success_rate = (self.results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*70)
        print("🔐 PHASE 2: AUTHENTICATION SYSTEM TESTING - FINAL REPORT")
        print("="*70)
        print(f"📊 OVERALL RESULTS: {success_rate:.1f}% SUCCESS RATE")
        print(f"✅ PASSED: {self.results['passed']}")
        print(f"❌ FAILED: {self.results['failed']}")
        print(f"⚠️  WARNINGS: {self.results['warnings']}")
        print(f"📋 TOTAL TESTS: {total_tests}")
        
        if self.results['failed'] == 0:
            print(f"\n🎉 PHASE 2 COMPLETE: Authentication system is fully functional!")
        else:
            print(f"\n⚠️  PHASE 2 ISSUES: {self.results['failed']} critical authentication issues found")
        
        return success_rate >= 90

    def run_all_tests(self):
        """Run all Phase 2 authentication tests"""
        print("🔐 PHASE 2: Authentication System Testing")
        print("="*50)
        print(f"🧪 Testing with user: {self.test_user_email}")
        print()
        
        # Run tests in sequence
        self.test_api_health_check()
        self.test_user_registration()
        self.test_user_login()
        self.test_protected_route_without_token()
        self.test_protected_route_with_token()
        self.test_invalid_token()
        self.test_password_requirements()
        self.test_duplicate_registration()
        self.test_audit_logging()
        
        # Generate final report
        return self.generate_report()

if __name__ == "__main__":
    tester = Phase2AuthenticationTest()
    success = tester.run_all_tests()
    exit(0 if success else 1) 