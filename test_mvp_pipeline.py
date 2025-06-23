#!/usr/bin/env python3
"""
MVP Pipeline Test - Production Readiness Validation
Tests the complete document processing pipeline for production MVP.
"""

import os
import time
import requests
import json
from datetime import datetime

# Configuration
BACKEND_BASE_URL = "***REMOVED***"
SUPABASE_URL = "https://jhrespvvhbnloxrieycf.supabase.co"

def test_user_login():
    """Test user authentication to get token"""
    print("🔐 Testing user authentication...")
    
    login_data = {
        "email": "databaserefactor@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BACKEND_BASE_URL}/login", json=login_data, timeout=10)
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Authentication successful")
        return token_data["access_token"]
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_small_document_upload(token):
    """Test small document upload and processing"""
    print("\n📄 Testing small document upload...")
    
    # Use the successful small document from logs
    test_file_path = "examples/test_serverless_processing.pdf"
    
    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(test_file_path, "rb") as f:
        files = {"file": (os.path.basename(test_file_path), f, "application/pdf")}
        
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_BASE_URL}/upload-document-backend",
            files=files,
            headers=headers,
            timeout=60
        )
        processing_time = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        document_id = result.get("document_id")
        print(f"✅ Small document uploaded successfully in {processing_time:.1f}s")
        print(f"   Document ID: {document_id}")
        print(f"   Status: {result.get('status')}")
        
        # Check final status after processing
        time.sleep(15)  # Wait for processing
        return check_document_status(token, document_id, "small")
    else:
        print(f"❌ Small document upload failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_regulatory_document_upload(token):
    """Test regulatory document upload"""
    print("\n📋 Testing regulatory document upload...")
    
    # Use a simple text file for regulatory test
    test_content = """
    INSURANCE REGULATORY GUIDANCE
    
    This is a test regulatory document for the Insurance Navigator system.
    It contains sample policy guidance and regulatory information.
    
    Section 1: Coverage Requirements
    - Minimum coverage limits must be maintained
    - Documentation requirements for claims processing
    
    Section 2: Compliance Standards
    - Regular reporting requirements
    - Audit procedures and timelines
    """.strip()
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Create temporary file
    temp_file = "/tmp/test_regulatory.txt"
    with open(temp_file, "w") as f:
        f.write(test_content)
    
    try:
        with open(temp_file, "rb") as f:
            files = {"file": ("test_regulatory.txt", f, "text/plain")}
            data = {
                "document_title": "Test Regulatory Guidance",
                "document_type": "guidance",
                "category": "regulatory"
            }
            
            start_time = time.time()
            response = requests.post(
                f"{BACKEND_BASE_URL}/upload-regulatory-document",
                files=files,
                data=data,
                headers=headers,
                timeout=60
            )
            processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            document_id = result.get("document_id")
            print(f"✅ Regulatory document uploaded successfully in {processing_time:.1f}s")
            print(f"   Document ID: {document_id}")
            print(f"   Status: {result.get('status')}")
            
            # Check final status after processing
            time.sleep(10)  # Wait for processing
            return True
        else:
            print(f"❌ Regulatory document upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)

def check_document_status(token, document_id, doc_type):
    """Check document processing status"""
    print(f"\n📊 Checking {doc_type} document status...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    max_checks = 12  # 2 minutes max
    for i in range(max_checks):
        try:
            response = requests.get(
                f"{BACKEND_BASE_URL}/documents/{document_id}/status",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                progress = status_data.get("progress_percentage", 0)
                
                print(f"   Status check {i+1}: {status} ({progress}%)")
                
                if status == "completed":
                    print(f"✅ {doc_type.title()} document processing completed!")
                    return True
                elif status == "failed":
                    error_msg = status_data.get("error_message", "Unknown error")
                    print(f"❌ {doc_type.title()} document processing failed: {error_msg}")
                    return False
                elif i == max_checks - 1:
                    print(f"⏰ {doc_type.title()} document still processing after 2 minutes")
                    return False
                
                time.sleep(10)  # Wait 10 seconds between checks
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return False
    
    return False

def check_vector_creation(document_id):
    """Check if vectors were created for the document"""
    print(f"\n🔢 Checking vector creation for document {document_id[:8]}...")
    
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/document_vectors?select=chunk_index,created_at&document_id=eq.{document_id}',
            headers=headers
        )
        
        if response.status_code == 200:
            vectors = response.json()
            print(f"✅ Found {len(vectors)} vectors for document")
            return len(vectors) > 0
        else:
            print(f"❌ Vector check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Vector check error: {e}")
        return False

def run_mvp_validation():
    """Run complete MVP validation"""
    print("🚀 PRODUCTION MVP VALIDATION")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Backend: {BACKEND_BASE_URL}")
    
    # Test 1: Authentication
    token = test_user_login()
    if not token:
        print("❌ MVP FAILED: Authentication not working")
        return False
    
    # Test 2: Small document processing
    small_doc_success = test_small_document_upload(token)
    
    # Test 3: Regulatory document processing  
    regulatory_doc_success = test_regulatory_document_upload(token)
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 MVP VALIDATION SUMMARY")
    print("=" * 50)
    
    results = {
        "Authentication": "✅ PASS" if token else "❌ FAIL",
        "User Document Upload": "✅ PASS" if small_doc_success else "❌ FAIL", 
        "Regulatory Document Upload": "✅ PASS" if regulatory_doc_success else "❌ FAIL"
    }
    
    for test, result in results.items():
        print(f"   {test}: {result}")
    
    all_passed = all([token, small_doc_success, regulatory_doc_success])
    
    print(f"\n🎯 MVP STATUS: {'✅ READY FOR PRODUCTION' if all_passed else '❌ NEEDS FIXES'}")
    
    if not all_passed:
        print("\n🔧 Required Fixes:")
        if not token:
            print("   - Fix authentication system")
        if not small_doc_success:
            print("   - Fix user document processing pipeline")
        if not regulatory_doc_success:
            print("   - Fix regulatory document processing pipeline")
    
    return all_passed

if __name__ == "__main__":
    run_mvp_validation() 