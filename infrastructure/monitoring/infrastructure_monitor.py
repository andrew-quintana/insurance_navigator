#!/usr/bin/env python3
"""
Infrastructure Monitor for 003 Worker Refactor - Phase 5

This module provides comprehensive monitoring and health checking for deployed
infrastructure, ensuring rapid detection of issues and preventing silent failures
experienced in 002.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import httpx
import psycopg2
import yaml
from dataclasses import dataclass, asdict

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.deployment.automated_rollback import AutomatedRollback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceHealth:
    """Health status of a service"""
    service_name: str
    status: str  # healthy, unhealthy, unknown
    response_time_ms: float
    last_check: datetime
    consecutive_failures: int
    uptime_percentage: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['last_check'] = self.last_check.isoformat()
        return result


@dataclass
class PerformanceMetric:
    """Performance metric for a service"""
    service_name: str
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    threshold: Optional[float] = None
    alert_level: str = "info"  # info, warning, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class Alert:
    """Alert for infrastructure issues"""
    alert_id: str
    severity: str  # info, warning, critical
    service: str
    message: str
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        if self.acknowledged_at:
            result['acknowledged_at'] = self.acknowledged_at.isoformat()
        if self.resolved_at:
            result['resolved_at'] = self.resolved_at.isoformat()
        return result


class InfrastructureMonitor:
    """
    Comprehensive infrastructure monitoring and health checking
    
    Provides real-time monitoring, performance tracking, and alerting
    to prevent silent failures experienced in 002.
    """
    
    def __init__(self, config_path: str, rollback_system: Optional[AutomatedRollback] = None):
        """Initialize monitor with configuration"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.rollback_system = rollback_system
        
        # Monitoring state
        self.service_health: Dict[str, ServiceHealth] = {}
        self.performance_metrics: List[PerformanceMetric] = []
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        
        # HTTP client for health checks
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Monitoring configuration
        self.monitoring_config = self.config.get('monitoring', {})
        self.health_check_interval = self.monitoring_config.get('health_check_interval_seconds', 30)
        self.metrics_collection_interval = self.monitoring_config.get('metrics_collection_interval_seconds', 10)
        self.alert_thresholds = self.monitoring_config.get('alert_thresholds', {})
        
        # Monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        self.shutdown_event = asyncio.Event()
        
        logger.info(f"Initialized InfrastructureMonitor with config: {config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    async def start_monitoring(self):
        """Start comprehensive infrastructure monitoring"""
        logger.info("Starting infrastructure monitoring...")
        
        try:
            # Start monitoring tasks
            self.monitoring_tasks = [
                asyncio.create_task(self._health_monitoring_loop()),
                asyncio.create_task(self._performance_monitoring_loop()),
                asyncio.create_task(self._alert_processing_loop()),
                asyncio.create_task(self._metrics_cleanup_loop())
            ]
            
            logger.info("Infrastructure monitoring started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            raise
    
    async def stop_monitoring(self):
        """Stop infrastructure monitoring"""
        logger.info("Stopping infrastructure monitoring...")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        # Close HTTP client
        await self.http_client.aclose()
        
        logger.info("Infrastructure monitoring stopped")
    
    async def _health_monitoring_loop(self):
        """Main health monitoring loop"""
        while not self.shutdown_event.is_set():
            try:
                await self._check_all_services_health()
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring loop error: {e}")
                await asyncio.sleep(5)
    
    async def _performance_monitoring_loop(self):
        """Main performance monitoring loop"""
        while not self.shutdown_event.is_set():
            try:
                await self._collect_performance_metrics()
                await asyncio.sleep(self.metrics_collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring loop error: {e}")
                await asyncio.sleep(5)
    
    async def _alert_processing_loop(self):
        """Main alert processing loop"""
        while not self.shutdown_event.is_set():
            try:
                await self._process_alerts()
                await asyncio.sleep(10)  # Check alerts every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert processing loop error: {e}")
                await asyncio.sleep(5)
    
    async def _metrics_cleanup_loop(self):
        """Clean up old metrics and alerts"""
        while not self.shutdown_event.is_set():
            try:
                await self._cleanup_old_metrics()
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics cleanup loop error: {e}")
                await asyncio.sleep(60)
    
    async def _check_all_services_health(self):
        """Check health of all configured services"""
        services = self.config.get('services', {})
        
        for service_name, service_config in services.items():
            try:
                health_status = await self._check_service_health(service_name, service_config)
                self.service_health[service_name] = health_status
                
                # Check for health degradation
                await self._check_health_degradation(service_name, health_status)
                
            except Exception as e:
                logger.error(f"Failed to check health for {service_name}: {e}")
                
                # Mark service as unhealthy
                self.service_health[service_name] = ServiceHealth(
                    service_name=service_name,
                    status="unhealthy",
                    response_time_ms=0.0,
                    last_check=datetime.utcnow(),
                    consecutive_failures=1,
                    uptime_percentage=0.0,
                    error_message=str(e)
                )
    
    async def _check_service_health(self, service_name: str, service_config: Dict[str, Any]) -> ServiceHealth:
        """Check health of a specific service"""
        try:
            host = service_config.get('host', 'localhost')
            port = service_config.get('port', 8000)
            health_endpoint = service_config.get('health_endpoint', '/health')
            
            url = f"http://{host}:{port}{health_endpoint}"
            
            # Measure response time
            start_time = time.time()
            response = await self.http_client.get(url, timeout=10.0)
            response_time = (time.time() - start_time) * 1000
            
            # Determine health status
            if response.status_code == 200:
                status = "healthy"
                consecutive_failures = 0
                error_message = None
            else:
                status = "unhealthy"
                consecutive_failures = 1
                error_message = f"HTTP {response.status_code}"
            
            # Calculate uptime percentage
            current_health = self.service_health.get(service_name)
            if current_health and current_health.status == "healthy":
                consecutive_failures = 0
            else:
                consecutive_failures = (current_health.consecutive_failures if current_health else 0) + 1
            
            # Simple uptime calculation (can be enhanced with more sophisticated logic)
            uptime_percentage = 100.0 if status == "healthy" else 0.0
            
            return ServiceHealth(
                service_name=service_name,
                status=status,
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                consecutive_failures=consecutive_failures,
                uptime_percentage=uptime_percentage,
                error_message=error_message,
                details={
                    'status_code': response.status_code,
                    'response_time_ms': response_time,
                    'url': url
                }
            )
            
        except Exception as e:
            # Service is unhealthy
            current_health = self.service_health.get(service_name)
            consecutive_failures = (current_health.consecutive_failures if current_health else 0) + 1
            
            return ServiceHealth(
                service_name=service_name,
                status="unhealthy",
                response_time_ms=0.0,
                last_check=datetime.utcnow(),
                consecutive_failures=consecutive_failures,
                uptime_percentage=0.0,
                error_message=str(e)
            )
    
    async def _check_health_degradation(self, service_name: str, health_status: ServiceHealth):
        """Check for health degradation and trigger alerts"""
        # Check consecutive failures
        if health_status.consecutive_failures >= 3:
            await self._create_alert(
                severity="critical",
                service=service_name,
                message=f"Service {service_name} has {health_status.consecutive_failures} consecutive failures"
            )
        
        # Check response time degradation
        if health_status.status == "healthy" and health_status.response_time_ms > 1000:
            await self._create_alert(
                severity="warning",
                service=service_name,
                message=f"Service {service_name} has slow response time: {health_status.response_time_ms:.2f}ms"
            )
    
    async def _collect_performance_metrics(self):
        """Collect performance metrics from all services"""
        try:
            # Database performance metrics
            await self._collect_database_metrics()
            
            # API performance metrics
            await self._collect_api_metrics()
            
            # Storage performance metrics
            await self._collect_storage_metrics()
            
            # System resource metrics
            await self._collect_system_metrics()
            
        except Exception as e:
            logger.error(f"Performance metrics collection failed: {e}")
    
    async def _collect_database_metrics(self):
        """Collect database performance metrics"""
        try:
            db_config = self.config.get('database', {})
            if not db_config:
                return
            
            # Test database connection and query performance
            start_time = time.time()
            
            import psycopg2
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config.get('password', '')
            )
            
            connection_time = (time.time() - start_time) * 1000
            
            # Test simple query performance
            cursor = conn.cursor()
            start_time = time.time()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            query_time = (time.time() - start_time) * 1000
            
            cursor.close()
            conn.close()
            
            # Add metrics
            self.performance_metrics.extend([
                PerformanceMetric(
                    service_name="database",
                    metric_name="connection_time",
                    value=connection_time,
                    unit="ms",
                    timestamp=datetime.utcnow(),
                    threshold=100.0
                ),
                PerformanceMetric(
                    service_name="database",
                    metric_name="query_time",
                    value=query_time,
                    unit="ms",
                    timestamp=datetime.utcnow(),
                    threshold=50.0
                )
            ])
            
        except Exception as e:
            logger.warning(f"Database metrics collection failed: {e}")
    
    async def _collect_api_metrics(self):
        """Collect API performance metrics"""
        try:
            api_config = self.config['services'].get('api_server', {})
            if not api_config:
                return
            
            host = api_config.get('host', 'localhost')
            port = api_config.get('port', 8000)
            
            # Test API response time
            url = f"http://{host}:{port}/health"
            start_time = time.time()
            response = await self.http_client.get(url, timeout=10.0)
            response_time = (time.time() - start_time) * 1000
            
            self.performance_metrics.append(
                PerformanceMetric(
                    service_name="api_server",
                    metric_name="health_endpoint_response_time",
                    value=response_time,
                    unit="ms",
                    timestamp=datetime.utcnow(),
                    threshold=100.0
                )
            )
            
        except Exception as e:
            logger.warning(f"API metrics collection failed: {e}")
    
    async def _collect_storage_metrics(self):
        """Collect storage performance metrics"""
        try:
            storage_config = self.config['services'].get('supabase_storage', {})
            if not storage_config:
                return
            
            host = storage_config.get('host', 'localhost')
            port = storage_config.get('port', 5000)
            
            # Test storage response time
            url = f"http://{host}:{port}/health"
            start_time = time.time()
            response = await self.http_client.get(url, timeout=10.0)
            response_time = (time.time() - start_time) * 1000
            
            self.performance_metrics.append(
                PerformanceMetric(
                    service_name="supabase_storage",
                    metric_name="health_endpoint_response_time",
                    value=response_time,
                    unit="ms",
                    timestamp=datetime.utcnow(),
                    threshold=100.0
                )
            )
            
        except Exception as e:
            logger.warning(f"Storage metrics collection failed: {e}")
    
    async def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.performance_metrics.append(
                PerformanceMetric(
                    service_name="system",
                    metric_name="cpu_usage",
                    value=cpu_percent,
                    unit="%",
                    timestamp=datetime.utcnow(),
                    threshold=80.0
                )
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.performance_metrics.append(
                PerformanceMetric(
                    service_name="system",
                    metric_name="memory_usage",
                    value=memory_percent,
                    unit="%",
                    timestamp=datetime.utcnow(),
                    threshold=80.0
                )
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            self.performance_metrics.append(
                PerformanceMetric(
                    service_name="system",
                    metric_name="disk_usage",
                    value=disk_percent,
                    unit="%",
                    timestamp=datetime.utcnow(),
                    threshold=90.0
                )
            )
            
        except ImportError:
            logger.warning("psutil not available, skipping system metrics")
        except Exception as e:
            logger.warning(f"System metrics collection failed: {e}")
    
    async def _process_alerts(self):
        """Process active alerts and check for resolution"""
        current_time = datetime.utcnow()
        
        # Check for new alerts based on performance metrics
        await self._check_performance_alerts()
        
        # Check for resolved alerts
        resolved_alerts = []
        for alert in self.active_alerts:
            if alert.resolved:
                resolved_alerts.append(alert)
                alert.resolved_at = current_time
        
        # Move resolved alerts to history
        for alert in resolved_alerts:
            self.active_alerts.remove(alert)
            self.alert_history.append(alert)
        
        # Check for critical alerts that might trigger rollback
        if self.rollback_system:
            await self._check_rollback_triggers()
    
    async def _check_performance_alerts(self):
        """Check performance metrics for alert conditions"""
        current_time = datetime.utcnow()
        
        # Get recent metrics (last 5 minutes)
        cutoff_time = current_time - timedelta(minutes=5)
        recent_metrics = [
            m for m in self.performance_metrics
            if m.timestamp > cutoff_time
        ]
        
        for metric in recent_metrics:
            if metric.threshold and metric.value > metric.threshold:
                # Check if alert already exists
                existing_alert = next(
                    (a for a in self.active_alerts
                     if a.service == metric.service_name
                     and a.message.startswith(f"Performance threshold exceeded: {metric.metric_name}")),
                    None
                )
                
                if not existing_alert:
                    # Determine alert severity
                    if metric.value > metric.threshold * 2:
                        severity = "critical"
                    elif metric.value > metric.threshold * 1.5:
                        severity = "warning"
                    else:
                        severity = "info"
                    
                    await self._create_alert(
                        severity=severity,
                        service=metric.service_name,
                        message=f"Performance threshold exceeded: {metric.metric_name} = {metric.value:.2f}{metric.unit} (threshold: {metric.threshold:.2f}{metric.unit})"
                    )
    
    async def _check_rollback_triggers(self):
        """Check if rollback should be triggered"""
        if not self.rollback_system:
            return
        
        # Check for critical health issues
        critical_services = [
            service for service in self.service_health.values()
            if service.status == "unhealthy" and service.consecutive_failures >= 5
        ]
        
        if critical_services:
            await self._create_alert(
                severity="critical",
                service="infrastructure",
                message=f"Critical health issues detected: {len(critical_services)} services unhealthy"
            )
            
            # Trigger rollback check
            current_state = {
                'health_check_failures': len(critical_services),
                'service_startup_failure': True
            }
            
            if await self.rollback_system.check_rollback_triggers(current_state):
                logger.warning("Rollback triggers activated - initiating rollback")
                await self.rollback_system.execute_rollback(
                    "Critical health issues detected by monitoring system"
                )
    
    async def _create_alert(self, severity: str, service: str, message: str):
        """Create a new alert"""
        alert_id = f"alert_{int(time.time())}"
        
        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            service=service,
            message=message,
            timestamp=datetime.utcnow()
        )
        
        self.active_alerts.append(alert)
        
        # Log alert
        log_level = logging.ERROR if severity == "critical" else logging.WARNING
        logger.log(log_level, f"ALERT [{severity.upper()}] {service}: {message}")
        
        # For critical alerts, also print to console
        if severity == "critical":
            print(f"\n🚨 CRITICAL ALERT: {service}")
            print(f"   {message}")
            print(f"   Time: {alert.timestamp}")
            print()
    
    async def _cleanup_old_metrics(self):
        """Clean up old performance metrics and alerts"""
        current_time = datetime.utcnow()
        
        # Keep metrics for last 24 hours
        metrics_cutoff = current_time - timedelta(hours=24)
        self.performance_metrics = [
            m for m in self.performance_metrics
            if m.timestamp > metrics_cutoff
        ]
        
        # Keep alert history for last 7 days
        alerts_cutoff = current_time - timedelta(days=7)
        self.alert_history = [
            a for a in self.alert_history
            if a.timestamp > alerts_cutoff
        ]
        
        logger.debug(f"Cleaned up metrics and alerts. Metrics: {len(self.performance_metrics)}, Alerts: {len(self.alert_history)}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get summary of all service health"""
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_services': len(self.service_health),
            'healthy_services': len([s for s in self.service_health.values() if s.status == "healthy"]),
            'unhealthy_services': len([s for s in self.service_health.values() if s.status == "unhealthy"]),
            'overall_health': "healthy" if all(s.status == "healthy" for s in self.service_health.values()) else "unhealthy",
            'services': {name: health.to_dict() for name, health in self.service_health.items()}
        }
        
        return summary
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics"""
        if not self.performance_metrics:
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'total_metrics': 0,
                'services': {}
            }
        
        # Group metrics by service
        service_metrics = {}
        for metric in self.performance_metrics:
            if metric.service_name not in service_metrics:
                service_metrics[metric.service_name] = []
            service_metrics[metric.service_name].append(metric)
        
        # Calculate summary for each service
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_metrics': len(self.performance_metrics),
            'services': {}
        }
        
        for service_name, metrics in service_metrics.items():
            service_summary = {}
            for metric in metrics:
                if metric.metric_name not in service_summary:
                    service_summary[metric.metric_name] = {
                        'current': metric.value,
                        'unit': metric.unit,
                        'threshold': metric.threshold,
                        'alert_level': metric.alert_level
                    }
            
            summary['services'][service_name] = service_summary
        
        return summary
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """Get summary of active alerts"""
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'active_alerts': len(self.active_alerts),
            'alert_history': len(self.alert_history),
            'critical_alerts': len([a for a in self.active_alerts if a.severity == "critical"]),
            'warning_alerts': len([a for a in self.active_alerts if a.severity == "warning"]),
            'info_alerts': len([a for a in self.active_alerts if a.severity == "info"]),
            'active_alerts': [alert.to_dict() for alert in self.active_alerts]
        }
        
        return summary
    
    async def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'health_summary': self.get_health_summary(),
            'performance_summary': self.get_performance_summary(),
            'alerts_summary': self.get_alerts_summary(),
            'monitoring_status': {
                'active': not self.shutdown_event.is_set(),
                'health_check_interval': self.health_check_interval,
                'metrics_collection_interval': self.metrics_collection_interval
            }
        }
        
        return report
    
    async def save_monitoring_report(self, report: Dict[str, Any], output_path: str = None):
        """Save monitoring report to file"""
        if output_path is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = f"infrastructure/reports/monitoring_report_{timestamp}.json"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Monitoring report saved: {output_file}")
        return str(output_file)


async def main():
    """Main entry point for infrastructure monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Infrastructure Monitor")
    parser.add_argument("--config", default="infrastructure/config/deployment_config.yaml",
                       help="Path to deployment configuration file")
    parser.add_argument("--action", choices=["start", "status", "report"],
                       default="start", help="Action to perform")
    parser.add_argument("--output", help="Output path for monitoring report")
    
    args = parser.parse_args()
    
    try:
        # Initialize monitor
        monitor = InfrastructureMonitor(args.config)
        
        if args.action == "start":
            # Start monitoring
            await monitor.start_monitoring()
            
            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping infrastructure monitoring...")
                await monitor.stop_monitoring()
            
        elif args.action == "status":
            # Show current status
            health_summary = monitor.get_health_summary()
            alerts_summary = monitor.get_alerts_summary()
            
            print(f"\n📊 Infrastructure Monitoring Status")
            print(f"==================================")
            print(f"Overall Health: {health_summary['overall_health'].upper()}")
            print(f"Services: {health_summary['healthy_services']}/{health_summary['total_services']} healthy")
            print(f"Active Alerts: {alerts_summary['active_alerts']}")
            print(f"Critical Alerts: {alerts_summary['critical_alerts']}")
            
            if alerts_summary['active_alerts'] > 0:
                print(f"\n🚨 Active Alerts:")
                for alert in alerts_summary['active_alerts']:
                    print(f"  [{alert['severity'].upper()}] {alert['service']}: {alert['message']}")
            
        elif args.action == "report":
            # Generate and save report
            report = await monitor.generate_monitoring_report()
            output_file = await monitor.save_monitoring_report(report, args.output)
            
            print(f"\n📋 Monitoring Report Generated")
            print(f"==============================")
            print(f"Report saved to: {output_file}")
            print(f"Overall Health: {report['health_summary']['overall_health']}")
            print(f"Active Alerts: {report['alerts_summary']['active_alerts']}")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Infrastructure monitoring failed: {e}")
        print(f"\n❌ Infrastructure monitoring failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
