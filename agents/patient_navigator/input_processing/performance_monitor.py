"""Performance monitoring for the Input Processing Workflow.

This module provides comprehensive performance tracking, metrics collection,
and performance optimization insights for the input processing pipeline.
"""

import asyncio
import logging
import time
import psutil
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a specific operation."""
    
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Get operation duration in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def duration_ms(self) -> float:
        """Get operation duration in milliseconds."""
        return self.duration * 1000


@dataclass
class PerformanceStats:
    """Aggregated performance statistics."""
    
    operation_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    avg_duration: float = 0.0
    median_duration: float = 0.0
    p95_duration: float = 0.0
    p99_duration: float = 0.0
    success_rate: float = 0.0
    error_rate: float = 0.0
    last_updated: float = 0.0
    
    def update(self, metric: PerformanceMetrics) -> None:
        """Update statistics with a new metric."""
        self.total_calls += 1
        self.total_duration += metric.duration
        
        if metric.success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        
        # Update duration statistics
        self.min_duration = min(self.min_duration, metric.duration)
        self.max_duration = max(self.max_duration, metric.duration)
        
        # Update rates
        self.success_rate = self.successful_calls / self.total_calls
        self.error_rate = self.failed_calls / self.total_calls
        
        self.last_updated = time.time()
    
    def calculate_percentiles(self, durations: List[float]) -> None:
        """Calculate percentile statistics."""
        if not durations:
            return
        
        sorted_durations = sorted(durations)
        self.avg_duration = statistics.mean(durations)
        self.median_duration = statistics.median(durations)
        
        if len(sorted_durations) >= 20:  # Need at least 20 samples for percentiles
            self.p95_duration = sorted_durations[int(len(sorted_durations) * 0.95)]
            self.p99_duration = sorted_durations[int(len(sorted_durations) * 0.99)]


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self, max_history: int = 1000):
        """Initialize performance monitor.
        
        Args:
            max_history: Maximum number of metrics to keep in history
        """
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.stats: Dict[str, PerformanceStats] = defaultdict(lambda: PerformanceStats(""))
        self.start_time = time.time()
        
        # System resource tracking
        self.system_start_time = time.time()
        self.initial_cpu_percent = psutil.cpu_percent()
        self.initial_memory = psutil.virtual_memory()
        
        logger.info("Performance monitor initialized")
    
    @asynccontextmanager
    async def track_operation(self, operation_name: str, **metadata):
        """Context manager for tracking operation performance.
        
        Args:
            operation_name: Name of the operation to track
            **metadata: Additional metadata for the operation
            
        Yields:
            PerformanceMetrics object for manual updates
        """
        metric = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            metadata=metadata
        )
        
        try:
            yield metric
        except Exception as e:
            metric.success = False
            metric.error_message = str(e)
            raise
        finally:
            metric.end_time = time.time()
            self._record_metric(metric)
    
    def _record_metric(self, metric: PerformanceMetrics) -> None:
        """Record a performance metric."""
        # Add to history
        self.metrics_history.append(metric)
        
        # Update statistics
        if metric.operation_name not in self.stats:
            self.stats[metric.operation_name] = PerformanceStats(metric.operation_name)
        
        self.stats[metric.operation_name].update(metric)
        
        # Log performance information
        if metric.duration > 1.0:  # Log slow operations
            logger.warning(
                f"Slow operation detected: {metric.operation_name} "
                f"took {metric.duration:.2f}s"
            )
        
        logger.debug(
            f"Operation {metric.operation_name}: "
            f"{'SUCCESS' if metric.success else 'FAILED'} "
            f"in {metric.duration:.3f}s"
        )
    
    def get_operation_stats(self, operation_name: str) -> Optional[PerformanceStats]:
        """Get performance statistics for a specific operation."""
        return self.stats.get(operation_name)
    
    def get_all_stats(self) -> Dict[str, PerformanceStats]:
        """Get performance statistics for all operations."""
        return dict(self.stats)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system resource metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "uptime_seconds": time.time() - self.system_start_time
            }
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            return {}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        summary = {
            "monitor_uptime": time.time() - self.start_time,
            "total_operations": sum(stats.total_calls for stats in self.stats.values()),
            "operations": {}
        }
        
        # Calculate overall statistics
        all_durations = []
        for metric in self.metrics_history:
            all_durations.append(metric.duration)
        
        if all_durations:
            summary["overall"] = {
                "avg_duration": statistics.mean(all_durations),
                "median_duration": statistics.median(all_durations),
                "min_duration": min(all_durations),
                "max_duration": max(all_durations)
            }
        
        # Add operation-specific statistics
        for op_name, stats in self.stats.items():
            summary["operations"][op_name] = {
                "total_calls": stats.total_calls,
                "success_rate": stats.success_rate,
                "avg_duration": stats.avg_duration,
                "min_duration": stats.min_duration,
                "max_duration": stats.max_duration
            }
        
        # Add system metrics
        summary["system"] = self.get_system_metrics()
        
        return summary
    
    def get_slow_operations(self, threshold_seconds: float = 1.0) -> List[PerformanceMetrics]:
        """Get list of operations that exceeded the duration threshold."""
        return [
            metric for metric in self.metrics_history
            if metric.duration > threshold_seconds
        ]
    
    def get_error_summary(self) -> Dict[str, List[str]]:
        """Get summary of errors by operation."""
        errors = defaultdict(list)
        for metric in self.metrics_history:
            if not metric.success and metric.error_message:
                errors[metric.operation_name].append(metric.error_message)
        return dict(errors)
    
    def clear_history(self) -> None:
        """Clear performance metrics history."""
        cleared_count = len(self.metrics_history)
        self.metrics_history.clear()
        logger.info(f"Cleared {cleared_count} performance metrics from history")
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Export metrics in specified format.
        
        Args:
            format_type: Export format ("json" or "csv")
            
        Returns:
            Exported metrics string
        """
        if format_type.lower() == "csv":
            return self._export_csv()
        else:
            return self._export_json()
    
    def _export_csv(self) -> str:
        """Export metrics as CSV."""
        if not self.metrics_history:
            return ""
        
        # CSV header
        csv_lines = ["operation_name,start_time,end_time,duration,success,error_message"]
        
        # CSV data
        for metric in self.metrics_history:
            csv_lines.append(
                f"{metric.operation_name},"
                f"{metric.start_time},"
                f"{metric.end_time or ''},"
                f"{metric.duration},"
                f"{metric.success},"
                f"\"{metric.error_message or ''}\""
            )
        
        return "\n".join(csv_lines)
    
    def _export_json(self) -> str:
        """Export metrics as JSON."""
        import json
        
        metrics_data = []
        for metric in self.metrics_history:
            metrics_data.append({
                "operation_name": metric.operation_name,
                "start_time": metric.start_time,
                "end_time": metric.end_time,
                "duration": metric.duration,
                "success": metric.success,
                "error_message": metric.error_message,
                "metadata": metric.metadata
            })
        
        return json.dumps(metrics_data, indent=2)


class PerformanceDecorator:
    """Decorator for automatically tracking function performance."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: Optional[str] = None):
        """Initialize performance decorator.
        
        Args:
            monitor: PerformanceMonitor instance
            operation_name: Custom operation name (defaults to function name)
        """
        self.monitor = monitor
        self.operation_name = operation_name
    
    def __call__(self, func: Callable):
        """Decorate function with performance tracking."""
        operation_name = self.operation_name or func.__name__
        
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                async with self.monitor.track_operation(operation_name):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with self.monitor.track_operation(operation_name):
                    return func(*args, **kwargs)
            return sync_wrapper


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def track_performance(operation_name: Optional[str] = None):
    """Decorator for tracking function performance.
    
    Args:
        operation_name: Custom operation name (defaults to function name)
    """
    return PerformanceDecorator(performance_monitor, operation_name)


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return performance_monitor 