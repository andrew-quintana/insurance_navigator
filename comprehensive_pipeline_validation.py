#!/usr/bin/env python3
"""
Comprehensive Insurance Navigator Pipeline Validation
Post-fix validation testing to characterize pipeline performance and validate fixes.
"""

import asyncio
import json
import aiohttp
import time
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class ComprehensivePipelineValidator:
    def __init__(self):
        self.render_api_base = "https://insurance-navigator.onrender.com"
        self.test_results = {}
        self.auth_token = None
        self.test_user_id = None
        
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive pipeline validation tests."""
        print("🔍 Starting Comprehensive Pipeline Validation")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "validation_phase": "post_fix_characterization",
            "infrastructure_health": await self._test_infrastructure_health(),
            "authentication_flow": await self._test_authentication_flow(),
            "edge_function_characterization": await self._test_edge_functions_direct(),
            "upload_pipeline_validation": await self._test_upload_pipeline(),
            "error_handling_validation": await self._test_error_handling(),
            "performance_characterization": await self._test_performance(),
            "summary": {}
        }
        
        # Generate comprehensive summary
        results["summary"] = self._generate_validation_summary(results)
        
        return results
    
    async def _test_infrastructure_health(self) -> Dict[str, Any]:
        """Test basic infrastructure health and connectivity."""
        print("\n🏥 Testing Infrastructure Health...")
        
        health_results = {}
        
        # Test main API health
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{self.render_api_base}/health") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ API Health: OK ({response_time:.2f}s)")
                        print(f"   Version: {data.get('version', 'unknown')}")
                        
                        health_results["api_health"] = {
                            "status": "healthy",
                            "response_time": response_time,
                            "version": data.get('version'),
                            "features": data.get('features', {})
                        }
                    else:
                        print(f"⚠️ API Health: Unexpected status {response.status}")
                        health_results["api_health"] = {
                            "status": "degraded",
                            "response_time": response_time,
                            "http_status": response.status
                        }
                        
        except Exception as e:
            print(f"❌ API Health: Failed - {e}")
            health_results["api_health"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # Test root endpoint
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.render_api_base}/") as response:
                    root_data = await response.text()
                    health_results["root_endpoint"] = {
                        "status": "accessible" if response.status == 200 else "degraded",
                        "http_status": response.status,
                        "has_content": bool(root_data and len(root_data) > 0)
                    }
                    print(f"✅ Root endpoint: HTTP {response.status}")
                    
        except Exception as e:
            health_results["root_endpoint"] = {
                "status": "failed",
                "error": str(e)
            }
        
        return health_results
    
    async def _test_authentication_flow(self) -> Dict[str, Any]:
        """Test complete authentication flow."""
        print("\n🔐 Testing Authentication Flow...")
        
        auth_results = {}
        test_timestamp = int(time.time())
        test_email = f"pipeline_test_{test_timestamp}@example.com"
        test_password = "TestPassword123!"
        
        # Test user registration
        try:
            async with aiohttp.ClientSession() as session:
                registration_payload = {
                    "email": test_email,
                    "password": test_password,
                    "full_name": "Pipeline Test User"
                }
                
                start_time = time.time()
                async with session.post(
                    f"{self.render_api_base}/register",
                    json=registration_payload
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        registration_data = await response.json()
                        self.auth_token = registration_data.get('access_token')
                        print(f"✅ Registration: Success ({response_time:.2f}s)")
                        
                        auth_results["registration"] = {
                            "status": "success",
                            "response_time": response_time,
                            "has_token": bool(self.auth_token)
                        }
                    else:
                        error_data = await response.text()
                        print(f"⚠️ Registration: Failed - {response.status}: {error_data}")
                        auth_results["registration"] = {
                            "status": "failed",
                            "http_status": response.status,
                            "error": error_data
                        }
                        
        except Exception as e:
            print(f"❌ Registration: Exception - {e}")
            auth_results["registration"] = {
                "status": "exception",
                "error": str(e)
            }
        
        # Test authentication token validation
        if self.auth_token:
            try:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                async with aiohttp.ClientSession() as session:
                    start_time = time.time()
                    async with session.get(
                        f"{self.render_api_base}/me",
                        headers=headers
                    ) as response:
                        response_time = time.time() - start_time
                        
                        if response.status == 200:
                            user_data = await response.json()
                            self.test_user_id = user_data.get('id')
                            print(f"✅ Token Validation: Success ({response_time:.2f}s)")
                            print(f"   User ID: {self.test_user_id}")
                            
                            auth_results["token_validation"] = {
                                "status": "success",
                                "response_time": response_time,
                                "user_id": self.test_user_id
                            }
                        else:
                            error_text = await response.text()
                            print(f"⚠️ Token Validation: Failed - {response.status}")
                            auth_results["token_validation"] = {
                                "status": "failed",
                                "http_status": response.status,
                                "error": error_text
                            }
                            
            except Exception as e:
                print(f"❌ Token Validation: Exception - {e}")
                auth_results["token_validation"] = {
                    "status": "exception",
                    "error": str(e)
                }
        
        return auth_results
    
    async def _test_edge_functions_direct(self) -> Dict[str, Any]:
        """Test edge functions directly to validate our fixes."""
        print("\n🔧 Testing Edge Functions Direct Access...")
        
        edge_functions = {
            "doc-parser": "https://zltxyfhcefzffjlbphnh.supabase.co/functions/v1/doc-parser",
            "vector-processor": "https://zltxyfhcefzffjlbphnh.supabase.co/functions/v1/vector-processor"
        }
        
        edge_results = {}
        
        for func_name, url in edge_functions.items():
            print(f"\n  Testing {func_name}...")
            
            try:
                async with aiohttp.ClientSession() as session:
                    # Test GET request (health check)
                    start_time = time.time()
                    async with session.get(url) as response:
                        response_time = time.time() - start_time
                        response_text = await response.text()
                        
                        if response.status == 200:
                            # Our fix should return JSON health check
                            try:
                                health_data = json.loads(response_text)
                                print(f"    ✅ GET Health Check: Success ({response_time:.2f}s)")
                                print(f"       Service: {health_data.get('service', 'unknown')}")
                                
                                edge_results[func_name] = {
                                    "get_health_check": {
                                        "status": "success",
                                        "response_time": response_time,
                                        "service_name": health_data.get('service'),
                                        "supports_health_check": True
                                    }
                                }
                            except json.JSONDecodeError:
                                print(f"    ⚠️ GET Health Check: Non-JSON response")
                                edge_results[func_name] = {
                                    "get_health_check": {
                                        "status": "non_json_response",
                                        "response_time": response_time,
                                        "response_text": response_text[:100]
                                    }
                                }
                        elif response.status == 405:
                            print(f"    ⚠️ GET Health Check: Method not allowed (old version)")
                            edge_results[func_name] = {
                                "get_health_check": {
                                    "status": "method_not_allowed",
                                    "response_time": response_time,
                                    "note": "Function doesn't support our health check fix"
                                }
                            }
                        else:
                            print(f"    ❌ GET Health Check: Unexpected status {response.status}")
                            edge_results[func_name] = {
                                "get_health_check": {
                                    "status": "unexpected_status",
                                    "response_time": response_time,
                                    "http_status": response.status
                                }
                            }
                            
            except Exception as e:
                print(f"    ❌ {func_name}: Exception - {e}")
                edge_results[func_name] = {
                    "get_health_check": {
                        "status": "exception",
                        "error": str(e)
                    }
                }
        
        return edge_results
    
    async def _test_upload_pipeline(self) -> Dict[str, Any]:
        """Test the complete upload pipeline functionality."""
        print("\n📤 Testing Upload Pipeline...")
        
        if not self.auth_token:
            print("❌ Cannot test upload pipeline: No authentication token")
            return {"status": "skipped", "reason": "no_auth_token"}
        
        upload_results = {}
        
        # Test regulatory document upload endpoint accessibility
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create a test document
            test_content = """
# Test Regulatory Document

This is a test document for pipeline validation.

## Contents
- Test content for validation
- Generated at: {timestamp}
- Purpose: Validate upload pipeline fixes

## Regulatory Information
- Document Type: Test Policy
- Category: Pipeline Validation
- Status: Test Document
            """.format(timestamp=datetime.now().isoformat())
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(test_content)
                temp_file_path = temp_file.name
            
            try:
                async with aiohttp.ClientSession() as session:
                    # Prepare form data
                    with open(temp_file_path, 'rb') as file:
                        form_data = aiohttp.FormData()
                        form_data.add_field('file', file, 
                                           filename='pipeline_validation_test.txt',
                                           content_type='text/plain')
                        form_data.add_field('document_title', 'Pipeline Validation Test Document')
                        form_data.add_field('document_type', 'test_policy')
                        form_data.add_field('category', 'validation')
                        
                        start_time = time.time()
                        async with session.post(
                            f"{self.render_api_base}/upload-regulatory-document",
                            headers=headers,
                            data=form_data
                        ) as response:
                            response_time = time.time() - start_time
                            response_text = await response.text()
                            
                            if response.status == 200:
                                upload_data = await response.json() if response.content_type == 'application/json' else None
                                print(f"✅ Document Upload: Success ({response_time:.2f}s)")
                                if upload_data:
                                    print(f"   Document ID: {upload_data.get('document_id', 'unknown')}")
                                    print(f"   Status: {upload_data.get('status', 'unknown')}")
                                
                                upload_results["regulatory_upload"] = {
                                    "status": "success",
                                    "response_time": response_time,
                                    "document_id": upload_data.get('document_id') if upload_data else None,
                                    "upload_status": upload_data.get('status') if upload_data else None,
                                    "processing_method": upload_data.get('processing_method') if upload_data else None
                                }
                            else:
                                print(f"⚠️ Document Upload: Failed - {response.status}")
                                print(f"   Response: {response_text[:200]}...")
                                
                                upload_results["regulatory_upload"] = {
                                    "status": "failed",
                                    "response_time": response_time,
                                    "http_status": response.status,
                                    "error": response_text[:500]
                                }
                                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            print(f"❌ Upload Pipeline: Exception - {e}")
            upload_results["regulatory_upload"] = {
                "status": "exception",
                "error": str(e)
            }
        
        return upload_results
    
    async def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling improvements."""
        print("\n🛡️ Testing Error Handling...")
        
        error_tests = {}
        
        # Test malformed requests
        test_cases = [
            {
                "name": "malformed_json",
                "url": f"{self.render_api_base}/register",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "data": b"invalid json{",
                "expected_status": 400
            },
            {
                "name": "missing_auth_header",
                "url": f"{self.render_api_base}/me",
                "method": "GET", 
                "headers": {},
                "data": None,
                "expected_status": 401
            }
        ]
        
        for test_case in test_cases:
            try:
                async with aiohttp.ClientSession() as session:
                    start_time = time.time()
                    
                    if test_case["method"] == "POST":
                        async with session.post(
                            test_case["url"],
                            headers=test_case["headers"],
                            data=test_case["data"]
                        ) as response:
                            response_time = time.time() - start_time
                            response_text = await response.text()
                            
                            if response.status == test_case["expected_status"]:
                                print(f"✅ {test_case['name']}: Correct error handling")
                                error_tests[test_case["name"]] = {
                                    "status": "correct_error_handling",
                                    "response_time": response_time,
                                    "expected_status": test_case["expected_status"],
                                    "actual_status": response.status
                                }
                            else:
                                print(f"⚠️ {test_case['name']}: Unexpected status {response.status}")
                                error_tests[test_case["name"]] = {
                                    "status": "unexpected_status",
                                    "response_time": response_time,
                                    "expected_status": test_case["expected_status"],
                                    "actual_status": response.status,
                                    "response": response_text[:200]
                                }
                    else:  # GET
                        async with session.get(
                            test_case["url"],
                            headers=test_case["headers"]
                        ) as response:
                            response_time = time.time() - start_time
                            
                            if response.status == test_case["expected_status"]:
                                print(f"✅ {test_case['name']}: Correct error handling")
                                error_tests[test_case["name"]] = {
                                    "status": "correct_error_handling", 
                                    "response_time": response_time,
                                    "expected_status": test_case["expected_status"],
                                    "actual_status": response.status
                                }
                            else:
                                print(f"⚠️ {test_case['name']}: Unexpected status {response.status}")
                                error_tests[test_case["name"]] = {
                                    "status": "unexpected_status",
                                    "response_time": response_time,
                                    "expected_status": test_case["expected_status"],
                                    "actual_status": response.status
                                }
                                
            except Exception as e:
                print(f"❌ {test_case['name']}: Exception - {e}")
                error_tests[test_case["name"]] = {
                    "status": "exception",
                    "error": str(e)
                }
        
        return error_tests
    
    async def _test_performance(self) -> Dict[str, Any]:
        """Test performance characteristics of the pipeline."""
        print("\n⚡ Testing Performance Characteristics...")
        
        performance_results = {}
        
        # Test API response times
        endpoints_to_test = [
            {"path": "/health", "method": "GET", "auth_required": False},
            {"path": "/", "method": "GET", "auth_required": False}
        ]
        
        if self.auth_token:
            endpoints_to_test.append({"path": "/me", "method": "GET", "auth_required": True})
        
        for endpoint in endpoints_to_test:
            endpoint_name = endpoint["path"].replace("/", "_").replace("_", "root") if endpoint["path"] == "/" else endpoint["path"].replace("/", "_")
            
            try:
                headers = {}
                if endpoint["auth_required"] and self.auth_token:
                    headers["Authorization"] = f"Bearer {self.auth_token}"
                
                response_times = []
                
                # Test multiple times for average
                for i in range(3):
                    async with aiohttp.ClientSession() as session:
                        start_time = time.time()
                        async with session.get(
                            f"{self.render_api_base}{endpoint['path']}",
                            headers=headers
                        ) as response:
                            response_time = time.time() - start_time
                            if response.status < 500:  # Only count non-server errors
                                response_times.append(response_time)
                
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
                    max_response_time = max(response_times)
                    min_response_time = min(response_times)
                    
                    print(f"✅ {endpoint['path']}: Avg {avg_response_time:.3f}s (min: {min_response_time:.3f}s, max: {max_response_time:.3f}s)")
                    
                    performance_results[endpoint_name] = {
                        "avg_response_time": avg_response_time,
                        "min_response_time": min_response_time,
                        "max_response_time": max_response_time,
                        "samples": len(response_times)
                    }
                else:
                    print(f"❌ {endpoint['path']}: No successful responses")
                    performance_results[endpoint_name] = {
                        "status": "no_successful_responses"
                    }
                    
            except Exception as e:
                print(f"❌ {endpoint['path']}: Performance test failed - {e}")
                performance_results[endpoint_name] = {
                    "status": "exception",
                    "error": str(e)
                }
        
        return performance_results
    
    def _generate_validation_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive validation summary."""
        print("\n📊 Generating Validation Summary...")
        
        # Analyze infrastructure health
        api_healthy = results.get("infrastructure_health", {}).get("api_health", {}).get("status") == "healthy"
        
        # Analyze authentication flow
        auth_working = (
            results.get("authentication_flow", {}).get("registration", {}).get("status") == "success" and
            results.get("authentication_flow", {}).get("token_validation", {}).get("status") == "success"
        )
        
        # Analyze edge functions
        edge_functions_improved = any(
            func_data.get("get_health_check", {}).get("status") == "success"
            for func_data in results.get("edge_function_characterization", {}).values()
            if isinstance(func_data, dict)
        )
        
        # Analyze upload pipeline
        upload_working = results.get("upload_pipeline_validation", {}).get("regulatory_upload", {}).get("status") == "success"
        
        # Analyze error handling
        error_handling_improved = all(
            test_data.get("status") == "correct_error_handling"
            for test_data in results.get("error_handling_validation", {}).values()
            if isinstance(test_data, dict)
        )
        
        # Calculate fix effectiveness
        fixes_effective = sum([
            api_healthy,
            auth_working, 
            edge_functions_improved,
            upload_working,
            error_handling_improved
        ])
        
        summary = {
            "overall_status": "operational" if fixes_effective >= 4 else "partially_operational" if fixes_effective >= 2 else "degraded",
            "fixes_effective": f"{fixes_effective}/5",
            "api_health": "healthy" if api_healthy else "degraded",
            "authentication": "working" if auth_working else "issues",
            "edge_functions": "improved" if edge_functions_improved else "needs_attention", 
            "upload_pipeline": "working" if upload_working else "issues",
            "error_handling": "improved" if error_handling_improved else "needs_work",
            "critical_issues_resolved": [],
            "remaining_issues": [],
            "recommendations": []
        }
        
        # Identify what was fixed
        if api_healthy:
            summary["critical_issues_resolved"].append("main.py IndentationError resolved - API now starts correctly")
        
        if edge_functions_improved:
            summary["critical_issues_resolved"].append("Edge function JSON parsing errors resolved - health checks working")
        
        if error_handling_improved:
            summary["critical_issues_resolved"].append("Error handling improvements validated")
        
        # Identify remaining issues
        if not upload_working:
            summary["remaining_issues"].append("Upload pipeline still has issues")
        
        if not auth_working:
            summary["remaining_issues"].append("Authentication flow needs attention")
        
        # Generate recommendations
        if summary["overall_status"] == "operational":
            summary["recommendations"].append("Pipeline fixes successful - ready for production validation")
        elif summary["overall_status"] == "partially_operational":
            summary["recommendations"].append("Core fixes working - address remaining issues for full functionality")
        else:
            summary["recommendations"].append("Additional fixes needed - investigate remaining deployment issues")
        
        # Display summary
        print(f"📈 Overall Status: {summary['overall_status'].upper()}")
        print(f"🔧 Fixes Effective: {summary['fixes_effective']}")
        print(f"🏥 API Health: {summary['api_health']}")
        print(f"🔐 Authentication: {summary['authentication']}")
        print(f"⚡ Edge Functions: {summary['edge_functions']}")
        print(f"📤 Upload Pipeline: {summary['upload_pipeline']}")
        print(f"🛡️ Error Handling: {summary['error_handling']}")
        
        if summary["critical_issues_resolved"]:
            print(f"\n✅ Critical Issues Resolved:")
            for issue in summary["critical_issues_resolved"]:
                print(f"   • {issue}")
        
        if summary["remaining_issues"]:
            print(f"\n⚠️ Remaining Issues:")
            for issue in summary["remaining_issues"]:
                print(f"   • {issue}")
        
        if summary["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in summary["recommendations"]:
                print(f"   • {rec}")
        
        return summary

async def main():
    """Main validation function."""
    print("🚀 Comprehensive Insurance Navigator Pipeline Validation")
    print("=" * 60)
    
    validator = ComprehensivePipelineValidator()
    results = await validator.run_comprehensive_validation()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"comprehensive_pipeline_validation_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Full validation results saved to: {filename}")
    print("\n" + "=" * 60)
    print("✅ Comprehensive pipeline validation complete!")
    
    return results

if __name__ == "__main__":
    asyncio.run(main()) 