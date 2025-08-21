# TVDb001 Operations Runbook: Real Service Management

## Executive Summary

This operations runbook provides comprehensive procedures for managing the TVDb001 Real API Integration Testing system in production. The runbook covers service startup, monitoring, troubleshooting, cost management, and emergency procedures for maintaining system reliability and cost control.

**System Overview**: TVDb001 integrates real external services (LlamaParse, OpenAI) with comprehensive cost tracking, health monitoring, and fallback mechanisms. The system operates in three modes: mock, real, and hybrid, with automatic fallback to mock services when real services are unavailable or cost limits are exceeded.

**Operational Status**: ✅ PRODUCTION READY  
**Last Updated**: December 2024  
**Next Review**: January 2025  

## System Architecture Overview

### Service Components
```
┌─────────────────────────────────────────────────────────────────┐
│                         TVDb001 System                         │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   API Server    │   BaseWorker    │        External Services    │
│   (FastAPI)     │   (Enhanced)    │                             │
│   - Upload      │   - Service     │   - LlamaParse API          │
│   - Webhooks    │     Router      │   - OpenAI API              │
│   - Health      │   - Cost        │   - Supabase Storage        │
│   - Monitoring  │     Tracker     │   - Database (PostgreSQL)   │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Service Modes
- **Mock Mode**: Uses simulated services (cost-free, reliable)
- **Real Mode**: Uses actual external APIs (cost-tracked, real performance)
- **Hybrid Mode**: Dynamically selects services based on availability and cost

## Service Startup Procedures

### 1. Environment Preparation

#### Prerequisites Check
```bash
# Verify environment variables are set
echo "Checking environment configuration..."
env | grep -E "(UPLOAD_PIPELINE|LLAMAPARSE|OPENAI|SUPABASE)" | sort

# Verify API keys are accessible
echo "Verifying API key accessibility..."
curl -s -H "Authorization: Bearer $UPLOAD_PIPELINE_LLAMAPARSE_API_KEY" \
  "https://api.llamaparse.com/v1/health" | jq '.status'
```

#### Configuration Validation
```bash
# Validate configuration files
python -c "
from backend.shared.config.enhanced_config import ProductionConfig
config = ProductionConfig()
print('✅ Configuration loaded successfully')
print(f'Service Mode: {config.service_mode}')
print(f'Daily Budget: ${config.daily_cost_limit}')
"
```

### 2. Service Startup Sequence

#### Step 1: Database and Storage
```bash
echo "Starting database and storage services..."
docker-compose up -d postgres supabase-storage

# Wait for database readiness
echo "Waiting for database readiness..."
until docker-compose exec postgres pg_isready -U postgres; do
  sleep 2
done
echo "✅ Database ready"
```

#### Step 2: Core Application Services
```bash
echo "Starting core application services..."
docker-compose up -d api-server base-worker

# Wait for service readiness
echo "Waiting for service readiness..."
until curl -f http://localhost:8000/health; do
  sleep 2
done
echo "✅ API server ready"
```

#### Step 3: Monitoring and Validation
```bash
echo "Starting monitoring services..."
docker-compose up -d monitoring

# Validate all services are healthy
echo "Validating service health..."
python scripts/validate-service-health.py

echo "✅ All services started successfully"
```

### 3. Service Mode Configuration

#### Mode Selection
```bash
# Set service mode (mock/real/hybrid)
export SERVICE_MODE="hybrid"  # Recommended for production

# Verify mode configuration
curl -s http://localhost:8000/health | jq '.service_mode'
```

#### Cost Limit Configuration
```bash
# Set daily cost limits
export DAILY_COST_LIMIT_LLAMAPARSE="50.00"  # $50/day for LlamaParse
export DAILY_COST_LIMIT_OPENAI="100.00"      # $100/day for OpenAI

# Verify cost limits
curl -s http://localhost:8000/monitoring/costs | jq '.daily_limits'
```

## Daily Operations

### 1. Morning Health Check

#### Service Status Verification
```bash
#!/bin/bash
# scripts/morning-health-check.sh

echo "=== Morning Health Check - $(date) ==="

# Check all service endpoints
echo "1. Checking API server health..."
curl -f http://localhost:8000/health || echo "❌ API server unhealthy"

echo "2. Checking worker process health..."
curl -f http://localhost:8000/workers/health || echo "❌ Worker unhealthy"

echo "3. Checking external service connectivity..."
python scripts/check-external-services.py

echo "4. Checking cost tracking status..."
curl -s http://localhost:8000/monitoring/costs | jq '.daily_usage'

echo "5. Checking database connectivity..."
docker-compose exec postgres pg_isready -U postgres || echo "❌ Database unhealthy"

echo "=== Health check complete ==="
```

#### Cost Status Review
```bash
# Review daily cost status
echo "Daily Cost Status:"
curl -s http://localhost:8000/monitoring/costs | jq '{
  daily_usage: .daily_usage,
  daily_limits: .daily_limits,
  remaining_budget: .remaining_budget,
  cost_alerts: .cost_alerts
}'
```

### 2. Ongoing Monitoring

#### Real-Time Cost Monitoring
```bash
# Monitor costs in real-time
watch -n 30 'curl -s http://localhost:8000/monitoring/costs | jq ".daily_usage, .remaining_budget"'
```

#### Service Health Monitoring
```bash
# Monitor service health
watch -n 60 'curl -s http://localhost:8000/monitoring/health | jq ".services[] | {name: .name, status: .status, response_time: .response_time}"'
```

#### Performance Monitoring
```bash
# Monitor performance metrics
watch -n 60 'curl -s http://localhost:8000/monitoring/performance | jq ".metrics | {avg_response_time: .avg_response_time, throughput: .throughput, error_rate: .error_rate}"'
```

### 3. Cost Management

#### Daily Budget Monitoring
```bash
# Check budget status every hour
while true; do
  echo "=== $(date) - Budget Status ==="
  curl -s http://localhost:8000/monitoring/costs | jq '{
    timestamp: .timestamp,
    daily_usage: .daily_usage,
    remaining_budget: .remaining_budget,
    alerts: .cost_alerts
  }'
  
  # Alert if budget exceeded
  remaining=$(curl -s http://localhost:8000/monitoring/costs | jq -r '.remaining_budget.total')
  if (( $(echo "$remaining < 10" | bc -l) )); then
    echo "🚨 WARNING: Budget nearly exceeded! Remaining: $remaining"
    # Send alert notification
    python scripts/send-cost-alert.py --remaining="$remaining"
  fi
  
  sleep 3600  # Check every hour
done
```

#### Cost Optimization
```bash
# Analyze cost patterns
echo "Cost Analysis Report:"
curl -s http://localhost:8000/monitoring/costs/analysis | jq '{
  cost_by_service: .cost_by_service,
  cost_by_hour: .cost_by_hour,
  optimization_recommendations: .optimization_recommendations
}'
```

## Troubleshooting Procedures

### 1. Service Unavailability Issues

#### LlamaParse Service Issues
```bash
# Check LlamaParse service status
echo "Diagnosing LlamaParse service issues..."

# Test API connectivity
curl -v -H "Authorization: Bearer $UPLOAD_PIPELINE_LLAMAPARSE_API_KEY" \
  "https://api.llamaparse.com/v1/health"

# Check service logs
docker-compose logs base-worker | grep -i llamaparse

# Verify fallback to mock service
curl -s http://localhost:8000/monitoring/health | jq '.services[] | select(.name=="llamaparse") | {status: .status, fallback: .fallback_active}'
```

#### OpenAI Service Issues
```bash
# Check OpenAI service status
echo "Diagnosing OpenAI service issues..."

# Test API connectivity
curl -v -H "Authorization: Bearer $UPLOAD_PIPELINE_OPENAI_API_KEY" \
  "https://api.openai.com/v1/models"

# Check rate limiting status
curl -s http://localhost:8000/monitoring/health | jq '.services[] | select(.name=="openai") | {status: .status, rate_limit: .rate_limit_status}'

# Verify fallback to mock service
curl -s http://localhost:8000/monitoring/health | jq '.services[] | select(.name=="openai") | {status: .status, fallback: .fallback_active}'
```

### 2. Cost Control Issues

#### Budget Exceeded
```bash
# Emergency cost control procedures
echo "🚨 EMERGENCY: Budget exceeded - implementing cost controls..."

# 1. Switch to mock mode immediately
export SERVICE_MODE="mock"
curl -X POST http://localhost:8000/admin/service-mode -d '{"mode": "mock"}'

# 2. Verify mode change
curl -s http://localhost:8000/health | jq '.service_mode'

# 3. Check for any pending real service jobs
curl -s http://localhost:8000/monitoring/jobs | jq '.jobs[] | select(.service_mode=="real") | {job_id: .job_id, status: .status}'

# 4. Send emergency alert
python scripts/send-emergency-alert.py --type="budget_exceeded" --details="Switched to mock mode"
```

#### Cost Tracking Issues
```bash
# Diagnose cost tracking problems
echo "Diagnosing cost tracking issues..."

# Check cost tracking service health
curl -s http://localhost:8000/monitoring/costs | jq '.status'

# Verify cost database connectivity
docker-compose exec postgres psql -U postgres -d accessa_dev -c "
SELECT COUNT(*) as cost_records, 
       MAX(created_at) as latest_cost_record
FROM cost_tracking 
WHERE created_at > NOW() - INTERVAL '24 hours';"

# Check cost calculation accuracy
python scripts/validate-cost-tracking.py
```

### 3. Performance Issues

#### High Response Times
```bash
# Diagnose performance issues
echo "Diagnosing performance issues..."

# Check response time metrics
curl -s http://localhost:8000/monitoring/performance | jq '{
  avg_response_time: .metrics.avg_response_time,
  p95_response_time: .metrics.p95_response_time,
  p99_response_time: .metrics.p99_response_time
}'

# Check resource utilization
docker stats --no-stream

# Analyze performance bottlenecks
python scripts/analyze-performance.py
```

#### Throughput Issues
```bash
# Check throughput metrics
echo "Checking throughput metrics..."

curl -s http://localhost:8000/monitoring/performance | jq '{
  requests_per_minute: .metrics.requests_per_minute,
  concurrent_requests: .metrics.concurrent_requests,
  queue_depth: .metrics.queue_depth
}'

# Check worker process status
curl -s http://localhost:8000/workers/status | jq '{
  active_workers: .active_workers,
  processing_jobs: .processing_jobs,
  queue_size: .queue_size
}'
```

### 4. Database Issues

#### Connection Problems
```bash
# Diagnose database connection issues
echo "Diagnosing database connection issues..."

# Check database connectivity
docker-compose exec postgres pg_isready -U postgres

# Check connection pool status
curl -s http://localhost:8000/monitoring/database | jq '{
  connection_pool: .connection_pool,
  active_connections: .active_connections,
  max_connections: .max_connections
}'

# Check database performance
docker-compose exec postgres psql -U postgres -d accessa_dev -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"
```

#### Performance Issues
```bash
# Check database performance
echo "Checking database performance..."

# Check slow queries
docker-compose exec postgres psql -U postgres -d accessa_dev -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Check table sizes and indexes
docker-compose exec postgres psql -U postgres -d accessa_dev -c "
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## Emergency Procedures

### 1. Complete Service Failure

#### Emergency Shutdown
```bash
#!/bin/bash
# scripts/emergency-shutdown.sh

echo "🚨 EMERGENCY SHUTDOWN INITIATED - $(date)"

# 1. Stop all services
echo "Stopping all services..."
docker-compose down

# 2. Switch to mock mode configuration
echo "Switching to mock mode configuration..."
export SERVICE_MODE="mock"
export EMERGENCY_MODE="true"

# 3. Restart in mock-only mode
echo "Restarting in mock-only mode..."
docker-compose up -d postgres
docker-compose up -d api-server base-worker

# 4. Verify mock mode operation
echo "Verifying mock mode operation..."
until curl -f http://localhost:8000/health; do
  sleep 2
done

echo "✅ Emergency shutdown complete - system running in mock mode"
```

#### Emergency Recovery
```bash
#!/bin/bash
# scripts/emergency-recovery.sh

echo "🔄 EMERGENCY RECOVERY INITIATED - $(date)"

# 1. Assess system health
echo "Assessing system health..."
python scripts/assess-system-health.py

# 2. Gradual service restoration
echo "Gradually restoring services..."

# Start with mock services
export SERVICE_MODE="mock"
docker-compose up -d

# Verify mock mode operation
echo "Verifying mock mode operation..."
python scripts/validate-service-health.py

# 3. Test real service connectivity
echo "Testing real service connectivity..."
python scripts/test-external-services.py

# 4. Gradual real service restoration
if [ $? -eq 0 ]; then
  echo "Real services available - switching to hybrid mode..."
  export SERVICE_MODE="hybrid"
  curl -X POST http://localhost:8000/admin/service-mode -d '{"mode": "hybrid"}'
else
  echo "Real services unavailable - remaining in mock mode..."
fi

echo "✅ Emergency recovery complete"
```

### 2. Cost Emergency Procedures

#### Budget Emergency
```bash
#!/bin/bash
# scripts/budget-emergency.sh

echo "💰 BUDGET EMERGENCY PROCEDURE - $(date)"

# 1. Immediate cost control
echo "Implementing immediate cost controls..."
curl -X POST http://localhost:8000/admin/cost-controls -d '{
  "emergency_mode": true,
  "daily_limit_multiplier": 0.1,
  "enable_strict_limits": true
}'

# 2. Switch to mock mode
echo "Switching to mock mode..."
export SERVICE_MODE="mock"
curl -X POST http://localhost:8000/admin/service-mode -d '{"mode": "mock"}'

# 3. Notify stakeholders
echo "Notifying stakeholders..."
python scripts/send-budget-emergency-alert.py

# 4. Implement cost monitoring
echo "Implementing enhanced cost monitoring..."
python scripts/enable-emergency-cost-monitoring.py

echo "✅ Budget emergency procedures implemented"
```

### 3. Security Emergency Procedures

#### API Key Compromise
```bash
#!/bin/bash
# scripts/security-emergency.sh

echo "🔒 SECURITY EMERGENCY - API Key Compromise - $(date)"

# 1. Immediate service shutdown
echo "Shutting down services immediately..."
docker-compose down

# 2. Revoke compromised keys
echo "Revoking compromised API keys..."
# Note: This requires manual intervention with service providers

# 3. Switch to mock mode
echo "Switching to mock mode..."
export SERVICE_MODE="mock"
export EMERGENCY_MODE="true"

# 4. Restart in secure mode
echo "Restarting in secure mode..."
docker-compose up -d postgres
docker-compose up -d api-server base-worker

# 5. Verify secure operation
echo "Verifying secure operation..."
python scripts/validate-security.py

echo "✅ Security emergency procedures implemented"
```

## Maintenance Procedures

### 1. Regular Maintenance

#### Daily Maintenance
```bash
#!/bin/bash
# scripts/daily-maintenance.sh

echo "=== Daily Maintenance - $(date) ==="

# 1. Log rotation
echo "Rotating logs..."
docker-compose exec api-server logrotate /etc/logrotate.conf
docker-compose exec base-worker logrotate /etc/logrotate.conf

# 2. Database maintenance
echo "Performing database maintenance..."
docker-compose exec postgres psql -U postgres -d accessa_dev -c "VACUUM ANALYZE;"

# 3. Cost data cleanup
echo "Cleaning up old cost data..."
python scripts/cleanup-old-cost-data.py --days=30

# 4. Health check
echo "Performing health check..."
python scripts/validate-service-health.py

echo "✅ Daily maintenance complete"
```

#### Weekly Maintenance
```bash
#!/bin/bash
# scripts/weekly-maintenance.sh

echo "=== Weekly Maintenance - $(date) ==="

# 1. Performance analysis
echo "Analyzing performance metrics..."
python scripts/analyze-weekly-performance.py

# 2. Cost analysis
echo "Analyzing cost patterns..."
python scripts/analyze-weekly-costs.py

# 3. Security review
echo "Performing security review..."
python scripts/security-review.py

# 4. Backup verification
echo "Verifying backups..."
python scripts/verify-backups.py

echo "✅ Weekly maintenance complete"
```

### 2. Configuration Updates

#### Service Configuration Updates
```bash
# Update service configuration
echo "Updating service configuration..."

# 1. Backup current configuration
cp .env.production .env.production.backup.$(date +%Y%m%d_%H%M%S)

# 2. Update configuration
echo "Updating configuration values..."
sed -i 's/DAILY_COST_LIMIT_OPENAI=.*/DAILY_COST_LIMIT_OPENAI=150.00/' .env.production

# 3. Validate configuration
echo "Validating configuration..."
python scripts/validate-configuration.py

# 4. Restart services if needed
if [ $? -eq 0 ]; then
  echo "Configuration updated successfully"
  docker-compose restart api-server base-worker
else
  echo "Configuration validation failed - rolling back..."
  cp .env.production.backup.* .env.production
fi
```

#### API Key Rotation
```bash
# Rotate API keys
echo "Rotating API keys..."

# 1. Generate new keys (manual process)
echo "Please generate new API keys manually:"
echo "- LlamaParse API key"
echo "- OpenAI API key"
echo "- Supabase service role key"

# 2. Update configuration
echo "Updating configuration with new keys..."
# Note: Update .env.production with new keys

# 3. Test new keys
echo "Testing new keys..."
python scripts/test-api-keys.py

# 4. Restart services
if [ $? -eq 0 ]; then
  echo "New keys working - restarting services..."
  docker-compose restart api-server base-worker
else
  echo "New keys failed - keeping old keys..."
fi
```

## Monitoring and Alerting

### 1. Alert Configuration

#### Cost Alerts
```bash
# Configure cost alerts
echo "Configuring cost alerts..."

# Set alert thresholds
curl -X POST http://localhost:8000/admin/alerts/cost -d '{
  "budget_warning_threshold": 0.8,
  "budget_critical_threshold": 0.95,
  "hourly_spike_threshold": 0.2
}'

# Configure alert channels
curl -X POST http://localhost:8000/admin/alerts/channels -d '{
  "email": "ops@company.com",
  "slack": "#alerts",
  "pagerduty": "PAGERDUTY_KEY"
}'
```

#### Service Health Alerts
```bash
# Configure service health alerts
echo "Configuring service health alerts..."

# Set health check thresholds
curl -X POST http://localhost:8000/admin/alerts/health -d '{
  "response_time_warning": 5000,
  "response_time_critical": 10000,
  "error_rate_warning": 0.05,
  "error_rate_critical": 0.1
}'
```

### 2. Dashboard Configuration

#### Cost Dashboard
```bash
# Configure cost dashboard
echo "Configuring cost dashboard..."

# Set dashboard refresh rate
curl -X POST http://localhost:8000/admin/dashboard/cost -d '{
  "refresh_rate": 30,
  "display_currency": "USD",
  "show_hourly_breakdown": true,
  "show_service_breakdown": true
}'
```

#### Performance Dashboard
```bash
# Configure performance dashboard
echo "Configuring performance dashboard..."

# Set performance metrics
curl -X POST http://localhost:8000/admin/dashboard/performance -d '{
  "refresh_rate": 60,
  "show_response_times": true,
  "show_throughput": true,
  "show_error_rates": true
}'
```

## Backup and Recovery

### 1. Backup Procedures

#### Database Backup
```bash
#!/bin/bash
# scripts/backup-database.sh

echo "=== Database Backup - $(date) ==="

# Create backup directory
BACKUP_DIR="/backups/database/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Perform database backup
echo "Creating database backup..."
docker-compose exec postgres pg_dump -U postgres -d accessa_dev > $BACKUP_DIR/database_backup.sql

# Compress backup
echo "Compressing backup..."
gzip $BACKUP_DIR/database_backup.sql

# Verify backup
echo "Verifying backup..."
gunzip -t $BACKUP_DIR/database_backup.sql.gz

echo "✅ Database backup complete: $BACKUP_DIR/database_backup.sql.gz"
```

#### Configuration Backup
```bash
#!/bin/bash
# scripts/backup-configuration.sh

echo "=== Configuration Backup - $(date) ==="

# Create backup directory
BACKUP_DIR="/backups/configuration/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup configuration files
echo "Backing up configuration files..."
cp .env.production $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/
cp -r config/ $BACKUP_DIR/

# Create backup archive
echo "Creating backup archive..."
tar -czf $BACKUP_DIR/configuration_backup.tar.gz -C $BACKUP_DIR .

echo "✅ Configuration backup complete: $BACKUP_DIR/configuration_backup.tar.gz"
```

### 2. Recovery Procedures

#### Database Recovery
```bash
#!/bin/bash
# scripts/recover-database.sh

echo "=== Database Recovery - $(date) ==="

# Select backup file
BACKUP_FILE="/backups/database/20241201/database_backup.sql.gz"
echo "Recovering from: $BACKUP_FILE"

# Stop services
echo "Stopping services..."
docker-compose down

# Restore database
echo "Restoring database..."
gunzip -c $BACKUP_FILE | docker-compose exec -T postgres psql -U postgres -d accessa_dev

# Verify restoration
echo "Verifying restoration..."
docker-compose exec postgres psql -U postgres -d accessa_dev -c "SELECT COUNT(*) FROM upload_jobs;"

# Restart services
echo "Restarting services..."
docker-compose up -d

echo "✅ Database recovery complete"
```

#### Configuration Recovery
```bash
#!/bin/bash
# scripts/recover-configuration.sh

echo "=== Configuration Recovery - $(date) ==="

# Select backup file
BACKUP_FILE="/backups/configuration/20241201/configuration_backup.tar.gz"
echo "Recovering from: $BACKUP_FILE"

# Extract backup
echo "Extracting backup..."
tar -xzf $BACKUP_FILE -C /tmp/recovery

# Restore configuration
echo "Restoring configuration..."
cp /tmp/recovery/.env.production .
cp /tmp/recovery/docker-compose.yml .
cp -r /tmp/recovery/config/ .

# Validate configuration
echo "Validating configuration..."
python scripts/validate-configuration.py

# Restart services if needed
if [ $? -eq 0 ]; then
  echo "Configuration restored successfully"
  docker-compose restart
else
  echo "Configuration validation failed"
fi

echo "✅ Configuration recovery complete"
```

## Performance Optimization

### 1. Cost Optimization

#### Batch Processing Optimization
```bash
# Optimize batch processing
echo "Optimizing batch processing..."

# Analyze current batch sizes
curl -s http://localhost:8000/monitoring/costs/analysis | jq '.optimization_recommendations.batch_processing'

# Apply batch size optimizations
curl -X POST http://localhost:8000/admin/optimization/batch-sizes -d '{
  "llamaparse_batch_size": 5,
  "openai_batch_size": 128,
  "enable_dynamic_batching": true
}'
```

#### Rate Limiting Optimization
```bash
# Optimize rate limiting
echo "Optimizing rate limiting..."

# Analyze rate limiting patterns
curl -s http://localhost:8000/monitoring/performance | jq '.rate_limiting'

# Adjust rate limits
curl -X POST http://localhost:8000/admin/optimization/rate-limits -d '{
  "llamaparse_requests_per_minute": 60,
  "openai_requests_per_minute": 3000,
  "enable_adaptive_rate_limiting": true
}'
```

### 2. Performance Tuning

#### Database Optimization
```bash
# Optimize database performance
echo "Optimizing database performance..."

# Analyze query performance
docker-compose exec postgres psql -U postgres -d accessa_dev -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Create performance indexes
docker-compose exec postgres psql -U postgres -d accessa_dev -c "
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_upload_jobs_status_created 
ON upload_jobs (status, created_at);"
```

#### Worker Optimization
```bash
# Optimize worker performance
echo "Optimizing worker performance..."

# Analyze worker performance
curl -s http://localhost:8000/workers/performance | jq '{
  avg_processing_time: .avg_processing_time,
  throughput: .throughput,
  resource_utilization: .resource_utilization
}'

# Adjust worker configuration
curl -X POST http://localhost:8000/admin/optimization/workers -d '{
  "max_concurrent_jobs": 10,
  "job_timeout": 300,
  "enable_adaptive_scaling": true
}'
```

## Conclusion

This operations runbook provides comprehensive procedures for managing the TVDb001 system in production. The runbook covers all aspects of system operation, from daily maintenance to emergency procedures, ensuring system reliability and cost control.

### Key Operational Principles
1. **Cost Control First**: Always prioritize cost control and budget management
2. **Service Reliability**: Maintain high service availability through monitoring and fallback
3. **Gradual Recovery**: Use incremental approaches for service restoration
4. **Continuous Monitoring**: Maintain real-time visibility into system health and costs
5. **Documentation**: Keep all procedures updated and accessible

### Success Metrics
- **Uptime**: Maintain 99.9% system availability
- **Cost Control**: Stay within daily budget limits
- **Performance**: Maintain response times within acceptable limits
- **Reliability**: Minimize service disruptions and errors

### Next Steps
1. **Review and Update**: Regularly review and update this runbook
2. **Training**: Ensure all operators are familiar with these procedures
3. **Testing**: Regularly test emergency procedures and recovery processes
4. **Improvement**: Continuously improve procedures based on operational experience

---

**Document Status**: ✅ COMPLETED  
**Last Updated**: December 2024  
**Next Review**: January 2025  
**Operational Status**: ✅ PRODUCTION READY  
**Maintenance Required**: Regular review and updates
