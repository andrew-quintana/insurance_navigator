#!/usr/bin/env python3
"""
Focused test for regulatory document upload workflow.
Tests the core functionality with optimized parameters.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://insurance-navigator-api.onrender.com"
TEST_EMAIL = "regtest@example.com"
TEST_PASSWORD = "regtest123"

def test_auth():
    """Get authentication token"""
    try:
        # Try login first
        response = requests.post(
            f"{BASE_URL}/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()["access_token"]
        
        # If login fails, try registration
        response = requests.post(
            f"{BASE_URL}/register",
            json={
                "full_name": "Regulatory Test User",
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return response.json()["access_token"]
            
        return None
        
    except Exception as e:
        print(f"Auth error: {e}")
        return None

def test_minimal_regulatory_upload():
    """Test regulatory document upload with minimal, fast document"""
    
    print("🔐 Getting authentication token...")
    token = test_auth()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful")
    
    # Use a very small, simple document that processes quickly
    payload = {
        "source_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "title": "Test Regulatory Document - Minimal",
        "document_type": "regulatory_document",
        "jurisdiction": "federal",
        "program": ["medicaid"],
        "metadata": {
            "test_type": "minimal_processing",
            "expected_fast_processing": True,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    print("📤 Testing regulatory document upload...")
    print(f"📄 Document: {payload['title']}")
    print(f"🔗 URL: {payload['source_url']}")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/documents/upload-regulatory",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=45  # Allow reasonable time but not excessive
        )
        
        processing_time = time.time() - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - Regulatory upload workflow working!")
            print(f"📋 Document ID: {result.get('document_id', 'N/A')}")
            print(f"🔄 Processing method: {result.get('processing_method', 'N/A')}")
            print(f"📊 Vector status: {result.get('vector_processing_status', 'N/A')}")
            return True
            
        elif response.status_code == 502:
            print("❌ 502 Bad Gateway - Server overloaded or deployment issue")
            print("   This indicates the server is struggling with processing load")
            return False
            
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"📝 Response: {response.text[:300]}...")
            
            # Check for specific errors
            if "upload_policy_document" in response.text:
                print("🔧 DIAGNOSIS: Storage service method not found - need deployment fix")
            elif "timeout" in response.text.lower():
                print("🔧 DIAGNOSIS: Processing timeout - need performance optimization")
            else:
                print("🔧 DIAGNOSIS: Other processing error - check logs")
            
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️  TIMEOUT - Processing is taking too long (45+ seconds)")
        print("🔧 DIAGNOSIS: Need performance optimization or async processing")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_user_document_upload():
    """Test user document upload workflow"""
    
    print("\n👤 Testing User Document Upload...")
    
    token = test_auth()
    if not token:
        print("❌ Authentication failed")
        return False
    
    # Test with file upload (multipart)
    files = {'file': ('test.txt', b'This is a test document for user upload validation.', 'text/plain')}
    data = {
        'request_data': json.dumps({
            "document_type": "user_document",
            "source_type": "file_upload",
            "title": "Test User Document",
            "metadata": {
                "test_type": "user_upload_validation",
                "timestamp": datetime.now().isoformat()
            }
        })
    }
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/documents/upload-unified",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        processing_time = time.time() - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - User document upload working!")
            print(f"📋 Document ID: {result.get('document_id', 'N/A')}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"📝 Response: {response.text[:300]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️  TIMEOUT - User document processing too slow")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run focused regulatory and user document upload tests"""
    print("=" * 80)
    print("🧪 FOCUSED DOCUMENT UPLOAD WORKFLOW TEST")
    print("=" * 80)
    print(f"🌐 Testing API: {BASE_URL}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test regulatory document upload
    regulatory_success = test_minimal_regulatory_upload()
    
    # Test user document upload
    user_success = test_user_document_upload()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"🏛️  Regulatory Upload: {'✅ WORKING' if regulatory_success else '❌ FAILING'}")
    print(f"👤 User Document Upload: {'✅ WORKING' if user_success else '❌ FAILING'}")
    
    overall_success = regulatory_success and user_success
    print(f"\n🎯 Overall Status: {'✅ BOTH WORKFLOWS FUNCTIONAL' if overall_success else '⚠️  NEEDS ATTENTION'}")
    
    if not overall_success:
        print("\n🔧 RECOMMENDED ACTIONS:")
        if not regulatory_success:
            print("   • Optimize regulatory document processing pipeline")
            print("   • Implement async processing for large documents")
            print("   • Check for storage service deployment issues")
        if not user_success:
            print("   • Debug user document upload endpoint")
            print("   • Verify multipart form handling")
            print("   • Check file processing pipeline")
    
    return overall_success

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1) 
"""
Focused test for regulatory document upload workflow.
Tests the core functionality with optimized parameters.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://insurance-navigator-api.onrender.com"
TEST_EMAIL = "regtest@example.com"
TEST_PASSWORD = "regtest123"

def test_auth():
    """Get authentication token"""
    try:
        # Try login first
        response = requests.post(
            f"{BASE_URL}/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()["access_token"]
        
        # If login fails, try registration
        response = requests.post(
            f"{BASE_URL}/register",
            json={
                "full_name": "Regulatory Test User",
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return response.json()["access_token"]
            
        return None
        
    except Exception as e:
        print(f"Auth error: {e}")
        return None

def test_minimal_regulatory_upload():
    """Test regulatory document upload with minimal, fast document"""
    
    print("🔐 Getting authentication token...")
    token = test_auth()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful")
    
    # Use a very small, simple document that processes quickly
    payload = {
        "source_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "title": "Test Regulatory Document - Minimal",
        "document_type": "regulatory_document",
        "jurisdiction": "federal",
        "program": ["medicaid"],
        "metadata": {
            "test_type": "minimal_processing",
            "expected_fast_processing": True,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    print("📤 Testing regulatory document upload...")
    print(f"📄 Document: {payload['title']}")
    print(f"🔗 URL: {payload['source_url']}")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/documents/upload-regulatory",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=45  # Allow reasonable time but not excessive
        )
        
        processing_time = time.time() - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - Regulatory upload workflow working!")
            print(f"📋 Document ID: {result.get('document_id', 'N/A')}")
            print(f"🔄 Processing method: {result.get('processing_method', 'N/A')}")
            print(f"📊 Vector status: {result.get('vector_processing_status', 'N/A')}")
            return True
            
        elif response.status_code == 502:
            print("❌ 502 Bad Gateway - Server overloaded or deployment issue")
            print("   This indicates the server is struggling with processing load")
            return False
            
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"📝 Response: {response.text[:300]}...")
            
            # Check for specific errors
            if "upload_policy_document" in response.text:
                print("🔧 DIAGNOSIS: Storage service method not found - need deployment fix")
            elif "timeout" in response.text.lower():
                print("🔧 DIAGNOSIS: Processing timeout - need performance optimization")
            else:
                print("🔧 DIAGNOSIS: Other processing error - check logs")
            
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️  TIMEOUT - Processing is taking too long (45+ seconds)")
        print("🔧 DIAGNOSIS: Need performance optimization or async processing")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_user_document_upload():
    """Test user document upload workflow"""
    
    print("\n👤 Testing User Document Upload...")
    
    token = test_auth()
    if not token:
        print("❌ Authentication failed")
        return False
    
    # Test with file upload (multipart)
    files = {'file': ('test.txt', b'This is a test document for user upload validation.', 'text/plain')}
    data = {
        'request_data': json.dumps({
            "document_type": "user_document",
            "source_type": "file_upload",
            "title": "Test User Document",
            "metadata": {
                "test_type": "user_upload_validation",
                "timestamp": datetime.now().isoformat()
            }
        })
    }
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/documents/upload-unified",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        processing_time = time.time() - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - User document upload working!")
            print(f"📋 Document ID: {result.get('document_id', 'N/A')}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"📝 Response: {response.text[:300]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️  TIMEOUT - User document processing too slow")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run focused regulatory and user document upload tests"""
    print("=" * 80)
    print("🧪 FOCUSED DOCUMENT UPLOAD WORKFLOW TEST")
    print("=" * 80)
    print(f"🌐 Testing API: {BASE_URL}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test regulatory document upload
    regulatory_success = test_minimal_regulatory_upload()
    
    # Test user document upload
    user_success = test_user_document_upload()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"🏛️  Regulatory Upload: {'✅ WORKING' if regulatory_success else '❌ FAILING'}")
    print(f"👤 User Document Upload: {'✅ WORKING' if user_success else '❌ FAILING'}")
    
    overall_success = regulatory_success and user_success
    print(f"\n🎯 Overall Status: {'✅ BOTH WORKFLOWS FUNCTIONAL' if overall_success else '⚠️  NEEDS ATTENTION'}")
    
    if not overall_success:
        print("\n🔧 RECOMMENDED ACTIONS:")
        if not regulatory_success:
            print("   • Optimize regulatory document processing pipeline")
            print("   • Implement async processing for large documents")
            print("   • Check for storage service deployment issues")
        if not user_success:
            print("   • Debug user document upload endpoint")
            print("   • Verify multipart form handling")
            print("   • Check file processing pipeline")
    
    return overall_success

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1) 