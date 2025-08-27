"""
Performance Monitor for Real API Integration

This module provides comprehensive performance monitoring for the integrated system
using real LlamaParse and OpenAI APIs, tracking key metrics and identifying
optimization opportunities.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric measurement."""
    operation: str
    duration: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class PerformanceSummary:
    """Summary of performance metrics for a specific operation."""
    operation: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_duration: float
    min_duration: float
    max_duration: float
    p95_duration: float
    p99_duration: float
    success_rate: float
    total_duration: float
    last_updated: datetime


class IntegrationPerformanceMonitor:
    """Comprehensive performance monitoring for integrated system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.summaries: Dict[str, PerformanceSummary] = {}
        self.alert_thresholds = {
            'upload_processing_time': config.get('UPLOAD_PROCESSING_TIMEOUT', 600) * 0.8,  # 80% of timeout
            'rag_query_time': config.get('AGENT_RESPONSE_TIMEOUT', 10) * 0.8,               # 80% of timeout
            'agent_response_time': config.get('AGENT_RESPONSE_TIMEOUT', 10) * 0.8,          # 80% of timeout
            'concurrent_operation_degradation': 0.2,  # 20% performance degradation threshold
            'api_error_rate': 0.05,                   # 5% error rate threshold
        }
        
        # Performance tracking windows
        self.tracking_window = timedelta(hours=1)  # 1-hour rolling window
        self.max_metrics_per_operation = 1000      # Keep last 1000 metrics per operation
        
        # Cost tracking
        self.cost_tracking = config.get('ENABLE_COST_MONITORING', True)
        self.total_cost = 0.0
        self.cost_by_service = defaultdict(float)
        self.cost_alert_threshold = config.get('COST_ALERT_THRESHOLD_USD', 10.00)
        
        # Alert tracking
        self.alerts: List[Dict[str, Any]] = []
        self.max_alerts = 100
    
    async def record_upload_processing_time(self, start_time: float, end_time: float, 
                                          document_id: str, document_size: Optional[int] = None):
        """Record upload processing time for performance monitoring."""
        duration = end_time - start_time
        
        metric = PerformanceMetric(
            operation="upload_processing",
            duration=duration,
            timestamp=datetime.now(),
            metadata={
                'document_id': document_id,
                'document_size': document_size,
                'start_time': start_time,
                'end_time': end_time
            }
        )
        
        await self._add_metric(metric)
        
        # Check for performance alerts
        if duration > self.alert_thresholds['upload_processing_time']:
            await self._create_performance_alert(
                'upload_processing',
                f"Upload processing time {duration:.2f}s exceeds threshold {self.alert_thresholds['upload_processing_time']:.2f}s",
                'warning'
            )
    
    async def record_rag_query_performance(self, query_time: float, result_count: int, 
                                         query_type: str, user_id: str):
        """Record RAG query performance metrics."""
        metric = PerformanceMetric(
            operation="rag_query",
            duration=query_time,
            timestamp=datetime.now(),
            metadata={
                'result_count': result_count,
                'query_type': query_type,
                'user_id': user_id
            }
        )
        
        await self._add_metric(metric)
        
        # Check for performance alerts
        if query_time > self.alert_thresholds['rag_query_time']:
            await self._create_performance_alert(
                'rag_query',
                f"RAG query time {query_time:.2f}s exceeds threshold {self.alert_thresholds['rag_query_time']:.2f}s",
                'warning'
            )
    
    async def record_agent_response_time(self, response_time: float, agent_type: str, 
                                       user_id: str, query_complexity: str = "standard"):
        """Record agent response time metrics."""
        metric = PerformanceMetric(
            operation="agent_response",
            duration=response_time,
            timestamp=datetime.now(),
            metadata={
                'agent_type': agent_type,
                'user_id': user_id,
                'query_complexity': query_complexity
            }
        )
        
        await self._add_metric(metric)
        
        # Check for performance alerts
        if response_time > self.alert_thresholds['agent_response_time']:
            await self._create_performance_alert(
                'agent_response',
                f"Agent response time {response_time:.2f}s exceeds threshold {self.alert_thresholds['agent_response_time']:.2f}s",
                'warning'
            )
    
    async def record_concurrent_operation_performance(self, operation_type: str, 
                                                    sequential_time: float, 
                                                    concurrent_time: float,
                                                    concurrent_count: int):
        """Record concurrent operation performance for degradation analysis."""
        degradation = (concurrent_time - sequential_time) / sequential_time
        
        metric = PerformanceMetric(
            operation="concurrent_operation",
            duration=concurrent_time,
            timestamp=datetime.now(),
            metadata={
                'operation_type': operation_type,
                'sequential_time': sequential_time,
                'concurrent_time': concurrent_time,
                'concurrent_count': concurrent_count,
                'degradation_percentage': degradation * 100
            }
        )
        
        await self._add_metric(metric)
        
        # Check for performance degradation alerts
        if degradation > self.alert_thresholds['concurrent_operation_degradation']:
            await self._create_performance_alert(
                'concurrent_operation',
                f"Concurrent operation degradation {degradation*100:.1f}% exceeds threshold {self.alert_thresholds['concurrent_operation_degradation']*100:.1f}%",
                'warning'
            )
    
    async def record_api_error(self, service: str, error_type: str, error_message: str, 
                              retry_count: int = 0, cost_impact: float = 0.0):
        """Record API errors for monitoring and alerting."""
        metric = PerformanceMetric(
            operation=f"api_error_{service}",
            duration=0.0,  # Error metrics don't have duration
            timestamp=datetime.now(),
            metadata={
                'service': service,
                'error_type': error_type,
                'error_message': error_message,
                'retry_count': retry_count,
                'cost_impact': cost_impact
            },
            success=False,
            error_message=error_message
        )
        
        await self._add_metric(metric)
        
        # Track costs if applicable
        if self.cost_tracking and cost_impact > 0:
            self.total_cost += cost_impact
            self.cost_by_service[service] += cost_impact
            
            # Check for cost alerts
            if self.total_cost > self.cost_alert_threshold:
                await self._create_performance_alert(
                    'cost_monitoring',
                    f"Total API cost ${self.total_cost:.2f} exceeds threshold ${self.cost_alert_threshold:.2f}",
                    'critical'
                )
    
    async def record_database_performance(self, operation: str, duration: float, 
                                        query_type: str, rows_affected: Optional[int] = None):
        """Record database operation performance."""
        metric = PerformanceMetric(
            operation="database_operation",
            duration=duration,
            timestamp=datetime.now(),
            metadata={
                'query_type': query_type,
                'rows_affected': rows_affected
            }
        )
        
        await self._add_metric(metric)
    
    async def _add_metric(self, metric: PerformanceMetric):
        """Add a performance metric to the tracking system."""
        operation = metric.operation
        
        # Add to metrics list
        self.metrics[operation].append(metric)
        
        # Maintain rolling window and size limits
        cutoff_time = datetime.now() - self.tracking_window
        self.metrics[operation] = [
            m for m in self.metrics[operation] 
            if m.timestamp > cutoff_time
        ]
        
        # Limit total metrics per operation
        if len(self.metrics[operation]) > self.max_metrics_per_operation:
            self.metrics[operation] = self.metrics[operation][-self.max_metrics_per_operation:]
        
        # Update summary
        await self._update_summary(operation)
    
    async def _update_summary(self, operation: str):
        """Update performance summary for an operation."""
        if not self.metrics[operation]:
            return
        
        metrics = self.metrics[operation]
        successful_metrics = [m for m in metrics if m.success]
        failed_metrics = [m for m in metrics if not m.success]
        
        if successful_metrics:
            durations = [m.duration for m in successful_metrics]
            
            summary = PerformanceSummary(
                operation=operation,
                total_requests=len(metrics),
                successful_requests=len(successful_metrics),
                failed_requests=len(failed_metrics),
                average_duration=statistics.mean(durations),
                min_duration=min(durations),
                max_duration=max(durations),
                p95_duration=statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations),
                p99_duration=statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else max(durations),
                success_rate=len(successful_metrics) / len(metrics),
                total_duration=sum(durations),
                last_updated=datetime.now()
            )
            
            self.summaries[operation] = summary
    
    async def _create_performance_alert(self, operation: str, message: str, severity: str):
        """Create a performance alert."""
        alert = {
            'timestamp': datetime.now(),
            'operation': operation,
            'message': message,
            'severity': severity,
            'threshold': self.alert_thresholds.get(operation, 'unknown')
        }
        
        self.alerts.append(alert)
        
        # Maintain alert list size
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # Log alert
        if severity == 'critical':
            logger.critical(f"Performance alert: {message}")
        elif severity == 'warning':
            logger.warning(f"Performance alert: {message}")
        else:
            logger.info(f"Performance alert: {message}")
    
    async def get_performance_summary(self) -> Dict[str, PerformanceSummary]:
        """Get comprehensive performance summary for all operations."""
        return dict(self.summaries)
    
    async def get_operation_summary(self, operation: str) -> Optional[PerformanceSummary]:
        """Get performance summary for a specific operation."""
        return self.summaries.get(operation)
    
    async def get_recent_metrics(self, operation: str, limit: int = 100) -> List[PerformanceMetric]:
        """Get recent performance metrics for an operation."""
        metrics = self.metrics.get(operation, [])
        return sorted(metrics, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    async def get_performance_alerts(self, severity: Optional[str] = None, 
                                   since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get performance alerts with optional filtering."""
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        
        if since:
            alerts = [a for a in alerts if a['timestamp'] > since]
        
        return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
    
    async def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for API usage."""
        if not self.cost_tracking:
            return {'cost_tracking_enabled': False}
        
        return {
            'cost_tracking_enabled': True,
            'total_cost': self.total_cost,
            'cost_by_service': dict(self.cost_by_service),
            'cost_alert_threshold': self.cost_alert_threshold,
            'cost_status': 'alert' if self.total_cost > self.cost_alert_threshold else 'normal'
        }
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            'timestamp': datetime.now(),
            'performance_summaries': {},
            'recent_alerts': await self.get_performance_alerts(limit=10),
            'cost_summary': await self.get_cost_summary(),
            'system_health': await self._assess_system_health()
        }
        
        # Add performance summaries
        for operation, summary in self.summaries.items():
            report['performance_summaries'][operation] = {
                'total_requests': summary.total_requests,
                'success_rate': summary.success_rate,
                'average_duration': summary.average_duration,
                'p95_duration': summary.p95_duration,
                'last_updated': summary.last_updated.isoformat()
            }
        
        return report
    
    async def _assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health based on performance metrics."""
        health_status = 'healthy'
        issues = []
        
        # Check success rates
        for operation, summary in self.summaries.items():
            if summary.success_rate < (1 - self.alert_thresholds['api_error_rate']):
                health_status = 'degraded'
                issues.append(f"Low success rate for {operation}: {summary.success_rate:.1%}")
        
        # Check performance thresholds
        for operation, summary in self.summaries.items():
            if operation == 'upload_processing' and summary.average_duration > self.alert_thresholds['upload_processing_time']:
                health_status = 'degraded'
                issues.append(f"Slow upload processing: {summary.average_duration:.2f}s average")
            elif operation == 'rag_query' and summary.average_duration > self.alert_thresholds['rag_query_time']:
                health_status = 'degraded'
                issues.append(f"Slow RAG queries: {summary.average_duration:.2f}s average")
            elif operation == 'agent_response' and summary.average_duration > self.alert_thresholds['agent_response_time']:
                health_status = 'degraded'
                issues.append(f"Slow agent responses: {summary.average_duration:.2f}s average")
        
        # Check cost status
        cost_summary = await self.get_cost_summary()
        if cost_summary.get('cost_status') == 'alert':
            health_status = 'critical'
            issues.append(f"High API costs: ${cost_summary.get('total_cost', 0):.2f}")
        
        return {
            'status': health_status,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }
    
    async def reset_metrics(self):
        """Reset all performance metrics (useful for testing)."""
        self.metrics.clear()
        self.summaries.clear()
        self.alerts.clear()
        self.total_cost = 0.0
        self.cost_by_service.clear()
        logger.info("Performance metrics reset")
    
    async def export_metrics(self, format: str = 'json') -> str:
        """Export performance metrics in specified format."""
        if format.lower() == 'json':
            import json
            return json.dumps(await self.get_performance_report(), default=str, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
