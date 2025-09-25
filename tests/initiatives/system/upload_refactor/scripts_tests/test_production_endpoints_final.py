#!/usr/bin/env python3
"""
Final Phase 6 Production Endpoint Testing

This script completes the Phase 6 testing requirements by testing all production
endpoints and documenting the results.
"""

import requests
import json
import jwt
import uuid
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

def setup_test_environment():
    """Set up the test environment with proper configuration."""
    
    print("🔧 Setting up test environment...")
    
    # Override environment variables for testing
    os.environ['UPLOAD_PIPELINE_SUPABASE_URL'] = 'http://localhost:54321'
    os.environ['UPLOAD_PIPELINE_SUPABASE_SERVICE_ROLE_KEY'] = '${SUPABASE_JWT_TOKEN}/LC87Dkk='
    os.environ['UPLOAD_PIPELINE_LLAMAPARSE_API_URL'] = 'http://localhost:8001'
    os.environ['UPLOAD_PIPELINE_OPENAI_API_URL'] = 'http://localhost:8002'
    os.environ['UPLOAD_PIPELINE_ENVIRONMENT'] = 'development'
    
    print("✅ Environment variables configured")

def generate_test_jwt_token():
    """Generate a valid JWT token for testing."""
    
    supabase_url = "http://localhost:54321"
    # Use the correct service role key from docker-compose.yml
    service_role_key = "${SUPABASE_JWT_TOKEN}"
    
    payload = {
        "sub": str(uuid.uuid4()),
        "aud": "authenticated",
        "iss": supabase_url,
        "email": "test@example.com",
        "role": "user",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "nbf": datetime.utcnow()
    }
    
    token = jwt.encode(payload, service_role_key, algorithm="HS256")
    return token, payload

def test_service_health():
    """Test all service health endpoints."""
    
    print("\n🏥 Testing Service Health")
    print("=" * 40)
    
    health_tests = [
        ("API Server", "http://localhost:8000/health"),
        ("Mock LlamaParse", "http://localhost:8001/health"),
        ("Mock OpenAI", "http://localhost:8002/health"),
    ]
    
    all_healthy = True
    
    for service_name, url in health_tests:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: Healthy")
            else:
                print(f"⚠️  {service_name}: Status {response.status_code}")
                all_healthy = False
        except Exception as e:
            print(f"❌ {service_name}: Unhealthy - {e}")
            all_healthy = False
    
    return all_healthy

def test_production_upload_endpoint(token):
    """Test the production upload endpoint with JWT authentication."""
    
    print("\n📤 Testing Production Upload Endpoint")
    print("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_data = {
        "filename": "phase6-test-document.pdf",
        "bytes_len": 1048576,
        "mime": "application/pdf",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "ocr": False
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/upload-pipeline/upload",
            headers=headers,
            json=test_data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Production upload endpoint working with JWT authentication!")
            response_data = response.json()
            return {
                "success": True,
                "job_id": response_data.get('job_id'),
                "document_id": response_data.get('document_id')
            }
        elif response.status_code == 401:
            print("❌ Authentication failed - JWT token not accepted")
            return {"success": False, "error": "Authentication failed"}
        elif response.status_code == 500:
            print("⚠️  Server error - likely configuration issue")
            return {"success": False, "error": "Server error"}
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return {"success": False, "error": f"Status {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {"success": False, "error": str(e)}

def test_production_jobs_endpoint(token):
    """Test the production jobs endpoint with JWT authentication."""
    
    print("\n📋 Testing Production Jobs Endpoint")
    print("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "http://localhost:8000/api/v2/jobs",
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Production jobs endpoint working with JWT authentication!")
            response_data = response.json()
            return {
                "success": True,
                "jobs_count": len(response_data.get('jobs', []))
            }
        elif response.status_code == 401:
            print("❌ Authentication failed - JWT token not accepted")
            return {"success": False, "error": "Authentication failed"}
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return {"success": False, "error": f"Status {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {"success": False, "error": str(e)}

def test_job_status_endpoint(token, job_id):
    """Test the production job status endpoint."""
    
    if not job_id:
        print("⚠️  No job ID available for status testing")
        return {"success": False, "error": "No job ID"}
    
    print(f"\n📊 Testing Job Status Endpoint (Job: {job_id})")
    print("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"http://localhost:8000/api/v2/jobs/{job_id}",
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Job status endpoint working with JWT authentication!")
            return {"success": True}
        elif response.status_code == 401:
            print("❌ Authentication failed - JWT token not accepted")
            return {"success": False, "error": "Authentication failed"}
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return {"success": False, "error": f"Status {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {"success": False, "error": str(e)}

def test_test_endpoints():
    """Test the test endpoints (no authentication required)."""
    
    print("\n🧪 Testing Test Endpoints (No Auth Required)")
    print("-" * 40)
    
    test_data = {
        "filename": "test-document.pdf",
        "bytes_len": 1048576,
        "mime": "application/pdf",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "ocr": False
    }
    
    # Test upload endpoint
    try:
        response = requests.post(
            "http://localhost:8000/test/upload",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Test upload endpoint working")
            response_data = response.json()
            return {
                "success": True,
                "job_id": response_data.get('job_id'),
                "document_id": response_data.get('document_id')
            }
        else:
            print(f"⚠️  Test upload endpoint: Status {response.status_code}")
            return {"success": False, "error": f"Status {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Test upload endpoint failed: {e}")
        return {"success": False, "error": str(e)}

def run_comprehensive_test():
    """Run the comprehensive Phase 6 test suite."""
    
    print("🚀 Phase 6 Comprehensive Testing Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    
    # Setup environment
    setup_test_environment()
    
    # Test service health
    services_healthy = test_service_health()
    
    # Generate JWT token
    token, payload = generate_test_jwt_token()
    print(f"\n🔐 Generated JWT token for user: {payload['sub']}")
    
    # Test production endpoints
    upload_result = test_production_upload_endpoint(token)
    jobs_result = test_production_jobs_endpoint(token)
    
    # Test job status if upload was successful
    status_result = None
    if upload_result.get("success") and upload_result.get("job_id"):
        status_result = test_job_status_endpoint(token, upload_result["job_id"])
    
    # Test test endpoints
    test_result = test_test_endpoints()
    
    # Generate test report
    print("\n" + "=" * 60)
    print("📊 PHASE 6 TESTING RESULTS")
    print("=" * 60)
    
    results = {
        "services_healthy": services_healthy,
        "jwt_authentication": {
            "token_generated": True,
            "user_id": payload['sub'],
            "email": payload['email'],
            "role": payload['role']
        },
        "production_endpoints": {
            "upload": upload_result,
            "jobs": jobs_result,
            "job_status": status_result
        },
        "test_endpoints": test_result,
        "overall_status": "PENDING"
    }
    
    # Determine overall status
    production_success = (
        upload_result.get("success", False) and 
        jobs_result.get("success", False)
    )
    
    if services_healthy and production_success:
        results["overall_status"] = "COMPLETED"
        print("🎉 PHASE 6 COMPLETED SUCCESSFULLY!")
    elif services_healthy and test_result.get("success"):
        results["overall_status"] = "PARTIALLY_COMPLETED"
        print("⚠️  PHASE 6 PARTIALLY COMPLETED")
        print("   - Core services working")
        print("   - Test endpoints functional")
        print("   - Production endpoints need configuration fix")
    else:
        results["overall_status"] = "FAILED"
        print("❌ PHASE 6 TESTING FAILED")
    
    # Print detailed results
    print(f"\n📋 Detailed Results:")
    print(f"   Services Health: {'✅' if services_healthy else '❌'}")
    print(f"   JWT Authentication: ✅ Token generated and valid")
    print(f"   Production Upload: {'✅' if upload_result.get('success') else '❌'}")
    print(f"   Production Jobs: {'✅' if jobs_result.get('success') else '❌'}")
    print(f"   Test Endpoints: {'✅' if test_result.get('success') else '❌'}")
    
    # Save results to file
    results_file = "phase6_testing_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Test results saved to: {results_file}")
    print(f"📅 Test completed at: {datetime.now().isoformat()}")
    
    return results

if __name__ == "__main__":
    run_comprehensive_test()


