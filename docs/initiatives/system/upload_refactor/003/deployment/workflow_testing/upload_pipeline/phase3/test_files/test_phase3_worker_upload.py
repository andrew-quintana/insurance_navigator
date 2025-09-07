#!/usr/bin/env python3
"""
Phase 3 Worker Upload Pipeline Test
Test the upload pipeline deployed as a background worker on Render.com
"""

import asyncio
import httpx
import json
import os
import time
from datetime import datetime

# Configuration
WORKER_BASE_URL = "https://insurance-navigator-worker.onrender.com"  # This will be the worker URL
API_BASE_URL = "***REMOVED***"  # Main API for auth

class Phase3WorkerTester:
    def __init__(self):
        self.worker_url = WORKER_BASE_URL
        self.api_url = API_BASE_URL
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {"total": 0, "passed": 0, "failed": 0}
        }
    
    def get_jwt_token(self) -> str:
        """Generate a test JWT token"""
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
    
    async def test_worker_health(self) -> dict:
        """Test if the worker is healthy and accessible"""
        test_name = "Worker Health Check"
        print(f"🔍 Testing {test_name}...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.worker_url}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"✅ Worker health: {health_data}")
                    return {
                        "test": test_name,
                        "passed": True,
                        "response_time": response.elapsed.total_seconds(),
                        "status_code": response.status_code,
                        "data": health_data
                    }
                else:
                    print(f"❌ Worker health failed: {response.status_code}")
                    return {
                        "test": test_name,
                        "passed": False,
                        "error": f"Status {response.status_code}: {response.text}"
                    }
        except Exception as e:
            print(f"❌ Worker health error: {e}")
            return {
                "test": test_name,
                "passed": False,
                "error": str(e)
            }
    
    async def test_upload_endpoint(self) -> dict:
        """Test the upload endpoint on the worker"""
        test_name = "Upload Endpoint Test"
        print(f"🔍 Testing {test_name}...")
        
        try:
            # Get JWT token
            token = self.get_jwt_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test upload data
            upload_data = {
                "filename": "test_document.pdf",
                "bytes_len": 1024,
                "sha256": "test_hash_123",
                "mime": "application/pdf",
                "ocr": False
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.worker_url}/api/v2/upload",
                    json=upload_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Upload successful: {result}")
                    return {
                        "test": test_name,
                        "passed": True,
                        "response_time": response.elapsed.total_seconds(),
                        "status_code": response.status_code,
                        "data": result
                    }
                else:
                    print(f"❌ Upload failed: {response.status_code} - {response.text}")
                    return {
                        "test": test_name,
                        "passed": False,
                        "error": f"Status {response.status_code}: {response.text}"
                    }
        except Exception as e:
            print(f"❌ Upload test error: {e}")
            return {
                "test": test_name,
                "passed": False,
                "error": str(e)
            }
    
    async def test_job_status_endpoint(self, job_id: str) -> dict:
        """Test the job status endpoint"""
        test_name = "Job Status Endpoint Test"
        print(f"🔍 Testing {test_name}...")
        
        try:
            token = self.get_jwt_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.worker_url}/api/v2/jobs/{job_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Job status retrieved: {result}")
                    return {
                        "test": test_name,
                        "passed": True,
                        "response_time": response.elapsed.total_seconds(),
                        "status_code": response.status_code,
                        "data": result
                    }
                else:
                    print(f"❌ Job status failed: {response.status_code} - {response.text}")
                    return {
                        "test": test_name,
                        "passed": False,
                        "error": f"Status {response.status_code}: {response.text}"
                    }
        except Exception as e:
            print(f"❌ Job status test error: {e}")
            return {
                "test": test_name,
                "passed": False,
                "error": str(e)
            }
    
    async def test_worker_endpoints(self) -> dict:
        """Test all worker endpoints"""
        test_name = "Worker Endpoints Test"
        print(f"🔍 Testing {test_name}...")
        
        try:
            token = self.get_jwt_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            endpoints = [
                "/health",
                "/api/v2/upload",
                "/api/v2/jobs",
                "/test/upload",
                "/test/jobs"
            ]
            
            results = []
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for endpoint in endpoints:
                    try:
                        if endpoint == "/api/v2/upload":
                            # POST request for upload
                            response = await client.post(
                                f"{self.worker_url}{endpoint}",
                                json={"filename": "test.pdf", "bytes_len": 100},
                                headers=headers
                            )
                        else:
                            # GET request for others
                            response = await client.get(
                                f"{self.worker_url}{endpoint}",
                                headers=headers
                            )
                        
                        results.append({
                            "endpoint": endpoint,
                            "status_code": response.status_code,
                            "response_time": response.elapsed.total_seconds(),
                            "accessible": True
                        })
                        print(f"  ✅ {endpoint}: {response.status_code}")
                        
                    except Exception as e:
                        results.append({
                            "endpoint": endpoint,
                            "status_code": None,
                            "response_time": None,
                            "accessible": False,
                            "error": str(e)
                        })
                        print(f"  ❌ {endpoint}: {e}")
            
            accessible_count = sum(1 for r in results if r["accessible"])
            total_count = len(results)
            
            return {
                "test": test_name,
                "passed": accessible_count > 0,
                "accessible_endpoints": accessible_count,
                "total_endpoints": total_count,
                "results": results
            }
            
        except Exception as e:
            print(f"❌ Worker endpoints test error: {e}")
            return {
                "test": test_name,
                "passed": False,
                "error": str(e)
            }
    
    async def run_comprehensive_test(self) -> dict:
        """Run all tests"""
        print("🚀 Starting Phase 3 Worker Upload Pipeline Test")
        print("=" * 60)
        
        # Test 1: Worker Health
        health_result = await self.test_worker_health()
        self.results["tests"].append(health_result)
        
        # Test 2: Worker Endpoints
        endpoints_result = await self.test_worker_endpoints()
        self.results["tests"].append(endpoints_result)
        
        # Test 3: Upload Endpoint (if worker is accessible)
        if health_result["passed"]:
            upload_result = await self.test_upload_endpoint()
            self.results["tests"].append(upload_result)
            
            # Test 4: Job Status (if upload worked)
            if upload_result["passed"] and "job_id" in upload_result.get("data", {}):
                job_id = upload_result["data"]["job_id"]
                job_result = await self.test_job_status_endpoint(job_id)
                self.results["tests"].append(job_result)
        
        # Calculate summary
        self.results["summary"]["total"] = len(self.results["tests"])
        self.results["summary"]["passed"] = sum(1 for t in self.results["tests"] if t["passed"])
        self.results["summary"]["failed"] = self.results["summary"]["total"] - self.results["summary"]["passed"]
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 PHASE 3 WORKER TEST RESULTS")
        print("=" * 60)
        print(f"Total Tests: {self.results['summary']['total']}")
        print(f"Passed: {self.results['summary']['passed']}")
        print(f"Failed: {self.results['summary']['failed']}")
        print(f"Success Rate: {(self.results['summary']['passed'] / self.results['summary']['total'] * 100):.1f}%")
        
        return self.results

async def main():
    """Main function"""
    tester = Phase3WorkerTester()
    
    try:
        # Run comprehensive test
        results = await tester.run_comprehensive_test()
        
        # Save results to file
        timestamp = int(time.time())
        filename = f"phase3_worker_test_results_{timestamp}.json"
        filepath = f"docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/upload_pipeline/phase3/results/{filename}"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📁 Results saved to: {filepath}")
        
        # Return success/failure
        success = results['summary']['failed'] == 0
        return success
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
