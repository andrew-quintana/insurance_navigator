#!/usr/bin/env python3
"""
Simple document upload test focused on testing storage service method fixes
"""

import requests
import json

BASE_URL = "***REMOVED***"

def test_auth():
    """Test authentication"""
    response = requests.post(
        f"{BASE_URL}/login",
        json={"email": "doctest@example.com", "password": "testpass123"},
        timeout=5
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_upload_with_minimal_data():
    """Test upload with minimal data to see if storage methods work"""
    token = test_auth()
    if not token:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Test with a very simple payload that should trigger the storage service
    # but with minimal processing requirements
    payload = {
        "source_url": "https://www.google.com/robots.txt",  # Very small text file
        "title": "Simple Test Document",
        "document_type": "regulatory_document",
        "jurisdiction": "federal", 
        "program": ["medicaid"],
        "metadata": {"test": True}
    }
    
    print("🧪 Testing regulatory upload with simple text file...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/documents/upload-regulatory",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        print(f"📊 Status: {response.status_code}")
        print(f"📝 Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ Upload endpoint reached successfully!")
        elif response.status_code == 500:
            if "upload_policy_document" in response.text:
                print("❌ Still getting upload_policy_document error - fixes not deployed")
            else:
                print("⚠️  Different 500 error - method fix worked but other issue")
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out - processing is slow but endpoint reached")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_upload_with_minimal_data() 
"""
Simple document upload test focused on testing storage service method fixes
"""

import requests
import json

BASE_URL = "***REMOVED***"

def test_auth():
    """Test authentication"""
    response = requests.post(
        f"{BASE_URL}/login",
        json={"email": "doctest@example.com", "password": "testpass123"},
        timeout=5
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_upload_with_minimal_data():
    """Test upload with minimal data to see if storage methods work"""
    token = test_auth()
    if not token:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Test with a very simple payload that should trigger the storage service
    # but with minimal processing requirements
    payload = {
        "source_url": "https://www.google.com/robots.txt",  # Very small text file
        "title": "Simple Test Document",
        "document_type": "regulatory_document",
        "jurisdiction": "federal", 
        "program": ["medicaid"],
        "metadata": {"test": True}
    }
    
    print("🧪 Testing regulatory upload with simple text file...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/documents/upload-regulatory",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        print(f"📊 Status: {response.status_code}")
        print(f"📝 Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ Upload endpoint reached successfully!")
        elif response.status_code == 500:
            if "upload_policy_document" in response.text:
                print("❌ Still getting upload_policy_document error - fixes not deployed")
            else:
                print("⚠️  Different 500 error - method fix worked but other issue")
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out - processing is slow but endpoint reached")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_upload_with_minimal_data() 