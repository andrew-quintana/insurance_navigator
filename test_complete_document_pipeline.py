#!/usr/bin/env python3
"""
Complete Document Pipeline Test
Tests both user document upload and regulatory document upload with authentication
"""

import requests
import json
import time
import io
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"  # Will test locally first, then Render
RENDER_URL = "***REMOVED***"
TEST_EMAIL = f"pipeline_{uuid.uuid4().hex[:8]}@example.com"  # Unique email for each test
TEST_PASSWORD = "testpass123"
TEST_NAME = "Pipeline Test User"

class DocumentPipelineTest:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def authenticate(self) -> bool:
        """Authenticate and get JWT token"""
        print(f"\n🔐 Testing Authentication on {self.base_url}")
        
        try:
            # Try login first
            login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
            response = requests.post(f"{self.base_url}/login", json=login_data, timeout=15)
            
            if response.status_code == 200:
                self.auth_token = response.json().get("access_token")
                self.log_test("Authentication - Login", "PASS", {
                    "email": TEST_EMAIL,
                    "token_length": len(self.auth_token) if self.auth_token else 0
                })
                return True
            elif response.status_code == 401:
                # User doesn't exist, try registration
                print("   User not found, attempting registration...")
                register_data = {
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "full_name": TEST_NAME
                }
                response = requests.post(f"{self.base_url}/register", json=register_data, timeout=15)
                
                if response.status_code == 200:
                    self.auth_token = response.json().get("access_token")
                    self.log_test("Authentication - Registration", "PASS", {
                        "email": TEST_EMAIL,
                        "token_length": len(self.auth_token) if self.auth_token else 0
                    })
                    return True
                else:
                    self.log_test("Authentication - Registration", "FAIL", {
                        "status_code": response.status_code,
                        "error": response.text[:200]
                    })
                    return False
            else:
                self.log_test("Authentication - Login", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })
                return False
                
        except Exception as e:
            self.log_test("Authentication", "FAIL", f"Exception: {str(e)}")
            return False
    
    def create_test_document(self, filename: str, content: str) -> io.BytesIO:
        """Create a test document file"""
        return io.BytesIO(content.encode('utf-8'))
    
    def test_user_document_upload(self) -> bool:
        """Test user document upload with backend orchestration"""
        print(f"\n📄 Testing User Document Upload")
        
        if not self.auth_token:
            self.log_test("User Document Upload", "SKIP", "No authentication token")
            return False
        
        try:
            # Create test insurance policy document
            policy_content = """
INSURANCE POLICY DOCUMENT
Policy Number: POL-123456789
Policyholder: John Doe
Coverage Type: Health Insurance

COVERAGE DETAILS:
- Medical Services: $5,000 deductible, 80% coverage after deductible
- Prescription Drugs: $25 copay for generic, $50 for brand name
- Emergency Room: $500 copay
- Specialist Visits: $40 copay

NETWORK PROVIDERS:
This policy includes access to our nationwide network of healthcare providers.
Please refer to the provider directory for in-network options.

EXCLUSIONS:
- Cosmetic procedures
- Experimental treatments
- Pre-existing conditions (first 12 months)
"""
            
            # Test file upload
            files = {
                'file': ('test_policy.txt', self.create_test_document('test_policy.txt', policy_content), 'text/plain')
            }
            
            headers = {
                'Authorization': f'Bearer {self.auth_token}'
            }
            
            data = {
                'document_type': 'policy',
                'metadata': json.dumps({
                    'test_upload': True,
                    'policy_number': 'POL-123456789',
                    'upload_source': 'automated_test'
                })
            }
            
            response = requests.post(
                f"{self.base_url}/upload-document-backend",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("User Document Upload", "PASS", {
                    "document_id": result.get("document_id"),
                    "upload_status": result.get("upload_status"),
                    "processing_status": result.get("processing_status"),
                    "file_size": result.get("file_size")
                })
                return True
            else:
                self.log_test("User Document Upload", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:500]
                })
                return False
                
        except Exception as e:
            self.log_test("User Document Upload", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_regulatory_document_upload(self) -> bool:
        """Test regulatory document upload"""
        print(f"\n📋 Testing Regulatory Document Upload")
        
        if not self.auth_token:
            self.log_test("Regulatory Document Upload", "SKIP", "No authentication token")
            return False
        
        try:
            # Create test regulatory document
            regulatory_content = """
HEALTHCARE REGULATION DOCUMENT
Title: Medicare Coverage Guidelines
Effective Date: January 1, 2024

COVERAGE REQUIREMENTS:

1. PREVENTIVE CARE
Medicare covers 100% of preventive services including:
- Annual wellness visits
- Screening mammograms
- Colonoscopy screening
- Flu shots and vaccines

2. PRESCRIPTION DRUG COVERAGE
Medicare Part D provides prescription drug coverage with:
- Standard deductible: $505 (2024)
- Coverage gap threshold: $5,030
- Catastrophic coverage threshold: $8,000

3. NETWORK REQUIREMENTS
Medicare Advantage plans must maintain adequate provider networks
including specialists within reasonable travel distances.

4. APPEALS PROCESS
Beneficiaries have the right to appeal coverage decisions through
a standardized appeals process with specific timeframes.
"""
            
            files = {
                'file': ('medicare_guidelines.txt', self.create_test_document('medicare_guidelines.txt', regulatory_content), 'text/plain')
            }
            
            headers = {
                'Authorization': f'Bearer {self.auth_token}'
            }
            
            data = {
                'title': 'Medicare Coverage Guidelines 2024',
                'document_type': 'regulation',
                'source_url': 'https://cms.gov/medicare-guidelines-2024',
                'effective_date': '2024-01-01',
                'metadata': json.dumps({
                    'test_upload': True,
                    'regulation_type': 'medicare_coverage',
                    'upload_source': 'automated_test'
                })
            }
            
            response = requests.post(
                f"{self.base_url}/upload-regulatory-document",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Regulatory Document Upload", "PASS", {
                    "document_id": result.get("document_id"),
                    "title": result.get("title"),
                    "processing_status": result.get("processing_status"),
                    "file_size": result.get("file_size")
                })
                return True
            else:
                self.log_test("Regulatory Document Upload", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:500]
                })
                return False
                
        except Exception as e:
            self.log_test("Regulatory Document Upload", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_health_check(self) -> bool:
        """Test health endpoint"""
        print(f"\n🏥 Testing Health Check")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                self.log_test("Health Check", "PASS", {
                    "status": health_data.get("status"),
                    "version": health_data.get("version"),
                    "features": health_data.get("features", {})
                })
                return True
            else:
                self.log_test("Health Check", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })
                return False
                
        except Exception as e:
            self.log_test("Health Check", "FAIL", f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        print(f"🚀 Starting Complete Document Pipeline Test")
        print(f"🎯 Target: {self.base_url}")
        print(f"📅 Timestamp: {datetime.now().isoformat()}")
        
        # Run tests in sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("Authentication", self.authenticate),
            ("User Document Upload", self.test_user_document_upload),
            ("Regulatory Document Upload", self.test_regulatory_document_upload),
        ]
        
        results_summary = {"passed": 0, "failed": 0, "skipped": 0}
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    results_summary["passed"] += 1
                else:
                    results_summary["failed"] += 1
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                results_summary["failed"] += 1
        
        print(f"\n📊 Test Results Summary:")
        print(f"   ✅ Passed: {results_summary['passed']}")
        print(f"   ❌ Failed: {results_summary['failed']}")
        print(f"   ⚠️  Skipped: {results_summary['skipped']}")
        
        return {
            "summary": results_summary,
            "detailed_results": self.test_results,
            "timestamp": datetime.now().isoformat(),
            "target_url": self.base_url
        }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "render":
        tester = DocumentPipelineTest(RENDER_URL)
        tester.run_all_tests()
    else:
        tester = DocumentPipelineTest(BASE_URL)
        tester.run_all_tests() 