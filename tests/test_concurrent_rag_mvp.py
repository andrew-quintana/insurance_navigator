#!/usr/bin/env python3
"""
MVP Async Fix - Concurrent Request Testing Script

Tests the MVP async conversion with concurrent requests to validate:
1. No hanging with 2-3 concurrent requests
2. No hanging with 5+ concurrent requests (previously hanging scenario)
3. Response times under 10 seconds
4. System stability under load
5. Performance improvements from async conversion

Reference: Threading Update Initiative - Step 2 Testing
"""

import os
import asyncio
import sys
import time
import statistics
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import logging

# Add project root to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load development environment
from dotenv import load_dotenv
load_dotenv('.env.development')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Individual test result"""
    test_id: str
    query: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: str = ""
    chunks_returned: int = 0
    user_id: str = ""

@dataclass
class TestSuiteResult:
    """Complete test suite result"""
    test_name: str
    concurrent_requests: int
    total_duration: float
    success_rate: float
    avg_response_time: float
    median_response_time: float
    min_response_time: float
    max_response_time: float
    timeout_count: int
    error_count: int
    hanging_count: int
    individual_results: List[TestResult]
    timestamp: str

class ConcurrentRAGTester:
    """Comprehensive concurrent testing for MVP async fix"""
    
    def __init__(self):
        self.test_queries = [
            "What does my insurance cover for preventive care?",
            "What are my copay amounts for specialist visits?",
            "Does my plan cover mental health services?",
            "What is my annual deductible?",
            "Are prescription drugs covered?",
            "What hospitals are in my network?",
            "How do I file a claim?",
            "What is covered under emergency care?",
            "Does my plan include dental coverage?",
            "What are the coverage limits?"
        ]
        
        # Test user ID (using the same one from existing tests)
        self.test_user_id = 'f0cfcc46-5fdb-48c4-af13-51c6cf53e408'
        
        # Timeout threshold (10 seconds as per MVP requirements)
        self.timeout_threshold = 10.0
        
        # Hanging threshold (60 seconds - anything taking this long is considered hanging)
        self.hanging_threshold = 60.0
        
    async def create_rag_tool(self) -> Any:
        """Create RAG tool instance"""
        try:
            from agents.tooling.rag.core import RAGTool, RetrievalConfig
            
            rag_config = RetrievalConfig(
                similarity_threshold=0.3,
                max_chunks=10,
                token_budget=4000
            )
            
            return RAGTool(user_id=self.test_user_id, config=rag_config)
        except Exception as e:
            logger.error(f"Failed to create RAG tool: {e}")
            raise
    
    async def single_request_test(self, test_id: str, query: str) -> TestResult:
        """Execute a single RAG request and measure performance"""
        start_time = time.time()
        
        try:
            rag_tool = await self.create_rag_tool()
            
            # Execute the request with timeout protection
            chunks = await asyncio.wait_for(
                rag_tool.retrieve_chunks_from_text(query),
                timeout=self.timeout_threshold
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            return TestResult(
                test_id=test_id,
                query=query,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=True,
                chunks_returned=len(chunks),
                user_id=self.test_user_id
            )
            
        except asyncio.TimeoutError:
            end_time = time.time()
            duration = end_time - start_time
            
            logger.error(f"Test {test_id} timed out after {duration:.2f}s")
            return TestResult(
                test_id=test_id,
                query=query,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=False,
                error_message=f"Timeout after {duration:.2f}s",
                user_id=self.test_user_id
            )
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            logger.error(f"Test {test_id} failed: {e}")
            return TestResult(
                test_id=test_id,
                query=query,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=False,
                error_message=str(e),
                user_id=self.test_user_id
            )
    
    async def run_concurrent_test(self, concurrent_requests: int, test_name: str) -> TestSuiteResult:
        """Run concurrent test with specified number of requests"""
        logger.info(f"🚀 Starting {test_name} with {concurrent_requests} concurrent requests")
        
        # Prepare test queries (cycle through available queries if needed)
        test_queries = []
        for i in range(concurrent_requests):
            query = self.test_queries[i % len(self.test_queries)]
            test_queries.append((f"test_{i+1}", query))
        
        # Record overall test start time
        suite_start_time = time.time()
        
        # Execute all requests concurrently
        tasks = [
            self.single_request_test(test_id, query)
            for test_id, query in test_queries
        ]
        
        # Wait for all tasks to complete
        individual_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Record overall test end time
        suite_end_time = time.time()
        total_duration = suite_end_time - suite_start_time
        
        # Process results
        processed_results = []
        for result in individual_results:
            if isinstance(result, Exception):
                # Handle unexpected exceptions
                processed_results.append(TestResult(
                    test_id="unknown",
                    query="unknown",
                    start_time=suite_start_time,
                    end_time=suite_end_time,
                    duration=total_duration,
                    success=False,
                    error_message=f"Unexpected exception: {result}",
                    user_id=self.test_user_id
                ))
            else:
                processed_results.append(result)
        
        # Calculate statistics
        successful_results = [r for r in processed_results if r.success]
        failed_results = [r for r in processed_results if not r.success]
        
        success_rate = len(successful_results) / len(processed_results) * 100
        
        # Response time statistics (only for successful requests)
        if successful_results:
            response_times = [r.duration for r in successful_results]
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = 0
        
        # Count different types of failures
        timeout_count = len([r for r in failed_results if "Timeout" in r.error_message])
        hanging_count = len([r for r in processed_results if r.duration > self.hanging_threshold])
        error_count = len(failed_results) - timeout_count
        
        # Create test suite result
        suite_result = TestSuiteResult(
            test_name=test_name,
            concurrent_requests=concurrent_requests,
            total_duration=total_duration,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            timeout_count=timeout_count,
            error_count=error_count,
            hanging_count=hanging_count,
            individual_results=processed_results,
            timestamp=datetime.now().isoformat()
        )
        
        return suite_result
    
    def print_test_results(self, result: TestSuiteResult):
        """Print formatted test results"""
        print(f"\n{'='*60}")
        print(f"📊 TEST RESULTS: {result.test_name}")
        print(f"{'='*60}")
        print(f"🕐 Timestamp: {result.timestamp}")
        print(f"🔢 Concurrent Requests: {result.concurrent_requests}")
        print(f"⏱️  Total Duration: {result.total_duration:.2f}s")
        print(f"✅ Success Rate: {result.success_rate:.1f}%")
        print(f"📈 Response Times:")
        print(f"   • Average: {result.avg_response_time:.2f}s")
        print(f"   • Median:  {result.median_response_time:.2f}s")
        print(f"   • Min:     {result.min_response_time:.2f}s")
        print(f"   • Max:     {result.max_response_time:.2f}s")
        print(f"❌ Failures:")
        print(f"   • Timeouts: {result.timeout_count}")
        print(f"   • Errors:   {result.error_count}")
        print(f"   • Hanging:  {result.hanging_count}")
        
        # MVP Success Criteria Check
        print(f"\n🎯 MVP SUCCESS CRITERIA CHECK:")
        print(f"   • No hanging (5+ requests): {'✅ PASS' if result.hanging_count == 0 else '❌ FAIL'}")
        print(f"   • Response times < 10s: {'✅ PASS' if result.max_response_time < 10.0 else '❌ FAIL'}")
        print(f"   • System stability: {'✅ PASS' if result.success_rate >= 90.0 else '❌ FAIL'}")
        
        # Overall MVP status
        mvp_passed = (
            result.hanging_count == 0 and
            result.max_response_time < 10.0 and
            result.success_rate >= 90.0
        )
        
        print(f"\n🏆 OVERALL MVP STATUS: {'✅ PASS' if mvp_passed else '❌ FAIL'}")
        
        # Individual results summary
        if result.individual_results:
            print(f"\n📋 Individual Results:")
            for i, res in enumerate(result.individual_results[:5]):  # Show first 5
                status = "✅" if res.success else "❌"
                print(f"   {i+1}. {status} {res.test_id}: {res.duration:.2f}s ({res.chunks_returned} chunks)")
            
            if len(result.individual_results) > 5:
                print(f"   ... and {len(result.individual_results) - 5} more results")
    
    def save_test_results(self, result: TestSuiteResult, filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"concurrent_test_results_{timestamp}.json"
        
        # Convert to serializable format
        result_dict = asdict(result)
        
        # Convert datetime objects to strings
        for individual_result in result_dict['individual_results']:
            individual_result['start_time'] = individual_result['start_time']
            individual_result['end_time'] = individual_result['end_time']
        
        with open(filename, 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        logger.info(f"📁 Test results saved to: {filename}")
    
    async def run_full_test_suite(self):
        """Run the complete test suite"""
        print("🧪 MVP Async Fix - Concurrent Request Testing")
        print("=" * 60)
        print(f"🎯 Testing MVP async conversion with concurrent requests")
        print(f"⏱️  Timeout threshold: {self.timeout_threshold}s")
        print(f"🚫 Hanging threshold: {self.hanging_threshold}s")
        print(f"👤 Test user: {self.test_user_id}")
        print("=" * 60)
        
        all_results = []
        
        # Test 1: Basic concurrent test (2-3 requests)
        print(f"\n🔬 Test 1: Basic Concurrent Test (3 requests)")
        result_1 = await self.run_concurrent_test(3, "Basic Concurrent Test")
        self.print_test_results(result_1)
        all_results.append(result_1)
        
        # Small delay between tests
        await asyncio.sleep(2)
        
        # Test 2: Hanging scenario test (5+ requests)
        print(f"\n🔬 Test 2: Hanging Scenario Test (7 requests)")
        result_2 = await self.run_concurrent_test(7, "Hanging Scenario Test")
        self.print_test_results(result_2)
        all_results.append(result_2)
        
        # Small delay between tests
        await asyncio.sleep(2)
        
        # Test 3: Stress test (10+ requests)
        print(f"\n🔬 Test 3: Stress Test (10 requests)")
        result_3 = await self.run_concurrent_test(10, "Stress Test")
        self.print_test_results(result_3)
        all_results.append(result_3)
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 COMPLETE TEST SUITE SUMMARY")
        print(f"{'='*60}")
        
        total_tests = len(all_results)
        passed_tests = 0
        
        for i, result in enumerate(all_results, 1):
            mvp_passed = (
                result.hanging_count == 0 and
                result.max_response_time < 10.0 and
                result.success_rate >= 90.0
            )
            
            if mvp_passed:
                passed_tests += 1
            
            status = "✅ PASS" if mvp_passed else "❌ FAIL"
            print(f"Test {i}: {result.test_name} - {status}")
            print(f"  • Hanging: {result.hanging_count}, Max time: {result.max_response_time:.2f}s, Success: {result.success_rate:.1f}%")
        
        print(f"\n🏆 OVERALL RESULT: {passed_tests}/{total_tests} tests passed MVP criteria")
        
        if passed_tests == total_tests:
            print("🎉 MVP ASYNC FIX VALIDATION: SUCCESS!")
            print("   The async conversion successfully prevents hanging and maintains performance.")
        else:
            print("⚠️  MVP ASYNC FIX VALIDATION: NEEDS ATTENTION")
            print("   Some tests failed MVP criteria. Review results for issues.")
        
        # Save all results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_filename = f"test-results/mvp_concurrent_test_summary_{timestamp}.json"
        
        summary_data = {
            "test_suite": "MVP Async Fix Concurrent Testing",
            "timestamp": datetime.now().isoformat(),
            "mvp_criteria": {
                "no_hanging": "No requests taking > 60s",
                "response_time_limit": "All requests < 10s",
                "stability_threshold": "Success rate >= 90%"
            },
            "results": [asdict(result) for result in all_results],
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "overall_status": "SUCCESS" if passed_tests == total_tests else "NEEDS_ATTENTION"
            }
        }
        
        with open(summary_filename, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        logger.info(f"📁 Complete test suite results saved to: {summary_filename}")
        
        return all_results

async def main():
    """Main test execution"""
    try:
        tester = ConcurrentRAGTester()
        results = await tester.run_full_test_suite()
        
        # Exit with appropriate code
        all_passed = all(
            result.hanging_count == 0 and
            result.max_response_time < 10.0 and
            result.success_rate >= 90.0
            for result in results
        )
        
        sys.exit(0 if all_passed else 1)
        
    except Exception as e:
        logger.error(f"Test suite failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
