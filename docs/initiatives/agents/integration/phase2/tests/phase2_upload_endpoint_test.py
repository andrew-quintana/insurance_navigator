#!/usr/bin/env python3
"""
Phase 2 - Upload Endpoint Functionality Test
Tests the /api/upload-pipeline/upload endpoint functionality
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List
import aiohttp
import os
from pathlib import Path

# Test configuration
UPLOAD_PIPELINE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = "/api/upload-pipeline/upload"
JOBS_ENDPOINT = "/api/v2/jobs"
AUTH_ENDPOINT = "/auth/v1/signup"
TOKEN_ENDPOINT = "/auth/v1/token"

class Phase2UploadEndpointTest:
    """Test upload endpoint functionality."""
    
    def __init__(self):
        self.test_user_id = str(uuid.uuid4())
        self.test_email = f"upload_test_{self.test_user_id}@example.com"
        self.test_password = "UploadTest123!"
        self.jwt_token = None
        self.test_document_path = "examples/test_insurance_document.pdf"
        
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Phase 2 upload endpoint test."""
        print("🚀 Starting Phase 2 Upload Endpoint Functionality Test")
        print("=" * 60)
        
        start_time = time.time()
        results = {
            "test_name": "Phase 2 Upload Endpoint Functionality",
            "timestamp": time.time(),
            "test_user_id": self.test_user_id,
            "test_email": self.test_email,
            "tests": {},
            "overall_status": "PENDING",
            "total_time": 0
        }
        
        try:
            # Test 1: Endpoint Availability
            print("\n1️⃣ Testing Upload Endpoint Availability...")
            availability_test = await self._test_endpoint_availability()
            results["tests"]["endpoint_availability"] = availability_test
            
            # Test 2: Authentication Setup
            print("\n2️⃣ Setting up Authentication...")
            auth_test = await self._test_authentication_setup()
            results["tests"]["authentication_setup"] = auth_test
            
            # Test 3: Basic Upload Functionality
            print("\n3️⃣ Testing Basic Upload Functionality...")
            basic_upload_test = await self._test_basic_upload()
            results["tests"]["basic_upload"] = basic_upload_test
            
            # Test 4: Upload with Different File Types
            print("\n4️⃣ Testing Upload with Different File Types...")
            file_types_test = await self._test_different_file_types()
            results["tests"]["different_file_types"] = file_types_test
            
            # Test 5: Upload Error Handling
            print("\n5️⃣ Testing Upload Error Handling...")
            error_handling_test = await self._test_upload_error_handling()
            results["tests"]["error_handling"] = error_handling_test
            
            # Test 6: Upload Performance
            print("\n6️⃣ Testing Upload Performance...")
            performance_test = await self._test_upload_performance()
            results["tests"]["upload_performance"] = performance_test
            
            # Test 7: Job Status Tracking
            print("\n7️⃣ Testing Job Status Tracking...")
            job_tracking_test = await self._test_job_status_tracking()
            results["tests"]["job_status_tracking"] = job_tracking_test
            
            # Calculate overall results
            total_time = time.time() - start_time
            results["total_time"] = total_time
            
            # Determine overall status
            all_tests_passed = all(
                test.get("status") == "PASS" 
                for test in results["tests"].values()
            )
            results["overall_status"] = "PASS" if all_tests_passed else "FAIL"
            
            # Generate summary
            self._generate_summary(results)
            
        except Exception as e:
            results["overall_status"] = "ERROR"
            results["error"] = str(e)
            print(f"❌ Test failed with error: {e}")
            
        return results
    
    async def _test_endpoint_availability(self) -> Dict[str, Any]:
        """Test if upload endpoint is available and responding."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test GET request (should return 405 Method Not Allowed)
                url = f"{UPLOAD_PIPELINE_URL}{UPLOAD_ENDPOINT}"
                async with session.get(url) as response:
                    if response.status == 405:
                        return {
                            "status": "PASS",
                            "message": "Upload endpoint is available and responding correctly",
                            "endpoint": url,
                            "response_status": response.status,
                            "expected_status": 405
                        }
                    else:
                        return {
                            "status": "FAIL",
                            "message": f"Unexpected response status: {response.status}",
                            "endpoint": url,
                            "response_status": response.status,
                            "expected_status": 405
                        }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Endpoint availability test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_authentication_setup(self) -> Dict[str, Any]:
        """Setup authentication for upload tests."""
        try:
            # Create test user
            user_data = {
                "email": self.test_email,
                "password": self.test_password,
                "user_metadata": {
                    "test_user": True,
                    "phase": "phase2_upload_endpoint",
                    "created_at": time.time()
                }
            }
            
            async with aiohttp.ClientSession() as session:
                # Create user
                url = f"{UPLOAD_PIPELINE_URL}{AUTH_ENDPOINT}"
                async with session.post(url, json=user_data) as response:
                    if response.status not in [200, 201, 409]:
                        return {
                            "status": "FAIL",
                            "message": f"User creation failed: {response.status}",
                            "response_status": response.status
                        }
                
                # Authenticate user
                auth_data = {
                    "email": self.test_email,
                    "password": self.test_password
                }
                
                url = f"{UPLOAD_PIPELINE_URL}{TOKEN_ENDPOINT}?grant_type=password"
                async with session.post(url, json=auth_data) as response:
                    if response.status == 200:
                        auth_response = await response.json()
                        self.jwt_token = auth_response.get('access_token')
                        
                        return {
                            "status": "PASS",
                            "message": "Authentication setup successful",
                            "user_id": self.test_user_id,
                            "has_jwt_token": bool(self.jwt_token),
                            "response_status": response.status
                        }
                    else:
                        return {
                            "status": "FAIL",
                            "message": f"User authentication failed: {response.status}",
                            "response_status": response.status
                        }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Authentication setup test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_basic_upload(self) -> Dict[str, Any]:
        """Test basic document upload functionality."""
        try:
            if not self.jwt_token:
                return {
                    "status": "FAIL",
                    "message": "No JWT token available for upload test"
                }
            
            if not os.path.exists(self.test_document_path):
                return {
                    "status": "FAIL",
                    "message": f"Test document not found: {self.test_document_path}",
                    "document_path": self.test_document_path
                }
            
            async with aiohttp.ClientSession() as session:
                # Prepare file upload
                with open(self.test_document_path, 'rb') as f:
                    file_data = f.read()
                
                # Create multipart form data
                data = aiohttp.FormData()
                data.add_field('file', file_data, filename='test_insurance_document.pdf', content_type='application/pdf')
                data.add_field('user_id', self.test_user_id)
                
                # Set authorization header
                headers = {
                    'Authorization': f'Bearer {self.jwt_token}'
                }
                
                # Upload document
                url = f"{UPLOAD_PIPELINE_URL}{UPLOAD_ENDPOINT}"
                start_time = time.time()
                async with session.post(url, data=data, headers=headers) as response:
                    upload_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        return {
                            "status": "PASS",
                            "message": "Basic upload successful",
                            "job_id": result.get('job_id'),
                            "document_id": result.get('document_id'),
                            "upload_time": upload_time,
                            "response_status": response.status,
                            "response_data": result
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "status": "FAIL",
                            "message": f"Basic upload failed: {response.status}",
                            "response_status": response.status,
                            "upload_time": upload_time,
                            "error": error_text
                        }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Basic upload test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_different_file_types(self) -> Dict[str, Any]:
        """Test upload with different file types."""
        try:
            if not self.jwt_token:
                return {
                    "status": "FAIL",
                    "message": "No JWT token available for file type test"
                }
            
            # Test different file types
            file_tests = [
                {
                    "filename": "test_document.pdf",
                    "content_type": "application/pdf",
                    "content": b"PDF content simulation",
                    "expected_status": 200
                },
                {
                    "filename": "test_document.txt",
                    "content_type": "text/plain",
                    "content": b"Plain text content",
                    "expected_status": 200
                },
                {
                    "filename": "test_document.docx",
                    "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "content": b"DOCX content simulation",
                    "expected_status": 200
                }
            ]
            
            results = []
            async with aiohttp.ClientSession() as session:
                for file_test in file_tests:
                    # Create multipart form data
                    data = aiohttp.FormData()
                    data.add_field('file', file_test["content"], filename=file_test["filename"], content_type=file_test["content_type"])
                    data.add_field('user_id', self.test_user_id)
                    
                    # Set authorization header
                    headers = {
                        'Authorization': f'Bearer {self.jwt_token}'
                    }
                    
                    # Upload document
                    url = f"{UPLOAD_PIPELINE_URL}{UPLOAD_ENDPOINT}"
                    async with session.post(url, data=data, headers=headers) as response:
                        result = await response.json() if response.status == 200 else await response.text()
                        
                        results.append({
                            "filename": file_test["filename"],
                            "content_type": file_test["content_type"],
                            "status": "PASS" if response.status == file_test["expected_status"] else "FAIL",
                            "response_status": response.status,
                            "expected_status": file_test["expected_status"],
                            "result": result
                        })
            
            # Calculate success rate
            successful_uploads = [r for r in results if r["status"] == "PASS"]
            success_rate = len(successful_uploads) / len(file_tests)
            
            return {
                "status": "PASS" if success_rate >= 0.8 else "FAIL",
                "message": f"File type upload test completed with {success_rate:.1%} success rate",
                "success_rate": success_rate,
                "total_tests": len(file_tests),
                "successful_uploads": len(successful_uploads),
                "file_test_results": results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"File type upload test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_upload_error_handling(self) -> Dict[str, Any]:
        """Test upload error handling with invalid inputs."""
        try:
            if not self.jwt_token:
                return {
                    "status": "FAIL",
                    "message": "No JWT token available for error handling test"
                }
            
            # Test various error conditions
            error_tests = [
                {
                    "name": "No file provided",
                    "data": aiohttp.FormData(),
                    "expected_status": 400
                },
                {
                    "name": "Invalid file type",
                    "data": self._create_form_data_with_file(b"invalid content", "test.exe", "application/x-executable"),
                    "expected_status": 400
                },
                {
                    "name": "File too large",
                    "data": self._create_form_data_with_file(b"x" * 10000000, "large_file.txt", "text/plain"),  # 10MB
                    "expected_status": 413
                },
                {
                    "name": "Missing user_id",
                    "data": self._create_form_data_with_file(b"content", "test.txt", "text/plain", include_user_id=False),
                    "expected_status": 400
                }
            ]
            
            results = []
            async with aiohttp.ClientSession() as session:
                for error_test in error_tests:
                    # Set authorization header
                    headers = {
                        'Authorization': f'Bearer {self.jwt_token}'
                    }
                    
                    # Attempt upload
                    url = f"{UPLOAD_PIPELINE_URL}{UPLOAD_ENDPOINT}"
                    async with session.post(url, data=error_test["data"], headers=headers) as response:
                        result = await response.text()
                        
                        results.append({
                            "test_name": error_test["name"],
                            "status": "PASS" if response.status == error_test["expected_status"] else "FAIL",
                            "response_status": response.status,
                            "expected_status": error_test["expected_status"],
                            "response": result
                        })
            
            # Calculate success rate
            successful_tests = [r for r in results if r["status"] == "PASS"]
            success_rate = len(successful_tests) / len(error_tests)
            
            return {
                "status": "PASS" if success_rate >= 0.8 else "FAIL",
                "message": f"Error handling test completed with {success_rate:.1%} success rate",
                "success_rate": success_rate,
                "total_tests": len(error_tests),
                "successful_tests": len(successful_tests),
                "error_test_results": results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Error handling test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_upload_performance(self) -> Dict[str, Any]:
        """Test upload performance with multiple concurrent uploads."""
        try:
            if not self.jwt_token:
                return {
                    "status": "FAIL",
                    "message": "No JWT token available for performance test"
                }
            
            # Test concurrent uploads
            num_concurrent_uploads = 5
            upload_tasks = []
            
            async with aiohttp.ClientSession() as session:
                # Create concurrent upload tasks
                for i in range(num_concurrent_uploads):
                    task = self._single_upload_task(session, i)
                    upload_tasks.append(task)
                
                # Execute all uploads concurrently
                start_time = time.time()
                results = await asyncio.gather(*upload_tasks, return_exceptions=True)
                total_time = time.time() - start_time
                
                # Analyze results
                successful_uploads = [r for r in results if isinstance(r, dict) and r.get("status") == "PASS"]
                failed_uploads = [r for r in results if isinstance(r, dict) and r.get("status") == "FAIL"]
                exceptions = [r for r in results if isinstance(r, Exception)]
                
                # Calculate performance metrics
                upload_times = [r.get("upload_time", 0) for r in successful_uploads if "upload_time" in r]
                avg_upload_time = sum(upload_times) / len(upload_times) if upload_times else 0
                max_upload_time = max(upload_times) if upload_times else 0
                min_upload_time = min(upload_times) if upload_times else 0
                
                return {
                    "status": "PASS" if len(successful_uploads) >= num_concurrent_uploads * 0.8 else "FAIL",
                    "message": f"Performance test completed with {len(successful_uploads)}/{num_concurrent_uploads} successful uploads",
                    "total_time": total_time,
                    "concurrent_uploads": num_concurrent_uploads,
                    "successful_uploads": len(successful_uploads),
                    "failed_uploads": len(failed_uploads),
                    "exceptions": len(exceptions),
                    "average_upload_time": avg_upload_time,
                    "max_upload_time": max_upload_time,
                    "min_upload_time": min_upload_time,
                    "throughput": len(successful_uploads) / total_time if total_time > 0 else 0,
                    "upload_results": results
                }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Performance test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_job_status_tracking(self) -> Dict[str, Any]:
        """Test job status tracking functionality."""
        try:
            if not self.jwt_token:
                return {
                    "status": "FAIL",
                    "message": "No JWT token available for job tracking test"
                }
            
            # First, upload a document to get a job ID
            upload_result = await self._test_basic_upload()
            if upload_result["status"] != "PASS":
                return {
                    "status": "FAIL",
                    "message": "Cannot test job tracking without successful upload",
                    "upload_result": upload_result
                }
            
            job_id = upload_result.get("job_id")
            if not job_id:
                return {
                    "status": "FAIL",
                    "message": "No job ID returned from upload"
                }
            
            # Test job status tracking
            status_checks = []
            async with aiohttp.ClientSession() as session:
                # Check job status multiple times
                for i in range(5):
                    url = f"{UPLOAD_PIPELINE_URL}{JOBS_ENDPOINT}/{job_id}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            job_data = await response.json()
                            status_checks.append({
                                "check_number": i + 1,
                                "status": "PASS",
                                "job_status": job_data.get('status'),
                                "response_status": response.status,
                                "job_data": job_data
                            })
                        else:
                            status_checks.append({
                                "check_number": i + 1,
                                "status": "FAIL",
                                "response_status": response.status,
                                "error": await response.text()
                            })
                    
                    # Wait between checks
                    await asyncio.sleep(2)
            
            # Calculate success rate
            successful_checks = [c for c in status_checks if c["status"] == "PASS"]
            success_rate = len(successful_checks) / len(status_checks)
            
            return {
                "status": "PASS" if success_rate >= 0.8 else "FAIL",
                "message": f"Job status tracking test completed with {success_rate:.1%} success rate",
                "success_rate": success_rate,
                "job_id": job_id,
                "total_checks": len(status_checks),
                "successful_checks": len(successful_checks),
                "status_checks": status_checks
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Job status tracking test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _single_upload_task(self, session: aiohttp.ClientSession, task_index: int) -> Dict[str, Any]:
        """Single upload task for performance testing."""
        try:
            # Create test content
            content = f"Test document content for upload {task_index}".encode()
            
            # Create multipart form data
            data = aiohttp.FormData()
            data.add_field('file', content, filename=f'test_upload_{task_index}.txt', content_type='text/plain')
            data.add_field('user_id', self.test_user_id)
            
            # Set authorization header
            headers = {
                'Authorization': f'Bearer {self.jwt_token}'
            }
            
            # Upload document
            url = f"{UPLOAD_PIPELINE_URL}{UPLOAD_ENDPOINT}"
            start_time = time.time()
            async with session.post(url, data=data, headers=headers) as response:
                upload_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    return {
                        "task_index": task_index,
                        "status": "PASS",
                        "upload_time": upload_time,
                        "job_id": result.get('job_id'),
                        "document_id": result.get('document_id')
                    }
                else:
                    error_text = await response.text()
                    return {
                        "task_index": task_index,
                        "status": "FAIL",
                        "upload_time": upload_time,
                        "response_status": response.status,
                        "error": error_text
                    }
        except Exception as e:
            return {
                "task_index": task_index,
                "status": "FAIL",
                "upload_time": 0,
                "error": str(e)
            }
    
    def _create_form_data_with_file(self, content: bytes, filename: str, content_type: str, include_user_id: bool = True) -> aiohttp.FormData:
        """Create form data with file for testing."""
        data = aiohttp.FormData()
        data.add_field('file', content, filename=filename, content_type=content_type)
        if include_user_id:
            data.add_field('user_id', self.test_user_id)
        return data
    
    def _generate_summary(self, results: Dict[str, Any]):
        """Generate test summary."""
        print("\n" + "=" * 60)
        print("📊 PHASE 2 UPLOAD ENDPOINT FUNCTIONALITY TEST SUMMARY")
        print("=" * 60)
        
        print(f"Overall Status: {results['overall_status']}")
        print(f"Total Time: {results['total_time']:.2f} seconds")
        print(f"Test User ID: {results['test_user_id']}")
        
        print("\nTest Results:")
        for test_name, test_result in results["tests"].items():
            status_icon = "✅" if test_result["status"] == "PASS" else "❌"
            print(f"  {status_icon} {test_name}: {test_result['status']}")
            if "message" in test_result:
                print(f"      {test_result['message']}")
        
        # Show specific metrics
        if "upload_performance" in results["tests"]:
            perf_result = results["tests"]["upload_performance"]
            if "throughput" in perf_result:
                print(f"\nUpload Throughput: {perf_result['throughput']:.2f} uploads/second")
            if "average_upload_time" in perf_result:
                print(f"Average Upload Time: {perf_result['average_upload_time']:.2f}s")
        
        if results["overall_status"] == "PASS":
            print("\n🎉 Phase 2 Upload Endpoint Functionality Test PASSED!")
        else:
            print("\n❌ Phase 2 Upload Endpoint Functionality Test FAILED!")

async def main():
    """Run Phase 2 upload endpoint test."""
    tester = Phase2UploadEndpointTest()
    results = await tester.run_comprehensive_test()
    
    # Save results
    results_file = f"phase2_upload_endpoint_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: {results_file}")
    return results

if __name__ == "__main__":
    asyncio.run(main())
