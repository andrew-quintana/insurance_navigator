"""
Alert Configuration System for Production Monitoring

This module provides comprehensive alert configuration and management
for production monitoring across all cloud services.
"""

import asyncio
import json
import logging
import smtplib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AlertThreshold:
    """Alert threshold configuration"""
    metric_name: str
    threshold_value: float
    comparison_operator: str  # ">", "<", ">=", "<=", "==", "!="
    severity: str  # "low", "medium", "high", "critical"
    duration_minutes: int = 5  # Duration before alert triggers
    cooldown_minutes: int = 30  # Cooldown period between alerts

@dataclass
class AlertRule:
    """Alert rule configuration"""
    rule_id: str
    name: str
    description: str
    thresholds: List[AlertThreshold]
    notification_channels: List[str]  # ["email", "slack", "sms"]
    escalation_policy: Optional[str] = None
    enabled: bool = True

@dataclass
class AlertEvent:
    """Alert event data"""
    alert_id: str
    rule_id: str
    severity: str
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    service: str
    resolved: bool = False

@dataclass
class NotificationResult:
    """Result of notification delivery"""
    channel: str
    success: bool
    error_message: Optional[str] = None
    delivery_time: Optional[datetime] = None

class AlertManager:
    """Manages alert rules and event processing"""
    
    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_history: List[AlertEvent] = []
        self.active_alerts: Dict[str, AlertEvent] = {}
        self.notification_handlers: Dict[str, Callable] = {}
        self.metric_history: Dict[str, List[tuple]] = {}  # metric_name -> [(timestamp, value)]
        
        # Register default notification handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default notification handlers"""
        self.notification_handlers['email'] = self._send_email_alert
        self.notification_handlers['slack'] = self._send_slack_alert
        self.notification_handlers['sms'] = self._send_sms_alert
        self.notification_handlers['log'] = self._log_alert
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.alert_rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_id: str):
        """Remove an alert rule"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
    
    def update_metric(self, metric_name: str, value: float, service: str = "unknown"):
        """Update metric value and check for alert conditions"""
        timestamp = datetime.now()
        
        # Store metric history
        if metric_name not in self.metric_history:
            self.metric_history[metric_name] = []
        
        self.metric_history[metric_name].append((timestamp, value))
        
        # Keep only last 1000 entries per metric
        if len(self.metric_history[metric_name]) > 1000:
            self.metric_history[metric_name] = self.metric_history[metric_name][-1000:]
        
        # Check alert rules
        await self._check_alert_conditions(metric_name, value, service, timestamp)
    
    async def _check_alert_conditions(self, metric_name: str, value: float, service: str, timestamp: datetime):
        """Check if metric value triggers any alert conditions"""
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            for threshold in rule.thresholds:
                if threshold.metric_name != metric_name:
                    continue
                
                # Check if threshold condition is met
                condition_met = self._evaluate_threshold(value, threshold)
                
                if condition_met:
                    # Check if alert is already active
                    alert_key = f"{rule_id}_{threshold.metric_name}"
                    
                    if alert_key not in self.active_alerts:
                        # Create new alert
                        alert = AlertEvent(
                            alert_id=f"{rule_id}_{timestamp.isoformat()}",
                            rule_id=rule_id,
                            severity=threshold.severity,
                            message=f"{rule.name}: {metric_name} {threshold.comparison_operator} {threshold.threshold_value} (current: {value})",
                            metric_name=metric_name,
                            current_value=value,
                            threshold_value=threshold.threshold_value,
                            timestamp=timestamp,
                            service=service
                        )
                        
                        self.active_alerts[alert_key] = alert
                        self.alert_history.append(alert)
                        
                        # Send notifications
                        await self._send_notifications(alert, rule)
                        
                        logger.warning(f"Alert triggered: {alert.message}")
                else:
                    # Check if we should resolve an active alert
                    alert_key = f"{rule_id}_{threshold.metric_name}"
                    if alert_key in self.active_alerts:
                        alert = self.active_alerts[alert_key]
                        alert.resolved = True
                        del self.active_alerts[alert_key]
                        
                        logger.info(f"Alert resolved: {alert.message}")
    
    def _evaluate_threshold(self, value: float, threshold: AlertThreshold) -> bool:
        """Evaluate if metric value meets threshold condition"""
        if threshold.comparison_operator == ">":
            return value > threshold.threshold_value
        elif threshold.comparison_operator == "<":
            return value < threshold.threshold_value
        elif threshold.comparison_operator == ">=":
            return value >= threshold.threshold_value
        elif threshold.comparison_operator == "<=":
            return value <= threshold.threshold_value
        elif threshold.comparison_operator == "==":
            return value == threshold.threshold_value
        elif threshold.comparison_operator == "!=":
            return value != threshold.threshold_value
        else:
            logger.error(f"Unknown comparison operator: {threshold.comparison_operator}")
            return False
    
    async def _send_notifications(self, alert: AlertEvent, rule: AlertRule):
        """Send notifications for an alert"""
        results = []
        
        for channel in rule.notification_channels:
            if channel in self.notification_handlers:
                try:
                    result = await self.notification_handlers[channel](alert, rule)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to send {channel} notification: {str(e)}")
                    results.append(NotificationResult(
                        channel=channel,
                        success=False,
                        error_message=str(e)
                    ))
            else:
                logger.warning(f"No handler registered for notification channel: {channel}")
        
        return results
    
    async def _send_email_alert(self, alert: AlertEvent, rule: AlertRule) -> NotificationResult:
        """Send email alert"""
        try:
            # Get email configuration from environment
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME', '')
            smtp_password = os.getenv('SMTP_PASSWORD', '')
            alert_email = os.getenv('ALERT_EMAIL', '')
            
            if not all([smtp_username, smtp_password, alert_email]):
                return NotificationResult(
                    channel='email',
                    success=False,
                    error_message='Email configuration incomplete'
                )
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = alert_email
            msg['Subject'] = f"[{alert.severity.upper()}] {rule.name}"
            
            body = f"""
Alert Details:
- Rule: {rule.name}
- Description: {rule.description}
- Severity: {alert.severity}
- Service: {alert.service}
- Metric: {alert.metric_name}
- Current Value: {alert.current_value}
- Threshold: {alert.threshold_value}
- Time: {alert.timestamp}
- Message: {alert.message}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_username, alert_email, text)
            server.quit()
            
            return NotificationResult(
                channel='email',
                success=True,
                delivery_time=datetime.now()
            )
            
        except Exception as e:
            return NotificationResult(
                channel='email',
                success=False,
                error_message=str(e)
            )
    
    async def _send_slack_alert(self, alert: AlertEvent, rule: AlertRule) -> NotificationResult:
        """Send Slack alert"""
        try:
            webhook_url = os.getenv('SLACK_WEBHOOK_URL', '')
            
            if not webhook_url:
                return NotificationResult(
                    channel='slack',
                    success=False,
                    error_message='Slack webhook URL not configured'
                )
            
            # Create Slack message
            color = {
                'low': '#36a64f',      # green
                'medium': '#ffaa00',   # yellow
                'high': '#ff6600',     # orange
                'critical': '#ff0000'  # red
            }.get(alert.severity, '#ff0000')
            
            payload = {
                'attachments': [{
                    'color': color,
                    'title': f"[{alert.severity.upper()}] {rule.name}",
                    'text': alert.message,
                    'fields': [
                        {'title': 'Service', 'value': alert.service, 'short': True},
                        {'title': 'Metric', 'value': alert.metric_name, 'short': True},
                        {'title': 'Current Value', 'value': str(alert.current_value), 'short': True},
                        {'title': 'Threshold', 'value': str(alert.threshold_value), 'short': True},
                        {'title': 'Time', 'value': alert.timestamp.isoformat(), 'short': False}
                    ],
                    'footer': 'Insurance Navigator Monitoring',
                    'ts': int(alert.timestamp.timestamp())
                }]
            }
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        return NotificationResult(
                            channel='slack',
                            success=True,
                            delivery_time=datetime.now()
                        )
                    else:
                        return NotificationResult(
                            channel='slack',
                            success=False,
                            error_message=f'HTTP {response.status}'
                        )
            
        except Exception as e:
            return NotificationResult(
                channel='slack',
                success=False,
                error_message=str(e)
            )
    
    async def _send_sms_alert(self, alert: AlertEvent, rule: AlertRule) -> NotificationResult:
        """Send SMS alert (simulated)"""
        try:
            # This is a simulated SMS implementation
            # In production, you would integrate with a service like Twilio
            phone_number = os.getenv('ALERT_PHONE_NUMBER', '')
            
            if not phone_number:
                return NotificationResult(
                    channel='sms',
                    success=False,
                    error_message='Phone number not configured'
                )
            
            # Simulate SMS sending
            await asyncio.sleep(0.1)
            
            logger.info(f"SMS Alert sent to {phone_number}: {alert.message}")
            
            return NotificationResult(
                channel='sms',
                success=True,
                delivery_time=datetime.now()
            )
            
        except Exception as e:
            return NotificationResult(
                channel='sms',
                success=False,
                error_message=str(e)
            )
    
    async def _log_alert(self, alert: AlertEvent, rule: AlertRule) -> NotificationResult:
        """Log alert to file"""
        try:
            log_entry = {
                'timestamp': alert.timestamp.isoformat(),
                'severity': alert.severity,
                'rule': rule.name,
                'service': alert.service,
                'metric': alert.metric_name,
                'value': alert.current_value,
                'threshold': alert.threshold_value,
                'message': alert.message
            }
            
            logger.warning(f"ALERT: {json.dumps(log_entry)}")
            
            return NotificationResult(
                channel='log',
                success=True,
                delivery_time=datetime.now()
            )
            
        except Exception as e:
            return NotificationResult(
                channel='log',
                success=False,
                error_message=str(e)
            )
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.alert_history)
        active_alerts = len(self.active_alerts)
        resolved_alerts = sum(1 for alert in self.alert_history if alert.resolved)
        
        severity_counts = {}
        for alert in self.alert_history:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'resolved_alerts': resolved_alerts,
            'severity_distribution': severity_counts,
            'alert_rules_count': len(self.alert_rules),
            'enabled_rules_count': sum(1 for rule in self.alert_rules.values() if rule.enabled)
        }

class ProductionAlertConfiguration:
    """Production alert configuration for Insurance Navigator"""
    
    def __init__(self):
        self.alert_manager = AlertManager()
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Set up default production alerts"""
        
        # Frontend Performance Alerts
        frontend_performance_rule = AlertRule(
            rule_id="frontend_performance",
            name="Frontend Performance Degradation",
            description="Alert when frontend performance degrades",
            thresholds=[
                AlertThreshold(
                    metric_name="page_load_time",
                    threshold_value=3.0,
                    comparison_operator=">",
                    severity="high",
                    duration_minutes=2
                ),
                AlertThreshold(
                    metric_name="api_response_time",
                    threshold_value=2.0,
                    comparison_operator=">",
                    severity="medium",
                    duration_minutes=3
                )
            ],
            notification_channels=["email", "slack"],
            escalation_policy="frontend_team"
        )
        
        # Backend Performance Alerts
        backend_performance_rule = AlertRule(
            rule_id="backend_performance",
            name="Backend Performance Issues",
            description="Alert when backend performance degrades",
            thresholds=[
                AlertThreshold(
                    metric_name="api_response_time",
                    threshold_value=2.0,
                    comparison_operator=">",
                    severity="high",
                    duration_minutes=2
                ),
                AlertThreshold(
                    metric_name="database_query_time",
                    threshold_value=0.5,
                    comparison_operator=">",
                    severity="medium",
                    duration_minutes=3
                )
            ],
            notification_channels=["email", "slack"],
            escalation_policy="backend_team"
        )
        
        # Error Rate Alerts
        error_rate_rule = AlertRule(
            rule_id="error_rate",
            name="High Error Rate",
            description="Alert when error rate exceeds threshold",
            thresholds=[
                AlertThreshold(
                    metric_name="error_rate",
                    threshold_value=1.0,
                    comparison_operator=">",
                    severity="critical",
                    duration_minutes=1
                ),
                AlertThreshold(
                    metric_name="4xx_error_rate",
                    threshold_value=5.0,
                    comparison_operator=">",
                    severity="medium",
                    duration_minutes=5
                )
            ],
            notification_channels=["email", "slack", "sms"],
            escalation_policy="oncall_engineer"
        )
        
        # Resource Usage Alerts
        resource_usage_rule = AlertRule(
            rule_id="resource_usage",
            name="High Resource Usage",
            description="Alert when resource usage is high",
            thresholds=[
                AlertThreshold(
                    metric_name="cpu_usage",
                    threshold_value=80.0,
                    comparison_operator=">",
                    severity="high",
                    duration_minutes=5
                ),
                AlertThreshold(
                    metric_name="memory_usage",
                    threshold_value=85.0,
                    comparison_operator=">",
                    severity="high",
                    duration_minutes=5
                )
            ],
            notification_channels=["email", "slack"],
            escalation_policy="infrastructure_team"
        )
        
        # Service Availability Alerts
        availability_rule = AlertRule(
            rule_id="service_availability",
            name="Service Availability Issues",
            description="Alert when service availability drops",
            thresholds=[
                AlertThreshold(
                    metric_name="service_availability",
                    threshold_value=99.0,
                    comparison_operator="<",
                    severity="critical",
                    duration_minutes=1
                )
            ],
            notification_channels=["email", "slack", "sms"],
            escalation_policy="oncall_engineer"
        )
        
        # Add all rules to alert manager
        self.alert_manager.add_alert_rule(frontend_performance_rule)
        self.alert_manager.add_alert_rule(backend_performance_rule)
        self.alert_manager.add_alert_rule(error_rate_rule)
        self.alert_manager.add_alert_rule(resource_usage_rule)
        self.alert_manager.add_alert_rule(availability_rule)
    
    async def test_alert_system(self) -> Dict[str, Any]:
        """Test the alert system with sample metrics"""
        logger.info("Testing alert system...")
        
        # Test metrics that should trigger alerts
        test_metrics = [
            ("page_load_time", 4.5, "frontend"),  # Should trigger high severity alert
            ("api_response_time", 2.5, "backend"),  # Should trigger high severity alert
            ("error_rate", 2.0, "api"),  # Should trigger critical alert
            ("cpu_usage", 85.0, "render"),  # Should trigger high severity alert
            ("service_availability", 98.5, "overall"),  # Should trigger critical alert
        ]
        
        # Update metrics to trigger alerts
        for metric_name, value, service in test_metrics:
            self.alert_manager.update_metric(metric_name, value, service)
            await asyncio.sleep(0.1)  # Small delay between updates
        
        # Wait for alert processing
        await asyncio.sleep(1.0)
        
        # Get statistics
        stats = self.alert_manager.get_alert_statistics()
        
        return {
            'test_completed': True,
            'alerts_triggered': stats['total_alerts'],
            'active_alerts': stats['active_alerts'],
            'severity_distribution': stats['severity_distribution'],
            'alert_rules_configured': stats['alert_rules_count']
        }

# Example usage
async def main():
    """Example usage of alert configuration system"""
    alert_config = ProductionAlertConfiguration()
    
    # Test the alert system
    test_results = await alert_config.test_alert_system()
    
    print("Alert System Test Results:")
    print(json.dumps(test_results, indent=2))
    
    # Get current statistics
    stats = alert_config.alert_manager.get_alert_statistics()
    print("\nAlert Statistics:")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
