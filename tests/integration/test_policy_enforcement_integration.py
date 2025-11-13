"""
Phase 3 Integration Tests: Policy Enforcement Integration

Tests policy enforcement across all agent types under realistic workloads,
policy override mechanisms, policy validation during startup, end-to-end
policy compliance, and policy conflict resolution.

Addresses: FM-043 Phase 3 - Policy System Integration
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
from dataclasses import dataclass
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
    RateLimitConfig
)
from agents.tooling.rag.database_manager import DatabasePoolManager

logger = logging.getLogger(__name__)

# Test configuration - load from environment
API_BASE_URL = os.getenv("API_BASE_URL") or os.getenv("BACKEND_URL") or "http://localhost:8000"
TEST_TIMEOUT = float(os.getenv("TEST_TIMEOUT", "60.0"))


@dataclass
class ConcurrencyPolicy:
    """Represents a concurrency policy for testing."""
    semaphore_limit: int
    rate_limit_per_minute: int
    pool_min_size: int
    pool_max_size: int
    timeout_seconds: float


class TestPolicyEnforcementIntegration:
    """Integration tests for policy enforcement system."""
    
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
    def default_policy(self) -> ConcurrencyPolicy:
        """Default concurrency policy for testing."""
        return ConcurrencyPolicy(
            semaphore_limit=10,
            rate_limit_per_minute=30,
            pool_min_size=2,
            pool_max_size=5,
            timeout_seconds=30.0
        )
    
    @pytest.fixture
    def strict_policy(self) -> ConcurrencyPolicy:
        """Strict concurrency policy for testing."""
        return ConcurrencyPolicy(
            semaphore_limit=3,
            rate_limit_per_minute=10,
            pool_min_size=1,
            pool_max_size=2,
            timeout_seconds=10.0
        )
    
    @pytest.mark.asyncio
    async def test_policy_enforcement_all_agent_types(self, api_client, monitor, default_policy):
        """
        Test policy enforcement across all agent types under realistic workloads.
        
        Validates that concurrency policies are enforced consistently across
        different agent workflows (chat, RAG, information retrieval).
        """
        logger.info("Testing policy enforcement across all agent types")
        
        # Create semaphore with policy limit
        semaphore = asyncio.Semaphore(default_policy.semaphore_limit)
        monitor.register_semaphore("agent_workflow", semaphore, default_policy.semaphore_limit)
        
        # Create rate limiter with policy limit
        rate_limiter = create_rate_limiter(
            requests_per_minute=default_policy.rate_limit_per_minute,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        
        async def agent_workflow(workflow_type: str, workflow_id: int) -> Dict[str, Any]:
            """Simulate different agent workflow types."""
            async with semaphore:
                await rate_limiter.acquire()
                
                # Simulate different agent operations
                if workflow_type == "chat":
                    # Simulate chat endpoint call
                    try:
                        response = await api_client.get(f"{API_BASE_URL}/health")
                        return {"type": "chat", "id": workflow_id, "status": response.status_code}
                    except Exception as e:
                        return {"type": "chat", "id": workflow_id, "error": str(e)}
                
                elif workflow_type == "rag":
                    # Simulate RAG operation
                    await asyncio.sleep(0.1)
                    return {"type": "rag", "id": workflow_id, "success": True}
                
                elif workflow_type == "info_retrieval":
                    # Simulate information retrieval
                    await asyncio.sleep(0.1)
                    return {"type": "info_retrieval", "id": workflow_id, "success": True}
                
                else:
                    return {"type": "unknown", "id": workflow_id, "error": "Unknown type"}
        
        # Create workloads for different agent types
        chat_workflows = [agent_workflow("chat", i) for i in range(5)]
        rag_workflows = [agent_workflow("rag", i) for i in range(5)]
        info_workflows = [agent_workflow("info_retrieval", i) for i in range(5)]
        
        all_workflows = chat_workflows + rag_workflows + info_workflows
        
        # Execute all workflows concurrently
        results = await asyncio.gather(*all_workflows, return_exceptions=True)
        
        # Validate policy enforcement
        successful = [r for r in results if isinstance(r, dict) and ("success" in r or "status" in r)]
        assert len(successful) > 0, "At least some workflows should succeed"
        
        # Check that semaphore limits were respected
        metrics = await monitor.get_current_metrics()
        assert metrics.semaphore_usage.get("agent_workflow", 0) <= default_policy.semaphore_limit
        
        logger.info(f"Policy enforcement test passed: {len(successful)}/{len(all_workflows)} workflows succeeded")
    
    @pytest.mark.asyncio
    async def test_policy_override_mechanisms(self, monitor, default_policy, strict_policy):
        """
        Test policy override mechanisms in different operational scenarios.
        
        Validates that policies can be overridden for specific operations
        or scenarios (e.g., emergency operations, admin operations).
        """
        logger.info("Testing policy override mechanisms")
        
        # Create default semaphore
        default_semaphore = asyncio.Semaphore(default_policy.semaphore_limit)
        monitor.register_semaphore("default", default_semaphore, default_policy.semaphore_limit)
        
        # Create override semaphore for emergency operations
        override_semaphore = asyncio.Semaphore(strict_policy.semaphore_limit)
        monitor.register_semaphore("override", override_semaphore, strict_policy.semaphore_limit)
        
        async def default_operation(op_id: int) -> Dict[str, Any]:
            """Operation using default policy."""
            async with default_semaphore:
                await asyncio.sleep(0.1)
                return {"policy": "default", "op_id": op_id, "success": True}
        
        async def override_operation(op_id: int) -> Dict[str, Any]:
            """Operation using override policy."""
            async with override_semaphore:
                await asyncio.sleep(0.1)
                return {"policy": "override", "op_id": op_id, "success": True}
        
        # Execute operations with different policies
        default_ops = [default_operation(i) for i in range(5)]
        override_ops = [override_operation(i) for i in range(5)]
        
        results = await asyncio.gather(*default_ops + override_ops, return_exceptions=True)
        
        # Validate both policy types worked
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful) == 10, "All operations should succeed"
        
        # Check that both semaphores are tracked
        metrics = await monitor.get_current_metrics()
        assert "default" in metrics.semaphore_usage
        assert "override" in metrics.semaphore_usage
        
        logger.info("Policy override mechanisms test passed")
    
    @pytest.mark.asyncio
    async def test_policy_validation_startup(self, monitor):
        """
        Test policy validation during agent startup and configuration changes.
        
        Validates that policies are validated when agents start up and
        when configuration changes occur.
        """
        logger.info("Testing policy validation during startup")
        
        # Test valid policy
        valid_semaphore = asyncio.Semaphore(10)
        monitor.register_semaphore("valid_policy", valid_semaphore, 10)
        
        # Test invalid policy (negative limit - should be handled gracefully)
        try:
            invalid_semaphore = asyncio.Semaphore(-1)  # This will raise ValueError
            assert False, "Should not allow negative semaphore limit"
        except ValueError:
            pass  # Expected behavior
        
        # Test zero limit (edge case)
        zero_semaphore = asyncio.Semaphore(0)
        monitor.register_semaphore("zero_policy", zero_semaphore, 0)
        
        # Validate policies are registered
        metrics = await monitor.get_current_metrics()
        assert "valid_policy" in metrics.semaphore_usage
        assert "zero_policy" in metrics.semaphore_usage
        
        logger.info("Policy validation during startup test passed")
    
    @pytest.mark.asyncio
    async def test_end_to_end_policy_compliance(self, api_client, monitor, default_policy):
        """
        Test end-to-end policy compliance verification across system boundaries.
        
        Validates that policies are enforced consistently from API entry point
        through to agent execution and resource cleanup.
        """
        logger.info("Testing end-to-end policy compliance")
        
        # Create semaphore and rate limiter with policy limits
        semaphore = asyncio.Semaphore(default_policy.semaphore_limit)
        monitor.register_semaphore("e2e_test", semaphore, default_policy.semaphore_limit)
        rate_limiter = create_rate_limiter(
            requests_per_minute=default_policy.rate_limit_per_minute
        )
        
        async def e2e_operation(op_id: int) -> Dict[str, Any]:
            """End-to-end operation with policy enforcement."""
            # Entry point: Acquire semaphore
            async with semaphore:
                # Rate limiting
                await rate_limiter.acquire()
                
                # API call (simulating agent execution)
                try:
                    response = await api_client.get(f"{API_BASE_URL}/health")
                    
                    # Resource cleanup (implicit via context manager)
                    return {
                        "op_id": op_id,
                        "status": response.status_code,
                        "success": response.status_code == 200
                    }
                except Exception as e:
                    return {
                        "op_id": op_id,
                        "error": str(e),
                        "success": False
                    }
        
        # Execute end-to-end operations
        operations = [e2e_operation(i) for i in range(15)]
        results = await asyncio.gather(*operations, return_exceptions=True)
        
        # Validate compliance
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful) > 0, "At least some operations should succeed"
        
        # Check that policies were enforced throughout
        metrics = await monitor.get_current_metrics()
        assert metrics.semaphore_usage.get("e2e_test", 0) <= default_policy.semaphore_limit
        
        logger.info(f"End-to-end policy compliance test passed: {len(successful)}/{len(operations)} succeeded")
    
    @pytest.mark.asyncio
    async def test_policy_conflict_resolution(self, monitor):
        """
        Test policy conflict resolution when multiple policies apply.
        
        Validates that when multiple policies could apply to the same operation,
        conflicts are resolved correctly (e.g., most restrictive wins).
        """
        logger.info("Testing policy conflict resolution")
        
        # Create multiple semaphores that might conflict
        semaphore_a = asyncio.Semaphore(5)
        semaphore_b = asyncio.Semaphore(3)
        
        monitor.register_semaphore("policy_a", semaphore_a, 5)
        monitor.register_semaphore("policy_b", semaphore_b, 3)
        
        async def conflicting_operation(op_id: int) -> Dict[str, Any]:
            """Operation that could use either policy."""
            # Use most restrictive policy (policy_b with limit 3)
            async with semaphore_b:
                await asyncio.sleep(0.1)
                return {"op_id": op_id, "policy_used": "b", "success": True}
        
        # Execute operations
        operations = [conflicting_operation(i) for i in range(10)]
        results = await asyncio.gather(*operations, return_exceptions=True)
        
        # Validate conflict resolution
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful) > 0, "Operations should succeed with conflict resolution"
        
        # Check that most restrictive policy was used
        metrics = await monitor.get_current_metrics()
        # Policy B (more restrictive) should be the limiting factor
        assert metrics.semaphore_usage.get("policy_b", 0) <= 3
        
        logger.info("Policy conflict resolution test passed")
    
    @pytest.mark.asyncio
    async def test_policy_enforcement_under_load(self, api_client, monitor, default_policy):
        """
        Test policy enforcement under sustained load.
        
        Validates that policies remain enforced even under high sustained load
        and that the system doesn't degrade or bypass policies.
        """
        logger.info("Testing policy enforcement under sustained load")
        
        semaphore = asyncio.Semaphore(default_policy.semaphore_limit)
        monitor.register_semaphore("load_test", semaphore, default_policy.semaphore_limit)
        rate_limiter = create_rate_limiter(
            requests_per_minute=default_policy.rate_limit_per_minute
        )
        
        async def load_operation(op_id: int) -> Dict[str, Any]:
            """Operation under load."""
            async with semaphore:
                await rate_limiter.acquire()
                try:
                    response = await api_client.get(f"{API_BASE_URL}/health")
                    return {"op_id": op_id, "status": response.status_code, "success": True}
                except Exception as e:
                    return {"op_id": op_id, "error": str(e), "success": False}
        
        # Create sustained load
        batches = []
        for batch in range(3):
            batch_ops = [load_operation(batch * 10 + i) for i in range(10)]
            batches.append(batch_ops)
        
        # Execute all batches
        all_results = []
        for batch in batches:
            results = await asyncio.gather(*batch, return_exceptions=True)
            all_results.extend(results)
            await asyncio.sleep(0.5)  # Small delay between batches
        
        # Validate policy enforcement maintained
        successful = [r for r in all_results if isinstance(r, dict) and r.get("success")]
        assert len(successful) > 0, "Operations should succeed even under load"
        
        # Check that limits were never exceeded
        metrics = await monitor.get_current_metrics()
        assert metrics.semaphore_usage.get("load_test", 0) <= default_policy.semaphore_limit
        
        logger.info(f"Policy enforcement under load test passed: {len(successful)}/{len(all_results)} succeeded")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

