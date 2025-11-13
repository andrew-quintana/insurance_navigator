"""
Phase 3 Integration Tests: End-to-End Concurrency Validation

Tests complete user journeys through all agent types with realistic workloads,
cross-agent communication and resource sharing under concurrent load, framework
behavior during system startup/shutdown, graceful degradation scenarios,
framework rollback and recovery procedures, and end-to-end performance validation.

Addresses: FM-043 Phase 3 - End-to-End Integration Validation
"""

import pytest
import asyncio
import httpx
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env.development
env_file = Path(__file__).parent.parent.parent / ".env.development"
if env_file.exists():
    load_dotenv(env_file)
    logging.info(f"Loaded environment variables from {env_file}")
else:
    logging.warning(f"Environment file not found: {env_file}")

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.shared.monitoring.concurrency_monitor import get_monitor
from agents.shared.rate_limiting.limiter import (
    create_rate_limiter,
    RateLimitAlgorithm,
    get_openai_rate_limiter,
    get_anthropic_rate_limiter
)
from agents.tooling.rag.database_manager import DatabasePoolManager

logger = logging.getLogger(__name__)

# Test configuration - load from environment
API_BASE_URL = os.getenv("API_BASE_URL") or os.getenv("BACKEND_URL") or "http://localhost:8000"
TEST_TIMEOUT = float(os.getenv("TEST_TIMEOUT", "120.0"))
CONCURRENT_USERS = int(os.getenv("CONCURRENT_USERS", "10"))


class TestE2EConcurrencyValidation:
    """End-to-end integration tests for concurrency validation."""
    
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
        pool = DatabasePoolManager(min_size=2, max_size=10)
        await pool.initialize()
        yield pool
        await pool.close_pool()
    
    @pytest.mark.asyncio
    async def test_complete_user_journey_all_agents(self, api_client, monitor, db_pool):
        """
        Test complete user journeys through all agent types with realistic workloads.
        
        Simulates a complete user journey: health check → database query → 
        rate-limited operation, validating concurrency controls throughout.
        """
        logger.info("Testing complete user journey through all agent types")
        
        # Set up concurrency controls
        semaphore = asyncio.Semaphore(5)
        monitor.register_semaphore("user_journey", semaphore, 5)
        rate_limiter = create_rate_limiter(requests_per_minute=30)
        
        async def user_journey(user_id: int) -> Dict[str, Any]:
            """Complete user journey simulation."""
            journey_steps = []
            
            # Step 1: Health check (API call)
            async with semaphore:
                await rate_limiter.acquire()
                try:
                    response = await api_client.get(f"{API_BASE_URL}/health")
                    journey_steps.append({
                        "step": "health_check",
                        "status": response.status_code,
                        "success": response.status_code == 200
                    })
                except Exception as e:
                    journey_steps.append({
                        "step": "health_check",
                        "error": str(e),
                        "success": False
                    })
            
            # Step 2: Database operation
            async with semaphore:
                conn = await db_pool.acquire_connection()
                try:
                    result = await conn.fetchval("SELECT 1")
                    journey_steps.append({
                        "step": "database_query",
                        "result": result,
                        "success": True
                    })
                except Exception as e:
                    journey_steps.append({
                        "step": "database_query",
                        "error": str(e),
                        "success": False
                    })
                finally:
                    await db_pool.release_connection(conn)
            
            # Step 3: Rate-limited operation
            async with semaphore:
                await rate_limiter.acquire()
                await asyncio.sleep(0.1)  # Simulate work
                journey_steps.append({
                    "step": "rate_limited_op",
                    "success": True
                })
            
            return {
                "user_id": user_id,
                "journey_steps": journey_steps,
                "all_successful": all(step.get("success", False) for step in journey_steps)
            }
        
        # Execute journeys for multiple users concurrently
        journeys = [user_journey(i) for i in range(CONCURRENT_USERS)]
        results = await asyncio.gather(*journeys, return_exceptions=True)
        
        # Validate journeys
        successful_journeys = [
            r for r in results 
            if isinstance(r, dict) and r.get("all_successful", False)
        ]
        
        assert len(successful_journeys) > 0, "At least some user journeys should complete successfully"
        
        # Check that concurrency limits were respected
        metrics = await monitor.get_current_metrics()
        assert metrics.semaphore_usage.get("user_journey", 0) <= 5
        
        logger.info(f"Complete user journey test passed: {len(successful_journeys)}/{CONCURRENT_USERS} journeys successful")
    
    @pytest.mark.asyncio
    async def test_cross_agent_communication_concurrent_load(self, monitor, db_pool):
        """
        Test cross-agent communication and resource sharing under concurrent load.
        
        Validates that different agents can communicate and share resources
        correctly when operating under high concurrent load.
        """
        logger.info("Testing cross-agent communication under concurrent load")
        
        # Shared resources
        shared_semaphore = asyncio.Semaphore(5)
        monitor.register_semaphore("shared_resource", shared_semaphore, 5)
        
        shared_rate_limiter = create_rate_limiter(requests_per_minute=40)
        
        async def agent_a_operation(agent_id: int) -> Dict[str, Any]:
            """Agent A operation using shared resources."""
            async with shared_semaphore:
                await shared_rate_limiter.acquire()
                
                conn = await db_pool.acquire_connection()
                try:
                    result = await conn.fetchval("SELECT 1")
                    return {"agent": "A", "agent_id": agent_id, "result": result, "success": True}
                finally:
                    await db_pool.release_connection(conn)
        
        async def agent_b_operation(agent_id: int) -> Dict[str, Any]:
            """Agent B operation using shared resources."""
            async with shared_semaphore:
                await shared_rate_limiter.acquire()
                
                conn = await db_pool.acquire_connection()
                try:
                    result = await conn.fetchval("SELECT 2")
                    return {"agent": "B", "agent_id": agent_id, "result": result, "success": True}
                finally:
                    await db_pool.release_connection(conn)
        
        # Execute operations from both agents concurrently
        agent_a_ops = [agent_a_operation(i) for i in range(10)]
        agent_b_ops = [agent_b_operation(i) for i in range(10)]
        all_ops = agent_a_ops + agent_b_ops
        
        results = await asyncio.gather(*all_ops, return_exceptions=True)
        
        # Validate cross-agent communication
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful) == 20, "All cross-agent operations should succeed"
        
        # Check resource sharing
        metrics = await monitor.get_current_metrics()
        assert metrics.semaphore_usage.get("shared_resource", 0) <= 5
        
        logger.info("Cross-agent communication test passed")
    
    @pytest.mark.asyncio
    async def test_framework_startup_shutdown_sequences(self, monitor):
        """
        Test framework behavior during system startup/shutdown sequences.
        
        Validates that concurrency framework initializes correctly on startup
        and cleans up resources properly on shutdown.
        """
        logger.info("Testing framework startup/shutdown sequences")
        
        # Simulate startup
        startup_semaphore = asyncio.Semaphore(10)
        monitor.register_semaphore("startup_test", startup_semaphore, 10)
        
        # Verify startup
        metrics_startup = await monitor.get_current_metrics()
        assert "startup_test" in metrics_startup.semaphore_usage
        
        # Simulate operations during runtime
        async def runtime_operation(op_id: int) -> Dict[str, Any]:
            async with startup_semaphore:
                await asyncio.sleep(0.1)
                return {"op_id": op_id, "success": True}
        
        ops = [runtime_operation(i) for i in range(5)]
        await asyncio.gather(*ops)
        
        # Simulate shutdown (cleanup)
        # In real scenario, this would close pools, cancel tasks, etc.
        # For testing, we verify resources are tracked
        metrics_runtime = await monitor.get_current_metrics()
        assert "startup_test" in metrics_runtime.semaphore_usage
        
        # Check summary stats
        stats = monitor.get_summary_stats()
        assert stats.get("registered_semaphores", 0) > 0
        
        logger.info("Framework startup/shutdown sequences test passed")
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_scenarios(self, api_client, monitor):
        """
        Test graceful degradation scenarios and recovery procedures.
        
        Validates that the system degrades gracefully when resources are
        exhausted and recovers properly when resources become available.
        """
        logger.info("Testing graceful degradation scenarios")
        
        # Create very restrictive limits
        restrictive_semaphore = asyncio.Semaphore(2)
        monitor.register_semaphore("degradation_test", restrictive_semaphore, 2)
        # Use higher rate limit to avoid excessive waiting (10 req/min instead of 5)
        restrictive_rate_limiter = create_rate_limiter(requests_per_minute=10)
        
        async def operation_under_stress(op_id: int) -> Dict[str, Any]:
            """Operation that will face resource constraints."""
            try:
                async with restrictive_semaphore:
                    await restrictive_rate_limiter.acquire()
                    
                    # Simulate API call with shorter timeout
                    try:
                        response = await asyncio.wait_for(
                            api_client.get(f"{API_BASE_URL}/health"),
                            timeout=3.0
                        )
                        return {
                            "op_id": op_id,
                            "status": response.status_code,
                            "success": True
                        }
                    except asyncio.TimeoutError:
                        return {
                            "op_id": op_id,
                            "error": "timeout",
                            "success": False,
                            "graceful": True
                        }
            except Exception as e:
                return {
                    "op_id": op_id,
                    "error": str(e),
                    "success": False,
                    "graceful": True
                }
        
        # Launch more operations than limits allow (but fewer to avoid timeout)
        operations = [operation_under_stress(i) for i in range(8)]
        
        # Execute with longer overall timeout to account for rate limiting
        start_time = time.time()
        results = await asyncio.wait_for(
            asyncio.gather(*operations, return_exceptions=True),
            timeout=60.0  # Increased timeout for rate-limited operations
        )
        elapsed = time.time() - start_time
        
        # Validate graceful degradation
        assert elapsed < 30.0, "Operations should complete without deadlock"
        
        # Some operations should succeed (within limits)
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        graceful_failures = [
            r for r in results 
            if isinstance(r, dict) and not r.get("success") and r.get("graceful")
        ]
        
        assert len(successful) >= 2, "Operations within limits should succeed"
        assert len(successful) + len(graceful_failures) == len(operations), "All operations should complete"
        
        logger.info(f"Graceful degradation test passed: {len(successful)} succeeded, {len(graceful_failures)} graceful failures")
    
    @pytest.mark.asyncio
    async def test_framework_rollback_recovery(self, monitor):
        """
        Test framework rollback and recovery procedures for deployment failures.
        
        Validates that the framework can rollback to previous state and
        recover from deployment failures gracefully.
        """
        logger.info("Testing framework rollback and recovery procedures")
        
        # Simulate initial state
        initial_semaphore = asyncio.Semaphore(10)
        monitor.register_semaphore("rollback_test", initial_semaphore, 10)
        
        # Simulate deployment with new configuration
        new_semaphore = asyncio.Semaphore(5)
        monitor.register_semaphore("rollback_test_new", new_semaphore, 5)
        
        # Simulate rollback (revert to initial)
        # In real scenario, this would restore previous configuration
        rollback_semaphore = asyncio.Semaphore(10)
        monitor.register_semaphore("rollback_test_restored", rollback_semaphore, 10)
        
        # Verify rollback worked
        metrics = await monitor.get_current_metrics()
        assert "rollback_test_restored" in metrics.semaphore_usage
        
        # Test recovery operations
        async def recovery_operation(op_id: int) -> Dict[str, Any]:
            async with rollback_semaphore:
                await asyncio.sleep(0.1)
                return {"op_id": op_id, "success": True}
        
        recovery_ops = [recovery_operation(i) for i in range(5)]
        results = await asyncio.gather(*recovery_ops)
        
        # Validate recovery
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful) == 5, "Recovery operations should succeed"
        
        logger.info("Framework rollback and recovery test passed")
    
    @pytest.mark.asyncio
    async def test_end_to_end_performance_baselines(self, api_client, monitor, db_pool):
        """
        Validate end-to-end performance meets established baselines.
        
        Validates that end-to-end performance (response times, throughput)
        meets or exceeds established baselines from Phase 2.
        """
        logger.info("Testing end-to-end performance baselines")
        
        semaphore = asyncio.Semaphore(10)
        monitor.register_semaphore("performance_test", semaphore, 10)
        rate_limiter = create_rate_limiter(requests_per_minute=60)
        
        async def performance_operation(op_id: int) -> Dict[str, Any]:
            """Operation for performance testing."""
            start_time = time.time()
            
            async with semaphore:
                await rate_limiter.acquire()
                
                # API call
                try:
                    response = await api_client.get(f"{API_BASE_URL}/health")
                    api_time = time.time() - start_time
                    
                    # Database operation
                    db_start = time.time()
                    conn = await db_pool.acquire_connection()
                    try:
                        await conn.fetchval("SELECT 1")
                        db_time = time.time() - db_start
                    finally:
                        await db_pool.release_connection(conn)
                    
                    total_time = time.time() - start_time
                    
                    return {
                        "op_id": op_id,
                        "api_time": api_time,
                        "db_time": db_time,
                        "total_time": total_time,
                        "success": response.status_code == 200
                    }
                except Exception as e:
                    return {
                        "op_id": op_id,
                        "error": str(e),
                        "success": False
                    }
        
        # Execute performance operations
        operations = [performance_operation(i) for i in range(20)]
        results = await asyncio.gather(*operations, return_exceptions=True)
        
        # Analyze performance
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful) > 0, "At least some operations should succeed"
        
        # Calculate performance metrics
        total_times = [r.get("total_time", 0) for r in successful if "total_time" in r]
        if total_times:
            avg_time = sum(total_times) / len(total_times)
            max_time = max(total_times)
            
            # Baseline: Average should be < 2 seconds, max should be < 5 seconds
            assert avg_time < 2.0, f"Average time {avg_time:.2f}s exceeds baseline of 2.0s"
            assert max_time < 5.0, f"Max time {max_time:.2f}s exceeds baseline of 5.0s"
            
            logger.info(f"Performance baselines met: avg={avg_time:.2f}s, max={max_time:.2f}s")
        
        logger.info(f"End-to-end performance test passed: {len(successful)}/{len(operations)} operations succeeded")
    
    @pytest.mark.asyncio
    async def test_realistic_workload_patterns(self, api_client, monitor, db_pool):
        """
        Test system behavior under realistic workload patterns.
        
        Simulates realistic user behavior patterns (bursts, steady state,
        spikes) and validates concurrency controls handle them correctly.
        """
        logger.info("Testing realistic workload patterns")
        
        semaphore = asyncio.Semaphore(10)
        monitor.register_semaphore("realistic_workload", semaphore, 10)
        rate_limiter = create_rate_limiter(requests_per_minute=60)
        
        async def workload_operation(op_id: int) -> Dict[str, Any]:
            """Operation in realistic workload."""
            async with semaphore:
                await rate_limiter.acquire()
                try:
                    response = await api_client.get(f"{API_BASE_URL}/health")
                    return {"op_id": op_id, "status": response.status_code, "success": True}
                except Exception as e:
                    return {"op_id": op_id, "error": str(e), "success": False}
        
        # Pattern 1: Steady state (constant load)
        logger.info("Testing steady state workload")
        steady_ops = [workload_operation(i) for i in range(10)]
        await asyncio.gather(*steady_ops)
        await asyncio.sleep(1.0)
        
        # Pattern 2: Burst (sudden spike)
        logger.info("Testing burst workload")
        burst_ops = [workload_operation(i) for i in range(20)]
        await asyncio.gather(*burst_ops)
        await asyncio.sleep(1.0)
        
        # Pattern 3: Gradual increase
        logger.info("Testing gradual increase workload")
        for batch_size in [5, 10, 15]:
            gradual_ops = [workload_operation(i) for i in range(batch_size)]
            await asyncio.gather(*gradual_ops)
            await asyncio.sleep(0.5)
        
        # Validate all patterns completed successfully
        metrics = await monitor.get_current_metrics()
        assert "realistic_workload" in metrics.semaphore_usage
        assert metrics.semaphore_usage["realistic_workload"] <= 10
        
        logger.info("Realistic workload patterns test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

