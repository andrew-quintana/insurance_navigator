"""
Monitoring and Alerting System for Production Resilience

This module provides comprehensive monitoring, metrics collection, and alerting
capabilities for production deployment.
"""

import asyncio
import time
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"      # Monotonically increasing value
    GAUGE = "gauge"          # Current value that can go up or down
    HISTOGRAM = "histogram"  # Distribution of values
    TIMER = "timer"         # Time-based measurements

@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE

@dataclass
class Alert:
    """Alert information."""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: float
    source: str
    tags: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[float] = None

@dataclass
class HealthCheck:
    """Health check configuration."""
    name: str
    check_func: Callable
    interval: float = 60.0  # seconds
    timeout: float = 10.0   # seconds
    enabled: bool = True
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """Collects and stores system metrics."""
    
    def __init__(self, max_points: int = 10000):
        self.max_points = max_points
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self._lock = asyncio.Lock()
    
    async def record_metric(
        self, 
        name: str, 
        value: float, 
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric data point."""
        async with self._lock:
            point = MetricPoint(
                name=name,
                value=value,
                timestamp=time.time(),
                tags=tags or {},
                metric_type=metric_type
            )
            self._metrics[name].append(point)
    
    async def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        await self.record_metric(name, value, MetricType.COUNTER, tags)
    
    async def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        await self.record_metric(name, value, MetricType.GAUGE, tags)
    
    async def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timer metric."""
        await self.record_metric(name, duration, MetricType.TIMER, tags)
    
    async def get_metrics(self, name: str, since: Optional[float] = None) -> List[MetricPoint]:
        """Get metric points for a given metric name."""
        async with self._lock:
            points = list(self._metrics[name])
            if since:
                points = [p for p in points if p.timestamp >= since]
            return points
    
    async def get_latest_value(self, name: str) -> Optional[float]:
        """Get the latest value for a metric."""
        async with self._lock:
            points = self._metrics[name]
            if points:
                return points[-1].value
            return None
    
    async def get_average(self, name: str, duration: float = 300.0) -> Optional[float]:
        """Get average value over the specified duration (in seconds)."""
        since = time.time() - duration
        points = await self.get_metrics(name, since)
        if not points:
            return None
        return sum(p.value for p in points) / len(points)
    
    def get_all_metric_names(self) -> List[str]:
        """Get all metric names."""
        return list(self._metrics.keys())

class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self, max_alerts: int = 1000):
        self.max_alerts = max_alerts
        self._alerts: deque = deque(maxlen=max_alerts)
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_handlers: List[Callable] = []
        self._lock = asyncio.Lock()
    
    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add an alert handler function."""
        self._alert_handlers.append(handler)
    
    async def create_alert(
        self,
        alert_id: str,
        level: AlertLevel,
        title: str,
        message: str,
        source: str,
        tags: Optional[Dict[str, str]] = None
    ) -> Alert:
        """Create and fire an alert."""
        async with self._lock:
            alert = Alert(
                id=alert_id,
                level=level,
                title=title,
                message=message,
                timestamp=time.time(),
                source=source,
                tags=tags or {}
            )
            
            self._alerts.append(alert)
            self._active_alerts[alert_id] = alert
            
            # Fire alert handlers
            for handler in self._alert_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(alert)
                    else:
                        handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")
            
            logger.log(
                self._get_log_level(level),
                f"Alert created: {title} - {message} (source: {source})"
            )
            
            return alert
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert."""
        async with self._lock:
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = time.time()
                del self._active_alerts[alert_id]
                
                logger.info(f"Alert resolved: {alert.title} (id: {alert_id})")
                return True
            return False
    
    async def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Get all active alerts, optionally filtered by level."""
        async with self._lock:
            alerts = list(self._active_alerts.values())
            if level:
                alerts = [a for a in alerts if a.level == level]
            return alerts
    
    async def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        async with self._lock:
            return list(self._alerts)[-limit:]
    
    def _get_log_level(self, alert_level: AlertLevel) -> int:
        """Convert alert level to logging level."""
        mapping = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }
        return mapping.get(alert_level, logging.INFO)

class HealthMonitor:
    """Monitors system health and triggers alerts."""
    
    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager):
        self.metrics = metrics_collector
        self.alerts = alert_manager
        self._health_checks: Dict[str, HealthCheck] = {}
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._running = False
        self._lock = asyncio.Lock()
    
    def add_health_check(self, health_check: HealthCheck) -> None:
        """Add a health check."""
        self._health_checks[health_check.name] = health_check
        logger.info(f"Added health check: {health_check.name}")
    
    async def start_monitoring(self) -> None:
        """Start all health check monitoring tasks."""
        async with self._lock:
            if self._running:
                logger.warning("Health monitoring is already running")
                return
            
            self._running = True
            
            for name, health_check in self._health_checks.items():
                if health_check.enabled:
                    task = asyncio.create_task(self._monitor_health_check(health_check))
                    self._monitoring_tasks[name] = task
            
            logger.info(f"Started monitoring {len(self._monitoring_tasks)} health checks")
    
    async def stop_monitoring(self) -> None:
        """Stop all health check monitoring tasks."""
        async with self._lock:
            if not self._running:
                return
            
            self._running = False
            
            for task in self._monitoring_tasks.values():
                task.cancel()
            
            # Wait for tasks to complete
            if self._monitoring_tasks:
                await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
            
            self._monitoring_tasks.clear()
            logger.info("Stopped health monitoring")
    
    async def _monitor_health_check(self, health_check: HealthCheck) -> None:
        """Monitor a single health check."""
        logger.info(f"Starting health check monitoring: {health_check.name}")
        
        while self._running:
            try:
                start_time = time.time()
                
                # Execute health check with timeout
                if asyncio.iscoroutinefunction(health_check.check_func):
                    result = await asyncio.wait_for(
                        health_check.check_func(),
                        timeout=health_check.timeout
                    )
                else:
                    result = health_check.check_func()
                
                duration = time.time() - start_time
                
                # Record metrics
                await self.metrics.record_timer(
                    f"health_check.{health_check.name}.duration",
                    duration,
                    health_check.tags
                )
                
                if result:
                    await self.metrics.set_gauge(
                        f"health_check.{health_check.name}.status",
                        1.0,
                        health_check.tags
                    )
                    # Resolve any existing alert
                    await self.alerts.resolve_alert(f"health_check_{health_check.name}")
                else:
                    await self.metrics.set_gauge(
                        f"health_check.{health_check.name}.status",
                        0.0,
                        health_check.tags
                    )
                    # Create alert for failed health check
                    await self.alerts.create_alert(
                        f"health_check_{health_check.name}",
                        AlertLevel.ERROR,
                        f"Health Check Failed: {health_check.name}",
                        f"Health check '{health_check.name}' is failing",
                        "health_monitor",
                        health_check.tags
                    )
                
            except asyncio.TimeoutError:
                await self.metrics.set_gauge(
                    f"health_check.{health_check.name}.status",
                    0.0,
                    health_check.tags
                )
                await self.alerts.create_alert(
                    f"health_check_{health_check.name}_timeout",
                    AlertLevel.WARNING,
                    f"Health Check Timeout: {health_check.name}",
                    f"Health check '{health_check.name}' timed out after {health_check.timeout}s",
                    "health_monitor",
                    health_check.tags
                )
            except Exception as e:
                logger.error(f"Health check '{health_check.name}' failed with exception: {e}")
                await self.metrics.set_gauge(
                    f"health_check.{health_check.name}.status",
                    0.0,
                    health_check.tags
                )
                await self.alerts.create_alert(
                    f"health_check_{health_check.name}_error",
                    AlertLevel.ERROR,
                    f"Health Check Error: {health_check.name}",
                    f"Health check '{health_check.name}' failed with error: {str(e)}",
                    "health_monitor",
                    health_check.tags
                )
            
            # Wait for next check
            await asyncio.sleep(health_check.interval)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        status = {}
        
        for name, health_check in self._health_checks.items():
            latest_status = await self.metrics.get_latest_value(f"health_check.{name}.status")
            status[name] = {
                "healthy": latest_status == 1.0 if latest_status is not None else None,
                "enabled": health_check.enabled,
                "last_check": latest_status
            }
        
        return status

class SystemMonitor:
    """Main system monitoring orchestrator."""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()
        self.health = HealthMonitor(self.metrics, self.alerts)
        self._system_checks_registered = False
        
        # Add default alert handler for logging
        self.alerts.add_alert_handler(self._log_alert)
    
    async def _log_alert(self, alert: Alert) -> None:
        """Default alert handler that logs alerts."""
        level_map = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }
        logger.log(level_map.get(alert.level, logging.INFO), f"ALERT: {alert.title} - {alert.message}")
    
    def register_system_health_checks(self) -> None:
        """Register standard system health checks."""
        if self._system_checks_registered:
            return
        
        # Database health check
        async def check_database():
            try:
                from config.database import db_pool
                client = await db_pool.get_client()
                return client is not None
            except Exception:
                return False
        
        self.health.add_health_check(HealthCheck(
            name="database",
            check_func=check_database,
            interval=30.0,
            timeout=5.0,
            tags={"component": "database"}
        ))
        
        # RAG service health check
        async def check_rag_service():
            try:
                from agents.tooling.rag.core import RAGTool, RetrievalConfig
                config = RetrievalConfig(similarity_threshold=0.3)
                rag_tool = RAGTool("health_check", config)
                return rag_tool is not None
            except Exception:
                return False
        
        self.health.add_health_check(HealthCheck(
            name="rag_service",
            check_func=check_rag_service,
            interval=60.0,
            timeout=10.0,
            tags={"component": "rag"}
        ))
        
        # Memory usage health check
        def check_memory_usage():
            try:
                import psutil
                import os
                memory = psutil.virtual_memory()
                
                # Adjust threshold based on environment
                environment = os.getenv('ENVIRONMENT', 'development')
                if environment == 'development':
                    threshold = 95.0  # More lenient for development
                else:
                    threshold = 90.0  # Stricter for production
                
                return memory.percent < threshold
            except ImportError:
                return True  # Skip if psutil not available
        
        self.health.add_health_check(HealthCheck(
            name="memory_usage",
            check_func=check_memory_usage,
            interval=60.0,
            timeout=5.0,
            tags={"component": "system"}
        ))
        
        self._system_checks_registered = True
        logger.info("Registered system health checks")
    
    async def start(self) -> None:
        """Start the monitoring system."""
        self.register_system_health_checks()
        await self.health.start_monitoring()
        logger.info("System monitoring started")
    
    async def stop(self) -> None:
        """Stop the monitoring system."""
        await self.health.stop_monitoring()
        logger.info("System monitoring stopped")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        health_status = await self.health.get_health_status()
        active_alerts = await self.alerts.get_active_alerts()
        
        # Calculate overall health
        healthy_checks = sum(1 for status in health_status.values() if status.get("healthy", False))
        total_checks = len(health_status)
        overall_health = healthy_checks / total_checks if total_checks > 0 else 1.0
        
        return {
            "overall_health": overall_health,
            "status": "healthy" if overall_health >= 0.8 else "degraded" if overall_health >= 0.5 else "unhealthy",
            "health_checks": health_status,
            "active_alerts": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
            "timestamp": time.time()
        }

# Global system monitor instance
_system_monitor: Optional[SystemMonitor] = None

def get_system_monitor() -> SystemMonitor:
    """Get the global system monitor instance."""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor

# Context manager for timing operations
class MetricTimer:
    """Context manager for timing operations and recording metrics."""
    
    def __init__(self, metrics: MetricsCollector, metric_name: str, tags: Optional[Dict[str, str]] = None):
        self.metrics = metrics
        self.metric_name = metric_name
        self.tags = tags or {}
        self.start_time: Optional[float] = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            await self.metrics.record_timer(self.metric_name, duration, self.tags)

# Decorator for timing functions
def time_metric(metric_name: str, tags: Optional[Dict[str, str]] = None):
    """Decorator to time function execution and record as metric."""
    import functools
    
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            monitor = get_system_monitor()
            async with MetricTimer(monitor.metrics, metric_name, tags):
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use async context manager
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                # Record metric asynchronously in background
                monitor = get_system_monitor()
                asyncio.create_task(monitor.metrics.record_timer(metric_name, duration, tags or {}))
                return result
            except Exception:
                duration = time.time() - start_time
                monitor = get_system_monitor()
                asyncio.create_task(monitor.metrics.record_timer(metric_name, duration, tags or {}))
                raise
        
        if asyncio.iscoroutinefunction(func):
            # Use functools.wraps to preserve function signature for FastAPI
            return functools.wraps(func)(async_wrapper)
        else:
            # Use functools.wraps to preserve function signature for FastAPI
            return functools.wraps(func)(sync_wrapper)
    
    return decorator
