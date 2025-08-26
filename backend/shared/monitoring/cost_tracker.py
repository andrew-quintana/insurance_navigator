"""
Cost tracking system for external API usage monitoring and budget control.

This module provides comprehensive tracking of API usage costs, token consumption,
and budget enforcement to prevent accidental overruns during development and testing.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class UsageMetrics:
    """Usage metrics for a specific service and time period."""
    service_name: str
    request_count: int = 0
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    error_count: int = 0
    last_request: Optional[datetime] = None
    first_request: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class CostLimit:
    """Cost limit configuration for a service."""
    daily_limit_usd: float
    hourly_rate_limit: int
    alert_threshold_percent: float = 80.0
    
    def is_exceeded(self, current_cost: float, current_rate: int) -> bool:
        """Check if cost or rate limits are exceeded."""
        return (current_cost >= self.daily_limit_usd or 
                current_rate >= self.hourly_rate_limit)


class CostTracker:
    """
    Comprehensive cost tracking system for external API usage.
    
    Tracks daily and hourly usage, enforces budget limits, and provides
    detailed analytics for cost optimization and monitoring.
    """
    
    def __init__(self):
        # Usage tracking
        self.daily_metrics: Dict[str, Dict[str, UsageMetrics]] = defaultdict(dict)
        self.hourly_metrics: Dict[str, Dict[str, UsageMetrics]] = defaultdict(dict)
        
        # Cost limits configuration
        self.cost_limits: Dict[str, CostLimit] = {}
        
        # Alerting and monitoring
        self.alert_threshold_percent = 80.0
        self.alerts_sent: Dict[str, datetime] = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def configure_service_limits(self, service_name: str, daily_limit_usd: float, 
                                hourly_rate_limit: int, alert_threshold_percent: float = 80.0) -> None:
        """
        Configure cost limits for a specific service.
        
        Args:
            service_name: Name of the service (e.g., 'llamaparse', 'openai')
            daily_limit_usd: Daily cost limit in USD
            hourly_rate_limit: Maximum requests per hour
            alert_threshold_percent: Percentage of limit to trigger alerts
        """
        with self._lock:
            self.cost_limits[service_name] = CostLimit(
                daily_limit_usd=daily_limit_usd,
                hourly_rate_limit=hourly_rate_limit,
                alert_threshold_percent=alert_threshold_percent
            )
            logger.info(f"Configured cost limits for {service_name}: "
                       f"${daily_limit_usd}/day, {hourly_rate_limit}/hour")
    
    def record_request(self, service_name: str, cost_usd: float = 0.0, 
                      token_count: int = 0, success: bool = True) -> None:
        """
        Record a service request with cost and token information.
        
        Args:
            service_name: Name of the service
            cost_usd: Cost of the request in USD
            token_count: Number of tokens consumed
            success: Whether the request was successful
        """
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        hour_key = now.strftime("%Y-%m-%d-%H")
        
        with self._lock:
            # Update daily metrics
            if service_name not in self.daily_metrics[date_key]:
                self.daily_metrics[date_key][service_name] = UsageMetrics(
                    service_name=service_name,
                    first_request=now
                )
            
            daily_metric = self.daily_metrics[date_key][service_name]
            daily_metric.request_count += 1
            daily_metric.total_cost_usd += cost_usd
            daily_metric.total_tokens += token_count
            daily_metric.last_request = now
            
            if not success:
                daily_metric.error_count += 1
            
            # Update hourly metrics
            if service_name not in self.hourly_metrics[hour_key]:
                self.hourly_metrics[hour_key][service_name] = UsageMetrics(
                    service_name=service_name,
                    first_request=now
                )
            
            hourly_metric = self.hourly_metrics[hour_key][service_name]
            hourly_metric.request_count += 1
            hourly_metric.total_cost_usd += cost_usd
            hourly_metric.total_tokens += token_count
            hourly_metric.last_request = now
            
            if not success:
                hourly_metric.error_count += 1
        
        # Check limits and send alerts
        self._check_limits_and_alert(service_name, date_key, hour_key)
        
        logger.debug(f"Recorded {service_name} request: ${cost_usd:.6f}, {token_count} tokens")
    
    def check_cost_limit(self, service_name: str, estimated_cost_usd: float) -> bool:
        """
        Check if a request would exceed cost limits before execution.
        
        Args:
            service_name: Name of the service
            estimated_cost_usd: Estimated cost of the request
            
        Returns:
            bool: True if request is within limits, False otherwise
        """
        if service_name not in self.cost_limits:
            return True  # No limits configured
        
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        hour_key = now.strftime("%Y-%m-%d-%H")
        
        with self._lock:
            # Check daily limit
            daily_cost = 0.0
            if date_key in self.daily_metrics and service_name in self.daily_metrics[date_key]:
                daily_cost = self.daily_metrics[date_key][service_name].total_cost_usd
            
            if daily_cost + estimated_cost_usd > self.cost_limits[service_name].daily_limit_usd:
                logger.warning(f"Daily cost limit would be exceeded for {service_name}: "
                             f"${daily_cost:.6f} + ${estimated_cost_usd:.6f} > "
                             f"${self.cost_limits[service_name].daily_limit_usd:.6f}")
                return False
            
            # Check hourly rate limit
            hourly_requests = 0
            if hour_key in self.hourly_metrics and service_name in self.hourly_metrics[hour_key]:
                hourly_requests = self.hourly_metrics[hour_key][service_name].request_count
            
            if hourly_requests + 1 > self.cost_limits[service_name].hourly_rate_limit:
                logger.warning(f"Hourly rate limit would be exceeded for {service_name}: "
                             f"{hourly_requests} + 1 > {self.cost_limits[service_name].hourly_rate_limit}")
                return False
        
        return True
    
    def get_service_usage(self, service_name: str, days: int = 7) -> Dict[str, Any]:
        """
        Get usage statistics for a service over a specified period.
        
        Args:
            service_name: Name of the service
            days: Number of days to include in the report
            
        Returns:
            Dict containing usage statistics
        """
        now = datetime.utcnow()
        end_date = now.date()
        start_date = end_date - timedelta(days=days)
        
        total_requests = 0
        total_cost = 0.0
        total_tokens = 0
        total_errors = 0
        daily_breakdown = []
        
        with self._lock:
            current_date = start_date
            while current_date <= end_date:
                date_key = current_date.strftime("%Y-%m-%d")
                
                if date_key in self.daily_metrics and service_name in self.daily_metrics[date_key]:
                    daily_metric = self.daily_metrics[date_key][service_name]
                    total_requests += daily_metric.request_count
                    total_cost += daily_metric.total_cost_usd
                    total_tokens += daily_metric.total_tokens
                    total_errors += daily_metric.error_count
                    
                    daily_breakdown.append({
                        'date': date_key,
                        'requests': daily_metric.request_count,
                        'cost_usd': daily_metric.total_cost_usd,
                        'tokens': daily_metric.total_tokens,
                        'errors': daily_metric.error_count
                    })
                else:
                    daily_breakdown.append({
                        'date': date_key,
                        'requests': 0,
                        'cost_usd': 0.0,
                        'tokens': 0,
                        'errors': 0
                    })
                
                current_date += timedelta(days=1)
        
        return {
            'service_name': service_name,
            'period_days': days,
            'total_requests': total_requests,
            'total_cost_usd': total_cost,
            'total_tokens': total_tokens,
            'total_errors': total_errors,
            'average_cost_per_request': total_cost / total_requests if total_requests > 0 else 0.0,
            'error_rate_percent': (total_errors / total_requests * 100) if total_requests > 0 else 0.0,
            'daily_breakdown': daily_breakdown
        }
    
    def get_all_services_summary(self) -> Dict[str, Any]:
        """Get summary of all services usage."""
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        
        summary = {
            'date': date_key,
            'total_cost_usd': 0.0,
            'total_requests': 0,
            'total_tokens': 0,
            'services': {}
        }
        
        with self._lock:
            if date_key in self.daily_metrics:
                for service_name, metrics in self.daily_metrics[date_key].items():
                    summary['total_cost_usd'] += metrics.total_cost_usd
                    summary['total_requests'] += metrics.request_count
                    summary['total_tokens'] += metrics.total_tokens
                    
                    summary['services'][service_name] = {
                        'requests': metrics.request_count,
                        'cost_usd': metrics.total_cost_usd,
                        'tokens': metrics.total_tokens,
                        'errors': metrics.error_count
                    }
        
        return summary
    
    def get_daily_cost(self, service_name: str) -> float:
        """
        Get the current day's cost for a specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Current day's cost in USD
        """
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        
        with self._lock:
            if date_key in self.daily_metrics and service_name in self.daily_metrics[date_key]:
                return self.daily_metrics[date_key][service_name].total_cost_usd
            return 0.0
    
    def get_hourly_requests(self, service_name: str) -> int:
        """
        Get the current hour's request count for a specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Current hour's request count
        """
        now = datetime.utcnow()
        hour_key = now.strftime("%Y-%m-%d-%H")
        
        with self._lock:
            if hour_key in self.hourly_metrics and service_name in self.hourly_metrics[hour_key]:
                return self.hourly_metrics[hour_key][service_name].request_count
            return 0
    
    def get_cost_forecast(self, service_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Generate cost forecast based on current usage patterns.
        
        Args:
            service_name: Name of the service
            days: Number of days to forecast
            
        Returns:
            Dict containing cost forecast information
        """
        usage_data = self.get_service_usage(service_name, days=7)
        
        if usage_data['total_requests'] == 0:
            return {
                'service_name': service_name,
                'forecast_days': days,
                'estimated_total_cost': 0.0,
                'estimated_daily_cost': 0.0,
                'confidence': 'low',
                'reason': 'No usage data available'
            }
        
        # Calculate daily averages
        avg_daily_requests = usage_data['total_requests'] / 7
        avg_daily_cost = usage_data['total_cost_usd'] / 7
        
        # Simple linear projection
        forecast_total_cost = avg_daily_cost * days
        forecast_daily_cost = avg_daily_cost
        
        # Determine confidence level based on data consistency
        daily_costs = [day['cost_usd'] for day in usage_data['daily_breakdown']]
        cost_variance = max(daily_costs) - min(daily_costs) if daily_costs else 0
        
        if cost_variance < avg_daily_cost * 0.1:
            confidence = 'high'
        elif cost_variance < avg_daily_cost * 0.3:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'service_name': service_name,
            'forecast_days': days,
            'estimated_total_cost': forecast_total_cost,
            'estimated_daily_cost': forecast_daily_cost,
            'confidence': confidence,
            'current_daily_average': avg_daily_cost,
            'current_daily_requests': avg_daily_requests,
            'cost_variance': cost_variance
        }
    
    def _check_limits_and_alert(self, service_name: str, date_key: str, hour_key: str) -> None:
        """Check cost limits and send alerts if thresholds are exceeded."""
        if service_name not in self.cost_limits:
            return
        
        cost_limit = self.cost_limits[service_name]
        
        with self._lock:
            # Check daily cost threshold
            daily_cost = 0.0
            if date_key in self.daily_metrics and service_name in self.daily_metrics[date_key]:
                daily_cost = self.daily_metrics[date_key][service_name].total_cost_usd
            
            threshold_amount = cost_limit.daily_limit_usd * (cost_limit.alert_threshold_percent / 100.0)
            
            if daily_cost >= threshold_amount:
                alert_key = f"{service_name}_daily_{date_key}"
                if alert_key not in self.alerts_sent:
                    logger.warning(f"Daily cost threshold alert for {service_name}: "
                                 f"${daily_cost:.6f} >= ${threshold_amount:.6f} "
                                 f"({cost_limit.alert_threshold_percent}% of ${cost_limit.daily_limit_usd:.6f})")
                    self.alerts_sent[alert_key] = datetime.utcnow()
            
            # Check hourly rate threshold
            hourly_requests = 0
            if hour_key in self.hourly_metrics and service_name in self.hourly_metrics[hour_key]:
                hourly_requests = self.hourly_metrics[hour_key][service_name].request_count
            
            rate_threshold = cost_limit.hourly_rate_limit * (cost_limit.alert_threshold_percent / 100.0)
            
            if hourly_requests >= rate_threshold:
                alert_key = f"{service_name}_hourly_{hour_key}"
                if alert_key not in self.alerts_sent:
                    logger.warning(f"Hourly rate threshold alert for {service_name}: "
                                 f"{hourly_requests} >= {rate_threshold} "
                                 f"({cost_limit.alert_threshold_percent}% of {cost_limit.hourly_rate_limit})")
                    self.alerts_sent[alert_key] = datetime.utcnow()
    
    def _start_cleanup_task(self) -> None:
        """Start background cleanup task for old metrics."""
        def cleanup_old_metrics():
            while True:
                try:
                    self._cleanup_old_metrics()
                    # Run cleanup every hour
                    time.sleep(3600)
                except Exception as e:
                    logger.error(f"Cleanup task error: {e}")
                    time.sleep(300)  # Shorter sleep on error
        
        import time
        cleanup_thread = threading.Thread(target=cleanup_old_metrics, daemon=True)
        cleanup_thread.start()
        logger.info("Cost tracker cleanup task started")
    
    def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics to prevent memory bloat."""
        now = datetime.utcnow()
        cutoff_date = now - timedelta(days=30)
        cutoff_hour = now - timedelta(hours=24)
        
        with self._lock:
            # Clean up old daily metrics
            old_dates = [date_key for date_key in self.daily_metrics.keys() 
                        if datetime.strptime(date_key, "%Y-%m-%d").date() < cutoff_date.date()]
            for old_date in old_dates:
                del self.daily_metrics[old_date]
            
            # Clean up old hourly metrics
            old_hours = [hour_key for hour_key in self.hourly_metrics.keys() 
                        if datetime.strptime(hour_key, "%Y-%m-%d-%H", "%Y-%m-%d-%H") < cutoff_hour]
            for old_hour in old_hours:
                del self.hourly_metrics[old_hour]
            
            # Clean up old alerts
            old_alerts = [alert_key for alert_key, alert_time in self.alerts_sent.items() 
                         if alert_time < cutoff_date]
            for old_alert in old_alerts:
                del self.alerts_sent[old_alert]
        
        if old_dates or old_hours:
            logger.info(f"Cleaned up {len(old_dates)} old daily metrics, "
                       f"{len(old_hours)} old hourly metrics, {len(old_alerts)} old alerts")
    
    def export_metrics(self, format_type: str = "json") -> str:
        """
        Export metrics data in specified format.
        
        Args:
            format_type: Export format ('json' or 'csv')
            
        Returns:
            str: Exported metrics data
        """
        if format_type.lower() == "json":
            return json.dumps({
                'daily_metrics': dict(self.daily_metrics),
                'hourly_metrics': dict(self.hourly_metrics),
                'cost_limits': {name: asdict(limit) for name, limit in self.cost_limits.items()},
                'export_timestamp': datetime.utcnow().isoformat()
            }, default=str, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def reset_metrics(self, service_name: Optional[str] = None) -> None:
        """
        Reset metrics for a specific service or all services.
        
        Args:
            service_name: Name of the service to reset, or None for all services
        """
        with self._lock:
            if service_name is None:
                # Reset all metrics
                self.daily_metrics.clear()
                self.hourly_metrics.clear()
                self.alerts_sent.clear()
                logger.info("Reset all cost tracking metrics")
            else:
                # Reset specific service metrics
                for date_key in self.daily_metrics:
                    if service_name in self.daily_metrics[date_key]:
                        del self.daily_metrics[date_key][service_name]
                
                for hour_key in self.hourly_metrics:
                    if service_name in self.hourly_metrics[hour_key]:
                        del self.hourly_metrics[hour_key][service_name]
                
                # Remove service-specific alerts
                service_alerts = [key for key in self.alerts_sent.keys() 
                                if key.startswith(f"{service_name}_")]
                for alert_key in service_alerts:
                    del self.alerts_sent[alert_key]
                
                logger.info(f"Reset cost tracking metrics for service: {service_name}")


# Global cost tracker instance
_cost_tracker = None


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


def configure_default_limits() -> None:
    """Configure default cost limits for common services."""
    tracker = get_cost_tracker()
    
    # Default limits (can be overridden by environment variables)
    tracker.configure_service_limits(
        'llamaparse',
        daily_limit_usd=10.00,
        hourly_rate_limit=100,
        alert_threshold_percent=80.0
    )
    
    tracker.configure_service_limits(
        'openai',
        daily_limit_usd=20.00,
        hourly_rate_limit=1000,
        alert_threshold_percent=80.0
    )
    
    logger.info("Configured default cost limits for external services")
