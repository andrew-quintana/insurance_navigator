#!/usr/bin/env python3
"""
Focused Regulatory Document Upload Test
Tests the /upload-regulatory-document endpoint with proper form data
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
RENDER_URL = "***REMOVED***"

def test_regulatory_upload(base_url: str = BASE_URL) -> Dict[str, Any]:
    """Test regulatory document upload with proper form data"""
    print(f"🧪 Testing Regulatory Upload at {base_url}")
    
    # Step 1: Register a test user
    print("\n📝 Step 1: Registering test user...")
    unique_email = f"regulatory_{uuid.uuid4().hex[:8]}@example.com"
    
    try:
        register_response = requests.post(f"{base_url}/register", json={
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Regulatory Test User"
        }, timeout=30)
        
        if register_response.status_code != 200:
            return {"error": f"Registration failed: {register_response.status_code} - {register_response.text}"}
        
        token = register_response.json()["access_token"]
        print(f"✅ User registered: {unique_email}")
        print(f"✅ Token received: {token[:20]}...")
        
    except Exception as e:
        return {"error": f"Registration error: {str(e)}"}
    
    # Step 2: Test regulatory upload with proper form data
    print("\n📋 Step 2: Testing regulatory document upload...")
    
    # Create test document content
    test_document_content = """
# Test Insurance Policy Document

## Coverage Details
- Plan Type: HMO
- Deductible: $1,000
- Out-of-pocket Maximum: $5,000
- Network: Blue Cross Blue Shield

## Benefits
- Primary Care: $20 copay
- Specialist: $40 copay
- Emergency Room: $200 copay
- Prescription Drugs: $10/$30/$50 tier

## Exclusions
- Cosmetic procedures
- Experimental treatments
- Alternative medicine

This is a test regulatory document for upload testing.
"""
    
    # Prepare form data (multipart/form-data)
    files = {
        'file': ('test_regulatory_policy.txt', test_document_content, 'text/plain')
    }
    
    # Form data fields
    form_data = {
        'document_title': 'Test Insurance Policy Document',  # Required field
        'document_type': 'insurance_policy',
        'category': 'regulatory',
        'metadata': json.dumps({
            'source': 'test_upload',
            'plan_type': 'HMO',
            'carrier': 'Test Insurance Co',
            'effective_date': '2024-01-01',
            'test_document': True
        })
    }
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        print(f"📤 Uploading regulatory document...")
        print(f"   Document type: {form_data['document_type']}")
        print(f"   Category: {form_data['category']}")
        print(f"   File size: {len(test_document_content)} bytes")
        
        upload_response = requests.post(
            f"{base_url}/upload-regulatory-document",
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
            print(f"   Processing: {result.get('processing_status', 'N/A')}")
            
            return {
                "status": "success",
                "user_email": unique_email,
                "document_id": result.get('document_id'),
                "upload_response": result
            }
        else:
            error_text = upload_response.text
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"   Error: {error_text}")
            
            return {
                "status": "failed",
                "user_email": unique_email,
                "error_code": upload_response.status_code,
                "error_message": error_text
            }
            
    except Exception as e:
        print(f"❌ Upload exception: {str(e)}")
        return {
            "status": "error",
            "user_email": unique_email,
            "exception": str(e)
        }

def main():
    """Run regulatory upload tests"""
    print("🔬 Regulatory Document Upload Test")
    print("=" * 50)
    
    # Test local server
    print("\n🏠 Testing Local Server...")
    local_result = test_regulatory_upload(BASE_URL)
    
    print(f"\n📋 Local Test Result:")
    print(f"   Status: {local_result.get('status', 'unknown')}")
    if local_result.get('error'):
        print(f"   Error: {local_result['error']}")
    elif local_result.get('document_id'):
        print(f"   Document ID: {local_result['document_id']}")
    
    # Test Render deployment
    print(f"\n☁️ Testing Render Deployment...")
    render_result = test_regulatory_upload(RENDER_URL)
    
    print(f"\n📋 Render Test Result:")
    print(f"   Status: {render_result.get('status', 'unknown')}")
    if render_result.get('error'):
        print(f"   Error: {render_result['error']}")
    elif render_result.get('document_id'):
        print(f"   Document ID: {render_result['document_id']}")
    
    # Summary
    print(f"\n🎯 Test Summary:")
    print(f"   Local: {'✅ PASS' if local_result.get('status') == 'success' else '❌ FAIL'}")
    print(f"   Render: {'✅ PASS' if render_result.get('status') == 'success' else '❌ FAIL'}")
    
    return {
        "local": local_result,
        "render": render_result
    }

if __name__ == "__main__":
    results = main() 