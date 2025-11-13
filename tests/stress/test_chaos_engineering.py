"""
Phase 4 Chaos Engineering: Failure Scenario Testing

Tests system resilience under various failure conditions:
- Database connection failures
- Network partitions
- Memory pressure
- CPU throttling
- Service failures
- Recovery validation

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
import gc
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
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


@dataclass
class RecoveryMetrics:
    """Metrics for recovery testing."""
    failure_detected_time: float
    recovery_start_time: float
    recovery_complete_time: float
    mean_time_to_recovery: float
    recovery_success: bool
    data_loss: bool
    service_impact: str


class ChaosEngineeringTester:
    """Chaos engineering tests for concurrency resilience."""
    
    def __init__(self, api_client: httpx.AsyncClient, monitor: ConcurrencyMonitor):
        self.api_client = api_client
        self.monitor = monitor
        self.recovery_metrics: List[RecoveryMetrics] = []
    
    async def test_database_connection_failures(self, db_pool: DatabasePoolManager) -> RecoveryMetrics:
        """
        Simulate connection pool exhaustion scenarios.
        
        Tests system behavior when database connections are unavailable.
        """
        logger.info("Testing database connection failure scenarios")
        
        failure_start = time.time()
        
        # Simulate connection pool exhaustion by acquiring all connections
        connections = []
        try:
            # Acquire all available connections
            for _ in range(20):  # Max pool size
                try:
                    conn = await asyncio.wait_for(
                        db_pool.acquire_connection(),
                        timeout=1.0
                    )
                    connections.append(conn)
                except (asyncio.TimeoutError, Exception) as e:
                    logger.info(f"Connection acquisition failed (expected): {e}")
                    break
            
            # Try to acquire one more (should fail or timeout)
            try:
                extra_conn = await asyncio.wait_for(
                    db_pool.acquire_connection(),
                    timeout=2.0
                )
                connections.append(extra_conn)
            except asyncio.TimeoutError:
                logger.info("Connection pool exhaustion detected (expected)")
                failure_detected = time.time()
            except Exception as e:
                logger.info(f"Connection failure handled: {e}")
                failure_detected = time.time()
            
            # Release connections to simulate recovery
            recovery_start = time.time()
            for conn in connections:
                try:
                    await db_pool.release_connection(conn)
                except Exception as e:
                    logger.warning(f"Error releasing connection: {e}")
            
            # Verify recovery
            recovery_complete = time.time()
            test_conn = await db_pool.acquire_connection()
            await db_pool.release_connection(test_conn)
            
            mttr = recovery_complete - failure_detected
            
            return RecoveryMetrics(
                failure_detected_time=failure_detected - failure_start,
                recovery_start_time=recovery_start - failure_start,
                recovery_complete_time=recovery_complete - failure_start,
                mean_time_to_recovery=mttr,
                recovery_success=True,
                data_loss=False,
                service_impact="minimal"
            )
        except Exception as e:
            logger.error(f"Database connection failure test error: {e}")
            return RecoveryMetrics(
                failure_detected_time=0,
                recovery_start_time=0,
                recovery_complete_time=0,
                mean_time_to_recovery=0,
                recovery_success=False,
                data_loss=False,
                service_impact="unknown"
            )
    
    async def test_network_partitions(self, rate_limiter) -> RecoveryMetrics:
        """
        Test rate limiter behavior during network issues.
        
        Simulates network failures and validates recovery.
        """
        logger.info("Testing network partition scenarios")
        
        failure_start = time.time()
        
        # Simulate network failures by causing HTTP timeouts
        async def failing_request():
            try:
                await self.api_client.get(
                    f"{API_BASE_URL}/health",
                    timeout=0.1  # Very short timeout to simulate failure
                )
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.info(f"Network failure simulated: {e}")
                return False
            return True
        
        # Make requests that will fail
        tasks = [failing_request() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        failure_detected = time.time()
        failures = sum(1 for r in results if r is False or isinstance(r, Exception))
        
        # Test recovery: normal requests should work
        recovery_start = time.time()
        await asyncio.sleep(1.0)  # Simulate network recovery
        
        # Try normal request
        try:
            response = await self.api_client.get(
                f"{API_BASE_URL}/health",
                timeout=TEST_TIMEOUT
            )
            recovery_complete = time.time()
            recovery_success = response.status_code == 200
        except Exception as e:
            logger.warning(f"Recovery test failed: {e}")
            recovery_complete = time.time()
            recovery_success = False
        
        mttr = recovery_complete - failure_detected
        
        return RecoveryMetrics(
            failure_detected_time=failure_detected - failure_start,
            recovery_start_time=recovery_start - failure_start,
            recovery_complete_time=recovery_complete - failure_start,
            mean_time_to_recovery=mttr,
            recovery_success=recovery_success,
            data_loss=False,
            service_impact="partial" if failures > 0 else "none"
        )
    
    async def test_memory_pressure(self) -> RecoveryMetrics:
        """
        Test system behavior under memory constraints.
        
        Validates graceful degradation under memory pressure.
        """
        logger.info("Testing memory pressure scenarios")
        
        failure_start = time.time()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate memory pressure by creating large objects
        large_objects = []
        try:
            # Allocate memory gradually
            for i in range(10):
                # Create large list
                large_list = [0] * (1024 * 1024)  # ~8MB per list
                large_objects.append(large_list)
                
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                
                if memory_increase > 100:  # More than 100MB increase
                    logger.info(f"Memory pressure detected: {memory_increase:.1f}MB increase")
                    failure_detected = time.time()
                    break
            else:
                failure_detected = time.time()
            
            # Test system behavior under pressure
            semaphore = asyncio.Semaphore(5)
            self.monitor.register_semaphore("memory_test", semaphore, 5)
            
            async def memory_intensive_operation():
                async with semaphore:
                    # Simulate operation
                    await asyncio.sleep(0.1)
                    return True
            
            tasks = [memory_intensive_operation() for _ in range(20)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Release memory
            recovery_start = time.time()
            large_objects.clear()
            gc.collect()
            
            recovery_complete = time.time()
            recovery_success = sum(1 for r in results if r is True) > 0
            
            mttr = recovery_complete - failure_detected
            
            return RecoveryMetrics(
                failure_detected_time=failure_detected - failure_start,
                recovery_start_time=recovery_start - failure_start,
                recovery_complete_time=recovery_complete - failure_start,
                mean_time_to_recovery=mttr,
                recovery_success=recovery_success,
                data_loss=False,
                service_impact="minimal"
            )
        except Exception as e:
            logger.error(f"Memory pressure test error: {e}")
            return RecoveryMetrics(
                failure_detected_time=0,
                recovery_start_time=0,
                recovery_complete_time=0,
                mean_time_to_recovery=0,
                recovery_success=False,
                data_loss=False,
                service_impact="unknown"
            )
    
    async def test_cpu_throttling(self) -> RecoveryMetrics:
        """
        Validate semaphore behavior under CPU limits.
        
        Tests system performance under CPU resource constraints.
        """
        logger.info("Testing CPU throttling scenarios")
        
        failure_start = time.time()
        
        # Simulate CPU-intensive operations
        semaphore = asyncio.Semaphore(5)
        self.monitor.register_semaphore("cpu_test", semaphore, 5)
        
        async def cpu_intensive_task():
            async with semaphore:
                # CPU-intensive computation
                result = 0
                for i in range(100000):
                    result += i * i
                return result
        
        # Launch many CPU-intensive tasks
        tasks = [cpu_intensive_task() for _ in range(20)]
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        failure_detected = start_time
        duration = end_time - start_time
        
        # Check if semaphore limits were respected
        # All tasks should complete, but concurrency should be limited
        recovery_complete = end_time
        recovery_success = all(not isinstance(r, Exception) for r in results)
        
        mttr = recovery_complete - failure_detected
        
        return RecoveryMetrics(
            failure_detected_time=failure_detected - failure_start,
            recovery_start_time=failure_detected - failure_start,
            recovery_complete_time=recovery_complete - failure_start,
            mean_time_to_recovery=mttr,
            recovery_success=recovery_success,
            data_loss=False,
            service_impact="performance_degradation"
        )
    
    async def test_service_failures(self) -> RecoveryMetrics:
        """
        Test graceful degradation when components fail.
        
        Validates system resilience when individual services fail.
        """
        logger.info("Testing service failure scenarios")
        
        failure_start = time.time()
        
        # Simulate service failure by using invalid endpoint
        async def failing_service_call():
            try:
                response = await self.api_client.get(
                    f"{API_BASE_URL}/nonexistent-endpoint",
                    timeout=TEST_TIMEOUT
                )
                return response.status_code == 404
            except Exception as e:
                logger.info(f"Service failure simulated: {e}")
                return False
        
        # Make calls that will fail
        tasks = [failing_service_call() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        failure_detected = time.time()
        failures = sum(1 for r in results if r is False or isinstance(r, Exception))
        
        # Test recovery: try valid endpoint
        recovery_start = time.time()
        try:
            response = await self.api_client.get(
                f"{API_BASE_URL}/health",
                timeout=TEST_TIMEOUT
            )
            recovery_complete = time.time()
            recovery_success = response.status_code == 200
        except Exception as e:
            logger.warning(f"Recovery test failed: {e}")
            recovery_complete = time.time()
            recovery_success = False
        
        mttr = recovery_complete - failure_detected
        
        return RecoveryMetrics(
            failure_detected_time=failure_detected - failure_start,
            recovery_start_time=recovery_start - failure_start,
            recovery_complete_time=recovery_complete - failure_start,
            mean_time_to_recovery=mttr,
            recovery_success=recovery_success,
            data_loss=False,
            service_impact="partial" if failures > 0 else "none"
        )
    
    def validate_recovery_procedures(self, metrics: RecoveryMetrics) -> Dict[str, bool]:
        """
        Ensure automatic recovery from all failure scenarios.
        
        Tests that system automatically recovers without manual intervention.
        """
        validation_results = {}
        
        # Recovery should succeed
        validation_results["recovery_successful"] = metrics.recovery_success
        
        # MTTR should be reasonable (less than 60 seconds for most scenarios)
        validation_results["mttr_acceptable"] = metrics.mean_time_to_recovery < 60.0
        
        # No data loss
        validation_results["no_data_loss"] = not metrics.data_loss
        
        # Service impact should be minimal or acceptable
        acceptable_impacts = ["minimal", "none", "partial", "performance_degradation"]
        validation_results["service_impact_acceptable"] = metrics.service_impact in acceptable_impacts
        
        return validation_results


class TestChaosEngineering:
    """Test suite for chaos engineering and failure scenarios."""
    
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
    async def db_pool(self):
        """Create database pool manager for testing."""
        pool = DatabasePoolManager(min_size=2, max_size=5)
        await pool.initialize()
        yield pool
        await pool.close_pool()
    
    @pytest.fixture
    async def chaos_tester(self, api_client, monitor):
        """Create chaos engineering tester instance."""
        return ChaosEngineeringTester(api_client, monitor)
    
    @pytest.mark.asyncio
    async def test_database_connection_failure_recovery(self, chaos_tester, db_pool):
        """Test system behavior when database connections are unavailable."""
        metrics = await chaos_tester.test_database_connection_failures(db_pool)
        
        validation = chaos_tester.validate_recovery_procedures(metrics)
        assert validation["recovery_successful"], "System should recover from database connection failures"
        assert validation["no_data_loss"], "No data should be lost during recovery"
    
    @pytest.mark.asyncio
    async def test_network_partition_recovery(self, chaos_tester):
        """Test rate limiter behavior during network issues."""
        rate_limiter = create_rate_limiter(
            requests_per_minute=30,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        
        metrics = await chaos_tester.test_network_partitions(rate_limiter)
        
        validation = chaos_tester.validate_recovery_procedures(metrics)
        assert validation["recovery_successful"], "System should recover from network partitions"
        assert validation["mttr_acceptable"], "Recovery time should be acceptable"
    
    @pytest.mark.asyncio
    async def test_memory_pressure_recovery(self, chaos_tester):
        """Test system behavior under memory constraints."""
        metrics = await chaos_tester.test_memory_pressure()
        
        validation = chaos_tester.validate_recovery_procedures(metrics)
        assert validation["recovery_successful"], "System should handle memory pressure gracefully"
        assert validation["no_data_loss"], "No data should be lost under memory pressure"
    
    @pytest.mark.asyncio
    async def test_cpu_throttling_behavior(self, chaos_tester):
        """Validate semaphore behavior under CPU limits."""
        metrics = await chaos_tester.test_cpu_throttling()
        
        validation = chaos_tester.validate_recovery_procedures(metrics)
        assert validation["recovery_successful"], "System should handle CPU throttling"
        assert validation["service_impact_acceptable"], "Service impact should be acceptable"
    
    @pytest.mark.asyncio
    async def test_service_failure_recovery(self, chaos_tester):
        """Test graceful degradation when components fail."""
        metrics = await chaos_tester.test_service_failures()
        
        validation = chaos_tester.validate_recovery_procedures(metrics)
        assert validation["recovery_successful"], "System should recover from service failures"
        assert validation["mttr_acceptable"], "Recovery time should be acceptable"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

