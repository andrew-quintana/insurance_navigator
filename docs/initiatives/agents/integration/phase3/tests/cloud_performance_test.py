#!/usr/bin/env python3
"""
Phase 3 - Cloud Performance Test

This test validates performance metrics in the cloud environment including
response times, throughput, scalability, and resource utilization.
"""

import asyncio
import os
import sys
import json
import time
import logging
import statistics
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase3CloudPerformanceTest:
    def __init__(self):
        self.results = {
            "test_name": "Phase 3 Cloud Performance Test",
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0.0
            }
        }
        
        # Load production environment
        load_dotenv('.env.production')
        
        # Test configuration
        self.agent_api_url = os.getenv('AGENT_API_URL', 'https://agents-api.yourdomain.com')
        self.test_user_email = f"phase3_perf_test_{int(time.time())}@example.com"
        self.test_user_password = "TestPassword123!"
        self.access_token = None
        
        # Performance test queries
        self.performance_queries = [
            "What is health insurance?",
            "How do I file a claim?",
            "What's the difference between HMO and PPO?",
            "How do I find a doctor in my network?",
            "What is covered under my plan?",
            "What is the deductible for my insurance?",
            "How do I check my benefits?",
            "What is a copay?",
            "How do I get a referral?",
            "What is an out-of-pocket maximum?"
        ]
    
    async def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        logger.info(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            test_result = {
                "name": test_name,
                "status": "PASSED" if result else "FAILED",
                "duration": duration,
                "details": result if isinstance(result, dict) else {"success": result}
            }
            
            self.results["tests"].append(test_result)
            self.results["summary"]["total_tests"] += 1
            
            if result:
                self.results["summary"]["passed"] += 1
                logger.info(f"✅ {test_name} - PASSED ({duration:.2f}s)")
            else:
                self.results["summary"]["failed"] += 1
                logger.error(f"❌ {test_name} - FAILED ({duration:.2f}s)")
                
        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "name": test_name,
                "status": "ERROR",
                "duration": duration,
                "error": str(e)
            }
            
            self.results["tests"].append(test_result)
            self.results["summary"]["total_tests"] += 1
            self.results["summary"]["failed"] += 1
            logger.error(f"❌ {test_name} - ERROR: {str(e)} ({duration:.2f}s)")
    
    async def authenticate_user(self) -> bool:
        """Authenticate test user"""
        try:
            async with httpx.AsyncClient() as client:
                # Try to register a test user
                register_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password,
                    "name": "Phase3 Performance Test User"
                }
                
                try:
                    await client.post(
                        f"{self.agent_api_url}/register",
                        json=register_data,
                        timeout=30.0
                    )
                except Exception:
                    pass  # User might already exist
                
                # Try to login
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password
                }
                
                login_response = await client.post(
                    f"{self.agent_api_url}/login",
                    json=login_data,
                    timeout=30.0
                )
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    self.access_token = login_data.get("access_token")
                    return bool(self.access_token)
                
                return False
                
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
    async def test_response_time_baseline(self) -> Dict[str, Any]:
        """Test baseline response times for various queries"""
        try:
            if not await self.authenticate_user():
                return {
                    "success": False,
                    "error": "Failed to authenticate user"
                }
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                response_times = []
                successful_requests = 0
                
                for i, query in enumerate(self.performance_queries):
                    try:
                        chat_data = {
                            "message": query,
                            "conversation_id": f"perf_baseline_conv_{i}"
                        }
                        
                        start_time = time.time()
                        response = await client.post(
                            f"{self.agent_api_url}/chat",
                            json=chat_data,
                            headers=headers,
                            timeout=60.0
                        )
                        end_time = time.time()
                        
                        if response.status_code == 200:
                            response_time = end_time - start_time
                            response_times.append(response_time)
                            successful_requests += 1
                            
                            logger.info(f"Query {i+1}: {response_time:.2f}s")
                        else:
                            logger.warning(f"Query {i+1} failed with status {response.status_code}")
                            
                    except Exception as e:
                        logger.warning(f"Query {i+1} failed: {str(e)}")
                
                if response_times:
                    performance_metrics = {
                        "total_queries": len(self.performance_queries),
                        "successful_requests": successful_requests,
                        "success_rate": (successful_requests / len(self.performance_queries)) * 100,
                        "average_response_time": statistics.mean(response_times),
                        "median_response_time": statistics.median(response_times),
                        "min_response_time": min(response_times),
                        "max_response_time": max(response_times),
                        "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 1 else response_times[0],
                        "response_times": response_times
                    }
                    
                    # Check if performance meets targets
                    meets_targets = (
                        performance_metrics["average_response_time"] < 3.0 and  # < 3 seconds average
                        performance_metrics["p95_response_time"] < 5.0 and      # < 5 seconds p95
                        performance_metrics["success_rate"] >= 90.0             # >= 90% success rate
                    )
                    
                    return {
                        "success": meets_targets,
                        "performance_metrics": performance_metrics,
                        "meets_targets": meets_targets,
                        "cloud_performance": True
                    }
                else:
                    return {
                        "success": False,
                        "error": "No successful requests"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_concurrent_requests(self) -> Dict[str, Any]:
        """Test performance under concurrent load"""
        try:
            if not await self.authenticate_user():
                return {
                    "success": False,
                    "error": "Failed to authenticate user"
                }
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Test with different concurrency levels
                concurrency_levels = [5, 10, 20]  # 5, 10, 20 concurrent requests
                concurrency_results = []
                
                for concurrency in concurrency_levels:
                    logger.info(f"Testing {concurrency} concurrent requests...")
                    
                    async def single_request(request_id):
                        try:
                            query = self.performance_queries[request_id % len(self.performance_queries)]
                            chat_data = {
                                "message": query,
                                "conversation_id": f"concurrent_test_conv_{request_id}"
                            }
                            
                            start_time = time.time()
                            response = await client.post(
                                f"{self.agent_api_url}/chat",
                                json=chat_data,
                                headers=headers,
                                timeout=60.0
                            )
                            end_time = time.time()
                            
                            return {
                                "request_id": request_id,
                                "success": response.status_code == 200,
                                "response_time": end_time - start_time,
                                "status_code": response.status_code
                            }
                        except Exception as e:
                            return {
                                "request_id": request_id,
                                "success": False,
                                "error": str(e)
                            }
                    
                    # Run concurrent requests
                    start_time = time.time()
                    tasks = [single_request(i) for i in range(concurrency)]
                    results = await asyncio.gather(*tasks)
                    end_time = time.time()
                    
                    # Calculate metrics for this concurrency level
                    successful_requests = [r for r in results if r.get("success")]
                    response_times = [r["response_time"] for r in successful_requests]
                    
                    concurrency_metrics = {
                        "concurrency_level": concurrency,
                        "total_requests": len(results),
                        "successful_requests": len(successful_requests),
                        "success_rate": (len(successful_requests) / len(results)) * 100,
                        "total_time": end_time - start_time,
                        "requests_per_second": len(results) / (end_time - start_time),
                        "average_response_time": statistics.mean(response_times) if response_times else 0,
                        "median_response_time": statistics.median(response_times) if response_times else 0,
                        "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 1 else (response_times[0] if response_times else 0)
                    }
                    
                    concurrency_results.append(concurrency_metrics)
                
                # Overall analysis
                max_rps = max(r["requests_per_second"] for r in concurrency_results)
                min_success_rate = min(r["success_rate"] for r in concurrency_results)
                max_avg_response_time = max(r["average_response_time"] for r in concurrency_results)
                
                meets_targets = (
                    max_rps >= 10.0 and           # >= 10 RPS
                    min_success_rate >= 80.0 and  # >= 80% success rate
                    max_avg_response_time < 5.0   # < 5 seconds average response time
                )
                
                return {
                    "success": meets_targets,
                    "concurrency_results": concurrency_results,
                    "max_rps": max_rps,
                    "min_success_rate": min_success_rate,
                    "max_avg_response_time": max_avg_response_time,
                    "meets_targets": meets_targets,
                    "cloud_concurrent_performance": True
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_memory_usage_under_load(self) -> Dict[str, Any]:
        """Test memory usage patterns under load"""
        try:
            if not await self.authenticate_user():
                return {
                    "success": False,
                    "error": "Failed to authenticate user"
                }
            
            # This is a simplified test - in a real scenario, you'd monitor actual memory usage
            # For now, we'll test that the system can handle sustained load without degradation
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Run sustained load test
                sustained_requests = 50
                response_times = []
                success_count = 0
                
                logger.info(f"Running sustained load test with {sustained_requests} requests...")
                
                for i in range(sustained_requests):
                    try:
                        query = self.performance_queries[i % len(self.performance_queries)]
                        chat_data = {
                            "message": query,
                            "conversation_id": f"sustained_load_conv_{i}"
                        }
                        
                        start_time = time.time()
                        response = await client.post(
                            f"{self.agent_api_url}/chat",
                            json=chat_data,
                            headers=headers,
                            timeout=60.0
                        )
                        end_time = time.time()
                        
                        if response.status_code == 200:
                            response_time = end_time - start_time
                            response_times.append(response_time)
                            success_count += 1
                        
                        # Small delay to avoid overwhelming the system
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        logger.warning(f"Request {i} failed: {str(e)}")
                
                if response_times:
                    # Check for performance degradation over time
                    first_half = response_times[:len(response_times)//2]
                    second_half = response_times[len(response_times)//2:]
                    
                    first_half_avg = statistics.mean(first_half)
                    second_half_avg = statistics.mean(second_half)
                    degradation_ratio = second_half_avg / first_half_avg if first_half_avg > 0 else 1.0
                    
                    memory_metrics = {
                        "total_requests": sustained_requests,
                        "successful_requests": success_count,
                        "success_rate": (success_count / sustained_requests) * 100,
                        "average_response_time": statistics.mean(response_times),
                        "first_half_avg": first_half_avg,
                        "second_half_avg": second_half_avg,
                        "degradation_ratio": degradation_ratio,
                        "performance_stable": degradation_ratio < 1.5  # Less than 50% degradation
                    }
                    
                    return {
                        "success": memory_metrics["performance_stable"] and memory_metrics["success_rate"] >= 80.0,
                        "memory_metrics": memory_metrics,
                        "cloud_memory_performance": True
                    }
                else:
                    return {
                        "success": False,
                        "error": "No successful requests in sustained load test"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_scalability_validation(self) -> Dict[str, Any]:
        """Test system scalability and auto-scaling behavior"""
        try:
            if not await self.authenticate_user():
                return {
                    "success": False,
                    "error": "Failed to authenticate user"
                }
            
            # Test with increasing load to validate auto-scaling
            load_levels = [
                {"concurrent": 5, "duration": 30},   # Light load
                {"concurrent": 15, "duration": 30},  # Medium load
                {"concurrent": 30, "duration": 30},  # Heavy load
            ]
            
            scalability_results = []
            
            for load_level in load_levels:
                logger.info(f"Testing scalability with {load_level['concurrent']} concurrent requests for {load_level['duration']} seconds...")
                
                async with httpx.AsyncClient() as client:
                    headers = {
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    }
                    
                    async def sustained_request(request_id):
                        start_time = time.time()
                        end_time = start_time + load_level['duration']
                        request_count = 0
                        success_count = 0
                        response_times = []
                        
                        while time.time() < end_time:
                            try:
                                query = self.performance_queries[request_id % len(self.performance_queries)]
                                chat_data = {
                                    "message": query,
                                    "conversation_id": f"scalability_test_conv_{request_id}_{request_count}"
                                }
                                
                                req_start = time.time()
                                response = await client.post(
                                    f"{self.agent_api_url}/chat",
                                    json=chat_data,
                                    headers=headers,
                                    timeout=60.0
                                )
                                req_end = time.time()
                                
                                request_count += 1
                                if response.status_code == 200:
                                    success_count += 1
                                    response_times.append(req_end - req_start)
                                
                                # Small delay between requests
                                await asyncio.sleep(0.5)
                                
                            except Exception as e:
                                logger.warning(f"Request failed in scalability test: {str(e)}")
                                await asyncio.sleep(1.0)
                        
                        return {
                            "request_id": request_id,
                            "total_requests": request_count,
                            "successful_requests": success_count,
                            "success_rate": (success_count / request_count) * 100 if request_count > 0 else 0,
                            "average_response_time": statistics.mean(response_times) if response_times else 0,
                            "response_times": response_times
                        }
                    
                    # Run concurrent sustained requests
                    tasks = [sustained_request(i) for i in range(load_level['concurrent'])]
                    results = await asyncio.gather(*tasks)
                    
                    # Calculate metrics for this load level
                    total_requests = sum(r["total_requests"] for r in results)
                    total_successful = sum(r["successful_requests"] for r in results)
                    all_response_times = []
                    for r in results:
                        all_response_times.extend(r["response_times"])
                    
                    load_metrics = {
                        "concurrent_requests": load_level['concurrent'],
                        "duration_seconds": load_level['duration'],
                        "total_requests": total_requests,
                        "successful_requests": total_successful,
                        "success_rate": (total_successful / total_requests) * 100 if total_requests > 0 else 0,
                        "requests_per_second": total_requests / load_level['duration'],
                        "average_response_time": statistics.mean(all_response_times) if all_response_times else 0,
                        "p95_response_time": sorted(all_response_times)[int(len(all_response_times) * 0.95)] if len(all_response_times) > 1 else (all_response_times[0] if all_response_times else 0)
                    }
                    
                    scalability_results.append(load_metrics)
            
            # Analyze scalability
            success_rates = [r["success_rate"] for r in scalability_results]
            response_times = [r["average_response_time"] for r in scalability_results]
            
            # Check if system maintains performance under increasing load
            performance_degradation = max(response_times) / min(response_times) if min(response_times) > 0 else 1.0
            min_success_rate = min(success_rates)
            
            scalable = (
                performance_degradation < 2.0 and  # Less than 2x performance degradation
                min_success_rate >= 70.0          # At least 70% success rate under heavy load
            )
            
            return {
                "success": scalable,
                "scalability_results": scalability_results,
                "performance_degradation": performance_degradation,
                "min_success_rate": min_success_rate,
                "scalable": scalable,
                "cloud_scalability": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_error_rate_under_load(self) -> Dict[str, Any]:
        """Test error rates under various load conditions"""
        try:
            if not await self.authenticate_user():
                return {
                    "success": False,
                    "error": "Failed to authenticate user"
                }
            
            # Test error rates with different load patterns
            error_test_scenarios = [
                {"name": "normal_load", "concurrent": 10, "requests": 50},
                {"name": "high_load", "concurrent": 25, "requests": 100},
                {"name": "burst_load", "concurrent": 50, "requests": 200}
            ]
            
            error_results = []
            
            for scenario in error_test_scenarios:
                logger.info(f"Testing error rates for {scenario['name']} scenario...")
                
                async with httpx.AsyncClient() as client:
                    headers = {
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    }
                    
                    async def error_test_request(request_id):
                        try:
                            query = self.performance_queries[request_id % len(self.performance_queries)]
                            chat_data = {
                                "message": query,
                                "conversation_id": f"error_test_conv_{request_id}"
                            }
                            
                            response = await client.post(
                                f"{self.agent_api_url}/chat",
                                json=chat_data,
                                headers=headers,
                                timeout=60.0
                            )
                            
                            return {
                                "request_id": request_id,
                                "success": response.status_code == 200,
                                "status_code": response.status_code,
                                "error": None
                            }
                        except Exception as e:
                            return {
                                "request_id": request_id,
                                "success": False,
                                "status_code": 0,
                                "error": str(e)
                            }
                    
                    # Run requests in batches
                    batch_size = scenario["concurrent"]
                    total_requests = scenario["requests"]
                    all_results = []
                    
                    for batch_start in range(0, total_requests, batch_size):
                        batch_end = min(batch_start + batch_size, total_requests)
                        batch_requests = list(range(batch_start, batch_end))
                        
                        tasks = [error_test_request(i) for i in batch_requests]
                        batch_results = await asyncio.gather(*tasks)
                        all_results.extend(batch_results)
                        
                        # Small delay between batches
                        await asyncio.sleep(0.5)
                    
                    # Calculate error metrics for this scenario
                    successful_requests = [r for r in all_results if r["success"]]
                    error_requests = [r for r in all_results if not r["success"]]
                    
                    error_metrics = {
                        "scenario": scenario["name"],
                        "total_requests": len(all_results),
                        "successful_requests": len(successful_requests),
                        "error_requests": len(error_requests),
                        "success_rate": (len(successful_requests) / len(all_results)) * 100,
                        "error_rate": (len(error_requests) / len(all_results)) * 100,
                        "status_codes": {}
                    }
                    
                    # Count status codes
                    for result in all_results:
                        status_code = result["status_code"]
                        error_metrics["status_codes"][str(status_code)] = error_metrics["status_codes"].get(str(status_code), 0) + 1
                    
                    error_results.append(error_metrics)
            
            # Overall error analysis
            max_error_rate = max(r["error_rate"] for r in error_results)
            min_success_rate = min(r["success_rate"] for r in error_results)
            
            acceptable_error_rate = max_error_rate <= 5.0  # <= 5% error rate
            acceptable_success_rate = min_success_rate >= 90.0  # >= 90% success rate
            
            return {
                "success": acceptable_error_rate and acceptable_success_rate,
                "error_results": error_results,
                "max_error_rate": max_error_rate,
                "min_success_rate": min_success_rate,
                "acceptable_error_rate": acceptable_error_rate,
                "acceptable_success_rate": acceptable_success_rate,
                "cloud_error_handling": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_all_tests(self):
        """Run all Phase 3 cloud performance tests"""
        logger.info("🚀 Starting Phase 3 Cloud Performance Tests")
        
        # Run all tests
        await self.run_test("Response Time Baseline", self.test_response_time_baseline)
        await self.run_test("Concurrent Requests", self.test_concurrent_requests)
        await self.run_test("Memory Usage Under Load", self.test_memory_usage_under_load)
        await self.run_test("Scalability Validation", self.test_scalability_validation)
        await self.run_test("Error Rate Under Load", self.test_error_rate_under_load)
        
        # Calculate success rate
        total = self.results["summary"]["total_tests"]
        passed = self.results["summary"]["passed"]
        self.results["summary"]["success_rate"] = (passed / total * 100) if total > 0 else 0
        
        # Log summary
        logger.info(f"📊 Phase 3 Cloud Performance Tests Complete")
        logger.info(f"   Total Tests: {total}")
        logger.info(f"   Passed: {passed}")
        logger.info(f"   Failed: {self.results['summary']['failed']}")
        logger.info(f"   Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        return self.results

async def main():
    """Main test execution"""
    test = Phase3CloudPerformanceTest()
    results = await test.run_all_tests()
    
    # Save results
    results_file = os.path.join(
        os.path.dirname(__file__), 
        '../results/cloud_performance_results.json'
    )
    
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"📁 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
