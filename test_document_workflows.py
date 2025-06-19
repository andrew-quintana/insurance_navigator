#!/usr/bin/env python3
"""
Focused test for document upload and vector processing workflows
Tests both user document upload and regulatory document upload with vector generation
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

BASE_URL = "***REMOVED***"
TEST_EMAIL = "doctest@example.com"
TEST_PASSWORD = "testpass123"
TEST_NAME = "Document Test User"

class DocumentWorkflowTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.auth_token = None
        
    def authenticate(self):
        """Get authentication token"""
        try:
            # Try login first
            login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
            response = requests.post(f"{self.base_url}/login", json=login_data, timeout=15)
            
            if response.status_code == 200:
                self.auth_token = response.json().get("access_token")
                print(f"✅ Authenticated: {self.auth_token[:20]}...")
                return True
            elif response.status_code == 401:
                # Try registration
                reg_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD, "full_name": TEST_NAME}
                response = requests.post(f"{self.base_url}/register", json=reg_data, timeout=15)
                if response.status_code == 200:
                    self.auth_token = response.json().get("access_token")
                    print(f"✅ Registered and authenticated: {self.auth_token[:20]}...")
                    return True
                    
            print(f"❌ Authentication failed: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_regulatory_document_upload(self):
        """Test regulatory document upload workflow"""
        print("\n🏛️ Testing Regulatory Document Upload...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {
                "source_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                "title": "Test Sample PDF Document",
                "document_type": "regulatory_document", 
                "jurisdiction": "federal",
                "program": ["medicaid"],
                "metadata": {
                    "test": True,
                    "workflow_test": "regulatory_upload",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            print(f"📤 Uploading: {payload['title']}")
            print(f"📍 URL: {payload['source_url']}")
            
            response = requests.post(
                f"{self.base_url}/api/documents/upload-regulatory",
                json=payload,
                headers=headers,
                timeout=60  # Longer timeout for document processing
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Regulatory Document Upload SUCCESS!")
                print(f"   📄 Document ID: {data.get('document_id')}")
                print(f"   🔄 Processing: {data.get('vector_processing_status')}")
                print(f"   📊 Vectors: {data.get('estimated_vectors', 'unknown')}")
                print(f"   💬 Message: {data.get('message')}")
                return data
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception during upload: {e}")
            return None
    
    def test_user_document_upload_via_unified(self):
        """Test user document upload via unified API"""
        print("\n👤 Testing User Document Upload (Unified API)...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test URL-based upload through unified API
            request_data = {
                "document_type": "user_document",
                "source_type": "url_download",
                "source_url": "https://www.africau.edu/images/default/sample.pdf",
                "title": "Test User Document Sample",
                "metadata": {
                    "test": True,
                    "workflow_test": "user_document_upload",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Use form data as required by unified endpoint
            data = {"request_data": json.dumps(request_data)}
            
            print(f"📤 Uploading: {request_data['title']}")
            print(f"📍 URL: {request_data['source_url']}")
            
            response = requests.post(
                f"{self.base_url}/api/documents/upload-unified",
                data=data,  # Using form data, no file upload
                headers=headers,
                timeout=60
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ User Document Upload SUCCESS!")
                print(f"   📄 Document ID: {data.get('document_id')}")
                print(f"   🔄 Processing: {data.get('vector_processing_status')}")
                print(f"   📊 Vectors: {data.get('estimated_vectors', 'unknown')}")
                print(f"   💬 Message: {data.get('message')}")
                return data
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception during upload: {e}")
            return None
    
    def test_vector_processing_status(self, document_id: str, document_type: str):
        """Check if vector processing completed for a document"""
        print(f"\n🔍 Checking vector processing for {document_type} document: {document_id}")
        
        # Give some time for processing
        print("⏳ Waiting 10 seconds for vector processing...")
        time.sleep(10)
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Check document status (this endpoint may not exist, so we'll catch errors)
            try:
                response = requests.get(
                    f"{self.base_url}/documents/{document_id}/status",
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    status_data = response.json()
                    print(f"📊 Document Status: {status_data}")
                    return status_data
            except:
                print("ℹ️  Document status endpoint not available")
            
            # Alternative: Try searching for the document to see if it's processed
            search_response = requests.post(
                f"{self.base_url}/search-documents",
                data={"query": "test", "limit": "10"},
                headers=headers,
                timeout=15
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                print(f"🔍 Search results: Found {len(search_data.get('results', []))} documents")
                return search_data
            else:
                print(f"⚠️  Search failed: {search_response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Status check error: {e}")
        
        return None
    
    def run_workflow_tests(self):
        """Run complete document workflow tests"""
        print("🚀 Starting Document Workflow Tests")
        print("=" * 60)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed")
            return
        
        results = {"regulatory": None, "user_document": None}
        
        # Test regulatory document upload
        print("\n" + "="*60)
        reg_result = self.test_regulatory_document_upload()
        results["regulatory"] = reg_result
        
        # Test user document upload
        print("\n" + "="*60)
        user_result = self.test_user_document_upload_via_unified()
        results["user_document"] = user_result
        
        # Check vector processing status
        if reg_result:
            self.test_vector_processing_status(
                reg_result.get('document_id'), 
                "regulatory"
            )
            
        if user_result:
            self.test_vector_processing_status(
                user_result.get('document_id'), 
                "user_document"
            )
        
        # Summary
        print("\n" + "="*60)
        print("📋 WORKFLOW TEST SUMMARY")
        print("="*60)
        
        reg_status = "✅ SUCCESS" if results["regulatory"] else "❌ FAILED"
        user_status = "✅ SUCCESS" if results["user_document"] else "❌ FAILED"
        
        print(f"🏛️  Regulatory Document Upload: {reg_status}")
        print(f"👤 User Document Upload: {user_status}")
        
        total_success = sum(1 for r in results.values() if r is not None)
        print(f"📊 Overall Success Rate: {total_success}/2 ({total_success/2*100:.0f}%)")
        
        if total_success == 2:
            print("\n🎉 ALL DOCUMENT WORKFLOWS WORKING!")
        elif total_success == 1:
            print("\n⚠️  PARTIAL SUCCESS - One workflow needs attention")
        else:
            print("\n❌ BOTH WORKFLOWS NEED FIXING")
        
        return results

if __name__ == "__main__":
    tester = DocumentWorkflowTester()
    tester.run_workflow_tests() 