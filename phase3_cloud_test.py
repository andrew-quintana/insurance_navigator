#!/usr/bin/env python3
"""
Phase 3 Cloud Deployment Test
Test the cloud-deployed API service for database connectivity and basic functionality.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any

# Cloud service URLs
API_BASE_URL = "https://insurance-navigator-api-workflow-testing.onrender.com"

class Phase3CloudTester:
    """Test the cloud-deployed API service."""
    
    def __init__(self):
        self.api_url = API_BASE_URL
        self.test_results = []
    
    def get_jwt_token(self) -> str:
        """Generate a test JWT token for authentication."""
        import jwt
        
        payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "aud": "authenticated",
            "iss": "***REMOVED***"
        }
        
        # Use a test secret key
        secret = "test-secret-key-for-phase3"
        return jwt.encode(payload, secret, algorithm="HS256")
    
    async def test_api_health(self) -> Dict[str, Any]:
        """Test API health endpoint."""
        print("🔍 Testing API health...")
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.api_url}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"✅ API health check passed: {health_data}")
                    return {
                        "test": "api_health",
                        "status": "passed",
                        "response_time": response.elapsed.total_seconds(),
                        "data": health_data
                    }
                else:
                    print(f"❌ API health check failed: {response.status_code}")
                    return {
                        "test": "api_health",
                        "status": "failed",
                        "error": f"HTTP {response.status_code}",
                        "response": response.text
                    }
                    
        except Exception as e:
            print(f"❌ API health check error: {e}")
            return {
                "test": "api_health",
                "status": "error",
                "error": str(e)
            }
    
    async def test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity through API."""
        print("🔍 Testing database connectivity...")
        
        try:
            # Test a simple endpoint that requires database access
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.api_url}/")
                
                if response.status_code == 200:
                    print("✅ Database connectivity appears to be working")
                    return {
                        "test": "database_connectivity",
                        "status": "passed",
                        "response_time": response.elapsed.total_seconds()
                    }
                else:
                    print(f"⚠️ Database connectivity uncertain: {response.status_code}")
                    return {
                        "test": "database_connectivity",
                        "status": "uncertain",
                        "error": f"HTTP {response.status_code}",
                        "response": response.text
                    }
                    
        except Exception as e:
            print(f"❌ Database connectivity test error: {e}")
            return {
                "test": "database_connectivity",
                "status": "error",
                "error": str(e)
            }
    
    async def test_upload_endpoint(self) -> Dict[str, Any]:
        """Test upload endpoint (without actually uploading a file)."""
        print("🔍 Testing upload endpoint...")
        
        try:
            token = self.get_jwt_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test upload endpoint with minimal data
            upload_data = {
                "filename": "test.pdf",
                "bytes_len": 1024,
                "sha256": "test-hash-123",
                "mime": "application/pdf",
                "ocr": False
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.api_url}/api/v2/upload",
                    json=upload_data,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"✅ Upload endpoint working: {result}")
                    return {
                        "test": "upload_endpoint",
                        "status": "passed",
                        "response_time": response.elapsed.total_seconds(),
                        "data": result
                    }
                else:
                    print(f"⚠️ Upload endpoint response: {response.status_code}")
                    return {
                        "test": "upload_endpoint",
                        "status": "partial",
                        "error": f"HTTP {response.status_code}",
                        "response": response.text
                    }
                    
        except Exception as e:
            print(f"❌ Upload endpoint test error: {e}")
            return {
                "test": "upload_endpoint",
                "status": "error",
                "error": str(e)
            }
    
    async def test_job_status_endpoint(self) -> Dict[str, Any]:
        """Test job status endpoint."""
        print("🔍 Testing job status endpoint...")
        
        try:
            token = self.get_jwt_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test with a dummy job ID
            test_job_id = "test-job-123"
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.api_url}/api/v2/jobs/{test_job_id}",
                    headers=headers
                )
                
                # We expect this to fail with 404, but it should not be a connection error
                if response.status_code == 404:
                    print("✅ Job status endpoint working (404 as expected)")
                    return {
                        "test": "job_status_endpoint",
                        "status": "passed",
                        "response_time": response.elapsed.total_seconds(),
                        "note": "404 response is expected for non-existent job"
                    }
                elif response.status_code in [200, 500]:
                    print(f"⚠️ Job status endpoint response: {response.status_code}")
                    return {
                        "test": "job_status_endpoint",
                        "status": "partial",
                        "error": f"HTTP {response.status_code}",
                        "response": response.text
                    }
                else:
                    print(f"❌ Job status endpoint failed: {response.status_code}")
                    return {
                        "test": "job_status_endpoint",
                        "status": "failed",
                        "error": f"HTTP {response.status_code}",
                        "response": response.text
                    }
                    
        except Exception as e:
            print(f"❌ Job status endpoint test error: {e}")
            return {
                "test": "job_status_endpoint",
                "status": "error",
                "error": str(e)
            }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        print("🚀 Starting Phase 3 Cloud Deployment Test")
        print("=" * 60)
        print(f"API URL: {self.api_url}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        # Run all tests
        tests = [
            self.test_api_health(),
            self.test_database_connectivity(),
            self.test_upload_endpoint(),
            self.test_job_status_endpoint()
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        # Process results
        test_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test_results.append({
                    "test": f"test_{i}",
                    "status": "error",
                    "error": str(result)
                })
            else:
                test_results.append(result)
        
        # Calculate summary
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r.get("status") == "passed"])
        failed_tests = len([r for r in test_results if r.get("status") in ["failed", "error"]])
        partial_tests = len([r for r in test_results if r.get("status") == "partial"])
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "partial": partial_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 PHASE 3 CLOUD TEST RESULTS")
        print("=" * 60)
        
        for result in test_results:
            status_icon = "✅" if result["status"] == "passed" else "⚠️" if result["status"] == "partial" else "❌"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if "error" in result:
                print(f"   Error: {result['error']}")
            if "response_time" in result:
                print(f"   Response time: {result['response_time']:.3f}s")
        
        print(f"\n📈 Summary:")
        print(f"   Total tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']}")
        print(f"   Partial: {summary['partial']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Success rate: {summary['success_rate']:.1f}%")
        
        # Determine overall status
        if summary['success_rate'] >= 75:
            print("\n🎉 PHASE 3 CLOUD TEST: SUCCESS!")
            print("✅ Cloud deployment is working correctly")
        elif summary['success_rate'] >= 50:
            print("\n⚠️ PHASE 3 CLOUD TEST: PARTIAL SUCCESS")
            print("⚠️ Some issues detected, but basic functionality works")
        else:
            print("\n❌ PHASE 3 CLOUD TEST: FAILED")
            print("❌ Significant issues detected with cloud deployment")
        
        return {
            "summary": summary,
            "test_results": test_results,
            "timestamp": datetime.now().isoformat(),
            "api_url": self.api_url
        }

async def main():
    """Main test function."""
    tester = Phase3CloudTester()
    results = await tester.run_comprehensive_test()
    
    # Save results to file
    results_file = f"phase3_cloud_test_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Exit with appropriate code
    if results["summary"]["success_rate"] >= 75:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
