# Patient Navigator Supervisor Workflow - Deployment Guide

**Version**: 1.0.0  
**Date**: August 5, 2025  
**Status**: Production Ready  

## Overview

This deployment guide provides step-by-step instructions for deploying the Patient Navigator Supervisor Workflow MVP to production. The guide covers installation, configuration, monitoring, and maintenance procedures.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Security Configuration](#security-configuration)
6. [Monitoring Setup](#monitoring-setup)
7. [Testing](#testing)
8. [Production Deployment](#production-deployment)
9. [Maintenance](#maintenance)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python**: 3.9+ (recommended 3.11+)
- **Memory**: Minimum 512MB RAM, recommended 1GB+
- **Storage**: 100MB for application code and dependencies
- **Network**: Internet access for LLM API calls and Supabase connectivity

### Dependencies

```bash
# Core dependencies
langgraph>=0.2.0
pydantic>=2.0.0
anthropic>=0.25.0
supabase>=2.0.0

# Optional dependencies for production
prometheus-client>=0.17.0
structlog>=23.0.0
```

### External Services

- **Supabase**: Database for document storage and user management
- **Anthropic Claude API**: LLM service for workflow prescription
- **Authentication Service**: User authentication and authorization

## Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd insurance_navigator
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
# Test import
python -c "from agents.patient_navigator.supervisor import SupervisorWorkflow; print('Installation successful')"

# Run tests
python -m pytest tests/agents/test_supervisor_phase4.py -v
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# LLM Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Workflow Configuration
SUPERVISOR_WORKFLOW_MOCK_MODE=false
SUPERVISOR_WORKFLOW_TIMEOUT=30
SUPERVISOR_WORKFLOW_MAX_RETRIES=3

# Performance Configuration
DOCUMENT_CHECK_TIMEOUT=500
WORKFLOW_PRESCRIPTION_TIMEOUT=1000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security Configuration
ENABLE_AUDIT_LOGGING=true
HIPAA_COMPLIANCE_MODE=true
```

### Configuration Validation

```python
# Test configuration
from agents.patient_navigator.supervisor import SupervisorWorkflow

# Test with mock mode first
workflow = SupervisorWorkflow(use_mock=True)
print("Mock mode configuration successful")

# Test production configuration
workflow = SupervisorWorkflow(use_mock=False)
print("Production configuration successful")
```

## Database Setup

### Supabase Configuration

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Note project URL and API keys

2. **Database Schema**
   ```sql
   -- Documents table (if not exists)
   CREATE TABLE IF NOT EXISTS documents (
       id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
       user_id UUID NOT NULL,
       document_type TEXT NOT NULL,
       file_path TEXT,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Row Level Security
   ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

   -- RLS Policies
   CREATE POLICY "Users can view own documents" ON documents
       FOR SELECT USING (auth.uid() = user_id);

   CREATE POLICY "Users can insert own documents" ON documents
       FOR INSERT WITH CHECK (auth.uid() = user_id);
   ```

3. **Test Database Connection**
   ```python
   from supabase import create_client
   import os

   supabase = create_client(
       os.getenv("SUPABASE_URL"),
       os.getenv("SUPABASE_ANON_KEY")
   )

   # Test connection
   response = supabase.table("documents").select("count").execute()
   print("Database connection successful")
   ```

## Security Configuration

### HIPAA Compliance Setup

1. **Audit Logging**
   ```python
   # Enable comprehensive audit logging
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s [%(levelname)s] %(message)s',
       handlers=[
           logging.FileHandler('audit.log'),
           logging.StreamHandler()
       ]
   )
   ```

2. **Data Encryption**
   - Ensure Supabase uses encrypted connections (HTTPS)
   - Verify database encryption at rest
   - Use secure API key storage

3. **Access Control**
   - Implement proper user authentication
   - Use Row Level Security (RLS) policies
   - Validate user permissions before document access

### Security Validation

```python
# Test security configuration
def test_security_config():
    # Test user isolation
    workflow = SupervisorWorkflow(use_mock=False)
    
    # Test with different users
    user1_result = await workflow.execute(
        SupervisorWorkflowInput(
            user_query="Test query",
            user_id="user_1"
        )
    )
    
    user2_result = await workflow.execute(
        SupervisorWorkflowInput(
            user_query="Test query",
            user_id="user_2"
        )
    )
    
    # Verify user data isolation
    assert user1_result.user_id == "user_1"
    assert user2_result.user_id == "user_2"
```

## Monitoring Setup

### Health Checks

Create a health check endpoint:

```python
from fastapi import FastAPI, HTTPException
from agents.patient_navigator.supervisor import SupervisorWorkflow

app = FastAPI()

@app.get("/health")
async def health_check():
    try:
        # Test workflow initialization
        workflow = SupervisorWorkflow(use_mock=True)
        
        # Test basic execution
        result = await workflow.execute(
            SupervisorWorkflowInput(
                user_query="Health check",
                user_id="health_check_user"
            )
        )
        
        return {
            "status": "healthy",
            "workflow_version": "1.0.0",
            "processing_time": result.processing_time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Performance Monitoring

```python
# Add performance monitoring
import time
import prometheus_client

# Metrics
workflow_execution_time = prometheus_client.Histogram(
    'workflow_execution_seconds',
    'Time spent executing workflows'
)

workflow_success_total = prometheus_client.Counter(
    'workflow_success_total',
    'Total successful workflow executions'
)

workflow_error_total = prometheus_client.Counter(
    'workflow_error_total',
    'Total workflow execution errors'
)

# Monitor workflow execution
@workflow_execution_time.time()
async def monitored_execute(workflow, input_data):
    try:
        result = await workflow.execute(input_data)
        workflow_success_total.inc()
        return result
    except Exception as e:
        workflow_error_total.inc()
        raise
```

### Logging Configuration

```python
# Structured logging setup
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

## Testing

### Pre-Deployment Testing

1. **Unit Tests**
   ```bash
   # Run all supervisor tests
   python -m pytest tests/agents/test_supervisor_phase4.py -v
   
   # Run with coverage
   python -m pytest tests/agents/test_supervisor_phase4.py --cov=agents.patient_navigator.supervisor
   ```

2. **Integration Tests**
   ```bash
   # Test with real Supabase
   python -m pytest tests/integration/test_supervisor_integration.py -v
   ```

3. **Performance Tests**
   ```bash
   # Test performance benchmarks
   python -m pytest tests/performance/test_supervisor_performance.py -v
   ```

### Load Testing

```python
# Load testing script
import asyncio
import time
from agents.patient_navigator.supervisor import SupervisorWorkflow, SupervisorWorkflowInput

async def load_test():
    workflow = SupervisorWorkflow(use_mock=False)
    
    # Simulate concurrent requests
    tasks = []
    for i in range(10):
        task = workflow.execute(
            SupervisorWorkflowInput(
                user_query=f"Test query {i}",
                user_id=f"user_{i}"
            )
        )
        tasks.append(task)
    
    # Execute concurrently
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    print(f"Processed {len(results)} requests in {end_time - start_time:.2f}s")
    print(f"Average time: {(end_time - start_time) / len(results):.2f}s per request")
```

## Production Deployment

### Step 1: Environment Preparation

```bash
# Set production environment
export NODE_ENV=production
export SUPERVISOR_WORKFLOW_MOCK_MODE=false

# Verify configuration
python scripts/verify_config.py
```

### Step 2: Database Migration

```bash
# Run database migrations
python scripts/migrate_database.py

# Verify database schema
python scripts/verify_database.py
```

### Step 3: Service Deployment

```bash
# Start the service
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Or using systemd service
sudo systemctl start supervisor-workflow
sudo systemctl enable supervisor-workflow
```

### Step 4: Health Check Verification

```bash
# Verify service is running
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "workflow_version": "1.0.0",
#   "processing_time": 0.01
# }
```

### Step 5: Monitoring Activation

```bash
# Start monitoring
python scripts/start_monitoring.py

# Verify metrics endpoint
curl http://localhost:8000/metrics
```

## Maintenance

### Daily Operations

1. **Health Check Monitoring**
   ```bash
   # Check service health
   curl http://localhost:8000/health
   
   # Check logs for errors
   tail -f /var/log/supervisor-workflow/application.log
   ```

2. **Performance Monitoring**
   ```bash
   # Monitor performance metrics
   curl http://localhost:8000/metrics | grep workflow
   
   # Check database performance
   python scripts/check_database_performance.py
   ```

3. **Backup Procedures**
   ```bash
   # Backup configuration
   cp .env .env.backup.$(date +%Y%m%d)
   
   # Backup logs
   tar -czf logs_backup_$(date +%Y%m%d).tar.gz /var/log/supervisor-workflow/
   ```

### Weekly Maintenance

1. **Log Rotation**
   ```bash
   # Rotate log files
   logrotate /etc/logrotate.d/supervisor-workflow
   ```

2. **Performance Review**
   ```bash
   # Generate performance report
   python scripts/generate_performance_report.py
   ```

3. **Security Audit**
   ```bash
   # Run security scan
   python scripts/security_audit.py
   ```

### Monthly Maintenance

1. **Dependency Updates**
   ```bash
   # Update dependencies
   pip install --upgrade -r requirements.txt
   
   # Test after updates
   python -m pytest tests/agents/test_supervisor_phase4.py -v
   ```

2. **Database Optimization**
   ```bash
   # Optimize database
   python scripts/optimize_database.py
   ```

3. **Configuration Review**
   ```bash
   # Review and update configuration
   python scripts/review_configuration.py
   ```

## Troubleshooting

### Common Issues

#### 1. LLM Service Unavailable

**Symptoms**: Workflow prescription fails with LLM errors

**Solutions**:
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "claude-3-sonnet-20240229", "max_tokens": 10, "messages": [{"role": "user", "content": "test"}]}' \
     https://api.anthropic.com/v1/messages

# Enable mock mode temporarily
export SUPERVISOR_WORKFLOW_MOCK_MODE=true
```

#### 2. Supabase Connection Issues

**Symptoms**: Document availability checks fail

**Solutions**:
```bash
# Check Supabase configuration
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# Test database connection
python scripts/test_database_connection.py

# Check RLS policies
python scripts/verify_rls_policies.py
```

#### 3. Performance Issues

**Symptoms**: Slow workflow execution times

**Solutions**:
```bash
# Check resource usage
top -p $(pgrep -f supervisor-workflow)

# Monitor database performance
python scripts/monitor_database_performance.py

# Check network latency
ping your-supabase-project.supabase.co
```

#### 4. Memory Issues

**Symptoms**: Out of memory errors

**Solutions**:
```bash
# Check memory usage
free -h

# Restart service with more memory
systemctl restart supervisor-workflow

# Monitor memory usage
python scripts/monitor_memory_usage.py
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Restart service
systemctl restart supervisor-workflow

# Monitor debug logs
tail -f /var/log/supervisor-workflow/debug.log
```

### Emergency Procedures

#### Service Recovery

```bash
# Emergency restart
systemctl restart supervisor-workflow

# Check service status
systemctl status supervisor-workflow

# View recent logs
journalctl -u supervisor-workflow -f
```

#### Fallback Mode

```bash
# Enable mock mode for emergency operation
export SUPERVISOR_WORKFLOW_MOCK_MODE=true
systemctl restart supervisor-workflow
```

#### Database Recovery

```bash
# Check database connectivity
python scripts/check_database_health.py

# Restore from backup if needed
python scripts/restore_database_backup.py
```

## Support

### Getting Help

1. **Documentation**: Review this deployment guide and API documentation
2. **Logs**: Check application logs for detailed error information
3. **Monitoring**: Use built-in monitoring for performance analysis
4. **Testing**: Use mock mode for development and testing

### Contact Information

- **Technical Issues**: Check logs and monitoring dashboards
- **Configuration Questions**: Review configuration documentation
- **Performance Issues**: Use performance monitoring tools
- **Security Concerns**: Review security audit reports

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-08-05  
**Status**: Production Ready 