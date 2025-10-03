# Production Monitoring Setup Procedures

## Overview

This document provides step-by-step procedures for setting up comprehensive production monitoring across all cloud services (Vercel, Render, Supabase) for the Insurance Navigator system.

---

## Prerequisites

### Required Access
- Vercel project dashboard access
- Render service dashboard access
- Supabase project dashboard access
- Admin access to notification services (email, Slack, SMS)

### Required Tools
- Modern web browser
- Access to cloud service dashboards
- Configuration files and environment variables
- Notification service credentials

---

## Part 1: Vercel Monitoring Setup

### 1.1 Access Vercel Dashboard

1. Navigate to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select the `insurance-navigator` project
3. Verify project is deployed and accessible

### 1.2 Configure Analytics and Monitoring

#### Enable Analytics
1. Go to the "Analytics" tab
2. Enable "Web Analytics" if not already enabled
3. Configure analytics settings:
   - Enable Core Web Vitals tracking
   - Enable Real User Monitoring (RUM)
   - Set up custom events tracking

#### Configure Performance Monitoring
1. Go to "Functions" tab
2. Enable function monitoring:
   - Set up function execution logging
   - Configure performance metrics collection
   - Enable error tracking and reporting

3. Go to "Settings" → "Functions"
4. Configure function settings:
   - Set appropriate timeout values
   - Configure memory allocation
   - Enable detailed logging

### 1.3 Set Up Custom Monitoring

#### Create Health Check Endpoint
1. Create `/api/health` endpoint in your Next.js app:
```typescript
// pages/api/health.ts
import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.VERCEL_GIT_COMMIT_SHA || 'unknown',
    environment: process.env.NODE_ENV || 'development'
  }
  
  res.status(200).json(health)
}
```

#### Create Metrics Endpoint
1. Create `/api/metrics` endpoint:
```typescript
// pages/api/metrics.ts
import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const metrics = {
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    version: process.env.VERCEL_GIT_COMMIT_SHA || 'unknown'
  }
  
  res.status(200).json(metrics)
}
```

### 1.4 Configure Alerts

#### Set Up Vercel Alerts
1. Go to "Settings" → "Notifications"
2. Configure email notifications:
   - Add alert email addresses
   - Set up deployment failure notifications
   - Configure performance degradation alerts

3. Configure webhook notifications:
   - Set up Slack webhook for critical alerts
   - Configure custom webhook endpoints
   - Test webhook delivery

### 1.5 Validation Steps

1. **Test Health Endpoints**:
   ```bash
   curl https://insurance-navigator.vercel.app/api/health
   curl https://insurance-navigator.vercel.app/api/metrics
   ```

2. **Verify Analytics**:
   - Check Analytics tab for data collection
   - Verify Core Web Vitals are being tracked
   - Confirm function execution logs are available

3. **Test Alerts**:
   - Trigger a test deployment failure
   - Verify alert notifications are received
   - Test webhook delivery

---

## Part 2: Render Service Monitoring Setup

### 2.1 Access Render Dashboard

1. Navigate to [Render Dashboard](https://dashboard.render.com)
2. Select the `insurance-navigator-api` service
3. Verify service is running and healthy

### 2.2 Configure Service Monitoring

#### Enable Metrics Collection
1. Go to "Metrics" tab
2. Enable the following metrics:
   - CPU usage monitoring
   - Memory usage monitoring
   - Network I/O monitoring
   - Disk I/O monitoring

#### Configure Log Aggregation
1. Go to "Logs" tab
2. Configure log retention:
   - Set log retention period (recommended: 30 days)
   - Enable log search and filtering
   - Configure log export options

### 2.3 Set Up Health Monitoring

#### Verify Health Check Endpoint
1. Ensure `/health` endpoint is implemented in your FastAPI app:
```python
# main.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "services": {
            "database": "healthy",
            "supabase_auth": "healthy",
            "llamaparse": "healthy",
            "openai": "healthy"
        }
    }
```

#### Test Health Endpoint
```bash
curl https://insurance-navigator-api.onrender.com/health
```

### 2.4 Configure Auto-scaling

#### Set Up Auto-scaling Rules
1. Go to "Settings" → "Auto Deploy"
2. Configure auto-scaling:
   - Set minimum instances: 1
   - Set maximum instances: 3
   - Set CPU threshold: 70%
   - Set memory threshold: 80%

#### Configure Scaling Policies
1. Set up scaling triggers:
   - CPU usage > 70% for 2 minutes
   - Memory usage > 80% for 2 minutes
   - Request queue depth > 10

### 2.5 Set Up Alerts

#### Configure Render Alerts
1. Go to "Settings" → "Notifications"
2. Set up email alerts:
   - Service health alerts
   - Resource usage alerts
   - Deployment status alerts

3. Configure webhook alerts:
   - Set up Slack webhook
   - Configure custom webhook endpoints
   - Test webhook delivery

### 2.6 Worker Service Monitoring

#### Configure Worker Service
1. Navigate to `insurance-navigator-worker` service
2. Enable worker monitoring:
   - Job processing metrics
   - Queue depth monitoring
   - Worker health checks

#### Set Up Worker Alerts
1. Configure worker-specific alerts:
   - Job processing failures
   - Queue depth alerts
   - Worker health alerts

### 2.7 Validation Steps

1. **Test Health Endpoints**:
   ```bash
   curl https://insurance-navigator-api.onrender.com/health
   ```

2. **Verify Metrics**:
   - Check Metrics tab for data collection
   - Verify resource usage monitoring
   - Confirm log aggregation is working

3. **Test Auto-scaling**:
   - Generate load to trigger scaling
   - Verify scaling behavior
   - Check scaling metrics

4. **Test Alerts**:
   - Trigger resource usage alerts
   - Verify alert notifications
   - Test webhook delivery

---

## Part 3: Supabase Monitoring Setup

### 3.1 Access Supabase Dashboard

1. Navigate to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select the `insurance-navigator` project
3. Verify project is active and accessible

### 3.2 Configure Database Monitoring

#### Enable Database Analytics
1. Go to "Reports" tab
2. Enable database performance monitoring:
   - Query performance tracking
   - Connection monitoring
   - Database size monitoring

#### Set Up Query Monitoring
1. Go to "SQL Editor" → "Query Performance"
2. Enable query performance insights:
   - Slow query detection
   - Query execution time tracking
   - Database index recommendations

### 3.3 Configure Authentication Monitoring

#### Set Up Auth Analytics
1. Go to "Authentication" → "Users"
2. Enable authentication monitoring:
   - User registration tracking
   - Login success/failure rates
   - Session management monitoring

#### Configure Auth Alerts
1. Set up authentication alerts:
   - Failed login attempts
   - Suspicious activity detection
   - User registration anomalies

### 3.4 Configure Storage Monitoring

#### Set Up Storage Analytics
1. Go to "Storage" → "Buckets"
2. Enable storage monitoring:
   - Storage usage tracking
   - File upload/download monitoring
   - Storage quota monitoring

#### Configure Storage Alerts
1. Set up storage alerts:
   - Storage quota warnings
   - Upload failure alerts
   - Storage access anomalies

### 3.5 Configure Real-time Monitoring

#### Set Up Real-time Analytics
1. Go to "Realtime" → "Channels"
2. Enable real-time monitoring:
   - Connection count monitoring
   - Message delivery tracking
   - Subscription performance monitoring

#### Configure Real-time Alerts
1. Set up real-time alerts:
   - Connection limit alerts
   - Message delivery failures
   - Subscription performance issues

### 3.6 Validation Steps

1. **Test Database Connectivity**:
   ```bash
   curl -H "apikey: YOUR_SUPABASE_ANON_KEY" \
        https://znvwzkdblknkkztqyfnu.supabase.co/rest/v1/
   ```

2. **Verify Analytics**:
   - Check Reports tab for data collection
   - Verify query performance monitoring
   - Confirm authentication analytics

3. **Test Alerts**:
   - Trigger database performance alerts
   - Verify alert notifications
   - Test authentication alerts

---

## Part 4: Unified Monitoring Dashboard

### 4.1 Create Monitoring Overview

#### Set Up Cross-Service Monitoring
1. Create a unified monitoring dashboard
2. Integrate metrics from all services:
   - Vercel frontend metrics
   - Render backend metrics
   - Supabase database metrics

#### Configure Metric Correlation
1. Set up metric correlation:
   - Frontend performance → Backend response times
   - Backend errors → Database performance
   - User activity → System resource usage

### 4.2 Set Up Business Metrics

#### Configure User Metrics
1. Track user engagement:
   - User registrations
   - Document uploads
   - Agent conversations
   - User session duration

#### Configure Processing Metrics
1. Track document processing:
   - Processing success rates
   - Processing times
   - Queue depths
   - Error rates

### 4.3 Set Up End-to-End Monitoring

#### Configure Transaction Tracing
1. Set up end-to-end transaction monitoring:
   - User request → Frontend → Backend → Database
   - Document upload → Processing → Storage
   - Agent conversation → Processing → Response

#### Configure Performance Correlation
1. Set up performance correlation:
   - Frontend load time → Backend response time
   - Database query time → API response time
   - Processing time → User experience

### 4.4 Validation Steps

1. **Test Unified Dashboard**:
   - Verify all service metrics are displayed
   - Check metric correlation is working
   - Confirm business metrics are tracked

2. **Test End-to-End Monitoring**:
   - Trace complete user workflows
   - Verify transaction monitoring
   - Check performance correlation

---

## Part 5: Alert Configuration

### 5.1 Set Up Alert Rules

#### Configure Performance Alerts
1. Set up response time alerts:
   - Frontend page load > 3 seconds
   - API response time > 2 seconds
   - Database query time > 500ms

2. Set up error rate alerts:
   - Application error rate > 1%
   - HTTP 4xx errors > 5%
   - HTTP 5xx errors > 1%

#### Configure Resource Alerts
1. Set up resource usage alerts:
   - CPU usage > 80%
   - Memory usage > 85%
   - Database connections > 80%

2. Set up availability alerts:
   - Service availability < 99%
   - Health check failures
   - Service downtime

### 5.2 Configure Notification Channels

#### Set Up Email Notifications
1. Configure SMTP settings:
   ```bash
   export SMTP_SERVER=smtp.gmail.com
   export SMTP_PORT=587
   export SMTP_USERNAME=your-email@gmail.com
   export SMTP_PASSWORD=your-app-password
   export ALERT_EMAIL=alerts@yourcompany.com
   ```

2. Test email delivery:
   - Send test alerts
   - Verify email formatting
   - Check delivery times

#### Set Up Slack Notifications
1. Configure Slack webhook:
   ```bash
   export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
   ```

2. Test Slack delivery:
   - Send test alerts
   - Verify message formatting
   - Check channel permissions

#### Set Up SMS Notifications
1. Configure SMS service:
   ```bash
   export ALERT_PHONE_NUMBER=+1234567890
   ```

2. Test SMS delivery:
   - Send test alerts
   - Verify message delivery
   - Check delivery times

### 5.3 Configure Escalation Policies

#### Set Up Escalation Rules
1. Configure escalation timing:
   - Level 1: Immediate notification
   - Level 2: 5 minutes if not acknowledged
   - Level 3: 15 minutes if not resolved

2. Configure escalation contacts:
   - Primary: Development team
   - Secondary: Operations team
   - Tertiary: On-call engineer

### 5.4 Validation Steps

1. **Test Alert Rules**:
   - Trigger test alerts
   - Verify alert conditions
   - Check alert resolution

2. **Test Notifications**:
   - Test all notification channels
   - Verify delivery success rates
   - Check message formatting

3. **Test Escalation**:
   - Test escalation procedures
   - Verify escalation timing
   - Check escalation contacts

---

## Part 6: Monitoring Validation

### 6.1 Comprehensive Testing

#### Test All Monitoring Systems
1. Test Vercel monitoring:
   - Verify analytics collection
   - Test health endpoints
   - Check alert delivery

2. Test Render monitoring:
   - Verify metrics collection
   - Test auto-scaling
   - Check log aggregation

3. Test Supabase monitoring:
   - Verify database monitoring
   - Test authentication analytics
   - Check storage monitoring

#### Test Unified Dashboard
1. Verify cross-service monitoring
2. Test metric correlation
3. Check business metrics tracking

### 6.2 Performance Validation

#### Test Monitoring Performance
1. Verify monitoring overhead:
   - Check system resource usage
   - Test monitoring response times
   - Validate monitoring accuracy

2. Test alert performance:
   - Check alert delivery times
   - Verify alert accuracy
   - Test alert resolution

### 6.3 Documentation

#### Document Monitoring Setup
1. Document all monitoring configurations
2. Create monitoring runbooks
3. Document troubleshooting procedures

#### Create Monitoring Procedures
1. Create monitoring maintenance procedures
2. Document monitoring updates
3. Create monitoring training materials

---

## Conclusion

This comprehensive monitoring setup ensures that all aspects of the Insurance Navigator system are properly monitored with appropriate alerts and notifications. The monitoring system provides:

- **Real-time visibility** into system performance and health
- **Proactive alerting** for issues before they impact users
- **Comprehensive coverage** across all cloud services
- **Business metrics tracking** for user engagement and processing
- **End-to-end monitoring** for complete transaction visibility

The monitoring system is now ready for production use and will provide the necessary visibility and alerting for maintaining system health and performance.
