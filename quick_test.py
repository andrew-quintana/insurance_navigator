#!/usr/bin/env python3
"""Quick regulatory upload test - minimal and fast."""

import requests
import json
import time

def quick_health_check():
    """Quick API health check."""
    try:
        response = requests.get('***REMOVED***/health', timeout=5)
        print(f"Health: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def quick_register_user():
    """Register a test user quickly."""
    timestamp = int(time.time())
    user_data = {
        'email': f'test_{timestamp}@example.com',
        'password': 'Test123!',
        'full_name': 'Test User'
    }
    
    try:
        response = requests.post(
            '***REMOVED***/register',
            json=user_data,
            timeout=10
        )
        print(f"Register: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            print(f"Registration failed: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"Registration error: {e}")
        return None

def quick_upload_test(token):
    """Quick regulatory document upload test."""
    content = b"TEST REGULATORY DOCUMENT\n\nThis is a minimal test document for network adequacy requirements.\n\nCompliance deadline: March 2025"
    
    headers = {'Authorization': f'Bearer {token}'}
    files = {'file': ('test_regulatory.txt', content, 'text/plain')}
    data = {
        'document_title': 'Test Regulatory Document',
        'document_type': 'regulatory_notice',
        'category': 'regulatory',
        'metadata': json.dumps({'jurisdiction': 'state', 'program': 'test'})
    }
    
    try:
        response = requests.post(
            '***REMOVED***/upload-regulatory-document',
            headers=headers,
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"Upload: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS! Doc ID: {result.get('document_id')}")
            return result.get('document_id')
        else:
            print(f"Upload failed: {response.text[:300]}")
            return None
            
    except Exception as e:
        print(f"Upload error: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Quick Regulatory Upload Test")
    
    # Step 1: Health check
    if not quick_health_check():
        exit(1)
    
    # Step 2: Register user
    token = quick_register_user()
    if not token:
        exit(1)
    
    # Step 3: Upload document
    doc_id = quick_upload_test(token)
    if doc_id:
        print(f"✅ SUCCESS! Document uploaded: {doc_id}")
    else:
        print("❌ Test failed") 