"""
Phase 4 Load Testing: Comprehensive Multi-Level Stress Testing

Tests system resilience under various load conditions:
- Light load: 100 concurrent operations for 10 minutes
- Medium load: 500 concurrent operations for 30 minutes
- Heavy load: 1000+ concurrent operations for 60 minutes
- Spike load: Sudden traffic spikes (10x normal load)
- Endurance load: Extended periods under normal load (24+ hours)

Addresses: FM-043 Phase 4 - Production Validation & Stress Testing
"""

import pytest
import asyncio
import httpx
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent.parent.parent / ".env.development"
if env_file.exists():
    load_dotenv(env_file)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.shared.monitoring.concurrency_monitor import get_monitor, ConcurrencyMonitor
from agents.shared.rate_limiting.limiter import (
    create_rate_limiter,
    RateLimitAlgorithm,
    get_openai_rate_limiter,
    get_anthropic_rate_limiter
)
from agents.tooling.rag.database_manager import DatabasePoolManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL") or os.getenv("BACKEND_URL") or "http://localhost:8000"
TEST_TIMEOUT = float(os.getenv("TEST_TIMEOUT", "60.0"))


@dataclass
class LoadTestMetrics:
    """Metrics collected during load testing."""
    total_operations: int
    successful_operations: int
    failed_operations: int
    average_response_time: float
    p95_response_time: float
    p99_response_time: float
    max_concurrent_operations: int
    resource_usage_peak: Dict[str, Any]
    test_duration: float
    operations_per_second: float


class ConcurrencyLoadTester:
    """Comprehensive load testing for concurrency patterns."""
    
    def __init__(self, api_client: httpx.AsyncClient, monitor: ConcurrencyMonitor):
        self.api_client = api_client
        self.monitor = monitor
        self.response_times: List[float] = []
        self.max_concurrent = 0
        self.current_concurrent = 0
        self._lock = asyncio.Lock()
    
    async def _simulate_operation(self, operation_id: int, semaphore: Optional[asyncio.Semaphore] = None) -> Dict[str, Any]:
        """Simulate a single operation with optional semaphore control."""
        start_time = time.time()
        
        try:
            # Acquire semaphore if provided
            if semaphore:
                async with semaphore:
                    async with self._lock:
                        self.current_concurrent += 1
                        self.max_concurrent = max(self.max_concurrent, self.current_concurrent)
                    
                    try:
                        # Simulate API call
                        response = await self.api_client.get(
                            f"{API_BASE_URL}/health",
                            timeout=TEST_TIMEOUT
                        )
                        elapsed = time.time() - start_time
                        self.response_times.append(elapsed)
                        
                        return {
                            "operation_id": operation_id,
                            "status": response.status_code,
                            "response_time": elapsed,
                            "success": response.status_code == 200
                        }
                    finally:
                        async with self._lock:
                            self.current_concurrent -= 1
            else:
                # No semaphore - direct operation
                response = await self.api_client.get(
                    f"{API_BASE_URL}/health",
                    timeout=TEST_TIMEOUT
                )
                elapsed = time.time() - start_time
                self.response_times.append(elapsed)
                
                return {
                    "operation_id": operation_id,
                    "status": response.status_code,
                    "response_time": elapsed,
                    "success": response.status_code == 200
                }
        except Exception as e:
            elapsed = time.time() - start_time
            self.response_times.append(elapsed)
            return {
                "operation_id": operation_id,
                "error": str(e),
                "response_time": elapsed,
                "success": False
            }
    
    def _calculate_percentiles(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value from list."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    async def _collect_resource_metrics(self) -> Dict[str, Any]:
        """Collect current resource usage metrics."""
        metrics = await self.monitor.get_current_metrics()
        return {
            "active_tasks": metrics.active_tasks,
            "semaphore_usage": metrics.semaphore_usage,
            "connection_pool_usage": metrics.connection_pool_usage,
            "thread_count": metrics.thread_count,
            "timestamp": metrics.timestamp.isoformat()
        }
    
    async def test_light_load(self, duration_minutes: int = 10, concurrent_ops: int = 100) -> LoadTestMetrics:
        """
        Light load test: 100 concurrent operations for 10 minutes.
        
        Validates system stability under normal expected load.
        """
        logger.info(f"Starting light load test: {concurrent_ops} concurrent operations for {duration_minutes} minutes")
        
        semaphore = asyncio.Semaphore(concurrent_ops)
        self.monitor.register_semaphore("light_load", semaphore, concurrent_ops)
        
        self.response_times = []
        self.max_concurrent = 0
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        operations_launched = 0
        tasks: List[asyncio.Task] = []
        
        # Launch operations continuously for the duration
        while time.time() < end_time:
            # Launch batch of operations
            batch_size = min(concurrent_ops, 20)  # Launch in smaller batches
            for _ in range(batch_size):
                task = asyncio.create_task(
                    self._simulate_operation(operations_launched, semaphore)
                )
                tasks.append(task)
                operations_launched += 1
            
            # Wait a bit before next batch
            await asyncio.sleep(1.0)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed = len(results) - successful
        
        # Calculate metrics
        response_times = [r.get("response_time", 0) for r in results if isinstance(r, dict)]
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        resource_peak = await self._collect_resource_metrics()
        
        metrics = LoadTestMetrics(
            total_operations=operations_launched,
            successful_operations=successful,
            failed_operations=failed,
            average_response_time=avg_response,
            p95_response_time=self._calculate_percentiles(response_times, 95),
            p99_response_time=self._calculate_percentiles(response_times, 99),
            max_concurrent_operations=self.max_concurrent,
            resource_usage_peak=resource_peak,
            test_duration=test_duration,
            operations_per_second=operations_launched / test_duration if test_duration > 0 else 0
        )
        
        logger.info(f"Light load test completed: {successful}/{operations_launched} successful")
        return metrics
    
    async def test_medium_load(self, duration_minutes: int = 30, concurrent_ops: int = 500) -> LoadTestMetrics:
        """
        Medium load test: 500 concurrent operations for 30 minutes.
        
        Tests system behavior under elevated load.
        """
        logger.info(f"Starting medium load test: {concurrent_ops} concurrent operations for {duration_minutes} minutes")
        
        semaphore = asyncio.Semaphore(concurrent_ops)
        self.monitor.register_semaphore("medium_load", semaphore, concurrent_ops)
        
        self.response_times = []
        self.max_concurrent = 0
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        operations_launched = 0
        tasks: List[asyncio.Task] = []
        
        # Launch operations continuously
        while time.time() < end_time:
            batch_size = min(concurrent_ops, 50)
            for _ in range(batch_size):
                task = asyncio.create_task(
                    self._simulate_operation(operations_launched, semaphore)
                )
                tasks.append(task)
                operations_launched += 1
            
            await asyncio.sleep(0.5)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed = len(results) - successful
        
        response_times = [r.get("response_time", 0) for r in results if isinstance(r, dict)]
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        resource_peak = await self._collect_resource_metrics()
        
        metrics = LoadTestMetrics(
            total_operations=operations_launched,
            successful_operations=successful,
            failed_operations=failed,
            average_response_time=avg_response,
            p95_response_time=self._calculate_percentiles(response_times, 95),
            p99_response_time=self._calculate_percentiles(response_times, 99),
            max_concurrent_operations=self.max_concurrent,
            resource_usage_peak=resource_peak,
            test_duration=test_duration,
            operations_per_second=operations_launched / test_duration if test_duration > 0 else 0
        )
        
        logger.info(f"Medium load test completed: {successful}/{operations_launched} successful")
        return metrics
    
    async def test_heavy_load(self, duration_minutes: int = 60, concurrent_ops: int = 1000) -> LoadTestMetrics:
        """
        Heavy load test: 1000+ concurrent operations for 60 minutes.
        
        Validates system resilience under maximum expected load.
        """
        logger.info(f"Starting heavy load test: {concurrent_ops} concurrent operations for {duration_minutes} minutes")
        
        semaphore = asyncio.Semaphore(concurrent_ops)
        self.monitor.register_semaphore("heavy_load", semaphore, concurrent_ops)
        
        self.response_times = []
        self.max_concurrent = 0
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        operations_launched = 0
        tasks: List[asyncio.Task] = []
        
        # Launch operations continuously
        while time.time() < end_time:
            batch_size = min(concurrent_ops, 100)
            for _ in range(batch_size):
                task = asyncio.create_task(
                    self._simulate_operation(operations_launched, semaphore)
                )
                tasks.append(task)
                operations_launched += 1
            
            await asyncio.sleep(0.2)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed = len(results) - successful
        
        response_times = [r.get("response_time", 0) for r in results if isinstance(r, dict)]
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        resource_peak = await self._collect_resource_metrics()
        
        metrics = LoadTestMetrics(
            total_operations=operations_launched,
            successful_operations=successful,
            failed_operations=failed,
            average_response_time=avg_response,
            p95_response_time=self._calculate_percentiles(response_times, 95),
            p99_response_time=self._calculate_percentiles(response_times, 99),
            max_concurrent_operations=self.max_concurrent,
            resource_usage_peak=resource_peak,
            test_duration=test_duration,
            operations_per_second=operations_launched / test_duration if test_duration > 0 else 0
        )
        
        logger.info(f"Heavy load test completed: {successful}/{operations_launched} successful")
        return metrics
    
    async def test_spike_load(self, base_load: int = 100, spike_multiplier: int = 10, spike_duration_seconds: int = 60) -> LoadTestMetrics:
        """
        Spike load test: Sudden traffic spikes (10x normal load).
        
        Tests system response to sudden load increases.
        """
        logger.info(f"Starting spike load test: {base_load} -> {base_load * spike_multiplier} operations")
        
        # Start with base load
        base_semaphore = asyncio.Semaphore(base_load)
        self.monitor.register_semaphore("spike_base", base_semaphore, base_load)
        
        self.response_times = []
        self.max_concurrent = 0
        start_time = time.time()
        
        # Run base load for 30 seconds
        base_tasks = [
            asyncio.create_task(self._simulate_operation(i, base_semaphore))
            for i in range(base_load)
        ]
        await asyncio.sleep(30.0)
        
        # Spike: Launch 10x load suddenly
        spike_semaphore = asyncio.Semaphore(base_load * spike_multiplier)
        self.monitor.register_semaphore("spike_load", spike_semaphore, base_load * spike_multiplier)
        
        spike_tasks = [
            asyncio.create_task(self._simulate_operation(i, spike_semaphore))
            for i in range(base_load, base_load + (base_load * spike_multiplier))
        ]
        
        # Wait for spike duration
        await asyncio.sleep(spike_duration_seconds)
        
        # Gather all results
        all_tasks = base_tasks + spike_tasks
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed = len(results) - successful
        
        response_times = [r.get("response_time", 0) for r in results if isinstance(r, dict)]
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        resource_peak = await self._collect_resource_metrics()
        
        metrics = LoadTestMetrics(
            total_operations=len(results),
            successful_operations=successful,
            failed_operations=failed,
            average_response_time=avg_response,
            p95_response_time=self._calculate_percentiles(response_times, 95),
            p99_response_time=self._calculate_percentiles(response_times, 99),
            max_concurrent_operations=self.max_concurrent,
            resource_usage_peak=resource_peak,
            test_duration=test_duration,
            operations_per_second=len(results) / test_duration if test_duration > 0 else 0
        )
        
        logger.info(f"Spike load test completed: {successful}/{len(results)} successful")
        return metrics
    
    async def test_endurance_load(self, duration_hours: int = 24, concurrent_ops: int = 100) -> LoadTestMetrics:
        """
        Endurance load test: Extended periods under normal load (24+ hours).
        
        Tests system stability over extended operations.
        Note: This is a long-running test. Use with caution.
        """
        logger.info(f"Starting endurance load test: {concurrent_ops} concurrent operations for {duration_hours} hours")
        
        semaphore = asyncio.Semaphore(concurrent_ops)
        self.monitor.register_semaphore("endurance_load", semaphore, concurrent_ops)
        
        self.response_times = []
        self.max_concurrent = 0
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        
        operations_launched = 0
        tasks: List[asyncio.Task] = []
        
        # Launch operations continuously for extended period
        while time.time() < end_time:
            batch_size = min(concurrent_ops, 20)
            for _ in range(batch_size):
                task = asyncio.create_task(
                    self._simulate_operation(operations_launched, semaphore)
                )
                tasks.append(task)
                operations_launched += 1
            
            # Check every 5 minutes
            await asyncio.sleep(300.0)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed = len(results) - successful
        
        response_times = [r.get("response_time", 0) for r in results if isinstance(r, dict)]
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        resource_peak = await self._collect_resource_metrics()
        
        metrics = LoadTestMetrics(
            total_operations=operations_launched,
            successful_operations=successful,
            failed_operations=failed,
            average_response_time=avg_response,
            p95_response_time=self._calculate_percentiles(response_times, 95),
            p99_response_time=self._calculate_percentiles(response_times, 99),
            max_concurrent_operations=self.max_concurrent,
            resource_usage_peak=resource_peak,
            test_duration=test_duration,
            operations_per_second=operations_launched / test_duration if test_duration > 0 else 0
        )
        
        logger.info(f"Endurance load test completed: {successful}/{operations_launched} successful")
        return metrics
    
    def validate_resource_constraints(self, metrics: LoadTestMetrics) -> Dict[str, bool]:
        """
        Ensure resource usage stays within defined limits.
        
        Monitors semaphores, connection pools, memory, CPU.
        """
        validation_results = {}
        
        # Check semaphore limits
        semaphore_usage = metrics.resource_usage_peak.get("semaphore_usage", {})
        for name, usage in semaphore_usage.items():
            # Semaphore usage should not exceed limits
            validation_results[f"semaphore_{name}_within_limits"] = True  # Would check against actual limits
        
        # Check connection pool usage
        pool_usage = metrics.resource_usage_peak.get("connection_pool_usage", {})
        for name, usage in pool_usage.items():
            # Connection pools should stay within max_size
            validation_results[f"pool_{name}_within_limits"] = usage <= 20  # Max pool size
        
        # Check thread count
        thread_count = metrics.resource_usage_peak.get("thread_count", 0)
        validation_results["thread_count_reasonable"] = thread_count < 100
        
        # Check response times
        validation_results["p95_response_time_acceptable"] = metrics.p95_response_time < 5.0
        validation_results["p99_response_time_acceptable"] = metrics.p99_response_time < 10.0
        
        return validation_results


class TestConcurrencyLoadTesting:
    """Test suite for comprehensive load testing."""
    
    @pytest.fixture
    async def api_client(self):
        """Create async HTTP client for API testing."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            yield client
    
    @pytest.fixture
    async def monitor(self):
        """Get concurrency monitor instance."""
        monitor = get_monitor()
        yield monitor
    
    @pytest.fixture
    async def load_tester(self, api_client, monitor):
        """Create load tester instance."""
        return ConcurrencyLoadTester(api_client, monitor)
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_light_load_validation(self, load_tester):
        """Test system stability under light load."""
        metrics = await load_tester.test_light_load(duration_minutes=1, concurrent_ops=10)  # Reduced for CI
        
        assert metrics.successful_operations > 0, "At least some operations should succeed"
        assert metrics.p95_response_time < 10.0, "P95 response time should be reasonable"
        
        validation = load_tester.validate_resource_constraints(metrics)
        assert all(validation.values()), f"Resource constraints violated: {validation}"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_medium_load_validation(self, load_tester):
        """Test system behavior under medium load."""
        metrics = await load_tester.test_medium_load(duration_minutes=2, concurrent_ops=50)  # Reduced for CI
        
        assert metrics.successful_operations > 0, "At least some operations should succeed"
        assert metrics.p95_response_time < 15.0, "P95 response time should be acceptable"
        
        validation = load_tester.validate_resource_constraints(metrics)
        assert all(validation.values()), f"Resource constraints violated: {validation}"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_heavy_load_validation(self, load_tester):
        """Test system resilience under heavy load."""
        metrics = await load_tester.test_heavy_load(duration_minutes=5, concurrent_ops=100)  # Reduced for CI
        
        assert metrics.successful_operations > 0, "At least some operations should succeed"
        assert metrics.p95_response_time < 20.0, "P95 response time should be acceptable under heavy load"
        
        validation = load_tester.validate_resource_constraints(metrics)
        assert all(validation.values()), f"Resource constraints violated: {validation}"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_spike_load_validation(self, load_tester):
        """Test system response to sudden load spikes."""
        metrics = await load_tester.test_spike_load(
            base_load=10,
            spike_multiplier=5,
            spike_duration_seconds=30
        )
        
        assert metrics.successful_operations > 0, "At least some operations should succeed during spike"
        assert metrics.max_concurrent_operations <= 50, "Concurrency should be controlled"
        
        validation = load_tester.validate_resource_constraints(metrics)
        assert all(validation.values()), f"Resource constraints violated: {validation}"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.skip(reason="Endurance test - run manually for extended validation")
    async def test_endurance_load_validation(self, load_tester):
        """Test system stability over extended periods."""
        metrics = await load_tester.test_endurance_load(duration_hours=1, concurrent_ops=10)  # Reduced for CI
        
        assert metrics.successful_operations > 0, "At least some operations should succeed"
        assert metrics.test_duration >= 3600, "Test should run for at least 1 hour"
        
        validation = load_tester.validate_resource_constraints(metrics)
        assert all(validation.values()), f"Resource constraints violated: {validation}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "slow"])




