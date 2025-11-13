# Unit Tests for Concurrency Monitoring (FM-043 Fix #4)
# Tests the basic concurrency monitoring system

import pytest
import asyncio
import threading
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from agents.shared.monitoring.concurrency_monitor import ConcurrencyMonitor, ResourceMetrics, get_monitor


class TestConcurrencyMonitor:
    """Test basic concurrency monitoring system."""
    
    @pytest.fixture
    def monitor(self):
        """Create a monitor instance for testing."""
        return ConcurrencyMonitor(alert_threshold=0.8)
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initializes with correct settings."""
        assert monitor.alert_threshold == 0.8
        assert isinstance(monitor.start_time, datetime)
        assert monitor.semaphores == {}
        assert monitor.semaphore_limits == {}
        assert monitor.connection_pools == {}
        assert monitor.metrics_history == []
        assert monitor.alert_counts == {}
    
    def test_semaphore_registration(self, monitor):
        """Test registering semaphores for monitoring."""
        semaphore = asyncio.Semaphore(10)
        monitor.register_semaphore("test_semaphore", semaphore, 10)
        
        assert "test_semaphore" in monitor.semaphores
        assert monitor.semaphores["test_semaphore"] is semaphore
        assert monitor.semaphore_limits["test_semaphore"] == 10
    
    def test_connection_pool_registration(self, monitor):
        """Test registering connection pools for monitoring."""
        pool_info = {
            "status": "active",
            "size": 5,
            "max_size": 20,
            "idle_size": 2
        }
        
        monitor.register_connection_pool("test_pool", pool_info)
        assert "test_pool" in monitor.connection_pools
        assert monitor.connection_pools["test_pool"] == pool_info
    
    @pytest.mark.asyncio
    async def test_get_current_metrics(self, monitor):
        """Test collecting current resource metrics."""
        # Register a semaphore for testing
        semaphore = asyncio.Semaphore(10)
        monitor.register_semaphore("test_sem", semaphore, 10)
        
        # Register a connection pool for testing
        pool_info = {"size": 7, "max_size": 20}
        monitor.register_connection_pool("test_pool", pool_info)
        
        # Get current metrics
        metrics = await monitor.get_current_metrics()
        
        assert isinstance(metrics, ResourceMetrics)
        assert isinstance(metrics.timestamp, datetime)
        assert metrics.active_tasks >= 0
        assert metrics.thread_count > 0
        assert "test_sem" in metrics.semaphore_usage
        assert "test_pool" in metrics.connection_pool_usage
    
    @pytest.mark.asyncio
    async def test_semaphore_usage_calculation(self, monitor):
        """Test accurate semaphore usage calculation."""
        semaphore = asyncio.Semaphore(5)
        monitor.register_semaphore("usage_test", semaphore, 5)
        
        # Acquire some semaphore slots
        acquired_slots = []
        for i in range(3):
            await semaphore.acquire()
            acquired_slots.append(i)
        
        try:
            metrics = await monitor.get_current_metrics()
            
            # Should show 3 out of 5 slots used
            usage = metrics.semaphore_usage["usage_test"]
            assert usage == 3, f"Expected usage 3, got {usage}"
            
        finally:
            # Clean up: release all acquired slots
            for _ in acquired_slots:
                semaphore.release()
    
    @pytest.mark.asyncio
    async def test_resource_usage_alerts(self, monitor):
        """Test resource usage alerting at threshold."""
        # Create semaphore with high usage (above 80% threshold)
        semaphore = asyncio.Semaphore(5)
        monitor.register_semaphore("alert_test", semaphore, 5)
        
        # Acquire 4 out of 5 slots (80% usage - exactly at threshold)
        acquired_slots = []
        for i in range(4):
            await semaphore.acquire()
            acquired_slots.append(i)
        
        try:
            # Mock the logger to capture alert messages
            with patch.object(monitor.logger, 'warning') as mock_warning:
                await monitor.check_resource_usage()
                
                # Should trigger alert at 80% usage (4/5 = 0.8)
                mock_warning.assert_called()
                alert_calls = [call.args[0] for call in mock_warning.call_args_list]
                
                # Check that alert was logged
                alert_found = any("alert_test" in str(call) and "80.0%" in str(call) for call in alert_calls)
                assert alert_found, f"Expected alert for 80% usage, got calls: {alert_calls}"
                
        finally:
            # Clean up
            for _ in acquired_slots:
                semaphore.release()
    
    @pytest.mark.asyncio
    async def test_alert_counting(self, monitor):
        """Test that alerts are properly counted."""
        semaphore = asyncio.Semaphore(10)
        monitor.register_semaphore("count_test", semaphore, 10)
        
        # Acquire enough to trigger alerts (9 out of 10 = 90% > 80% threshold)
        acquired_slots = []
        for i in range(9):
            await semaphore.acquire()
            acquired_slots.append(i)
        
        try:
            # Trigger multiple alert checks
            await monitor.check_resource_usage()
            await monitor.check_resource_usage()
            await monitor.check_resource_usage()
            
            # Should have counted 3 alerts
            alert_count = monitor.alert_counts.get("semaphore_count_test", 0)
            assert alert_count == 3, f"Expected 3 alerts, got {alert_count}"
            
        finally:
            # Clean up
            for _ in acquired_slots:
                semaphore.release()
    
    @pytest.mark.asyncio
    async def test_metrics_history_management(self, monitor):
        """Test metrics history is properly managed."""
        # Generate multiple metrics entries
        for _ in range(5):
            await monitor.check_resource_usage()
        
        assert len(monitor.metrics_history) == 5
        
        # Verify metrics are ResourceMetrics instances
        for metric in monitor.metrics_history:
            assert isinstance(metric, ResourceMetrics)
            assert isinstance(metric.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_metrics_history_limit(self, monitor):
        """Test metrics history is limited to prevent memory growth."""
        # Mock metrics to quickly fill history beyond limit
        with patch.object(monitor, 'get_current_metrics') as mock_metrics:
            mock_metrics.return_value = ResourceMetrics(
                timestamp=datetime.now(),
                active_tasks=1,
                semaphore_usage={},
                connection_pool_usage={},
                thread_count=5
            )
            
            # Generate more than 100 metrics (the limit)
            for _ in range(150):
                await monitor.check_resource_usage()
            
            # Should be limited to 100 entries
            assert len(monitor.metrics_history) == 100
    
    @pytest.mark.asyncio
    async def test_status_logging(self, monitor):
        """Test status logging provides comprehensive information."""
        # Set up test semaphores and pools
        semaphore = asyncio.Semaphore(8)
        monitor.register_semaphore("status_test", semaphore, 10)
        
        pool_info = {"size": 15, "max_size": 20}
        monitor.register_connection_pool("status_pool", pool_info)
        
        # Acquire some semaphore slots and generate alerts
        acquired_slots = []
        for i in range(8):  # 80% usage
            await semaphore.acquire()
            acquired_slots.append(i)
        
        try:
            # Generate some alerts
            await monitor.check_resource_usage()
            
            # Mock logger to capture status output
            with patch.object(monitor.logger, 'info') as mock_info:
                await monitor.log_status()
                
                # Verify various status information was logged
                log_messages = [call.args[0] for call in mock_info.call_args_list]
                
                # Check for expected status elements
                status_elements = [
                    "Concurrency Status",
                    "Uptime:",
                    "Active async tasks:",
                    "Active threads:",
                    "Semaphore usage:",
                    "status_test:",
                    "Connection pool usage:",
                    "status_pool:"
                ]
                
                for element in status_elements:
                    found = any(element in msg for msg in log_messages)
                    assert found, f"Status element '{element}' not found in logs: {log_messages}"
                    
        finally:
            # Clean up
            for _ in acquired_slots:
                semaphore.release()
    
    def test_summary_statistics(self, monitor):
        """Test summary statistics calculation."""
        # Add some mock metrics to history
        for i in range(10):
            metric = ResourceMetrics(
                timestamp=datetime.now(),
                active_tasks=i + 5,  # 5-14
                semaphore_usage={},
                connection_pool_usage={},
                thread_count=i + 10  # 10-19
            )
            monitor.metrics_history.append(metric)
        
        # Add some alert counts
        monitor.alert_counts = {
            "semaphore_test": 3,
            "pool_test": 2
        }
        
        # Get summary stats
        summary = monitor.get_summary_stats()
        
        assert "uptime" in summary
        assert summary["total_alerts"] == 5
        assert summary["avg_active_tasks"] == 9.5  # Average of last 10: (5+14)/2 = 9.5
        assert summary["avg_thread_count"] == 14.5  # Average of last 10: (10+19)/2 = 14.5
        assert summary["metrics_collected"] == 10
    
    def test_summary_stats_no_metrics(self, monitor):
        """Test summary stats with no metrics available."""
        summary = monitor.get_summary_stats()
        assert summary["status"] == "no_metrics_available"
    
    @pytest.mark.asyncio
    async def test_connection_pool_high_usage_alerts(self, monitor):
        """Test alerts for high connection pool usage."""
        # Register pool with high usage (above basic threshold of 15)
        high_usage_pool = {"size": 18, "max_size": 20}
        monitor.register_connection_pool("high_usage_pool", high_usage_pool)
        
        with patch.object(monitor.logger, 'warning') as mock_warning:
            await monitor.check_resource_usage()
            
            # Should trigger alert for high connection usage
            mock_warning.assert_called()
            alert_calls = [call.args[0] for call in mock_warning.call_args_list]
            
            alert_found = any("high_usage_pool" in str(call) and "18 connections" in str(call) 
                             for call in alert_calls)
            assert alert_found, f"Expected connection pool alert, got: {alert_calls}"
    
    @pytest.mark.asyncio
    async def test_thread_count_alerts(self, monitor):
        """Test alerts for high thread count."""
        # Mock threading.active_count to return high value
        with patch('agents.shared.monitoring.concurrency_monitor.threading.active_count', return_value=25):
            with patch.object(monitor.logger, 'warning') as mock_warning:
                await monitor.check_resource_usage()
                
                # Should trigger alert for high thread count (> 20)
                mock_warning.assert_called()
                alert_calls = [call.args[0] for call in mock_warning.call_args_list]
                
                alert_found = any("High thread count" in str(call) and "25 threads" in str(call)
                                 for call in alert_calls)
                assert alert_found, f"Expected thread count alert, got: {alert_calls}"
    
    @pytest.mark.asyncio
    async def test_error_handling_in_metrics_collection(self, monitor):
        """Test error handling when metrics collection fails."""
        # Mock get_current_metrics to raise an exception
        with patch.object(monitor, 'get_current_metrics', side_effect=Exception("Metrics error")):
            with patch.object(monitor.logger, 'error') as mock_error:
                await monitor.check_resource_usage()
                
                # Should log error and continue
                mock_error.assert_called_with("Error checking resource usage: Metrics error")
    
    def test_global_monitor_singleton(self):
        """Test global monitor singleton behavior."""
        monitor1 = get_monitor()
        monitor2 = get_monitor()
        
        # Should return the same instance
        assert monitor1 is monitor2
        assert isinstance(monitor1, ConcurrencyMonitor)


class TestResourceMetrics:
    """Test ResourceMetrics data class."""
    
    def test_resource_metrics_creation(self):
        """Test ResourceMetrics can be created with all fields."""
        timestamp = datetime.now()
        metrics = ResourceMetrics(
            timestamp=timestamp,
            active_tasks=5,
            semaphore_usage={"sem1": 3, "sem2": 7},
            connection_pool_usage={"pool1": 10},
            thread_count=15
        )
        
        assert metrics.timestamp == timestamp
        assert metrics.active_tasks == 5
        assert metrics.semaphore_usage == {"sem1": 3, "sem2": 7}
        assert metrics.connection_pool_usage == {"pool1": 10}
        assert metrics.thread_count == 15


class TestMonitoringIntegration:
    """Test integration with monitoring in concurrent scenarios."""
    
    @pytest.mark.asyncio
    async def test_monitoring_during_concurrent_operations(self):
        """Test monitoring works correctly during concurrent operations."""
        monitor = ConcurrencyMonitor(alert_threshold=0.7)
        
        # Set up monitored resources
        semaphore = asyncio.Semaphore(10)
        monitor.register_semaphore("concurrent_test", semaphore, 10)
        
        operation_count = 0
        max_concurrent = 0
        current_concurrent = 0
        
        async def monitored_operation():
            nonlocal operation_count, max_concurrent, current_concurrent
            
            async with semaphore:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
                
                # Simulate work
                await asyncio.sleep(0.1)
                
                operation_count += 1
                current_concurrent -= 1
        
        # Start monitoring task
        monitoring_task = asyncio.create_task(monitor.start_monitoring(0.05))  # Fast monitoring
        
        try:
            # Run concurrent operations
            tasks = [monitored_operation() for _ in range(20)]
            await asyncio.gather(*tasks)
            
            # Let monitoring collect some data
            await asyncio.sleep(0.2)
            
            # Verify operations completed
            assert operation_count == 20
            assert max_concurrent <= 10  # Semaphore limit respected
            
            # Verify monitoring collected metrics
            assert len(monitor.metrics_history) > 0
            
            # Check that semaphore usage was tracked
            final_metrics = await monitor.get_current_metrics()
            assert "concurrent_test" in final_metrics.semaphore_usage
            
        finally:
            # Clean up monitoring task
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass