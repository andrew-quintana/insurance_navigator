#!/usr/bin/env python3
"""
Test script for Unified API implementation on Render deployment.
Tests all the new unified API endpoints we implemented.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Render deployment URL
BASE_URL = "https://insurance-navigator-api.onrender.com"

# Test credentials - using admin user
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "test123"

def print_step(message):
    """Print a formatted step message."""
    print(f"\n🔍 {message}")

def print_success(message):
    """Print a success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message."""
    print(f"❌ {message}")

def print_info(message):
    """Print an info message."""
    print(f"ℹ️  {message}")

def test_health_check():
    """Test if the backend is responding."""
    print_step("Testing health check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print_success(f"Backend is healthy: {response.json()}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_docs_endpoint():
    """Test if FastAPI docs are accessible."""
    print_step("Testing FastAPI docs endpoint")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            print_success("FastAPI docs are accessible")
            return True
        else:
            print_error(f"Docs endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Docs endpoint failed: {e}")
        return False

def authenticate():
    """Authenticate and get JWT token."""
    print_step("Authenticating with backend")
    try:
        # Try login first
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print_success(f"Authentication successful")
            return token
        elif response.status_code in [401, 404]:
            print_info("User not found or invalid credentials, trying to register...")
            # Try to register
            register_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": "Test Admin User"
            }
            response = requests.post(f"{BASE_URL}/register", json=register_data, timeout=10)
            if response.status_code == 200:
                print_success("Registration successful, now logging in...")
                # Now login
                response = requests.post(f"{BASE_URL}/login", json=login_data, timeout=10)
                if response.status_code == 200:
                    token = response.json().get("access_token")
                    print_success("Login after registration successful")
                    return token
        
        print_error(f"Authentication failed: {response.status_code} - {response.text}")
        return None
        
    except Exception as e:
        print_error(f"Authentication failed: {e}")
        return None

def test_unified_endpoints_availability(token):
    """Test if the new unified API endpoints are available."""
    print_step("Testing unified API endpoints availability")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test endpoints to check
    endpoints_to_test = [
        ("/api/documents/upload-regulatory", "POST"),
        ("/api/documents/upload-unified", "POST"),
    ]
    
    results = {}
    
    for endpoint, method in endpoints_to_test:
        try:
            if method == "POST":
                # Send a test request without proper data to check if endpoint exists
                response = requests.post(f"{BASE_URL}{endpoint}", 
                                       headers=headers, 
                                       json={}, 
                                       timeout=10)
            else:
                response = requests.get(f"{BASE_URL}{endpoint}", 
                                      headers=headers, 
                                      timeout=10)
            
            # We expect 422 for validation error or 400 for bad request
            # 404 would mean endpoint doesn't exist
            if response.status_code in [400, 422, 500]:
                print_success(f"Endpoint {endpoint} exists (got {response.status_code})")
                results[endpoint] = "available"
            elif response.status_code == 404:
                print_error(f"Endpoint {endpoint} not found (404)")
                results[endpoint] = "missing"
            else:
                print_info(f"Endpoint {endpoint} responded with {response.status_code}")
                results[endpoint] = "unknown"
                
        except Exception as e:
            print_error(f"Failed to test {endpoint}: {e}")
            results[endpoint] = "error"
    
    return results

def test_regulatory_document_upload(token):
    """Test uploading a regulatory document via the unified API."""
    print_step("Testing regulatory document upload")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Sample regulatory document data
    sample_doc = {
        "title": "Test Medicaid Regulation",
        "source_url": "https://www.medicaid.gov/sites/default/files/2019-12/smdl19003.pdf",
        "jurisdiction": "Federal",
        "program": "Medicaid",
        "document_type": "Guidance",
        "description": "Test regulatory document for unified API",
        "effective_date": "2019-12-01"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/documents/upload-regulatory",
            headers=headers,
            json=sample_doc,
            timeout=30
        )
        
        print_info(f"Response status: {response.status_code}")
        print_info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Regulatory document upload successful!")
            print_info(f"Document ID: {result.get('document_id')}")
            print_info(f"Processing status: {result.get('processing_status')}")
            return result
        else:
            print_error(f"Regulatory document upload failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Regulatory document upload failed: {e}")
        return None

def test_unified_document_upload(token):
    """Test uploading via the unified endpoint."""
    print_step("Testing unified document upload")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Sample unified document data
    sample_doc = {
        "document_type": "regulatory",
        "title": "Test Unified Upload",
        "source_url": "https://www.cms.gov/files/document/se21011.pdf",
        "metadata": {
            "jurisdiction": "Federal",
            "program": "Medicare",
            "document_type": "State Education",
            "description": "Test document via unified endpoint"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/documents/upload-unified",
            headers=headers,
            json=sample_doc,
            timeout=30
        )
        
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Unified document upload successful!")
            print_info(f"Document ID: {result.get('document_id')}")
            print_info(f"Processing status: {result.get('processing_status')}")
            return result
        else:
            print_error(f"Unified document upload failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Unified document upload failed: {e}")
        return None

def test_existing_endpoints(token):
    """Test that existing endpoints still work."""
    print_step("Testing existing endpoints compatibility")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test the me endpoint
        response = requests.get(f"{BASE_URL}/me", headers=headers, timeout=10)
        if response.status_code == 200:
            print_success("Existing /me endpoint works")
        else:
            print_error(f"Existing /me endpoint failed: {response.status_code}")
        
        # Test documents list endpoint
        response = requests.get(f"{BASE_URL}/documents", headers=headers, timeout=10)
        if response.status_code == 200:
            docs = response.json()
            print_success(f"Existing /documents endpoint works (found {len(docs)} documents)")
        else:
            print_error(f"Existing /documents endpoint failed: {response.status_code}")
            
    except Exception as e:
        print_error(f"Testing existing endpoints failed: {e}")

def main():
    """Main test function."""
    print("=" * 60)
    print("🧪 TESTING UNIFIED API WITH RENDER DEPLOYMENT")
    print("=" * 60)
    print(f"Backend URL: {BASE_URL}")
    print(f"Test started at: {datetime.now()}")
    
    # Step 1: Health check
    if not test_health_check():
        print_error("Backend is not responding. Aborting tests.")
        sys.exit(1)
    
    # Step 2: Test docs endpoint
    test_docs_endpoint()
    
    # Step 3: Authenticate
    token = authenticate()
    if not token:
        print_error("Authentication failed. Aborting tests.")
        sys.exit(1)
    
    # Step 4: Test endpoint availability
    endpoint_results = test_unified_endpoints_availability(token)
    
    # Step 5: Test existing endpoints
    test_existing_endpoints(token)
    
    # Step 6: Test regulatory document upload (if endpoint exists)
    if endpoint_results.get("/api/documents/upload-regulatory") == "available":
        test_regulatory_document_upload(token)
    else:
        print_info("Skipping regulatory upload test - endpoint not available")
    
    # Step 7: Test unified document upload (if endpoint exists)
    if endpoint_results.get("/api/documents/upload-unified") == "available":
        test_unified_document_upload(token)
    else:
        print_info("Skipping unified upload test - endpoint not available")
    
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    # Summary
    missing_endpoints = [ep for ep, status in endpoint_results.items() if status == "missing"]
    if missing_endpoints:
        print_error("Missing endpoints detected:")
        for endpoint in missing_endpoints:
            print(f"   - {endpoint}")
        print_info("\nThis suggests the unified API implementation needs to be deployed.")
        print_info("Check if the latest main.py with unified endpoints was deployed to Render.")
    else:
        print_success("All endpoints are available!")
    
    print(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    main() 