#!/usr/bin/env python3
"""
MVP Async Fix Production API Testing Script

This script tests the MVP async fix against the production backend API service.
It validates:
1. Concurrent request handling
2. Hanging issue prevention
3. Response time improvements
4. System stability under load

Usage:
    python scripts/test_mvp_async_fix_production.py --api-url https://your-api.com
    python scripts/test_mvp_async_fix_production.py --api-url https://your-api.com --concurrent 10
    python scripts/test_mvp_async_fix_production.py --api-url https://your-api.com --monitor 24
"""

import asyncio
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
import psutil
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mvp_production_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestMetrics:
    """Metrics for production API testing."""
    timestamp: datetime
    test_type: str
    success: bool
    response_time: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    concurrent_requests: int = 1
    hanging_detected: bool = False
    api_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'test_type': self.test_type,
            'success': self.success,
            'response_time': self.response_time,
            'status_code': self.status_code,
            'error_message': self.error_message,
            'concurrent_requests': self.concurrent_requests,
            'hanging_detected': self.hanging_detected,
            'api_url': self.api_url
        }

class ProductionAPITester:
    """Tests MVP async fix against production API."""
    
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/')
        self.metrics: List[TestMetrics] = []
        self.test_start_time = None
        
    async def test_single_request(self) -> bool:
        """Test single request to validate basic functionality."""
        logger.info("🧪 TESTING SINGLE REQUEST")
        logger.info("=" * 40)
        
        try:
            test_payload = {
                "query": "test query for MVP async fix validation",
                "user_id": "test-user-single",
                "context": "production_test"
            }
            
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/api/chat",
                    json=test_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                response_time = time.time() - start_time
                
                success = response.status_code == 200
                hanging = response_time > 30.0
                
                logger.info(f"📊 Single Request Results:")
                logger.info(f"   Status Code: {response.status_code}")
                logger.info(f"   Response Time: {response_time:.2f}s")
                logger.info(f"   Success: {success}")
                logger.info(f"   Hanging: {hanging}")
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        logger.info(f"   Response Keys: {list(response_data.keys())}")
                    except:
                        logger.warning("   Could not parse JSON response")
                
                # Record metrics
                self.metrics.append(TestMetrics(
                    timestamp=datetime.now(),
                    test_type="single_request",
                    success=success,
                    response_time=response_time,
                    status_code=response.status_code,
                    hanging_detected=hanging,
                    api_url=self.api_url
                ))
                
                return success and not hanging
                
        except Exception as e:
            logger.error(f"❌ Single request test failed: {e}")
            self.metrics.append(TestMetrics(
                timestamp=datetime.now(),
                test_type="single_request",
                success=False,
                response_time=0.0,
                error_message=str(e),
                api_url=self.api_url
            ))
            return False
    
    async def test_concurrent_requests(self, num_requests: int = 5) -> bool:
        """Test concurrent requests to validate hanging fix."""
        logger.info(f"🧪 TESTING CONCURRENT REQUESTS ({num_requests} requests)")
        logger.info("=" * 50)
        
        try:
            # Create test payloads
            test_payloads = [
                {
                    "query": f"concurrent test query {i} for MVP async fix",
                    "user_id": f"test-user-concurrent-{i}",
                    "context": "production_concurrent_test"
                }
                for i in range(num_requests)
            ]
            
            async def make_request(payload: Dict[str, Any], request_id: int) -> Dict[str, Any]:
                """Make a single API request."""
                try:
                    start_time = time.time()
                    
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            f"{self.api_url}/api/chat",
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        response_time = time.time() - start_time
                        
                        return {
                            'request_id': request_id,
                            'success': response.status_code == 200,
                            'response_time': response_time,
                            'status_code': response.status_code,
                            'hanging': response_time > 30.0,
                            'error': None
                        }
                        
                except Exception as e:
                    return {
                        'request_id': request_id,
                        'success': False,
                        'response_time': 0.0,
                        'status_code': None,
                        'hanging': False,
                        'error': str(e)
                    }
            
            # Execute concurrent requests
            start_time = time.time()
            tasks = [make_request(payload, i) for i, payload in enumerate(test_payloads)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Analyze results
            successful_requests = 0
            hanging_requests = 0
            failed_requests = 0
            total_response_time = 0.0
            status_codes = []
            
            for result in results:
                if isinstance(result, dict):
                    if result['success']:
                        successful_requests += 1
                        total_response_time += result['response_time']
                        status_codes.append(result['status_code'])
                        if result.get('hanging', False):
                            hanging_requests += 1
                    else:
                        failed_requests += 1
                        logger.error(f"Request {result['request_id']} failed: {result.get('error', 'Unknown error')}")
                else:
                    failed_requests += 1
                    logger.error(f"Request failed with exception: {result}")
            
            avg_response_time = total_response_time / max(successful_requests, 1)
            
            logger.info(f"📊 CONCURRENT TEST RESULTS:")
            logger.info(f"   Total requests: {num_requests}")
            logger.info(f"   Successful: {successful_requests}")
            logger.info(f"   Failed: {failed_requests}")
            logger.info(f"   Hanging: {hanging_requests}")
            logger.info(f"   Average response time: {avg_response_time:.2f}s")
            logger.info(f"   Total test time: {total_time:.2f}s")
            logger.info(f"   Status codes: {set(status_codes)}")
            
            # Record metrics
            self.metrics.append(TestMetrics(
                timestamp=datetime.now(),
                test_type="concurrent_requests",
                success=hanging_requests == 0 and successful_requests == num_requests,
                response_time=avg_response_time,
                concurrent_requests=num_requests,
                hanging_detected=hanging_requests > 0,
                api_url=self.api_url
            ))
            
            # Determine success
            success = (hanging_requests == 0 and 
                     successful_requests == num_requests and 
                     avg_response_time < 10.0)
            
            if success:
                logger.info("✅ Concurrent request test PASSED")
            else:
                logger.error("❌ Concurrent request test FAILED")
                if hanging_requests > 0:
                    logger.error(f"   {hanging_requests} requests hung (>30s)")
                if successful_requests < num_requests:
                    logger.error(f"   {num_requests - successful_requests} requests failed")
                if avg_response_time >= 10.0:
                    logger.error(f"   Average response time too high: {avg_response_time:.2f}s")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Concurrent request test failed: {e}")
            self.metrics.append(TestMetrics(
                timestamp=datetime.now(),
                test_type="concurrent_requests",
                success=False,
                response_time=0.0,
                error_message=str(e),
                concurrent_requests=num_requests,
                api_url=self.api_url
            ))
            return False
    
    async def test_stress_load(self, num_requests: int = 20, duration_minutes: int = 5) -> bool:
        """Test system under stress load."""
        logger.info(f"🧪 TESTING STRESS LOAD ({num_requests} requests over {duration_minutes} minutes)")
        logger.info("=" * 60)
        
        try:
            self.test_start_time = datetime.now()
            end_time = self.test_start_time + timedelta(minutes=duration_minutes)
            
            successful_requests = 0
            failed_requests = 0
            hanging_requests = 0
            total_response_time = 0.0
            
            while datetime.now() < end_time:
                # Create batch of requests
                batch_size = min(5, num_requests - successful_requests - failed_requests)
                if batch_size <= 0:
                    break
                
                test_payloads = [
                    {
                        "query": f"stress test query {i} at {datetime.now().isoformat()}",
                        "user_id": f"stress-test-user-{i}",
                        "context": "production_stress_test"
                    }
                    for i in range(batch_size)
                ]
                
                async def make_stress_request(payload: Dict[str, Any], request_id: int) -> Dict[str, Any]:
                    """Make a stress test request."""
                    try:
                        start_time = time.time()
                        
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            response = await client.post(
                                f"{self.api_url}/api/chat",
                                json=payload,
                                headers={"Content-Type": "application/json"}
                            )
                            
                            response_time = time.time() - start_time
                            
                            return {
                                'request_id': request_id,
                                'success': response.status_code == 200,
                                'response_time': response_time,
                                'status_code': response.status_code,
                                'hanging': response_time > 30.0
                            }
                            
                    except Exception as e:
                        return {
                            'request_id': request_id,
                            'success': False,
                            'response_time': 0.0,
                            'status_code': None,
                            'hanging': False,
                            'error': str(e)
                        }
                
                # Execute batch
                tasks = [make_stress_request(payload, i) for i, payload in enumerate(test_payloads)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in results:
                    if isinstance(result, dict):
                        if result['success']:
                            successful_requests += 1
                            total_response_time += result['response_time']
                            if result.get('hanging', False):
                                hanging_requests += 1
                        else:
                            failed_requests += 1
                
                # Log progress
                elapsed = datetime.now() - self.test_start_time
                logger.info(f"   Progress: {successful_requests + failed_requests}/{num_requests} requests, "
                           f"{elapsed.total_seconds():.0f}s elapsed")
                
                # Wait before next batch
                await asyncio.sleep(2)
            
            avg_response_time = total_response_time / max(successful_requests, 1)
            
            logger.info(f"📊 STRESS TEST RESULTS:")
            logger.info(f"   Total requests: {successful_requests + failed_requests}")
            logger.info(f"   Successful: {successful_requests}")
            logger.info(f"   Failed: {failed_requests}")
            logger.info(f"   Hanging: {hanging_requests}")
            logger.info(f"   Average response time: {avg_response_time:.2f}s")
            logger.info(f"   Test duration: {(datetime.now() - self.test_start_time).total_seconds():.0f}s")
            
            # Record metrics
            self.metrics.append(TestMetrics(
                timestamp=datetime.now(),
                test_type="stress_load",
                success=hanging_requests == 0 and successful_requests > 0,
                response_time=avg_response_time,
                concurrent_requests=successful_requests + failed_requests,
                hanging_detected=hanging_requests > 0,
                api_url=self.api_url
            ))
            
            # Determine success
            success = (hanging_requests == 0 and 
                     successful_requests > 0 and 
                     avg_response_time < 15.0)
            
            if success:
                logger.info("✅ Stress load test PASSED")
            else:
                logger.error("❌ Stress load test FAILED")
                if hanging_requests > 0:
                    logger.error(f"   {hanging_requests} requests hung (>30s)")
                if successful_requests == 0:
                    logger.error("   No successful requests")
                if avg_response_time >= 15.0:
                    logger.error(f"   Average response time too high: {avg_response_time:.2f}s")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Stress load test failed: {e}")
            self.metrics.append(TestMetrics(
                timestamp=datetime.now(),
                test_type="stress_load",
                success=False,
                response_time=0.0,
                error_message=str(e),
                concurrent_requests=num_requests,
                api_url=self.api_url
            ))
            return False
    
    async def monitor_production(self, duration_hours: int = 24) -> None:
        """Monitor production API for hanging issues."""
        logger.info(f"📊 MONITORING PRODUCTION API FOR {duration_hours} HOURS")
        logger.info("=" * 60)
        
        end_time = datetime.now() + timedelta(hours=duration_hours)
        check_count = 0
        
        logger.info(f"Monitoring started at: {datetime.now().isoformat()}")
        logger.info(f"Monitoring will end at: {end_time.isoformat()}")
        
        try:
            while datetime.now() < end_time:
                check_count += 1
                logger.info(f"🔍 Monitoring check #{check_count}")
                
                # Test API responsiveness
                success = await self.test_single_request()
                
                if success:
                    logger.info(f"✅ Check #{check_count}: API responsive")
                else:
                    logger.warning(f"⚠️  Check #{check_count}: API issues detected")
                
                # Log system resources
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                logger.info(f"   System resources - CPU: {cpu_percent}%, Memory: {memory_percent}%")
                
                # Wait 5 minutes before next check
                await asyncio.sleep(300)  # 5 minutes
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        finally:
            logger.info(f"📊 MONITORING COMPLETED ({check_count} checks performed)")
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate test report."""
        if not self.metrics:
            return {"error": "No metrics available"}
        
        # Calculate statistics
        total_tests = len(self.metrics)
        successful_tests = sum(1 for m in self.metrics if m.success)
        hanging_tests = sum(1 for m in self.metrics if m.hanging_detected)
        
        response_times = [m.response_time for m in self.metrics if m.response_time > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Group by test type
        test_type_stats = {}
        for metric in self.metrics:
            test_type = metric.test_type
            if test_type not in test_type_stats:
                test_type_stats[test_type] = {
                    'total': 0,
                    'successful': 0,
                    'hanging': 0,
                    'avg_response_time': 0
                }
            
            test_type_stats[test_type]['total'] += 1
            if metric.success:
                test_type_stats[test_type]['successful'] += 1
            if metric.hanging_detected:
                test_type_stats[test_type]['hanging'] += 1
        
        # Calculate average response times per test type
        for test_type in test_type_stats:
            type_times = [m.response_time for m in self.metrics 
                         if m.test_type == test_type and m.response_time > 0]
            test_type_stats[test_type]['avg_response_time'] = sum(type_times) / len(type_times) if type_times else 0
        
        report = {
            'test_summary': {
                'api_url': self.api_url,
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': successful_tests / total_tests if total_tests > 0 else 0,
                'hanging_tests': hanging_tests,
                'hanging_rate': hanging_tests / total_tests if total_tests > 0 else 0,
                'average_response_time': avg_response_time
            },
            'test_type_statistics': test_type_stats,
            'metrics': [metric.to_dict() for metric in self.metrics],
            'test_start_time': self.test_start_time.isoformat() if self.test_start_time else None,
            'report_generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def save_report(self, filename: Optional[str] = None) -> str:
        """Save test report to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mvp_production_test_report_{timestamp}.json"
        
        report = self.generate_test_report()
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        filepath = os.path.join('logs', filename)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Test report saved to: {filepath}")
        return filepath

async def main():
    """Main testing function."""
    parser = argparse.ArgumentParser(description='MVP Async Fix Production API Testing')
    parser.add_argument('--api-url', required=True, help='Production API URL')
    parser.add_argument('--test-single', action='store_true', help='Test single request')
    parser.add_argument('--test-concurrent', action='store_true', help='Test concurrent requests')
    parser.add_argument('--test-stress', action='store_true', help='Test stress load')
    parser.add_argument('--monitor', action='store_true', help='Monitor production')
    parser.add_argument('--requests', type=int, default=5, help='Number of concurrent requests')
    parser.add_argument('--stress-requests', type=int, default=20, help='Number of stress test requests')
    parser.add_argument('--stress-duration', type=int, default=5, help='Stress test duration in minutes')
    parser.add_argument('--monitor-hours', type=int, default=24, help='Hours to monitor')
    
    args = parser.parse_args()
    
    if not any([args.test_single, args.test_concurrent, args.test_stress, args.monitor]):
        parser.print_help()
        return
    
    # Initialize tester
    tester = ProductionAPITester(args.api_url)
    
    try:
        logger.info(f"🚀 STARTING MVP ASYNC FIX PRODUCTION TESTING")
        logger.info(f"API URL: {args.api_url}")
        logger.info("=" * 60)
        
        if args.test_single:
            logger.info("🧪 RUNNING SINGLE REQUEST TEST")
            success = await tester.test_single_request()
            if success:
                logger.info("✅ Single request test PASSED")
            else:
                logger.error("❌ Single request test FAILED")
        
        if args.test_concurrent:
            logger.info("🧪 RUNNING CONCURRENT REQUEST TEST")
            success = await tester.test_concurrent_requests(args.requests)
            if success:
                logger.info("✅ Concurrent request test PASSED")
            else:
                logger.error("❌ Concurrent request test FAILED")
        
        if args.test_stress:
            logger.info("🧪 RUNNING STRESS LOAD TEST")
            success = await tester.test_stress_load(args.stress_requests, args.stress_duration)
            if success:
                logger.info("✅ Stress load test PASSED")
            else:
                logger.error("❌ Stress load test FAILED")
        
        if args.monitor:
            logger.info("📊 STARTING PRODUCTION MONITORING")
            await tester.monitor_production(args.monitor_hours)
        
        # Generate and save report
        report_file = tester.save_report()
        logger.info(f"📊 Test report: {report_file}")
        
    except KeyboardInterrupt:
        logger.info("Testing interrupted by user")
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always generate final report
        if tester.metrics:
            report_file = tester.save_report()
            logger.info(f"📄 Final report saved: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())
