#!/usr/bin/env python3
"""
Production Monitoring System for 003 Worker Refactor
Provides comprehensive monitoring, alerting, and incident response capabilities
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import httpx
import psutil
import yaml
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from shared.config import ProductionConfig
from shared.database import DatabaseManager
from shared.logging import setup_logging

console = Console()
logger = logging.getLogger(__name__)


class ProductionMonitor:
    """Production monitoring and alerting system"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.db_manager = DatabaseManager(self.config.database_url)
        self.alert_history = []
        self.incident_history = []
        self.metrics_history = []
        self.health_status = {}
        
    def _load_config(self) -> ProductionConfig:
        """Load production configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            return ProductionConfig(**config_data)
        except Exception as e:
            console.print(f"[red]Failed to load config: {e}[/red]")
            sys.exit(1)
    
    async def start_monitoring(self):
        """Start comprehensive production monitoring"""
        console.print("[bold blue]🚀 Starting Production Monitoring System[/bold blue]")
        
        try:
            # Initialize monitoring components
            await self._initialize_monitoring()
            
            # Start monitoring loops
            monitoring_tasks = [
                asyncio.create_task(self._monitor_system_health()),
                asyncio.create_task(self._monitor_application_health()),
                asyncio.create_task(self._monitor_database_health()),
                asyncio.create_task(self._monitor_external_services()),
                asyncio.create_task(self._monitor_performance_metrics()),
                asyncio.create_task(self._monitor_security_events()),
                asyncio.create_task(self._process_alerts()),
                asyncio.create_task(self._update_dashboard())
            ]
            
            # Wait for all monitoring tasks
            await asyncio.gather(*monitoring_tasks)
            
        except Exception as e:
            console.print(f"[red]❌ Monitoring failed: {e}[/red]")
            logger.error(f"Monitoring failed: {e}", exc_info=True)
            raise
    
    async def _initialize_monitoring(self):
        """Initialize monitoring components"""
        console.print("[bold]🔧 Initializing Monitoring Components[/bold]")
        
        # Initialize database connection
        await self.db_manager.connect()
        
        # Initialize health status
        self.health_status = {
            'system': 'unknown',
            'application': 'unknown',
            'database': 'unknown',
            'external_services': 'unknown',
            'performance': 'unknown',
            'security': 'unknown'
        }
        
        # Initialize metrics collection
        self.metrics_history = []
        
        console.print("[green]✅ Monitoring components initialized[/green]")
    
    async def _monitor_system_health(self):
        """Monitor system-level health metrics"""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                
                # Network I/O
                network = psutil.net_io_counters()
                
                # System metrics
                system_metrics = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'network_bytes_sent': network.bytes_sent,
                    'network_bytes_recv': network.bytes_recv
                }
                
                # Update health status
                if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                    self.health_status['system'] = 'critical'
                    await self._create_alert('SYSTEM_CRITICAL', f"System resources critical: CPU={cpu_percent}%, Memory={memory_percent}%, Disk={disk_percent}%")
                elif cpu_percent > 80 or memory_percent > 80 or disk_percent > 80:
                    self.health_status['system'] = 'warning'
                    await self._create_alert('SYSTEM_WARNING', f"System resources warning: CPU={cpu_percent}%, Memory={memory_percent}%, Disk={disk_percent}%")
                else:
                    self.health_status['system'] = 'healthy'
                
                # Store metrics
                self.metrics_history.append(system_metrics)
                
                # Keep only last 1000 metrics
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"System health monitoring failed: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_application_health(self):
        """Monitor application health and performance"""
        while True:
            try:
                # Check API server health
                api_health = await self._check_api_health()
                
                # Check worker health
                worker_health = await self._check_worker_health()
                
                # Check processing pipeline health
                pipeline_health = await self._check_pipeline_health()
                
                # Overall application health
                if api_health and worker_health and pipeline_health:
                    self.health_status['application'] = 'healthy'
                elif not api_health or not worker_health:
                    self.health_status['application'] = 'critical'
                    await self._create_alert('APPLICATION_CRITICAL', "Application health check failed")
                else:
                    self.health_status['application'] = 'warning'
                    await self._create_alert('APPLICATION_WARNING', "Application health degraded")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Application health monitoring failed: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_database_health(self):
        """Monitor database health and performance"""
        while True:
            try:
                # Check database connectivity
                db_connected = await self._check_database_connectivity()
                
                # Check database performance
                db_performance = await self._check_database_performance()
                
                # Check buffer table health
                buffer_health = await self._check_buffer_health()
                
                # Overall database health
                if db_connected and db_performance and buffer_health:
                    self.health_status['database'] = 'healthy'
                elif not db_connected:
                    self.health_status['database'] = 'critical'
                    await self._create_alert('DATABASE_CRITICAL', "Database connectivity failed")
                else:
                    self.health_status['database'] = 'warning'
                    await self._create_alert('DATABASE_WARNING', "Database performance degraded")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Database health monitoring failed: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_external_services(self):
        """Monitor external service health and performance"""
        while True:
            try:
                # Check LlamaIndex API
                llamaparse_health = await self._check_llamaparse_health()
                
                # Check OpenAI API
                openai_health = await self._check_openai_health()
                
                # Overall external services health
                if llamaparse_health and openai_health:
                    self.health_status['external_services'] = 'healthy'
                elif not llamaparse_health or not openai_health:
                    self.health_status['external_services'] = 'critical'
                    await self._create_alert('EXTERNAL_SERVICES_CRITICAL', "External service health check failed")
                else:
                    self.health_status['external_services'] = 'warning'
                    await self._create_alert('EXTERNAL_SERVICES_WARNING', "External service performance degraded")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"External services monitoring failed: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_performance_metrics(self):
        """Monitor application performance metrics"""
        while True:
            try:
                # Check job processing rates
                processing_metrics = await self._get_processing_metrics()
                
                # Check response times
                response_metrics = await self._get_response_metrics()
                
                # Check error rates
                error_metrics = await self._get_error_metrics()
                
                # Overall performance health
                if processing_metrics['success_rate'] > 95 and error_metrics['error_rate'] < 5:
                    self.health_status['performance'] = 'healthy'
                elif processing_metrics['success_rate'] < 90 or error_metrics['error_rate'] > 10:
                    self.health_status['performance'] = 'critical'
                    await self._create_alert('PERFORMANCE_CRITICAL', f"Performance degraded: Success rate={processing_metrics['success_rate']}%, Error rate={error_metrics['error_rate']}%")
                else:
                    self.health_status['performance'] = 'warning'
                    await self._create_alert('PERFORMANCE_WARNING', f"Performance warning: Success rate={processing_metrics['success_rate']}%, Error rate={error_metrics['error_rate']}%")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Performance monitoring failed: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_security_events(self):
        """Monitor security events and compliance"""
        while True:
            try:
                # Check authentication events
                auth_events = await self._get_authentication_events()
                
                # Check authorization events
                authz_events = await self._get_authorization_events()
                
                # Check data access events
                data_access_events = await self._get_data_access_events()
                
                # Overall security health
                if not auth_events['failures'] and not authz_events['failures']:
                    self.health_status['security'] = 'healthy'
                elif auth_events['failures'] > 10 or authz_events['failures'] > 5:
                    self.health_status['security'] = 'critical'
                    await self._create_alert('SECURITY_CRITICAL', f"Security events detected: Auth failures={auth_events['failures']}, Authz failures={authz_events['failures']}")
                else:
                    self.health_status['security'] = 'warning'
                    await self._create_alert('SECURITY_WARNING', f"Security warning: Auth failures={auth_events['failures']}, Authz failures={authz_events['failures']}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Security monitoring failed: {e}")
                await asyncio.sleep(300)
    
    async def _check_api_health(self) -> bool:
        """Check API server health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.api_url}/health",
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def _check_worker_health(self) -> bool:
        """Check worker health"""
        try:
            # Check worker process status
            # This would typically involve checking worker process health
            return True
        except Exception:
            return False
    
    async def _check_pipeline_health(self) -> bool:
        """Check processing pipeline health"""
        try:
            # Check recent job processing success
            query = """
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'complete' THEN 1 END) as successful_jobs,
                    COUNT(CASE WHEN status IN ('failed_parse', 'failed_chunking', 'failed_embedding') THEN 1 END) as failed_jobs
                FROM upload_jobs 
                WHERE created_at > NOW() - INTERVAL '1 hour'
            """
            
            result = await self.db_manager.execute_query(query)
            if result and len(result) > 0:
                row = result[0]
                total_jobs = row[0] or 0
                successful_jobs = row[1] or 0
                failed_jobs = row[2] or 0
                
                if total_jobs > 0:
                    success_rate = (successful_jobs / total_jobs) * 100
                    return success_rate > 90
                
            return True
        except Exception:
            return False
    
    async def _check_database_connectivity(self) -> bool:
        """Check database connectivity"""
        try:
            await self.db_manager.execute_query("SELECT 1")
            return True
        except Exception:
            return False
    
    async def _check_database_performance(self) -> bool:
        """Check database performance"""
        try:
            # Check query performance
            query = """
                SELECT 
                    AVG(EXTRACT(EPOCH FROM (query_end - query_start))) as avg_query_time
                FROM pg_stat_statements 
                WHERE query_start > NOW() - INTERVAL '1 hour'
            """
            
            result = await self.db_manager.execute_query(query)
            if result and len(result) > 0:
                avg_query_time = result[0][0] or 0
                return avg_query_time < 1.0  # Less than 1 second
            
            return True
        except Exception:
            return False
    
    async def _check_buffer_health(self) -> bool:
        """Check buffer table health"""
        try:
            # Check buffer table sizes
            query = """
                SELECT 
                    COUNT(*) as chunk_buffer_count,
                    COUNT(*) as vector_buffer_count
                FROM document_chunk_buffer, document_vector_buffer
            """
            
            result = await self.db_manager.execute_query(query)
            if result and len(result) > 0:
                chunk_buffer_count = result[0][0] or 0
                vector_buffer_count = result[0][1] or 0
                
                # Alert if buffers are too large
                if chunk_buffer_count > 1000 or vector_buffer_count > 1000:
                    await self._create_alert('BUFFER_WARNING', f"Buffer tables large: Chunk buffer={chunk_buffer_count}, Vector buffer={vector_buffer_count}")
                
                return True
            
            return True
        except Exception:
            return False
    
    async def _check_llamaparse_health(self) -> bool:
        """Check LlamaIndex API health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.llamaparse_api_url}/health",
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def _check_openai_health(self) -> bool:
        """Check OpenAI API health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.openai_api_url}/v1/embeddings",
                    headers={"Authorization": f"Bearer {self.config.openai_api_key}"},
                    json={"input": "test", "model": "text-embedding-3-small"},
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def _get_processing_metrics(self) -> Dict[str, Any]:
        """Get job processing metrics"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'complete' THEN 1 END) as successful_jobs,
                    COUNT(CASE WHEN status IN ('failed_parse', 'failed_chunking', 'failed_embedding') THEN 1 END) as failed_jobs,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_processing_time
                FROM upload_jobs 
                WHERE created_at > NOW() - INTERVAL '1 hour'
            """
            
            result = await self.db_manager.execute_query(query)
            if result and len(result) > 0:
                row = result[0]
                total_jobs = row[0] or 0
                successful_jobs = row[1] or 0
                failed_jobs = row[2] or 0
                avg_processing_time = row[3] or 0
                
                success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 100
                
                return {
                    'total_jobs': total_jobs,
                    'successful_jobs': successful_jobs,
                    'failed_jobs': failed_jobs,
                    'success_rate': success_rate,
                    'avg_processing_time': avg_processing_time
                }
            
            return {
                'total_jobs': 0,
                'successful_jobs': 0,
                'failed_jobs': 0,
                'success_rate': 100,
                'avg_processing_time': 0
            }
        except Exception:
            return {
                'total_jobs': 0,
                'successful_jobs': 0,
                'failed_jobs': 0,
                'success_rate': 0,
                'avg_processing_time': 0
            }
    
    async def _get_response_metrics(self) -> Dict[str, Any]:
        """Get API response time metrics"""
        # This would typically involve collecting response time metrics
        # For now, return placeholder data
        return {
            'avg_response_time': 0.1,
            'p95_response_time': 0.5,
            'p99_response_time': 1.0
        }
    
    async def _get_error_metrics(self) -> Dict[str, Any]:
        """Get error rate metrics"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_requests
                FROM api_requests 
                WHERE timestamp > NOW() - INTERVAL '1 hour'
            """
            
            result = await self.db_manager.execute_query(query)
            if result and len(result) > 0:
                row = result[0]
                total_requests = row[0] or 0
                error_requests = row[1] or 0
                
                error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
                
                return {
                    'total_requests': total_requests,
                    'error_requests': error_requests,
                    'error_rate': error_rate
                }
            
            return {
                'total_requests': 0,
                'error_requests': 0,
                'error_rate': 0
            }
        except Exception:
            return {
                'total_requests': 0,
                'error_requests': 0,
                'error_rate': 0
            }
    
    async def _get_authentication_events(self) -> Dict[str, int]:
        """Get authentication event metrics"""
        # This would typically involve collecting auth event metrics
        # For now, return placeholder data
        return {
            'total': 100,
            'successes': 95,
            'failures': 5
        }
    
    async def _get_authorization_events(self) -> Dict[str, int]:
        """Get authorization event metrics"""
        # This would typically involve collecting authz event metrics
        # For now, return placeholder data
        return {
            'total': 100,
            'successes': 98,
            'failures': 2
        }
    
    async def _get_data_access_events(self) -> Dict[str, int]:
        """Get data access event metrics"""
        # This would typically involve collecting data access metrics
        # For now, return placeholder data
        return {
            'total': 100,
            'successes': 100,
            'failures': 0
        }
    
    async def _create_alert(self, alert_type: str, message: str):
        """Create and store an alert"""
        alert = {
            'id': f"alert_{int(time.time())}",
            'type': alert_type,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': self._get_alert_severity(alert_type),
            'status': 'active'
        }
        
        self.alert_history.append(alert)
        
        # Keep only last 1000 alerts
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        # Log alert
        logger.warning(f"Alert created: {alert_type} - {message}")
        
        # Send notifications
        await self._send_alert_notifications(alert)
    
    def _get_alert_severity(self, alert_type: str) -> str:
        """Get alert severity based on type"""
        critical_types = [
            'SYSTEM_CRITICAL', 'APPLICATION_CRITICAL', 'DATABASE_CRITICAL',
            'EXTERNAL_SERVICES_CRITICAL', 'PERFORMANCE_CRITICAL', 'SECURITY_CRITICAL'
        ]
        
        warning_types = [
            'SYSTEM_WARNING', 'APPLICATION_WARNING', 'DATABASE_WARNING',
            'EXTERNAL_SERVICES_WARNING', 'PERFORMANCE_WARNING', 'SECURITY_WARNING',
            'BUFFER_WARNING'
        ]
        
        if alert_type in critical_types:
            return 'critical'
        elif alert_type in warning_types:
            return 'warning'
        else:
            return 'info'
    
    async def _send_alert_notifications(self, alert: Dict[str, Any]):
        """Send alert notifications"""
        try:
            # Send Slack notification
            if self.config.slack_webhook:
                await self._send_slack_notification(alert)
            
            # Send email notification
            if self.config.email_notifications:
                await self._send_email_notification(alert)
            
            # Send PagerDuty notification for critical alerts
            if alert['severity'] == 'critical' and self.config.pagerduty_integration_key:
                await self._send_pagerduty_notification(alert)
                
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")
    
    async def _send_slack_notification(self, alert: Dict[str, Any]):
        """Send Slack notification"""
        try:
            color = {
                'critical': '#ff0000',
                'warning': '#ffaa00',
                'info': '#0000ff'
            }.get(alert['severity'], '#000000')
            
            message = {
                "attachments": [{
                    "color": color,
                    "title": f"Alert: {alert['type']}",
                    "text": alert['message'],
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert['severity'].upper(),
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": alert['timestamp'],
                            "short": True
                        }
                    ]
                }]
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    self.config.slack_webhook,
                    json=message,
                    timeout=10.0
                )
                
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    async def _send_email_notification(self, alert: Dict[str, Any]):
        """Send email notification"""
        # This would typically involve sending email notifications
        # For now, just log the attempt
        logger.info(f"Email notification would be sent for alert: {alert['type']}")
    
    async def _send_pagerduty_notification(self, alert: Dict[str, Any]):
        """Send PagerDuty notification"""
        try:
            message = {
                "routing_key": self.config.pagerduty_integration_key,
                "event_action": "trigger",
                "payload": {
                    "summary": f"Critical Alert: {alert['type']}",
                    "severity": "critical",
                    "source": "production-monitor",
                    "custom_details": {
                        "message": alert['message'],
                        "timestamp": alert['timestamp']
                    }
                }
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=message,
                    timeout=10.0
                )
                
        except Exception as e:
            logger.error(f"Failed to send PagerDuty notification: {e}")
    
    async def _process_alerts(self):
        """Process and manage alerts"""
        while True:
            try:
                # Process active alerts
                active_alerts = [alert for alert in self.alert_history if alert['status'] == 'active']
                
                for alert in active_alerts:
                    # Check if alert should be escalated
                    if alert['severity'] == 'critical':
                        await self._escalate_alert(alert)
                    
                    # Check if alert should be resolved
                    if await self._should_resolve_alert(alert):
                        alert['status'] = 'resolved'
                        alert['resolved_at'] = datetime.utcnow().isoformat()
                
                await asyncio.sleep(60)  # Process every minute
                
            except Exception as e:
                logger.error(f"Alert processing failed: {e}")
                await asyncio.sleep(60)
    
    async def _escalate_alert(self, alert: Dict[str, Any]):
        """Escalate critical alert"""
        try:
            # Create incident if not exists
            incident = await self._get_or_create_incident(alert)
            
            # Update incident with alert
            if incident:
                incident['alerts'].append(alert)
                incident['last_updated'] = datetime.utcnow().isoformat()
                
                # Escalate if needed
                if len(incident['alerts']) >= 3:
                    incident['level'] = 'escalated'
                    await self._escalate_incident(incident)
                    
        except Exception as e:
            logger.error(f"Alert escalation failed: {e}")
    
    async def _get_or_create_incident(self, alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get or create incident for alert"""
        # Check if incident already exists for this alert type
        for incident in self.incident_history:
            if incident['type'] == alert['type'] and incident['status'] == 'active':
                return incident
        
        # Create new incident
        incident = {
            'id': f"incident_{int(time.time())}",
            'type': alert['type'],
            'status': 'active',
            'level': 'normal',
            'alerts': [alert],
            'created_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        self.incident_history.append(incident)
        
        # Keep only last 100 incidents
        if len(self.incident_history) > 100:
            self.incident_history = self.incident_history[-100:]
        
        return incident
    
    async def _escalate_incident(self, incident: Dict[str, Any]):
        """Escalate incident to next level"""
        try:
            # Send escalation notifications
            if incident['level'] == 'escalated':
                await self._send_escalation_notification(incident)
                
        except Exception as e:
            logger.error(f"Incident escalation failed: {e}")
    
    async def _send_escalation_notification(self, incident: Dict[str, Any]):
        """Send escalation notification"""
        try:
            # Send to management
            escalation_message = f"Incident {incident['id']} has been escalated: {incident['type']}"
            
            if self.config.slack_webhook:
                await self._send_slack_notification({
                    'type': 'INCIDENT_ESCALATED',
                    'message': escalation_message,
                    'severity': 'critical',
                    'timestamp': datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Escalation notification failed: {e}")
    
    async def _should_resolve_alert(self, alert: Dict[str, Any]) -> bool:
        """Check if alert should be resolved"""
        try:
            # Resolve if alert is older than 1 hour
            alert_time = datetime.fromisoformat(alert['timestamp'])
            if datetime.utcnow() - alert_time > timedelta(hours=1):
                return True
            
            # Resolve if underlying issue is fixed
            if alert['type'] == 'SYSTEM_CRITICAL' and self.health_status['system'] == 'healthy':
                return True
            elif alert['type'] == 'APPLICATION_CRITICAL' and self.health_status['application'] == 'healthy':
                return True
            elif alert['type'] == 'DATABASE_CRITICAL' and self.health_status['database'] == 'healthy':
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _update_dashboard(self):
        """Update monitoring dashboard"""
        while True:
            try:
                # Create dashboard content
                dashboard = self._create_dashboard()
                
                # Display dashboard
                console.clear()
                console.print(dashboard)
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Dashboard update failed: {e}")
                await asyncio.sleep(5)
    
    def _create_dashboard(self) -> Panel:
        """Create monitoring dashboard"""
        # Health status table
        health_table = Table(title="System Health Status")
        health_table.add_column("Component", style="cyan")
        health_table.add_column("Status", style="green")
        health_table.add_column("Last Updated", style="yellow")
        
        for component, status in self.health_status.items():
            status_style = {
                'healthy': 'green',
                'warning': 'yellow',
                'critical': 'red',
                'unknown': 'white'
            }.get(status, 'white')
            
            health_table.add_row(
                component.replace('_', ' ').title(),
                f"[{status_style}]{status.upper()}[/{status_style}]",
                datetime.utcnow().strftime("%H:%M:%S")
            )
        
        # Recent alerts table
        alerts_table = Table(title="Recent Alerts")
        alerts_table.add_column("Time", style="cyan")
        alerts_table.add_column("Type", style="yellow")
        alerts_table.add_column("Message", style="white")
        alerts_table.add_column("Severity", style="red")
        
        recent_alerts = self.alert_history[-10:]  # Last 10 alerts
        for alert in recent_alerts:
            severity_style = {
                'critical': 'red',
                'warning': 'yellow',
                'info': 'blue'
            }.get(alert['severity'], 'white')
            
            alerts_table.add_row(
                alert['timestamp'][11:19],  # Just time part
                alert['type'],
                alert['message'][:50] + "..." if len(alert['message']) > 50 else alert['message'],
                f"[{severity_style}]{alert['severity'].upper()}[/{severity_style}]"
            )
        
        # Metrics summary
        if self.metrics_history:
            latest_metrics = self.metrics_history[-1]
            metrics_text = f"""
            CPU: {latest_metrics['cpu_percent']:.1f}%
            Memory: {latest_metrics['memory_percent']:.1f}%
            Disk: {latest_metrics['disk_percent']:.1f}%
            """
        else:
            metrics_text = "No metrics available"
        
        metrics_panel = Panel(metrics_text, title="System Metrics", border_style="blue")
        
        # Combine all components
        dashboard_content = f"{health_table}\n\n{alerts_table}\n\n{metrics_panel}"
        
        return Panel(
            dashboard_content,
            title="🚀 Production Monitoring Dashboard",
            border_style="blue"
        )


async def main():
    """Main monitoring execution"""
    if len(sys.argv) != 2:
        console.print("[red]Usage: python production_monitor.py <config_path>[/red]")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    # Setup logging
    setup_logging()
    
    # Start monitoring
    monitor = ProductionMonitor(config_path)
    await monitor.start_monitoring()


if __name__ == "__main__":
    import sys
    asyncio.run(main())
