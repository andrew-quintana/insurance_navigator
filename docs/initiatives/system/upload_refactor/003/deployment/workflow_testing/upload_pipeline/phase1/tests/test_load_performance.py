#!/usr/bin/env python3
"""
Load testing for upload pipeline
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

class LoadTester:
    """Load testing for upload pipeline"""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.test_document = "examples/simulated_insurance_document.pdf"
        self.results = []
    
    def single_upload_test(self, test_id):
        """Test a single upload"""
        start_time = time.time()
        
        try:
            # Test upload
            response = requests.post(
                f"{self.api_base_url}/test/upload",
                json={"filename": f"test_{test_id}.pdf"},
                timeout=10
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = response.status_code == 200
            result = {
                "test_id": test_id,
                "success": success,
                "duration": duration,
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            result = {
                "test_id": test_id,
                "success": False,
                "duration": duration,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return result
    
    def run_concurrent_tests(self, num_concurrent=5, num_requests=20):
        """Run concurrent load tests"""
        print(f"🚀 Running load test: {num_concurrent} concurrent, {num_requests} total requests")
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            # Submit all requests
            futures = [
                executor.submit(self.single_upload_test, i) 
                for i in range(num_requests)
            ]
            
            # Collect results
            results = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Analyze results
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        success_rate = len(successful) / len(results) * 100
        avg_duration = sum(r['duration'] for r in successful) / len(successful) if successful else 0
        max_duration = max(r['duration'] for r in results) if results else 0
        min_duration = min(r['duration'] for r in results) if results else 0
        
        throughput = len(results) / total_duration
        
        print(f"\n📊 Load Test Results:")
        print(f"   Total requests: {len(results)}")
        print(f"   Successful: {len(successful)}")
        print(f"   Failed: {len(failed)}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Total duration: {total_duration:.2f}s")
        print(f"   Throughput: {throughput:.2f} requests/second")
        print(f"   Avg response time: {avg_duration:.3f}s")
        print(f"   Min response time: {min_duration:.3f}s")
        print(f"   Max response time: {max_duration:.3f}s")
        
        # Check if we meet the acceptance criteria
        criteria_met = (
            success_rate >= 95.0 and  # > 95% success rate
            avg_duration <= 2.0 and   # < 2 seconds average response time
            len(failed) <= 1          # < 1% error rate
        )
        
        if criteria_met:
            print("✅ Load test PASSED - All criteria met")
        else:
            print("❌ Load test FAILED - Criteria not met")
            if success_rate < 95.0:
                print(f"   - Success rate too low: {success_rate:.1f}% < 95%")
            if avg_duration > 2.0:
                print(f"   - Response time too high: {avg_duration:.3f}s > 2.0s")
            if len(failed) > 1:
                print(f"   - Too many failures: {len(failed)} > 1")
        
        return {
            "total_requests": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": success_rate,
            "total_duration": total_duration,
            "throughput": throughput,
            "avg_duration": avg_duration,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "criteria_met": criteria_met,
            "results": results
        }
    
    def run_stress_test(self):
        """Run stress test with increasing load"""
        print("\n🔥 Running stress test...")
        
        test_scenarios = [
            {"concurrent": 2, "requests": 10, "name": "Light Load"},
            {"concurrent": 5, "requests": 25, "name": "Medium Load"},
            {"concurrent": 10, "requests": 50, "name": "Heavy Load"},
        ]
        
        all_results = []
        
        for scenario in test_scenarios:
            print(f"\n📈 {scenario['name']}: {scenario['concurrent']} concurrent, {scenario['requests']} requests")
            result = self.run_concurrent_tests(
                scenario['concurrent'], 
                scenario['requests']
            )
            result['scenario'] = scenario['name']
            all_results.append(result)
            
            # Brief pause between scenarios
            time.sleep(2)
        
        # Overall analysis
        print(f"\n📊 Overall Stress Test Results:")
        print("=" * 50)
        
        all_passed = all(r['criteria_met'] for r in all_results)
        
        for result in all_results:
            status = "✅ PASS" if result['criteria_met'] else "❌ FAIL"
            print(f"{status} {result['scenario']}: {result['success_rate']:.1f}% success, {result['avg_duration']:.3f}s avg")
        
        if all_passed:
            print("\n🎉 All stress test scenarios PASSED!")
        else:
            print("\n⚠️  Some stress test scenarios FAILED!")
        
        return all_passed

async def main():
    """Main test function"""
    tester = LoadTester()
    
    print("🧪 Running upload pipeline load tests...")
    print("=" * 60)
    
    # Run basic load test
    print("\n1️⃣ Basic Load Test")
    basic_result = tester.run_concurrent_tests(num_concurrent=3, num_requests=15)
    
    # Run stress test
    print("\n2️⃣ Stress Test")
    stress_passed = tester.run_stress_test()
    
    # Overall result
    overall_success = basic_result['criteria_met'] and stress_passed
    
    print(f"\n{'='*60}")
    print(f"🏁 Overall Load Test Result: {'✅ PASS' if overall_success else '❌ FAIL'}")
    print(f"{'='*60}")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
