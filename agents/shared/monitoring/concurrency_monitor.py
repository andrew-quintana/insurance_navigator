# Basic Concurrency Monitoring System
# Addresses: FM-043 - Add basic resource usage monitoring with logging alerts

import logging
import asyncio
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import threading


@dataclass
class ResourceMetrics:
    """Represents resource usage metrics at a point in time."""
    timestamp: datetime
    active_tasks: int
    semaphore_usage: Dict[str, int]  # semaphore_name -> current_usage
    connection_pool_usage: Dict[str, int]  # pool_name -> active_connections
    thread_count: int


class ConcurrencyMonitor:
    """
    Basic concurrency monitoring with resource tracking and alerting.
    Provides real-time monitoring of semaphores, connection pools, and tasks.
    """
    
    def __init__(self, alert_threshold: float = 0.8):
        """
        Initialize the concurrency monitor.
        
        Args:
            alert_threshold: Percentage threshold (0.0-1.0) for resource usage alerts
        """
        self.alert_threshold = alert_threshold
        self.logger = logging.getLogger(__name__)
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        self.semaphore_limits: Dict[str, int] = {}
        self.connection_pools: Dict[str, Dict[str, Any]] = {}
        self.start_time = datetime.now()
        
        # Metrics tracking
        self.metrics_history: list = []
        self.alert_counts: Dict[str, int] = {}
        
        self.logger.info("ConcurrencyMonitor initialized with alert threshold: {:.1%}".format(alert_threshold))

    def register_semaphore(self, name: str, semaphore: asyncio.Semaphore, limit: int) -> None:
        """
        Register a semaphore for monitoring.
        
        Args:
            name: Unique name for the semaphore
            semaphore: The asyncio.Semaphore instance
            limit: Maximum allowed concurrent operations
        """
        self.semaphores[name] = semaphore
        self.semaphore_limits[name] = limit
        self.logger.info(f"Registered semaphore '{name}' with limit {limit}")

    def register_connection_pool(self, name: str, pool_info: Dict[str, Any]) -> None:
        """
        Register a connection pool for monitoring.
        
        Args:
            name: Unique name for the connection pool
            pool_info: Dictionary with pool status information
        """
        self.connection_pools[name] = pool_info
        self.logger.info(f"Registered connection pool '{name}'")

    async def get_current_metrics(self) -> ResourceMetrics:
        """
        Collect current resource usage metrics.
        
        Returns:
            ResourceMetrics object with current resource usage
        """
        try:
            # Get current running tasks
            current_task = asyncio.current_task()
            all_tasks = asyncio.all_tasks()
            active_tasks = len([t for t in all_tasks if not t.done()])
            
            # Get semaphore usage
            semaphore_usage = {}
            for name, semaphore in self.semaphores.items():
                limit = self.semaphore_limits[name]
                # Calculate current usage (limit - available)
                current_usage = limit - semaphore._value
                semaphore_usage[name] = current_usage
            
            # Get connection pool usage
            connection_pool_usage = {}
            for name, pool_info in self.connection_pools.items():
                if 'size' in pool_info:
                    connection_pool_usage[name] = pool_info['size']
            
            # Get thread count
            thread_count = threading.active_count()
            
            metrics = ResourceMetrics(
                timestamp=datetime.now(),
                active_tasks=active_tasks,
                semaphore_usage=semaphore_usage,
                connection_pool_usage=connection_pool_usage,
                thread_count=thread_count
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return ResourceMetrics(
                timestamp=datetime.now(),
                active_tasks=0,
                semaphore_usage={},
                connection_pool_usage={},
                thread_count=0
            )

    async def check_resource_usage(self) -> None:
        """
        Check current resource usage and log alerts if thresholds exceeded.
        """
        try:
            metrics = await self.get_current_metrics()
            alerts_triggered = []
            
            # Check semaphore usage
            for name, current_usage in metrics.semaphore_usage.items():
                if name in self.semaphore_limits:
                    limit = self.semaphore_limits[name]
                    usage_percentage = current_usage / limit if limit > 0 else 0
                    
                    if usage_percentage >= self.alert_threshold:
                        alert_msg = f"Semaphore '{name}' usage: {current_usage}/{limit} ({usage_percentage:.1%})"
                        alerts_triggered.append(alert_msg)
                        self.alert_counts[f"semaphore_{name}"] = self.alert_counts.get(f"semaphore_{name}", 0) + 1
            
            # Check connection pool usage (if we have limits)
            for name, current_usage in metrics.connection_pool_usage.items():
                # For now, just log usage without specific limits
                if current_usage > 15:  # Basic threshold for connection pools
                    alert_msg = f"Connection pool '{name}' high usage: {current_usage} connections"
                    alerts_triggered.append(alert_msg)
                    self.alert_counts[f"pool_{name}"] = self.alert_counts.get(f"pool_{name}", 0) + 1
            
            # Check thread count
            if metrics.thread_count > 20:  # Basic threshold for thread count
                alert_msg = f"High thread count: {metrics.thread_count} threads active"
                alerts_triggered.append(alert_msg)
                self.alert_counts["thread_count"] = self.alert_counts.get("thread_count", 0) + 1
            
            # Log alerts
            if alerts_triggered:
                self.logger.warning("Resource usage alerts:")
                for alert in alerts_triggered:
                    self.logger.warning(f"  - {alert}")
            
            # Store metrics for history
            self.metrics_history.append(metrics)
            
            # Keep only recent metrics (last 100 entries)
            if len(self.metrics_history) > 100:
                self.metrics_history = self.metrics_history[-100:]
                
        except Exception as e:
            self.logger.error(f"Error checking resource usage: {e}")

    async def log_status(self) -> None:
        """
        Log current concurrency status for debugging and monitoring.
        """
        try:
            metrics = await self.get_current_metrics()
            uptime = datetime.now() - self.start_time
            
            self.logger.info("=== Concurrency Status ===")
            self.logger.info(f"Uptime: {uptime}")
            self.logger.info(f"Active async tasks: {metrics.active_tasks}")
            self.logger.info(f"Active threads: {metrics.thread_count}")
            
            if metrics.semaphore_usage:
                self.logger.info("Semaphore usage:")
                for name, usage in metrics.semaphore_usage.items():
                    limit = self.semaphore_limits.get(name, 0)
                    percentage = (usage / limit * 100) if limit > 0 else 0
                    self.logger.info(f"  {name}: {usage}/{limit} ({percentage:.1f}%)")
            
            if metrics.connection_pool_usage:
                self.logger.info("Connection pool usage:")
                for name, usage in metrics.connection_pool_usage.items():
                    self.logger.info(f"  {name}: {usage} connections")
            
            if self.alert_counts:
                self.logger.info("Alert counts:")
                for alert_type, count in self.alert_counts.items():
                    self.logger.info(f"  {alert_type}: {count} alerts")
            
            self.logger.info("==========================")
            
        except Exception as e:
            self.logger.error(f"Error logging status: {e}")

    async def start_monitoring(self, interval_seconds: float = 30.0) -> None:
        """
        Start periodic monitoring of resources.
        
        Args:
            interval_seconds: How often to check resource usage
        """
        self.logger.info(f"Starting resource monitoring (interval: {interval_seconds}s)")
        
        while True:
            try:
                await self.check_resource_usage()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                self.logger.info("Resource monitoring stopped")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for the monitoring period.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.metrics_history:
            return {"status": "no_metrics_available"}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 metrics
        
        avg_tasks = sum(m.active_tasks for m in recent_metrics) / len(recent_metrics)
        avg_threads = sum(m.thread_count for m in recent_metrics) / len(recent_metrics)
        
        return {
            "uptime": str(datetime.now() - self.start_time),
            "total_alerts": sum(self.alert_counts.values()),
            "avg_active_tasks": round(avg_tasks, 1),
            "avg_thread_count": round(avg_threads, 1),
            "registered_semaphores": len(self.semaphores),
            "registered_pools": len(self.connection_pools),
            "metrics_collected": len(self.metrics_history)
        }


# Global monitor instance
_monitor: Optional[ConcurrencyMonitor] = None


def get_monitor() -> ConcurrencyMonitor:
    """
    Get the global concurrency monitor instance.
    
    Returns:
        ConcurrencyMonitor instance
    """
    global _monitor
    if _monitor is None:
        _monitor = ConcurrencyMonitor()
    return _monitor


async def start_background_monitoring(interval_seconds: float = 30.0) -> None:
    """
    Start background monitoring task.
    
    Args:
        interval_seconds: Monitoring interval in seconds
    """
    monitor = get_monitor()
    await monitor.start_monitoring(interval_seconds)