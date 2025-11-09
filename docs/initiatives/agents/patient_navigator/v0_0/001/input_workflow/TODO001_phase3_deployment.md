# Phase 3 Deployment Guide - Input Processing Workflow

## Deployment Overview

Phase 3 deployment focuses on production-ready deployment of the Insurance Navigator Input Processing Workflow with comprehensive fallback systems, performance optimization, and monitoring capabilities.

## Deployment Strategy

### 1. Three-Stage Deployment Process

**Stage 1: Local Development**
- Mock providers for rapid iteration
- Local testing and validation
- Development environment configuration

**Stage 2: Staging Environment**
- Real API integration testing
- Performance and load testing
- Security and compliance validation
- User acceptance testing (UAT)

**Stage 3: Production Deployment**
- Gradual rollout with monitoring
- Performance validation
- Error rate monitoring
- User feedback collection

### 2. Deployment Architecture

**Containerized Deployment**: Docker containers for consistency
**Load Balancing**: Multiple instances for high availability
**Database Integration**: Supabase for data persistence
**Monitoring**: Comprehensive logging and metrics
**Security**: API key management and access control

## Pre-Deployment Requirements

### 1. Environment Configuration

#### 1.1 Environment Variables

**Required Variables**:
```bash
# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_BASE_URL=https://api.elevenlabs.io/v1

# Flash v2.5 Configuration
FLASH_API_KEY=your_flash_api_key
FLASH_BASE_URL=https://api.flash.ai/v2.5
FLASH_MOCK_ENABLED=false

# Circuit Breaker Configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60.0
CIRCUIT_BREAKER_EXPECTED_TIMEOUT=30.0

# Performance Configuration
PERFORMANCE_MONITORING_ENABLED=true
PERFORMANCE_METRICS_RETENTION=24h
PERFORMANCE_EXPORT_ENABLED=true

# Quality Configuration
QUALITY_VALIDATION_ENABLED=true
MIN_TRANSLATION_ACCURACY=0.7
MIN_SANITIZATION_EFFECTIVENESS=0.6
MIN_INTENT_PRESERVATION=0.8

# Security Configuration
API_KEY_ROTATION_ENABLED=true
RATE_LIMITING_ENABLED=true
AUDIT_LOGGING_ENABLED=true
```

**Optional Variables**:
```bash
# Development Configuration
DEBUG_MODE=false
LOG_LEVEL=INFO
MOCK_PROVIDERS_ENABLED=false

# Performance Tuning
CACHE_ENABLED=true
CACHE_TTL=3600
MAX_CONCURRENT_REQUESTS=100

# Monitoring Configuration
METRICS_EXPORT_INTERVAL=300
HEALTH_CHECK_INTERVAL=60
```

#### 1.2 Configuration Files

**Configuration Priority**:
1. Environment variables (highest priority)
2. Configuration files
3. Default values (lowest priority)

**Configuration Validation**:
```python
# Configuration validation rules
- Required API keys must be present
- Timeout values must be positive
- Quality thresholds must be 0.0-1.0
- Cache TTL must be positive
- Performance intervals must be reasonable
```

### 2. Infrastructure Requirements

#### 2.1 Compute Resources

**Minimum Requirements**:
- **CPU**: 2 vCPUs per instance
- **Memory**: 4GB RAM per instance
- **Storage**: 20GB SSD per instance
- **Network**: 100 Mbps bandwidth

**Recommended Requirements**:
- **CPU**: 4 vCPUs per instance
- **Memory**: 8GB RAM per instance
- **Storage**: 50GB SSD per instance
- **Network**: 1 Gbps bandwidth

**Scaling Configuration**:
- **Auto-scaling**: Enabled with CPU/memory thresholds
- **Min Instances**: 2 for high availability
- **Max Instances**: 10 for load handling
- **Scale-up Threshold**: 70% CPU or memory usage
- **Scale-down Threshold**: 30% CPU and memory usage

#### 2.2 Database Requirements

**Supabase Configuration**:
- **Database**: PostgreSQL 15+
- **Connection Pool**: 20-100 connections
- **Backup**: Daily automated backups
- **Monitoring**: Query performance monitoring

**Database Tables**:
```sql
-- Performance metrics table
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    operation_name VARCHAR(255) NOT NULL,
    duration_ms INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    error_type VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW(),
    context JSONB
);

-- Quality validation results
CREATE TABLE quality_validation (
    id SERIAL PRIMARY KEY,
    input_hash VARCHAR(64) NOT NULL,
    translation_accuracy DECIMAL(3,2),
    sanitization_effectiveness DECIMAL(3,2),
    intent_preservation DECIMAL(3,2),
    overall_score DECIMAL(3,2),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Circuit breaker state
CREATE TABLE circuit_breaker_state (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(100) NOT NULL,
    state VARCHAR(20) NOT NULL,
    failure_count INTEGER DEFAULT 0,
    last_failure_time TIMESTAMP,
    last_state_change TIMESTAMP DEFAULT NOW()
);
```

#### 2.3 Network Requirements

**Load Balancer Configuration**:
- **Health Checks**: Every 30 seconds
- **Session Affinity**: Disabled (stateless design)
- **SSL Termination**: Enabled with valid certificates
- **Rate Limiting**: 1000 requests per minute per IP

**Security Groups**:
- **Inbound**: HTTPS (443), HTTP (80) for health checks
- **Outbound**: All traffic to external APIs
- **Internal**: Communication between instances

## Deployment Process

### 1. Local Development Setup

#### 1.1 Development Environment

**Prerequisites**:
```bash
# Python 3.11+ installation
python --version

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Dependencies installation
pip install -r requirements-dev.txt
```

**Local Configuration**:
```bash
# Copy environment template
cp .env.example .env.local

# Configure local environment
ELEVENLABS_API_KEY=your_dev_key
FLASH_API_KEY=your_dev_key
FLASH_MOCK_ENABLED=true
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

**Local Testing**:
```bash
# Run unit tests
pytest tests/agents/patient_navigator/input_processing/

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/load/ -v

# Run security tests
pytest tests/security/ -v
```

#### 1.2 Mock Provider Testing

**Mock Configuration**:
```python
# Enable mock providers for local development
MOCK_PROVIDERS_ENABLED=true
FLASH_MOCK_ENABLED=true

# Mock provider behavior simulation
MOCK_RESPONSE_DELAY=0.1  # 100ms delay
MOCK_ERROR_RATE=0.05     # 5% error rate
MOCK_PERFORMANCE_VARIANCE=0.2  # 20% variance
```

### 2. Staging Environment Deployment

#### 2.1 Staging Infrastructure

**Environment Setup**:
```bash
# Staging environment variables
ENVIRONMENT=staging
ELEVENLABS_API_KEY=your_staging_key
FLASH_API_KEY=your_staging_key
FLASH_MOCK_ENABLED=false
DEBUG_MODE=false
LOG_LEVEL=INFO
```

**Staging Configuration**:
```yaml
# docker-compose.staging.yml
version: '3.8'
services:
  input-processing:
    build: .
    environment:
      - ENVIRONMENT=staging
      - ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
      - FLASH_API_KEY=${FLASH_API_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    depends_on:
      - supabase
    restart: unless-stopped
```

#### 2.2 Staging Testing

**Integration Testing**:
```bash
# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Run integration tests
pytest tests/integration/ --env=staging

# Run performance tests
pytest tests/load/ --env=staging

# Run security tests
pytest tests/security/ --env=staging
```

**User Acceptance Testing**:
- Test real API integrations
- Validate fallback systems
- Verify error handling
- Test performance under load
- Validate quality metrics

### 3. Production Deployment

#### 3.1 Production Infrastructure

**Production Configuration**:
```yaml
# docker-compose.production.yml
version: '3.8'
services:
  input-processing:
    build: .
    environment:
      - ENVIRONMENT=production
      - ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
      - FLASH_API_KEY=${FLASH_API_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./metrics:/app/metrics
    depends_on:
      - supabase
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

**Load Balancer Configuration**:
```nginx
# nginx.conf
upstream input_processing {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name api.insurancenavigator.com;
    
    location / {
        proxy_pass http://input_processing;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api burst=100 nodelay;
        limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    }
}
```

#### 3.2 Production Validation

**Deployment Validation**:
```bash
# Deploy to production
docker-compose -f docker-compose.production.yml up -d

# Health check validation
curl -f http://localhost:8000/health

# Smoke test execution
pytest tests/smoke/ --env=production

# Performance baseline validation
pytest tests/performance/ --env=production
```

**Monitoring Validation**:
- Verify metrics collection
- Validate error rate monitoring
- Check performance baselines
- Confirm fallback system status

## Monitoring and Observability

### 1. Health Monitoring

#### 1.1 Health Check Endpoints

**Health Check API**:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

@app.get("/health/detailed")
async def detailed_health_check():
    return {
        "status": "healthy",
        "providers": {
            "elevenlabs": await check_provider_health("elevenlabs"),
            "flash": await check_provider_health("flash"),
            "mock": await check_provider_health("mock")
        },
        "circuit_breakers": await get_circuit_breaker_status(),
        "performance": await get_performance_summary()
    }
```

**Health Check Configuration**:
```yaml
# Health check intervals
HEALTH_CHECK_INTERVAL=60s
HEALTH_CHECK_TIMEOUT=10s
HEALTH_CHECK_RETRIES=3

# Health check thresholds
HEALTH_CHECK_FAILURE_THRESHOLD=3
HEALTH_CHECK_RECOVERY_THRESHOLD=2
```

#### 1.2 Performance Monitoring

**Performance Metrics**:
```python
# Key performance indicators
- Response time (p50, p95, p99)
- Throughput (requests per second)
- Error rate (percentage)
- Circuit breaker state changes
- Fallback activation frequency
- Quality validation scores
- Cost optimization effectiveness
```

**Performance Dashboards**:
- Real-time performance metrics
- Historical performance trends
- Provider performance comparison
- Error rate monitoring
- Quality score tracking

### 2. Logging and Tracing

#### 2.1 Logging Configuration

**Log Levels**:
```python
# Log level configuration
DEBUG: Detailed debugging information
INFO: General operational information
WARNING: Warning messages for potential issues
ERROR: Error messages for actual problems
CRITICAL: Critical errors requiring immediate attention
```

**Log Format**:
```python
# Structured logging format
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "service": "input_processing",
    "operation": "translate_with_fallback",
    "provider": "elevenlabs",
    "duration_ms": 1250,
    "success": true,
    "context": {
        "source_language": "es",
        "target_language": "en",
        "text_length": 150
    }
}
```

#### 2.2 Distributed Tracing

**Trace Configuration**:
```python
# Trace context propagation
TRACE_ID_HEADER = "X-Trace-ID"
SPAN_ID_HEADER = "X-Span-ID"

# Trace sampling configuration
TRACE_SAMPLING_RATE = 0.1  # 10% of requests
TRACE_SAMPLING_RULES = {
    "error_requests": 1.0,  # 100% of error requests
    "slow_requests": 0.5,   # 50% of slow requests (>2s)
    "fallback_requests": 1.0  # 100% of fallback requests
}
```

## Security and Compliance

### 1. Security Configuration

#### 1.1 API Security

**API Key Management**:
```python
# API key rotation
API_KEY_ROTATION_ENABLED = True
API_KEY_ROTATION_INTERVAL = 30  # days
API_KEY_EXPIRY_NOTIFICATION = 7  # days before expiry

# API key validation
API_KEY_VALIDATION_ENABLED = True
API_KEY_FORMAT_VALIDATION = True
API_KEY_PERMISSION_VALIDATION = True
```

**Rate Limiting**:
```python
# Rate limiting configuration
RATE_LIMITING_ENABLED = True
RATE_LIMIT_REQUESTS_PER_MINUTE = 1000
RATE_LIMIT_BURST_SIZE = 100
RATE_LIMIT_STRATEGY = "token_bucket"
```

#### 1.2 Data Security

**Data Encryption**:
```python
# Data encryption configuration
DATA_ENCRYPTION_ENABLED = True
ENCRYPTION_ALGORITHM = "AES-256-GCM"
ENCRYPTION_KEY_ROTATION = True
ENCRYPTION_KEY_ROTATION_INTERVAL = 90  # days
```

**Privacy Protection**:
```python
# Privacy protection features
PII_DETECTION_ENABLED = True
PII_MASKING_ENABLED = True
AUDIT_LOGGING_ENABLED = True
DATA_RETENTION_POLICY = "30_days"
```

### 2. Compliance Requirements

#### 2.1 HIPAA Compliance

**HIPAA Requirements**:
- Data encryption at rest and in transit
- Access control and authentication
- Audit logging and monitoring
- Data backup and recovery
- Incident response procedures

**Compliance Validation**:
```python
# HIPAA compliance checks
HIPAA_COMPLIANCE_ENABLED = True
HIPAA_AUDIT_LOGGING = True
HIPAA_DATA_ENCRYPTION = True
HIPAA_ACCESS_CONTROL = True
HIPAA_INCIDENT_RESPONSE = True
```

#### 2.2 Insurance Industry Compliance

**Industry Standards**:
- SOC 2 Type II compliance
- ISO 27001 security standards
- PCI DSS compliance (if applicable)
- State insurance regulations
- Federal compliance requirements

## Rollback and Recovery

### 1. Rollback Strategy

#### 1.1 Rollback Triggers

**Automatic Rollback**:
- Error rate > 5% for 5 minutes
- Response time > 10 seconds (p95)
- Health check failures > 3 consecutive
- Circuit breaker activation > 80% of providers

**Manual Rollback**:
- User-reported issues
- Performance degradation
- Security vulnerabilities
- Compliance violations

#### 1.2 Rollback Process

**Rollback Steps**:
1. Stop new deployment
2. Revert to previous version
3. Validate system health
4. Monitor performance metrics
5. Investigate root cause
6. Plan remediation

### 2. Disaster Recovery

#### 2.1 Recovery Procedures

**Recovery Scenarios**:
- Complete system failure
- Database corruption
- Provider API outages
- Security breaches
- Natural disasters

**Recovery Steps**:
1. Assess damage and scope
2. Activate disaster recovery plan
3. Restore from backups
4. Validate system integrity
5. Resume normal operations
6. Post-incident analysis

## Performance Optimization

### 1. Caching Strategy

#### 1.1 Cache Configuration

**Cache Levels**:
```python
# Multi-level caching
SESSION_CACHE: Redis for session data
PERSISTENCE_CACHE: Database for persistent data
PROVIDER_CACHE: In-memory for provider responses
```

**Cache Policies**:
```python
# Cache configuration
CACHE_TTL = 3600  # 1 hour
CACHE_MAX_SIZE = 10000  # entries
CACHE_EVICTION_POLICY = "LRU"
CACHE_PERSISTENCE = True
```

#### 1.2 Cache Optimization

**Cache Warming**:
- Pre-load common translations
- Cache insurance terminology
- Warm provider connections
- Optimize cache hit rates

### 2. Load Balancing

#### 2.1 Load Balancer Configuration

**Load Balancing Strategy**:
- Round-robin distribution
- Health check-based routing
- Performance-based routing
- Geographic distribution

**Load Balancer Health Checks**:
- HTTP health check endpoint
- Response time monitoring
- Error rate monitoring
- Circuit breaker status

## Deployment Validation

### 1. Post-Deployment Testing

#### 1.1 Smoke Tests

**Smoke Test Scenarios**:
```python
# Basic functionality validation
def test_basic_translation():
    """Test basic translation functionality"""
    
def test_fallback_system():
    """Test fallback system activation"""
    
def test_error_handling():
    """Test error handling and recovery"""
    
def test_performance_monitoring():
    """Test performance monitoring functionality"""
```

#### 1.2 Performance Validation

**Performance Baselines**:
- Response time < 2 seconds (p95)
- Throughput > 100 requests/second
- Error rate < 1%
- Circuit breaker activation < 5%

### 2. Monitoring Validation

#### 2.1 Metrics Validation

**Key Metrics**:
- System health status
- Performance metrics
- Error rates and types
- Circuit breaker states
- Fallback activation frequency

#### 2.2 Alert Configuration

**Alert Thresholds**:
- Error rate > 5%
- Response time > 5 seconds
- Circuit breaker activation > 80%
- Provider health check failures

## Conclusion

Phase 3 deployment provides:

1. **Production Readiness**: Comprehensive testing and validation
2. **High Availability**: Load balancing and failover systems
3. **Performance Optimization**: Caching and load distribution
4. **Security and Compliance**: HIPAA and industry standards
5. **Monitoring and Observability**: Real-time metrics and alerts
6. **Disaster Recovery**: Rollback and recovery procedures

This deployment approach ensures the Input Processing Workflow is ready for production use while maintaining high reliability, performance, and security standards. 