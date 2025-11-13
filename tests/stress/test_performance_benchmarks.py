"""
Phase 4 Performance Benchmarking: Continuous Performance Monitoring

Establishes and monitors performance benchmarks:
- Response time benchmarks (P50, P95, P99)
- Throughput benchmarks (requests per second)
- Resource usage benchmarks (memory, CPU, connections)
- Scalability benchmarks (performance vs. concurrent users)
- Regression detection (>5% degradation alerts)

Addresses: FM-043 Phase 4 - Production Validation & Stress Testing
"""

import pytest
import asyncio
import httpx
import os
import sys
import time
import logging
import psutil
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent.parent.parent / ".env.development"
if env_file.exists():
    load_dotenv(env_file)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.shared.monitoring.concurrency_monitor import get_monitor, ConcurrencyMonitor
from agents.shared.rate_limiting.limiter import create_rate_limiter, RateLimitAlgorithm
from agents.tooling.rag.database_manager import DatabasePoolManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL") or os.getenv("BACKEND_URL") or "http://localhost:8000"
TEST_TIMEOUT = float(os.getenv("TEST_TIMEOUT", "60.0"))
BENCHMARK_BASELINE_FILE = Path(__file__).parent / "benchmark_baselines.json"


@dataclass
class ResponseTimeBenchmark:
    """Response time benchmark metrics."""
    p50: float
    p95: float
    p99: float
    min: float
    max: float
    mean: float
    sample_size: int


@dataclass
class ThroughputBenchmark:
    """Throughput benchmark metrics."""
    requests_per_second: float
    total_requests: int
    duration_seconds: float
    successful_requests: int
    failed_requests: int


@dataclass
class ResourceUsageBenchmark:
    """Resource usage benchmark metrics."""
    memory_mb: float
    cpu_percent: float
    active_connections: int
    thread_count: int
    active_tasks: int


@dataclass
class ScalabilityBenchmark:
    """Scalability benchmark metrics."""
    concurrent_users: int
    response_time_p95: float
    throughput_rps: float
    resource_usage: ResourceUsageBenchmark
    scalability_coefficient: float  # Performance per concurrent user


@dataclass
class PerformanceBaseline:
    """Performance baseline for regression detection."""
    response_time_p95: float
    response_time_p99: float
    throughput_rps: float
    memory_mb: float
    cpu_percent: float
    timestamp: str
    test_conditions: Dict[str, Any]


class PerformanceBenchmarkTester:
    """Continuous performance monitoring and benchmark validation."""
    
    def __init__(self, api_client: httpx.AsyncClient, monitor: ConcurrencyMonitor):
        self.api_client = api_client
        self.monitor = monitor
        self.baselines: Dict[str, PerformanceBaseline] = {}
        self._load_baselines()
    
    def _load_baselines(self):
        """Load performance baselines from file."""
        if BENCHMARK_BASELINE_FILE.exists():
            try:
                with open(BENCHMARK_BASELINE_FILE, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        self.baselines[key] = PerformanceBaseline(**value)
                logger.info(f"Loaded {len(self.baselines)} performance baselines")
            except Exception as e:
                logger.warning(f"Failed to load baselines: {e}")
    
    def _save_baselines(self):
        """Save performance baselines to file."""
        try:
            data = {
                key: asdict(baseline) for key, baseline in self.baselines.items()
            }
            with open(BENCHMARK_BASELINE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.baselines)} performance baselines")
        except Exception as e:
            logger.error(f"Failed to save baselines: {e}")
    
    def _calculate_percentiles(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value from list."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    async def test_response_time_benchmarks(
        self,
        concurrent_requests: int = 100,
        requests_per_batch: int = 10
    ) -> ResponseTimeBenchmark:
        """
        P95/P99 latency benchmarks under various loads.
        
        Establishes and validates response time baselines.
        """
        logger.info(f"Testing response time benchmarks: {concurrent_requests} requests")
        
        response_times: List[float] = []
        semaphore = asyncio.Semaphore(requests_per_batch)
        self.monitor.register_semaphore("response_time_test", semaphore, requests_per_batch)
        
        async def timed_request(request_id: int) -> Optional[float]:
            """Make a timed request."""
            async with semaphore:
                start_time = time.time()
                try:
                    response = await self.api_client.get(
                        f"{API_BASE_URL}/health",
                        timeout=TEST_TIMEOUT
                    )
                    elapsed = time.time() - start_time
                    if response.status_code == 200:
                        return elapsed
                except Exception as e:
                    logger.debug(f"Request {request_id} failed: {e}")
                return None
        
        # Execute requests
        tasks = [timed_request(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect response times
        response_times = [r for r in results if isinstance(r, float) and r is not None]
        
        if not response_times:
            logger.warning("No successful requests for response time benchmark")
            return ResponseTimeBenchmark(
                p50=0, p95=0, p99=0, min=0, max=0, mean=0, sample_size=0
            )
        
        benchmark = ResponseTimeBenchmark(
            p50=self._calculate_percentiles(response_times, 50),
            p95=self._calculate_percentiles(response_times, 95),
            p99=self._calculate_percentiles(response_times, 99),
            min=min(response_times),
            max=max(response_times),
            mean=sum(response_times) / len(response_times),
            sample_size=len(response_times)
        )
        
        logger.info(
            f"Response time benchmark: P50={benchmark.p50:.3f}s, "
            f"P95={benchmark.p95:.3f}s, P99={benchmark.p99:.3f}s"
        )
        
        return benchmark
    
    async def test_throughput_benchmarks(
        self,
        duration_seconds: int = 60,
        concurrent_ops: int = 50
    ) -> ThroughputBenchmark:
        """
        Requests per second capability testing.
        
        Measures maximum sustainable throughput.
        """
        logger.info(f"Testing throughput benchmarks: {duration_seconds}s, {concurrent_ops} concurrent")
        
        semaphore = asyncio.Semaphore(concurrent_ops)
        self.monitor.register_semaphore("throughput_test", semaphore, concurrent_ops)
        
        successful = 0
        failed = 0
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        async def throughput_request():
            """Make a request for throughput testing."""
            async with semaphore:
                try:
                    response = await self.api_client.get(
                        f"{API_BASE_URL}/health",
                        timeout=TEST_TIMEOUT
                    )
                    if response.status_code == 200:
                        return True
                except Exception:
                    pass
                return False
        
        # Launch requests continuously
        tasks: List[asyncio.Task] = []
        request_count = 0
        
        while time.time() < end_time:
            # Launch batch
            batch = [asyncio.create_task(throughput_request()) for _ in range(concurrent_ops)]
            tasks.extend(batch)
            request_count += concurrent_ops
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        # Wait for remaining tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count results
        for result in results:
            if result is True:
                successful += 1
            else:
                failed += 1
        
        actual_duration = time.time() - start_time
        throughput = successful / actual_duration if actual_duration > 0 else 0
        
        benchmark = ThroughputBenchmark(
            requests_per_second=throughput,
            total_requests=request_count,
            duration_seconds=actual_duration,
            successful_requests=successful,
            failed_requests=failed
        )
        
        logger.info(
            f"Throughput benchmark: {benchmark.requests_per_second:.2f} req/s "
            f"({benchmark.successful_requests}/{benchmark.total_requests} successful)"
        )
        
        return benchmark
    
    async def test_resource_usage_benchmarks(self) -> ResourceUsageBenchmark:
        """
        Memory, CPU, connection usage pattern analysis.
        
        Monitors resource consumption under different load patterns.
        """
        logger.info("Testing resource usage benchmarks")
        
        process = psutil.Process()
        
        # Collect metrics
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        cpu_percent = process.cpu_percent(interval=1.0)
        
        # Get concurrency metrics
        metrics = await self.monitor.get_current_metrics()
        active_connections = sum(metrics.connection_pool_usage.values())
        thread_count = metrics.thread_count
        active_tasks = metrics.active_tasks
        
        benchmark = ResourceUsageBenchmark(
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            active_connections=active_connections,
            thread_count=thread_count,
            active_tasks=active_tasks
        )
        
        logger.info(
            f"Resource usage: {benchmark.memory_mb:.1f}MB memory, "
            f"{benchmark.cpu_percent:.1f}% CPU, {benchmark.active_connections} connections"
        )
        
        return benchmark
    
    async def test_scalability_benchmarks(
        self,
        concurrent_users_list: List[int] = [10, 50, 100, 200]
    ) -> List[ScalabilityBenchmark]:
        """
        Performance vs. concurrent user scaling analysis.
        
        Validates how performance scales with concurrent users.
        """
        logger.info(f"Testing scalability benchmarks: {concurrent_users_list} concurrent users")
        
        scalability_results: List[ScalabilityBenchmark] = []
        
        for concurrent_users in concurrent_users_list:
            logger.info(f"Testing with {concurrent_users} concurrent users")
            
            # Run response time test
            response_benchmark = await self.test_response_time_benchmarks(
                concurrent_requests=concurrent_users,
                requests_per_batch=min(concurrent_users, 20)
            )
            
            # Run throughput test
            throughput_benchmark = await self.test_throughput_benchmarks(
                duration_seconds=30,
                concurrent_ops=concurrent_users
            )
            
            # Get resource usage
            resource_benchmark = await self.test_resource_usage_benchmarks()
            
            # Calculate scalability coefficient
            # Higher is better: more throughput per user
            scalability_coefficient = (
                throughput_benchmark.requests_per_second / concurrent_users
                if concurrent_users > 0 else 0
            )
            
            benchmark = ScalabilityBenchmark(
                concurrent_users=concurrent_users,
                response_time_p95=response_benchmark.p95,
                throughput_rps=throughput_benchmark.requests_per_second,
                resource_usage=resource_benchmark,
                scalability_coefficient=scalability_coefficient
            )
            
            scalability_results.append(benchmark)
            
            logger.info(
                f"Scalability at {concurrent_users} users: "
                f"{benchmark.throughput_rps:.2f} req/s, "
                f"P95={benchmark.response_time_p95:.3f}s, "
                f"coefficient={benchmark.scalability_coefficient:.3f}"
            )
        
        return scalability_results
    
    def detect_performance_regression(
        self,
        current_metrics: Dict[str, float],
        baseline_name: str = "default"
    ) -> Dict[str, Any]:
        """
        Automated detection of performance degradation >5%.
        
        Alerts on any performance regression exceeding threshold.
        """
        if baseline_name not in self.baselines:
            logger.warning(f"Baseline '{baseline_name}' not found, creating new baseline")
            return {"status": "no_baseline", "regressions": []}
        
        baseline = self.baselines[baseline_name]
        regressions = []
        threshold = 0.05  # 5% threshold
        
        # Check response time P95
        if "response_time_p95" in current_metrics:
            current = current_metrics["response_time_p95"]
            baseline_value = baseline.response_time_p95
            if baseline_value > 0:
                degradation = (current - baseline_value) / baseline_value
                if degradation > threshold:
                    regressions.append({
                        "metric": "response_time_p95",
                        "current": current,
                        "baseline": baseline_value,
                        "degradation": degradation * 100,
                        "threshold": threshold * 100
                    })
        
        # Check response time P99
        if "response_time_p99" in current_metrics:
            current = current_metrics["response_time_p99"]
            baseline_value = baseline.response_time_p99
            if baseline_value > 0:
                degradation = (current - baseline_value) / baseline_value
                if degradation > threshold:
                    regressions.append({
                        "metric": "response_time_p99",
                        "current": current,
                        "baseline": baseline_value,
                        "degradation": degradation * 100,
                        "threshold": threshold * 100
                    })
        
        # Check throughput
        if "throughput_rps" in current_metrics:
            current = current_metrics["throughput_rps"]
            baseline_value = baseline.throughput_rps
            if baseline_value > 0:
                degradation = (baseline_value - current) / baseline_value  # Inverted for throughput
                if degradation > threshold:
                    regressions.append({
                        "metric": "throughput_rps",
                        "current": current,
                        "baseline": baseline_value,
                        "degradation": degradation * 100,
                        "threshold": threshold * 100
                    })
        
        return {
            "status": "checked",
            "regressions": regressions,
            "baseline": baseline_name
        }
    
    def establish_baseline(
        self,
        response_time_p95: float,
        response_time_p99: float,
        throughput_rps: float,
        memory_mb: float,
        cpu_percent: float,
        baseline_name: str = "default",
        test_conditions: Optional[Dict[str, Any]] = None
    ):
        """Establish a new performance baseline."""
        baseline = PerformanceBaseline(
            response_time_p95=response_time_p95,
            response_time_p99=response_time_p99,
            throughput_rps=throughput_rps,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            timestamp=datetime.now().isoformat(),
            test_conditions=test_conditions or {}
        )
        
        self.baselines[baseline_name] = baseline
        self._save_baselines()
        
        logger.info(f"Established performance baseline '{baseline_name}'")
    
    def generate_performance_report(
        self,
        response_benchmark: ResponseTimeBenchmark,
        throughput_benchmark: ThroughputBenchmark,
        resource_benchmark: ResourceUsageBenchmark,
        scalability_results: List[ScalabilityBenchmark]
    ) -> Dict[str, Any]:
        """
        Comprehensive performance analysis reporting.
        
        Generates detailed performance analysis and trending.
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "response_time": {
                "p50": response_benchmark.p50,
                "p95": response_benchmark.p95,
                "p99": response_benchmark.p99,
                "mean": response_benchmark.mean,
                "min": response_benchmark.min,
                "max": response_benchmark.max,
                "sample_size": response_benchmark.sample_size
            },
            "throughput": {
                "requests_per_second": throughput_benchmark.requests_per_second,
                "total_requests": throughput_benchmark.total_requests,
                "successful_requests": throughput_benchmark.successful_requests,
                "failed_requests": throughput_benchmark.failed_requests,
                "duration_seconds": throughput_benchmark.duration_seconds
            },
            "resource_usage": {
                "memory_mb": resource_benchmark.memory_mb,
                "cpu_percent": resource_benchmark.cpu_percent,
                "active_connections": resource_benchmark.active_connections,
                "thread_count": resource_benchmark.thread_count,
                "active_tasks": resource_benchmark.active_tasks
            },
            "scalability": [
                {
                    "concurrent_users": b.concurrent_users,
                    "response_time_p95": b.response_time_p95,
                    "throughput_rps": b.throughput_rps,
                    "scalability_coefficient": b.scalability_coefficient
                }
                for b in scalability_results
            ]
        }
        
        return report


class TestPerformanceBenchmarks:
    """Test suite for performance benchmarking."""
    
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
    async def benchmark_tester(self, api_client, monitor):
        """Create performance benchmark tester instance."""
        return PerformanceBenchmarkTester(api_client, monitor)
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_response_time_benchmarks(self, benchmark_tester):
        """Test P95/P99 latency benchmarks."""
        benchmark = await benchmark_tester.test_response_time_benchmarks(
            concurrent_requests=50,
            requests_per_batch=10
        )
        
        assert benchmark.sample_size > 0, "Should have successful requests"
        assert benchmark.p95 > 0, "P95 should be measurable"
        assert benchmark.p99 >= benchmark.p95, "P99 should be >= P95"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_throughput_benchmarks(self, benchmark_tester):
        """Test requests per second capability."""
        benchmark = await benchmark_tester.test_throughput_benchmarks(
            duration_seconds=30,
            concurrent_ops=20
        )
        
        assert benchmark.requests_per_second > 0, "Should have measurable throughput"
        assert benchmark.successful_requests > 0, "Should have successful requests"
    
    @pytest.mark.asyncio
    async def test_resource_usage_benchmarks(self, benchmark_tester):
        """Test memory, CPU, connection usage patterns."""
        benchmark = await benchmark_tester.test_resource_usage_benchmarks()
        
        assert benchmark.memory_mb > 0, "Should have memory usage"
        assert benchmark.cpu_percent >= 0, "CPU usage should be non-negative"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_scalability_benchmarks(self, benchmark_tester):
        """Test performance vs. concurrent user scaling."""
        results = await benchmark_tester.test_scalability_benchmarks(
            concurrent_users_list=[10, 20]  # Reduced for CI
        )
        
        assert len(results) > 0, "Should have scalability results"
        for result in results:
            assert result.concurrent_users > 0, "Should have concurrent users"
            assert result.throughput_rps >= 0, "Throughput should be non-negative"
    
    @pytest.mark.asyncio
    async def test_performance_regression_detection(self, benchmark_tester):
        """Test automated performance regression detection."""
        # Establish baseline
        benchmark_tester.establish_baseline(
            response_time_p95=1.0,
            response_time_p99=2.0,
            throughput_rps=10.0,
            memory_mb=100.0,
            cpu_percent=50.0,
            baseline_name="test_baseline"
        )
        
        # Test with regression (slower response time)
        regression_result = benchmark_tester.detect_performance_regression(
            {
                "response_time_p95": 1.1,  # 10% degradation
                "response_time_p99": 2.2,  # 10% degradation
                "throughput_rps": 9.0  # 10% degradation
            },
            baseline_name="test_baseline"
        )
        
        assert regression_result["status"] == "checked", "Should check for regressions"
        assert len(regression_result["regressions"]) > 0, "Should detect regressions"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_performance_report_generation(self, benchmark_tester):
        """Test comprehensive performance report generation."""
        response_benchmark = await benchmark_tester.test_response_time_benchmarks(
            concurrent_requests=20,
            requests_per_batch=5
        )
        throughput_benchmark = await benchmark_tester.test_throughput_benchmarks(
            duration_seconds=10,
            concurrent_ops=10
        )
        resource_benchmark = await benchmark_tester.test_resource_usage_benchmarks()
        scalability_results = await benchmark_tester.test_scalability_benchmarks(
            concurrent_users_list=[10]
        )
        
        report = benchmark_tester.generate_performance_report(
            response_benchmark,
            throughput_benchmark,
            resource_benchmark,
            scalability_results
        )
        
        assert "timestamp" in report, "Report should have timestamp"
        assert "response_time" in report, "Report should have response time metrics"
        assert "throughput" in report, "Report should have throughput metrics"
        assert "resource_usage" in report, "Report should have resource usage metrics"
        assert "scalability" in report, "Report should have scalability metrics"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "slow"])

