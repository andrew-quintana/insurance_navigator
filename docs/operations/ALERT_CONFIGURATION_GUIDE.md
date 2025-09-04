# Alert Configuration and Testing Guide

## Overview

This guide provides comprehensive instructions for configuring and testing alert systems for the Insurance Navigator production environment. The alert system provides proactive monitoring and notification for critical system events.

---

## Prerequisites

### Required Access
- Admin access to notification services (email, Slack, SMS)
- Access to cloud service dashboards (Vercel, Render, Supabase)
- Configuration access to alert systems
- Test environment for alert validation

### Required Tools
- Email client for testing email alerts
- Slack workspace for testing Slack notifications
- SMS-capable phone for testing SMS alerts
- Browser for accessing cloud dashboards

---

## Part 1: Alert System Architecture

### 1.1 Alert Components

#### Alert Manager
- **Purpose**: Central alert management and processing
- **Location**: `backend/monitoring/alert_configuration.py`
- **Features**: Rule management, event processing, notification delivery

#### Alert Rules
- **Purpose**: Define alert conditions and thresholds
- **Types**: Performance, error rate, resource usage, availability
- **Configuration**: Thresholds, severity levels, notification channels

#### Notification Channels
- **Email**: SMTP-based email notifications
- **Slack**: Webhook-based Slack notifications
- **SMS**: Phone-based SMS notifications
- **Log**: File-based logging notifications

### 1.2 Alert Flow

```
Metric Update → Alert Manager → Rule Evaluation → Alert Generation → Notification Delivery
```

1. **Metric Update**: System metrics are updated in real-time
2. **Alert Manager**: Processes metrics and evaluates alert rules
3. **Rule Evaluation**: Checks if metric values meet alert conditions
4. **Alert Generation**: Creates alert events for triggered conditions
5. **Notification Delivery**: Sends notifications through configured channels

---

## Part 2: Alert Rule Configuration

### 2.1 Performance Alerts

#### Frontend Performance Alerts

**Page Load Time Alert**
```python
AlertThreshold(
    metric_name="page_load_time",
    threshold_value=3.0,
    comparison_operator=">",
    severity="high",
    duration_minutes=2,
    cooldown_minutes=30
)
```

**API Response Time Alert**
```python
AlertThreshold(
    metric_name="api_response_time",
    threshold_value=2.0,
    comparison_operator=">",
    severity="medium",
    duration_minutes=3,
    cooldown_minutes=15
)
```

**Core Web Vitals Alerts**
```python
# Largest Contentful Paint
AlertThreshold(
    metric_name="lcp",
    threshold_value=2.5,
    comparison_operator=">",
    severity="high",
    duration_minutes=2
)

# First Input Delay
AlertThreshold(
    metric_name="fid",
    threshold_value=100,
    comparison_operator=">",
    severity="medium",
    duration_minutes=2
)

# Cumulative Layout Shift
AlertThreshold(
    metric_name="cls",
    threshold_value=0.1,
    comparison_operator=">",
    severity="medium",
    duration_minutes=2
)
```

#### Backend Performance Alerts

**Database Query Time Alert**
```python
AlertThreshold(
    metric_name="database_query_time",
    threshold_value=0.5,
    comparison_operator=">",
    severity="medium",
    duration_minutes=3,
    cooldown_minutes=15
)
```

**Worker Processing Time Alert**
```python
AlertThreshold(
    metric_name="worker_processing_time",
    threshold_value=30.0,
    comparison_operator=">",
    severity="high",
    duration_minutes=5,
    cooldown_minutes=30
)
```

### 2.2 Error Rate Alerts

#### Application Error Rate Alert
```python
AlertThreshold(
    metric_name="error_rate",
    threshold_value=1.0,
    comparison_operator=">",
    severity="critical",
    duration_minutes=1,
    cooldown_minutes=15
)
```

#### HTTP Status Code Alerts
```python
# 4xx Client Errors
AlertThreshold(
    metric_name="4xx_error_rate",
    threshold_value=5.0,
    comparison_operator=">",
    severity="medium",
    duration_minutes=5,
    cooldown_minutes=15
)

# 5xx Server Errors
AlertThreshold(
    metric_name="5xx_error_rate",
    threshold_value=1.0,
    comparison_operator=">",
    severity="critical",
    duration_minutes=1,
    cooldown_minutes=15
)
```

### 2.3 Resource Usage Alerts

#### CPU Usage Alert
```python
AlertThreshold(
    metric_name="cpu_usage",
    threshold_value=80.0,
    comparison_operator=">",
    severity="high",
    duration_minutes=5,
    cooldown_minutes=30
)
```

#### Memory Usage Alert
```python
AlertThreshold(
    metric_name="memory_usage",
    threshold_value=85.0,
    comparison_operator=">",
    severity="high",
    duration_minutes=5,
    cooldown_minutes=30
)
```

#### Database Connection Alert
```python
AlertThreshold(
    metric_name="database_connections",
    threshold_value=80.0,
    comparison_operator=">",
    severity="high",
    duration_minutes=3,
    cooldown_minutes=15
)
```

### 2.4 Availability Alerts

#### Service Availability Alert
```python
AlertThreshold(
    metric_name="service_availability",
    threshold_value=99.0,
    comparison_operator="<",
    severity="critical",
    duration_minutes=1,
    cooldown_minutes=15
)
```

#### Health Check Failure Alert
```python
AlertThreshold(
    metric_name="health_check_failures",
    threshold_value=1.0,
    comparison_operator=">=",
    severity="critical",
    duration_minutes=1,
    cooldown_minutes=5
)
```

---

## Part 3: Notification Channel Configuration

### 3.1 Email Configuration

#### SMTP Settings
```bash
# Environment Variables
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
export ALERT_EMAIL=alerts@yourcompany.com
```

#### Email Alert Format
```html
Subject: [SEVERITY] Alert Name

Alert Details:
- Rule: Alert Rule Name
- Description: Alert Description
- Severity: high/medium/low/critical
- Service: Service Name
- Metric: Metric Name
- Current Value: 2.5
- Threshold: 2.0
- Time: 2025-09-03T16:30:00Z
- Message: Detailed alert message
```

#### Email Configuration Steps
1. **Set up SMTP credentials**:
   - Create app-specific password for Gmail
   - Configure SMTP server settings
   - Test SMTP connection

2. **Configure alert recipients**:
   - Add primary alert email addresses
   - Set up escalation email lists
   - Configure email distribution groups

3. **Test email delivery**:
   - Send test alerts
   - Verify email formatting
   - Check delivery times

### 3.2 Slack Configuration

#### Slack Webhook Setup
1. **Create Slack App**:
   - Go to [Slack API](https://api.slack.com/apps)
   - Create new app
   - Enable incoming webhooks

2. **Configure Webhook**:
   - Add webhook URL to environment variables
   - Set up webhook permissions
   - Test webhook delivery

#### Slack Alert Format
```json
{
  "attachments": [{
    "color": "#ff0000",
    "title": "[CRITICAL] High Error Rate",
    "text": "Error rate has exceeded threshold",
    "fields": [
      {"title": "Service", "value": "API", "short": true},
      {"title": "Metric", "value": "error_rate", "short": true},
      {"title": "Current Value", "value": "2.5%", "short": true},
      {"title": "Threshold", "value": "1.0%", "short": true},
      {"title": "Time", "value": "2025-09-03T16:30:00Z", "short": false}
    ],
    "footer": "Insurance Navigator Monitoring",
    "ts": 1693756200
  }]
}
```

#### Slack Configuration Steps
1. **Set up Slack workspace**:
   - Create dedicated alert channel
   - Configure channel permissions
   - Set up notification settings

2. **Configure webhook**:
   - Add webhook URL to environment
   - Test webhook delivery
   - Verify message formatting

3. **Test Slack notifications**:
   - Send test alerts
   - Check message formatting
   - Verify channel notifications

### 3.3 SMS Configuration

#### SMS Service Setup
```bash
# Environment Variables
export ALERT_PHONE_NUMBER=+1234567890
export SMS_SERVICE_PROVIDER=twilio
export TWILIO_ACCOUNT_SID=your_account_sid
export TWILIO_AUTH_TOKEN=your_auth_token
```

#### SMS Alert Format
```
[CRITICAL] Insurance Navigator Alert
Service: API
Metric: error_rate
Value: 2.5% (threshold: 1.0%)
Time: 2025-09-03 16:30:00 UTC
```

#### SMS Configuration Steps
1. **Set up SMS service**:
   - Choose SMS provider (Twilio, AWS SNS, etc.)
   - Configure API credentials
   - Set up phone number routing

2. **Configure alert recipients**:
   - Add primary on-call phone numbers
   - Set up escalation phone lists
   - Configure SMS distribution groups

3. **Test SMS delivery**:
   - Send test SMS alerts
   - Verify message formatting
   - Check delivery times

---

## Part 4: Alert Testing Procedures

### 4.1 Alert Rule Testing

#### Test Performance Alerts
1. **Frontend Performance Testing**:
   ```bash
   # Simulate slow page load
   curl -w "@curl-format.txt" -o /dev/null -s "https://insurance-navigator.vercel.app"
   
   # Check alert trigger
   # Verify notification delivery
   # Test alert resolution
   ```

2. **Backend Performance Testing**:
   ```bash
   # Simulate slow API response
   curl -w "@curl-format.txt" -o /dev/null -s "https://insurance-navigator-api.onrender.com/health"
   
   # Check alert trigger
   # Verify notification delivery
   # Test alert resolution
   ```

#### Test Error Rate Alerts
1. **Simulate Error Conditions**:
   ```bash
   # Generate 4xx errors
   curl -X POST "https://insurance-navigator-api.onrender.com/invalid-endpoint"
   
   # Generate 5xx errors (if possible)
   # Check alert trigger
   # Verify notification delivery
   ```

2. **Test Error Recovery**:
   - Fix error conditions
   - Verify alert resolution
   - Check notification delivery

#### Test Resource Usage Alerts
1. **Simulate High Resource Usage**:
   ```bash
   # Generate CPU load
   stress --cpu 4 --timeout 60s
   
   # Generate memory load
   stress --vm 2 --vm-bytes 1G --timeout 60s
   
   # Check alert trigger
   # Verify notification delivery
   ```

2. **Test Resource Recovery**:
   - Stop load generation
   - Verify alert resolution
   - Check notification delivery

### 4.2 Notification Channel Testing

#### Test Email Notifications
1. **Send Test Email**:
   ```python
   # Test email configuration
   from backend.monitoring.alert_configuration import AlertManager
   
   alert_manager = AlertManager()
   await alert_manager._send_email_alert(test_alert, test_rule)
   ```

2. **Verify Email Delivery**:
   - Check email inbox
   - Verify email formatting
   - Check delivery time

#### Test Slack Notifications
1. **Send Test Slack Message**:
   ```python
   # Test Slack configuration
   await alert_manager._send_slack_alert(test_alert, test_rule)
   ```

2. **Verify Slack Delivery**:
   - Check Slack channel
   - Verify message formatting
   - Check notification settings

#### Test SMS Notifications
1. **Send Test SMS**:
   ```python
   # Test SMS configuration
   await alert_manager._send_sms_alert(test_alert, test_rule)
   ```

2. **Verify SMS Delivery**:
   - Check phone for SMS
   - Verify message formatting
   - Check delivery time

### 4.3 Escalation Testing

#### Test Escalation Procedures
1. **Primary Escalation**:
   - Trigger critical alert
   - Verify primary notification
   - Check acknowledgment

2. **Secondary Escalation**:
   - Wait for escalation timeout
   - Verify secondary notification
   - Check escalation procedures

3. **Tertiary Escalation**:
   - Wait for final escalation
   - Verify tertiary notification
   - Check on-call procedures

---

## Part 5: Alert System Validation

### 5.1 Comprehensive Testing

#### Test All Alert Rules
1. **Performance Alerts**:
   - Test all performance thresholds
   - Verify alert accuracy
   - Check notification delivery

2. **Error Rate Alerts**:
   - Test all error rate thresholds
   - Verify alert accuracy
   - Check notification delivery

3. **Resource Alerts**:
   - Test all resource thresholds
   - Verify alert accuracy
   - Check notification delivery

4. **Availability Alerts**:
   - Test all availability thresholds
   - Verify alert accuracy
   - Check notification delivery

#### Test All Notification Channels
1. **Email Channel**:
   - Test email delivery
   - Verify email formatting
   - Check delivery times

2. **Slack Channel**:
   - Test Slack delivery
   - Verify message formatting
   - Check channel notifications

3. **SMS Channel**:
   - Test SMS delivery
   - Verify message formatting
   - Check delivery times

### 5.2 Performance Validation

#### Test Alert System Performance
1. **Alert Processing Time**:
   - Measure alert processing latency
   - Verify processing within 1 second
   - Check system resource usage

2. **Notification Delivery Time**:
   - Measure notification delivery latency
   - Verify delivery within 30 seconds
   - Check delivery success rates

3. **System Overhead**:
   - Measure monitoring system overhead
   - Verify minimal impact on performance
   - Check resource usage

### 5.3 Reliability Validation

#### Test Alert System Reliability
1. **Alert Accuracy**:
   - Verify alerts trigger correctly
   - Check false positive rates
   - Verify alert resolution

2. **Notification Reliability**:
   - Test notification delivery success rates
   - Verify message formatting consistency
   - Check delivery time consistency

3. **System Availability**:
   - Test alert system availability
   - Verify system recovery procedures
   - Check backup notification channels

---

## Part 6: Alert System Maintenance

### 6.1 Regular Maintenance

#### Alert Rule Review
1. **Monthly Review**:
   - Review alert thresholds
   - Analyze alert frequency
   - Update alert rules as needed

2. **Quarterly Review**:
   - Review alert effectiveness
   - Update notification channels
   - Optimize alert rules

#### Notification Channel Maintenance
1. **Email Maintenance**:
   - Update email addresses
   - Test SMTP configuration
   - Verify email delivery

2. **Slack Maintenance**:
   - Update webhook URLs
   - Test Slack integration
   - Verify channel permissions

3. **SMS Maintenance**:
   - Update phone numbers
   - Test SMS service
   - Verify SMS delivery

### 6.2 Alert System Updates

#### Configuration Updates
1. **Threshold Updates**:
   - Update alert thresholds based on performance
   - Adjust severity levels
   - Update notification channels

2. **Rule Updates**:
   - Add new alert rules
   - Remove obsolete rules
   - Update existing rules

#### System Updates
1. **Software Updates**:
   - Update alert system software
   - Test system functionality
   - Verify alert delivery

2. **Infrastructure Updates**:
   - Update monitoring infrastructure
   - Test system integration
   - Verify alert functionality

---

## Part 7: Troubleshooting

### 7.1 Common Issues

#### Alert Not Triggering
1. **Check Alert Rules**:
   - Verify rule configuration
   - Check threshold values
   - Verify metric names

2. **Check Metric Collection**:
   - Verify metric collection
   - Check metric values
   - Verify data flow

#### Notifications Not Delivered
1. **Check Notification Configuration**:
   - Verify SMTP settings
   - Check webhook URLs
   - Verify phone numbers

2. **Check Network Connectivity**:
   - Test network connectivity
   - Check firewall settings
   - Verify DNS resolution

#### False Positives
1. **Adjust Thresholds**:
   - Review threshold values
   - Adjust based on historical data
   - Update alert rules

2. **Improve Alert Logic**:
   - Add duration requirements
   - Implement cooldown periods
   - Add context validation

### 7.2 Debugging Procedures

#### Alert System Debugging
1. **Check Logs**:
   - Review alert system logs
   - Check error messages
   - Verify system status

2. **Test Components**:
   - Test individual components
   - Verify system integration
   - Check data flow

#### Notification Debugging
1. **Test Notification Channels**:
   - Test each channel individually
   - Verify configuration
   - Check delivery status

2. **Check External Services**:
   - Test SMTP connectivity
   - Check Slack webhook
   - Verify SMS service

---

## Conclusion

This comprehensive alert configuration and testing guide ensures that the Insurance Navigator alert system is properly configured, tested, and maintained. The alert system provides:

- **Proactive monitoring** with appropriate thresholds
- **Reliable notification delivery** across multiple channels
- **Effective escalation procedures** for critical issues
- **Comprehensive testing** to ensure system reliability
- **Regular maintenance** to keep the system current

The alert system is now ready for production use and will provide the necessary proactive monitoring and notification for maintaining system health and performance.
