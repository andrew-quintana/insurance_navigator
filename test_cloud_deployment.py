#!/usr/bin/env python3
"""
Test cloud deployment and compare with Phase 1 baselines
"""

import asyncio
import sys
import os
import json
import time
import requests
import concurrent.futures
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.append(os.path.dirname(__file__))

class CloudTester:
    """Test cloud deployment performance"""
    
    def __init__(self):
        # Cloud service URLs (these would be the actual deployed URLs)
        self.cloud_api_url = "***REMOVED***"  # Update with actual URL
        self.local_api_url = "http://localhost:8000"
        
        # Phase 1 baselines from our testing
        self.phase1_baselines = {
            "avg_response_time": 0.061,  # seconds
            "max_response_time": 0.067,  # seconds
            "throughput": 400.0,  # requests/second
            "success_rate": 100.0,  # percentage
            "error_rate": 0.0  # percentage
        }
        
        self.results = {}
    
    def test_cloud_health(self):
        """Test cloud service health"""
        print("🏥 Testing cloud service health...")
        
        try:
            response = requests.get(f"{self.cloud_api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Cloud API health: {data['status']} (v{data['version']})")
                return True
            else:
                print(f"❌ Cloud API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cloud API health check error: {e}")
            return False
    
    def test_cloud_endpoints(self):
        """Test cloud API endpoints"""
        print("\n🔗 Testing cloud API endpoints...")
        
        endpoints = [
            ("/health", "GET"),
            ("/api/v1/status", "GET"),
            ("/upload-document-backend", "POST", {"filename": "cloud_test.pdf"})
        ]
        
        all_success = True
        
        for endpoint in endpoints:
            url = f"{self.cloud_api_url}{endpoint[0]}"
            method = endpoint[1]
            
            try:
                if method == "GET":
                    response = requests.get(url, timeout=10)
                elif method == "POST":
                    response = requests.post(url, json=endpoint[2], timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ {method} {endpoint[0]}: OK")
                else:
                    print(f"❌ {method} {endpoint[0]}: HTTP {response.status_code}")
                    all_success = False
                    
            except Exception as e:
                print(f"❌ {method} {endpoint[0]}: Error - {e}")
                all_success = False
        
        return all_success
    
    def test_cloud_performance(self, num_requests=20):
        """Test cloud performance and compare with Phase 1 baselines"""
        print(f"\n⚡ Testing cloud performance ({num_requests} requests)...")
        
        response_times = []
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        for i in range(num_requests):
            try:
                request_start = time.time()
                response = requests.post(
                    f"{self.cloud_api_url}/test/upload",
                    json={"filename": f"perf_test_{i}.pdf"},
                    timeout=10
                )
                request_end = time.time()
                
                if response.status_code == 200:
                    successful += 1
                    response_times.append(request_end - request_start)
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                print(f"   Request {i} failed: {e}")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate metrics
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = 0
            max_response_time = 0
            min_response_time = 0
        
        success_rate = (successful / num_requests) * 100
        error_rate = (failed / num_requests) * 100
        throughput = num_requests / total_duration
        
        # Store results
        self.results = {
            "avg_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "min_response_time": min_response_time,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "throughput": throughput,
            "total_requests": num_requests,
            "successful": successful,
            "failed": failed,
            "total_duration": total_duration
        }
        
        print(f"   Average response time: {avg_response_time:.3f}s")
        print(f"   Max response time: {max_response_time:.3f}s")
        print(f"   Min response time: {min_response_time:.3f}s")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Error rate: {error_rate:.1f}%")
        print(f"   Throughput: {throughput:.2f} requests/second")
        
        return self.results
    
    def compare_with_phase1(self):
        """Compare cloud performance with Phase 1 baselines"""
        print("\n📊 Comparing with Phase 1 baselines...")
        
        if not self.results:
            print("❌ No performance results to compare")
            return False
        
        comparisons = []
        
        # Response time comparison (allow 50% degradation for cloud)
        response_time_threshold = self.phase1_baselines["avg_response_time"] * 1.5
        if self.results["avg_response_time"] <= response_time_threshold:
            comparisons.append(("Response Time", True, f"{self.results['avg_response_time']:.3f}s <= {response_time_threshold:.3f}s"))
        else:
            comparisons.append(("Response Time", False, f"{self.results['avg_response_time']:.3f}s > {response_time_threshold:.3f}s"))
        
        # Success rate comparison (should be > 95%)
        if self.results["success_rate"] >= 95.0:
            comparisons.append(("Success Rate", True, f"{self.results['success_rate']:.1f}% >= 95%"))
        else:
            comparisons.append(("Success Rate", False, f"{self.results['success_rate']:.1f}% < 95%"))
        
        # Error rate comparison (should be < 5%)
        if self.results["error_rate"] <= 5.0:
            comparisons.append(("Error Rate", True, f"{self.results['error_rate']:.1f}% <= 5%"))
        else:
            comparisons.append(("Error Rate", False, f"{self.results['error_rate']:.1f}% > 5%"))
        
        # Print comparison results
        print("   Phase 1 vs Cloud Performance:")
        for metric, passed, details in comparisons:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status} {metric}: {details}")
        
        # Overall assessment
        all_passed = all(passed for _, passed, _ in comparisons)
        
        if all_passed:
            print("✅ Cloud performance meets Phase 1 criteria")
        else:
            print("❌ Cloud performance does not meet Phase 1 criteria")
        
        return all_passed
    
    def test_cloud_load(self, concurrent_users=5, requests_per_user=10):
        """Test cloud load handling"""
        print(f"\n🚀 Testing cloud load ({concurrent_users} users, {requests_per_user} requests each)...")
        
        def user_simulation(user_id):
            """Simulate a user making requests"""
            user_results = []
            
            for i in range(requests_per_user):
                try:
                    start_time = time.time()
                    response = requests.post(
                        f"{self.cloud_api_url}/test/upload",
                        json={"filename": f"load_test_user_{user_id}_req_{i}.pdf"},
                        timeout=15
                    )
                    end_time = time.time()
                    
                    user_results.append({
                        "user_id": user_id,
                        "request_id": i,
                        "success": response.status_code == 200,
                        "response_time": end_time - start_time,
                        "status_code": response.status_code
                    })
                    
                except Exception as e:
                    user_results.append({
                        "user_id": user_id,
                        "request_id": i,
                        "success": False,
                        "response_time": 0,
                        "error": str(e)
                    })
            
            return user_results
        
        # Run concurrent users
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(user_simulation, user_id) 
                for user_id in range(concurrent_users)
            ]
            
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                user_results = future.result()
                all_results.extend(user_results)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Analyze results
        successful = [r for r in all_results if r['success']]
        failed = [r for r in all_results if not r['success']]
        
        success_rate = len(successful) / len(all_results) * 100
        avg_response_time = sum(r['response_time'] for r in successful) / len(successful) if successful else 0
        throughput = len(all_results) / total_duration
        
        print(f"   Total requests: {len(all_results)}")
        print(f"   Successful: {len(successful)}")
        print(f"   Failed: {len(failed)}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Average response time: {avg_response_time:.3f}s")
        print(f"   Throughput: {throughput:.2f} requests/second")
        
        # Check if load test passed
        load_passed = success_rate >= 90.0 and avg_response_time <= 5.0
        
        if load_passed:
            print("✅ Cloud load test passed")
        else:
            print("❌ Cloud load test failed")
        
        return load_passed
    
    def run_cloud_tests(self):
        """Run all cloud tests"""
        print("☁️  Testing Cloud Deployment")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_cloud_health),
            ("API Endpoints", self.test_cloud_endpoints),
            ("Performance", lambda: self.test_cloud_performance(20)),
            ("Load Test", lambda: self.test_cloud_load(3, 5))
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name}...")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Performance comparison
        if self.results:
            print(f"\n📊 Performance Comparison:")
            self.compare_with_phase1()
        
        # Print final results
        print(f"\n{'='*50}")
        print("📊 Cloud Test Results:")
        print(f"{'='*50}")
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n📈 Summary: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("\n🎉 All cloud tests passed!")
            return True
        else:
            print("\n⚠️  Some cloud tests failed")
            return False

async def main():
    """Main test function"""
    tester = CloudTester()
    success = tester.run_cloud_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
