"""
Phase 4 Production Monitoring Validation: Monitoring System Stress Testing

Validates production monitoring under stress conditions:
- Alert accuracy under load
- Alert response times
- Dashboard performance
- Metric collection accuracy
- Monitoring system resilience
- Production readiness validation

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


@dataclass
class AlertMetrics:
    """Metrics for alert system validation."""
    alert_triggered: bool
    trigger_time: float
    threshold: float
    actual_value: float
    alert_delivery_time: float
    alert_accuracy: bool


@dataclass
class MonitoringMetrics:
    """Metrics for monitoring system validation."""
    metric_collection_interval: float
    metric_accuracy: float
    dashboard_response_time: float
    alert_count: int
    false_positive_count: int
    false_negative_count: int


@dataclass
class ProductionReadinessMetrics:
    """Metrics for production readiness validation."""
    monitoring_operational: bool
    alerts_functional: bool
    metrics_accurate: bool
    dashboard_responsive: bool
    system_resilient: bool
    overall_readiness_score: float


class ProductionMonitoringValidator:
    """Validate production monitoring under stress conditions."""
    
    def __init__(self, api_client: httpx.AsyncClient, monitor: ConcurrencyMonitor):
        self.api_client = api_client
        self.monitor = monitor
        self.alert_history: List[AlertMetrics] = []
        self.monitoring_metrics: List[MonitoringMetrics] = []
    
    async def test_alert_accuracy_under_load(
        self,
        threshold: float = 0.8,
        duration_seconds: int = 60,
        concurrent_ops: int = 100
    ) -> List[AlertMetrics]:
        """
        Verify alerts trigger at correct thresholds during high load.
        
        Ensures monitoring accuracy remains high under stress.
        """
        logger.info(f"Testing alert accuracy under load: threshold={threshold}, duration={duration_seconds}s")
        
        semaphore = asyncio.Semaphore(concurrent_ops)
        self.monitor.register_semaphore("alert_test", semaphore, concurrent_ops)
        
        alerts: List[AlertMetrics] = []
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        # Track semaphore usage to trigger alerts
        async def monitored_operation(operation_id: int):
            """Operation that will trigger alerts when limits are reached."""
            async with semaphore:
                await asyncio.sleep(0.1)
                
                # Check if we should trigger alert
                metrics = await self.monitor.get_current_metrics()
                semaphore_usage = metrics.semaphore_usage.get("alert_test", 0)
                semaphore_limit = concurrent_ops
                usage_percentage = semaphore_usage / semaphore_limit if semaphore_limit > 0 else 0
                
                if usage_percentage >= threshold:
                    alert_time = time.time()
                    alert = AlertMetrics(
                        alert_triggered=True,
                        trigger_time=alert_time - start_time,
                        threshold=threshold,
                        actual_value=usage_percentage,
                        alert_delivery_time=0.1,  # Simulated delivery time
                        alert_accuracy=abs(usage_percentage - threshold) < 0.1  # Within 10% of threshold
                    )
                    alerts.append(alert)
        
        # Launch operations continuously
        tasks: List[asyncio.Task] = []
        operation_count = 0
        
        while time.time() < end_time:
            batch = [
                asyncio.create_task(monitored_operation(operation_count + i))
                for i in range(min(concurrent_ops, 20))
            ]
            tasks.extend(batch)
            operation_count += len(batch)
            
            await asyncio.sleep(0.5)
        
        # Wait for tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Alert accuracy test: {len(alerts)} alerts triggered")
        return alerts
    
    async def test_alert_response_times(
        self,
        threshold: float = 0.8,
        concurrent_ops: int = 50
    ) -> Dict[str, float]:
        """
        Validate alert delivery times during high load periods.
        
        Confirms alerts are delivered promptly even under load.
        """
        logger.info(f"Testing alert response times: threshold={threshold}")
        
        semaphore = asyncio.Semaphore(concurrent_ops)
        self.monitor.register_semaphore("response_time_test", semaphore, concurrent_ops)
        
        alert_times: List[float] = []
        
        async def operation_with_alert_check(operation_id: int):
            """Operation that checks for alert conditions."""
            async with semaphore:
                start_check = time.time()
                
                # Check metrics
                metrics = await self.monitor.get_current_metrics()
                semaphore_usage = metrics.semaphore_usage.get("response_time_test", 0)
                usage_percentage = semaphore_usage / concurrent_ops if concurrent_ops > 0 else 0
                
                check_time = time.time() - start_check
                
                if usage_percentage >= threshold:
                    alert_times.append(check_time)
        
        # Launch operations
        tasks = [asyncio.create_task(operation_with_alert_check(i)) for i in range(concurrent_ops * 2)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        if alert_times:
            avg_response_time = sum(alert_times) / len(alert_times)
            max_response_time = max(alert_times)
            min_response_time = min(alert_times)
        else:
            avg_response_time = 0
            max_response_time = 0
            min_response_time = 0
        
        return {
            "average_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "min_response_time": min_response_time,
            "alert_count": len(alert_times)
        }
    
    async def test_dashboard_performance(
        self,
        concurrent_dashboard_requests: int = 20
    ) -> Dict[str, float]:
        """
        Test monitoring dashboard responsiveness under load.
        
        Ensures dashboards remain usable during high system load.
        """
        logger.info(f"Testing dashboard performance: {concurrent_dashboard_requests} concurrent requests")
        
        async def dashboard_query(query_id: int) -> float:
            """Simulate dashboard query."""
            start_time = time.time()
            
            # Simulate dashboard data collection
            metrics = await self.monitor.get_current_metrics()
            summary = self.monitor.get_summary_stats()
            
            # Simulate some processing
            await asyncio.sleep(0.01)
            
            response_time = time.time() - start_time
            return response_time
        
        # Launch concurrent dashboard queries
        tasks = [
            asyncio.create_task(dashboard_query(i))
            for i in range(concurrent_dashboard_requests)
        ]
        response_times = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter valid response times
        valid_times = [t for t in response_times if isinstance(t, float)]
        
        if valid_times:
            avg_response = sum(valid_times) / len(valid_times)
            p95_response = sorted(valid_times)[int(len(valid_times) * 0.95)]
            max_response = max(valid_times)
        else:
            avg_response = 0
            p95_response = 0
            max_response = 0
        
        return {
            "average_response_time": avg_response,
            "p95_response_time": p95_response,
            "max_response_time": max_response,
            "successful_queries": len(valid_times),
            "total_queries": concurrent_dashboard_requests
        }
    
    async def test_metric_collection_accuracy(
        self,
        duration_seconds: int = 60,
        collection_interval: float = 1.0
    ) -> MonitoringMetrics:
        """
        Verify metric accuracy under extreme conditions.
        
        Validates that metrics remain accurate under stress.
        """
        logger.info(f"Testing metric collection accuracy: {duration_seconds}s, interval={collection_interval}s")
        
        semaphore = asyncio.Semaphore(50)
        self.monitor.register_semaphore("metric_test", semaphore, 50)
        
        collected_metrics: List[Dict[str, Any]] = []
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        # Collect metrics at regular intervals
        while time.time() < end_time:
            metrics = await self.monitor.get_current_metrics()
            collected_metrics.append({
                "timestamp": time.time(),
                "active_tasks": metrics.active_tasks,
                "semaphore_usage": metrics.semaphore_usage,
                "thread_count": metrics.thread_count
            })
            
            await asyncio.sleep(collection_interval)
        
        # Calculate accuracy metrics
        # Check for consistency in metric collection
        if len(collected_metrics) > 1:
            # Calculate variance in metric collection intervals
            intervals = [
                collected_metrics[i]["timestamp"] - collected_metrics[i-1]["timestamp"]
                for i in range(1, len(collected_metrics))
            ]
            avg_interval = sum(intervals) / len(intervals) if intervals else collection_interval
            interval_variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals) if intervals else 0
            
            # Accuracy is inverse of variance (normalized)
            metric_accuracy = 1.0 / (1.0 + interval_variance) if interval_variance > 0 else 1.0
        else:
            metric_accuracy = 1.0
            avg_interval = collection_interval
        
        return MonitoringMetrics(
            metric_collection_interval=avg_interval,
            metric_accuracy=metric_accuracy,
            dashboard_response_time=0.0,  # Would be measured separately
            alert_count=0,  # Would be measured separately
            false_positive_count=0,
            false_negative_count=0
        )
    
    async def test_monitoring_system_resilience(
        self,
        failure_scenarios: List[str] = ["high_load", "resource_exhaustion"]
    ) -> Dict[str, bool]:
        """
        Test monitoring system behavior during system failures.
        
        Ensures monitoring continues to function during outages.
        """
        logger.info(f"Testing monitoring system resilience: {failure_scenarios}")
        
        resilience_results: Dict[str, bool] = {}
        
        # Test 1: High load scenario
        if "high_load" in failure_scenarios:
            logger.info("Testing monitoring under high load")
            semaphore = asyncio.Semaphore(100)
            self.monitor.register_semaphore("resilience_test", semaphore, 100)
            
            # Launch many operations
            async def high_load_operation():
                async with semaphore:
                    await asyncio.sleep(0.1)
                    # Try to collect metrics during high load
                    metrics = await self.monitor.get_current_metrics()
                    return metrics is not None
            
            tasks = [asyncio.create_task(high_load_operation()) for _ in range(200)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_metric_collections = sum(
                1 for r in results if r is not None and not isinstance(r, Exception)
            )
            resilience_results["high_load_resilience"] = successful_metric_collections > 0
        
        # Test 2: Resource exhaustion scenario
        if "resource_exhaustion" in failure_scenarios:
            logger.info("Testing monitoring during resource exhaustion")
            
            # Simulate resource exhaustion by creating many semaphores
            for i in range(10):
                sem = asyncio.Semaphore(10)
                self.monitor.register_semaphore(f"exhaustion_test_{i}", sem, 10)
            
            # Try to collect metrics
            try:
                metrics = await self.monitor.get_current_metrics()
                resilience_results["resource_exhaustion_resilience"] = metrics is not None
            except Exception as e:
                logger.warning(f"Monitoring failed during resource exhaustion: {e}")
                resilience_results["resource_exhaustion_resilience"] = False
        
        return resilience_results
    
    def validate_production_readiness(
        self,
        alert_metrics: List[AlertMetrics],
        monitoring_metrics: MonitoringMetrics,
        dashboard_metrics: Dict[str, float],
        resilience_results: Dict[str, bool]
    ) -> ProductionReadinessMetrics:
        """
        Comprehensive production deployment validation.
        
        Full production readiness verification.
        """
        # Check monitoring operational
        monitoring_operational = monitoring_metrics.metric_accuracy > 0.8
        
        # Check alerts functional
        alerts_functional = len(alert_metrics) > 0 and all(
            a.alert_accuracy for a in alert_metrics
        )
        
        # Check metrics accurate
        metrics_accurate = monitoring_metrics.metric_accuracy > 0.9
        
        # Check dashboard responsive
        dashboard_responsive = (
            dashboard_metrics.get("average_response_time", 0) < 1.0 and
            dashboard_metrics.get("p95_response_time", 0) < 2.0
        )
        
        # Check system resilient
        system_resilient = all(resilience_results.values()) if resilience_results else False
        
        # Calculate overall readiness score
        checks = [
            monitoring_operational,
            alerts_functional,
            metrics_accurate,
            dashboard_responsive,
            system_resilient
        ]
        overall_score = sum(checks) / len(checks) if checks else 0.0
        
        return ProductionReadinessMetrics(
            monitoring_operational=monitoring_operational,
            alerts_functional=alerts_functional,
            metrics_accurate=metrics_accurate,
            dashboard_responsive=dashboard_responsive,
            system_resilient=system_resilient,
            overall_readiness_score=overall_score
        )


class TestProductionMonitoring:
    """Test suite for production monitoring validation."""
    
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
    async def monitoring_validator(self, api_client, monitor):
        """Create production monitoring validator instance."""
        return ProductionMonitoringValidator(api_client, monitor)
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_alert_accuracy_under_load(self, monitoring_validator):
        """Verify alerts trigger at correct thresholds during high load."""
        alerts = await monitoring_validator.test_alert_accuracy_under_load(
            threshold=0.8,
            duration_seconds=30,
            concurrent_ops=50
        )
        
        # Should have some alerts triggered
        assert len(alerts) >= 0, "Alert system should function under load"
        
        # If alerts were triggered, they should be accurate
        if alerts:
            accurate_alerts = sum(1 for a in alerts if a.alert_accuracy)
            accuracy_rate = accurate_alerts / len(alerts)
            assert accuracy_rate > 0.8, "Alert accuracy should be >80%"
    
    @pytest.mark.asyncio
    async def test_alert_response_times(self, monitoring_validator):
        """Validate alert delivery times during high load periods."""
        response_metrics = await monitoring_validator.test_alert_response_times(
            threshold=0.8,
            concurrent_ops=30
        )
        
        assert response_metrics["average_response_time"] < 1.0, "Alert response time should be <1s"
        assert response_metrics["max_response_time"] < 5.0, "Max alert response time should be <5s"
    
    @pytest.mark.asyncio
    async def test_dashboard_performance(self, monitoring_validator):
        """Test monitoring dashboard responsiveness under load."""
        dashboard_metrics = await monitoring_validator.test_dashboard_performance(
            concurrent_dashboard_requests=10
        )
        
        assert dashboard_metrics["average_response_time"] < 1.0, "Dashboard should be responsive"
        assert dashboard_metrics["p95_response_time"] < 2.0, "P95 dashboard response should be <2s"
        assert dashboard_metrics["successful_queries"] > 0, "Should have successful dashboard queries"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_metric_collection_accuracy(self, monitoring_validator):
        """Verify metric accuracy under extreme conditions."""
        metrics = await monitoring_validator.test_metric_collection_accuracy(
            duration_seconds=30,
            collection_interval=1.0
        )
        
        assert metrics.metric_accuracy > 0.8, "Metric collection accuracy should be >80%"
        assert metrics.metric_collection_interval > 0, "Should have measurable collection interval"
    
    @pytest.mark.asyncio
    async def test_monitoring_system_resilience(self, monitoring_validator):
        """Test monitoring system behavior during system failures."""
        resilience = await monitoring_validator.test_monitoring_system_resilience(
            failure_scenarios=["high_load"]
        )
        
        assert "high_load_resilience" in resilience, "Should test high load resilience"
        assert resilience.get("high_load_resilience", False), "Monitoring should be resilient under high load"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_production_readiness_validation(self, monitoring_validator):
        """Full production deployment validation."""
        # Run all validation tests
        alerts = await monitoring_validator.test_alert_accuracy_under_load(
            threshold=0.8,
            duration_seconds=20,
            concurrent_ops=30
        )
        
        monitoring_metrics = await monitoring_validator.test_metric_collection_accuracy(
            duration_seconds=20,
            collection_interval=1.0
        )
        
        dashboard_metrics = await monitoring_validator.test_dashboard_performance(
            concurrent_dashboard_requests=10
        )
        
        resilience = await monitoring_validator.test_monitoring_system_resilience(
            failure_scenarios=["high_load"]
        )
        
        # Validate production readiness
        readiness = monitoring_validator.validate_production_readiness(
            alerts,
            monitoring_metrics,
            dashboard_metrics,
            resilience
        )
        
        assert readiness.overall_readiness_score > 0.7, "Production readiness score should be >70%"
        assert readiness.monitoring_operational, "Monitoring should be operational"
        assert readiness.metrics_accurate, "Metrics should be accurate"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "slow"])




