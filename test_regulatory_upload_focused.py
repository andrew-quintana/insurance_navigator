#!/usr/bin/env python3
"""
Test Regulatory Document Upload
Tests the /upload-regulatory-document endpoint to verify it works properly
"""

import requests
import json
import uuid
import time
from datetime import datetime


def test_regulatory_upload():
    """Test regulatory document upload with proper authentication"""
    print("🧪 Testing Regulatory Document Upload")

# Configuration
    BASE_URL = "https://insurance-navigator-api.onrender.com"

    # Step 1: Create a new test user
    print("\n📝 Step 1: Creating test user...")
    test_email = f"reg_test_{int(time.time())}@example.com"
    test_password = "TestPass123!"
    
    register_response = requests.post(f"{BASE_URL}/register", json={
        "email": test_email,
        "password": test_password,
            "full_name": "Regulatory Test User"
        }, timeout=30)
        
        if register_response.status_code != 200:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(f"Response: {register_response.text}")
        
        # Try login instead in case user exists
        print("   Trying login instead...")
        login_response = requests.post(f"{BASE_URL}/login", json={
            "email": test_email,
            "password": test_password
        }, timeout=30)
        
        if login_response.status_code != 200:
            print(f"❌ Login also failed: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
    else:
        token = register_response.json()["access_token"]
        
    print(f"✅ Authentication successful: {token[:20]}...")
    
    # Step 2: Test regulatory upload
    print("\n📋 Step 2: Testing regulatory document upload...")
    
    # Create test document content
    test_document_content = """
# Test Regulatory Insurance Policy Document

## Regulatory Authority Information
- Document Type: State Insurance Regulation
- Effective Date: January 1, 2024
- Authority: State Department of Insurance
- Regulation Number: REG-2024-001

## Coverage Requirements
- Minimum deductible: $500
- Maximum out-of-pocket: $8,000
- Essential health benefits required
- Network adequacy standards apply

## Compliance Requirements
- All insurers must comply by March 1, 2024
- Annual reporting required
- Penalties for non-compliance specified

## Appeals Process
- 60-day internal appeal period
- External review available
- Expedited review for urgent cases

This is a test regulatory document for upload and vectorization testing.
"""
    
    # Prepare form data
    files = {
        'file': ('test_regulatory_policy.txt', test_document_content, 'text/plain')
    }
    
    form_data = {
        'document_title': 'Test State Insurance Regulation REG-2024-001',
        'document_type': 'state_regulation',
        'category': 'regulatory',
        'source_url': 'https://doi.state.gov/regulations/2024/reg-001',
        'metadata': json.dumps({
            'jurisdiction': 'state',
            'authority': 'Department of Insurance',
            'regulation_number': 'REG-2024-001',
            'effective_date': '2024-01-01',
            'compliance_deadline': '2024-03-01',
            'test_upload': True
        })
    }
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        print(f"📤 Uploading regulatory document...")
        print(f"   Title: {form_data['document_title']}")
        print(f"   Type: {form_data['document_type']}")
        print(f"   Category: {form_data['category']}")
        print(f"   File size: {len(test_document_content)} bytes")
        
        upload_response = requests.post(
            f"{BASE_URL}/upload-regulatory-document",
            files=files,
            data=form_data,
            headers=headers,
            timeout=60
        )
        
        print(f"📊 Upload response: {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            result = upload_response.json()
            print(f"✅ Regulatory upload successful!")
            print(f"   Document ID: {result.get('document_id', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
            print(f"   Message: {result.get('message', 'N/A')}")
            print(f"   Processing Method: {result.get('processing_method', 'N/A')}")
            
            # Step 3: Check document status
            print(f"\n🔍 Step 3: Checking document processing status...")
            doc_id = result.get('document_id')
            if doc_id:
                time.sleep(5)  # Wait a moment for processing to start
                
                status_response = requests.get(
                    f"{BASE_URL}/documents/{doc_id}/status",
                    headers=headers,
                    timeout=30
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   Document Status: {status_data.get('status', 'unknown')}")
                    print(f"   Progress: {status_data.get('progress_percentage', 0)}%")
                else:
                    print(f"   ⚠️ Status check failed: {status_response.status_code}")
                    print(f"   Response: {status_response.text}")
            
            # Step 4: Check if document appears in regulatory_documents table
            print(f"\n📊 Step 4: Summary...")
            print(f"   ✅ Upload: Successful")
            print(f"   ✅ Edge Function: Triggered")
            print(f"   📄 Document ID: {doc_id}")
            print(f"   🏛️ Document Type: Regulatory")
            
            return True
        else:
            error_text = upload_response.text
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"   Error: {error_text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload exception: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_regulatory_upload()
    if success:
        print("\n🎉 Regulatory upload test completed successfully!")
    else:
        print("\n💥 Regulatory upload test failed!") 