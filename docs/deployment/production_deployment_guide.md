# Production Deployment Guide for 003 Worker Refactor

## Overview

This guide provides comprehensive instructions for deploying the 003 Worker Refactor to production. The deployment process follows a local-first development approach, ensuring that production functionality matches the local environment baseline established in Phase 6.

## Prerequisites

### Required Tools
- Docker and Docker Compose
- Python 3.8+
- Git
- Access to production infrastructure
- Production environment variables configured

### Required Files
- `infrastructure/config/production.yaml` - Production configuration
- `infrastructure/deployment/production_deployer.py` - Deployment orchestrator
- `infrastructure/monitoring/production_monitor.py` - Production monitoring
- `infrastructure/testing/production_validation.py` - Production validation
- `scripts/deployment/deploy_production.sh` - Deployment script
- `.env.production` - Production environment variables

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://username:password@host:port/database

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# External Services
LLAMAPARSE_API_KEY=your_llamaparse_api_key
OPENAI_API_KEY=your_openai_api_key

# Security
JWT_SECRET_KEY=your_jwt_secret_key
```

## Deployment Architecture

### Components
1. **Infrastructure Layer**
   - Production database (PostgreSQL)
   - Storage services (Supabase)
   - Monitoring infrastructure

2. **Application Layer**
   - API Server (FastAPI)
   - BaseWorker (Celery)
   - Testing infrastructure

3. **Monitoring Layer**
   - Real-time monitoring dashboard
   - Alerting system (Slack, Email, PagerDuty)
   - Metrics collection and analysis

### Deployment Flow
```
Local Environment → Production Validation → Infrastructure Deployment → Application Deployment → Validation → Monitoring → Health Check
```

## Pre-Deployment Checklist

### 1. Local Environment Validation
- [ ] Phase 6 local environment is fully functional
- [ ] All tests pass in local environment
- [ ] Local monitoring is working correctly
- [ ] Local validation baseline is documented

### 2. Production Environment Preparation
- [ ] Production database is accessible
- [ ] Production storage is configured
- [ ] Production monitoring is set up
- [ ] Production environment variables are configured

### 3. Security Review
- [ ] All API keys are valid and have correct permissions
- [ ] Database connections use SSL
- [ ] CORS settings are properly configured
- [ ] Rate limiting is enabled
- [ ] Audit logging is configured

### 4. Backup and Recovery
- [ ] Current production state is backed up
- [ ] Rollback procedures are documented
- [ ] Recovery procedures are tested
- [ ] Backup retention policies are configured

## Deployment Process

### Step 1: Pre-Deployment Validation
```bash
# Run pre-deployment checks
./scripts/deployment/deploy_production.sh --dry-run
```

This step validates:
- Prerequisites are met
- Configuration files are valid
- Environment variables are set
- Required tools are available

### Step 2: Infrastructure Deployment
```bash
# Deploy infrastructure components
python3 infrastructure/deployment/production_deployer.py infrastructure/config/production.yaml --deploy-infrastructure
```

This step deploys:
- Database schema updates
- Storage configuration
- Monitoring infrastructure
- Security settings

### Step 3: Application Deployment
```bash
# Deploy applications
python3 infrastructure/deployment/production_deployer.py infrastructure/config/production.yaml --deploy-applications
```

This step deploys:
- API server
- BaseWorker
- Testing infrastructure
- Configuration updates

### Step 4: Post-Deployment Validation
```bash
# Validate deployment
python3 infrastructure/testing/production_validation.py infrastructure/config/production.yaml
```

This step validates:
- Infrastructure deployment
- Database connectivity
- API server functionality
- BaseWorker functionality
- External service integration
- End-to-end pipeline
- Performance metrics
- Security compliance

### Step 5: Start Monitoring
```bash
# Start production monitoring
python3 infrastructure/monitoring/production_monitor.py infrastructure/config/production.yaml
```

This step starts:
- Real-time monitoring dashboard
- Alerting system
- Metrics collection
- Health monitoring

### Step 6: Smoke Tests
```bash
# Run smoke tests
./scripts/deployment/deploy_production.sh --skip-validation
```

This step runs:
- API health checks
- Database connectivity tests
- Basic functionality tests
- Performance baseline tests

### Step 7: Health Check
```bash
# Perform comprehensive health check
# This is automatically done by the deployment script
```

This step verifies:
- All services are running
- Performance metrics are within acceptable ranges
- Error rates are minimal
- Resource usage is optimal

## Automated Deployment

### Using the Deployment Script
```bash
# Full deployment with validation
./scripts/deployment/deploy_production.sh

# Dry run (no actual deployment)
./scripts/deployment/deploy_production.sh --dry-run

# Skip validation
./scripts/deployment/deploy_production.sh --skip-validation

# Disable auto-rollback
./scripts/deployment/deploy_production.sh --no-rollback
```

### Deployment Script Features
- **Prerequisites Check**: Validates all requirements
- **Backup Creation**: Creates backup before deployment
- **Infrastructure Deployment**: Deploys infrastructure components
- **Application Deployment**: Deploys application components
- **Validation**: Runs comprehensive validation tests
- **Monitoring Start**: Starts production monitoring
- **Smoke Tests**: Runs basic functionality tests
- **Health Check**: Performs comprehensive health check
- **Auto-rollback**: Automatically rolls back on failure
- **Logging**: Comprehensive logging of all operations

## Validation and Testing

### Production Validation Suite
The production validation script tests:

1. **Infrastructure Validation**
   - Database connectivity and performance
   - Storage service accessibility
   - Network connectivity
   - Resource availability

2. **Application Validation**
   - API server functionality
   - BaseWorker processing
   - Database operations
   - External service integration

3. **Pipeline Validation**
   - End-to-end document processing
   - State machine transitions
   - Error handling and recovery
   - Performance metrics

4. **Security Validation**
   - Authentication and authorization
   - Data encryption
   - Audit logging
   - Compliance requirements

5. **Monitoring Validation**
   - Alerting system functionality
   - Metrics collection
   - Dashboard accessibility
   - Incident response procedures

### Baseline Comparison
The validation compares production behavior against the local environment baseline:
- Processing times
- Error rates
- Resource usage
- Functionality correctness
- Performance characteristics

## Monitoring and Alerting

### Real-Time Dashboard
- System health metrics
- Application performance
- Database performance
- External service status
- Error rates and trends

### Alerting System
- **Critical Alerts**: Immediate response required
- **Warning Alerts**: Attention needed within 15 minutes
- **Info Alerts**: Informational notifications

### Notification Channels
- Slack channels
- Email notifications
- PagerDuty escalations
- SMS alerts (for critical issues)

### Metrics Collection
- System metrics (CPU, memory, disk, network)
- Application metrics (response times, throughput, error rates)
- Business metrics (document processing rates, success rates)
- Custom metrics (pipeline stage performance, external service latency)

## Rollback Procedures

### Automatic Rollback
The deployment script automatically rolls back on:
- Validation failures
- Smoke test failures
- Health check failures
- Critical errors

### Manual Rollback
```bash
# Stop monitoring
pkill -f production_monitor.py

# Restore from backup
cp -r backups/pre_deployment_<ID>/config/* infrastructure/config/
cp -r backups/pre_deployment_<ID>/deployment/* infrastructure/deployment/
cp -r backups/pre_deployment_<ID>/monitoring/* infrastructure/monitoring/

# Restart services
# (Follow service-specific restart procedures)
```

### Rollback Validation
After rollback:
1. Verify services are running
2. Run smoke tests
3. Check monitoring is functional
4. Validate data integrity

## Post-Deployment Operations

### Ongoing Monitoring
- Monitor system health continuously
- Review alert history
- Analyze performance trends
- Optimize resource usage

### Maintenance Procedures
- Regular backup verification
- Performance optimization
- Security updates
- Compliance audits

### Incident Response
- Follow incident response procedures
- Escalate issues according to severity
- Document all incidents
- Implement preventive measures

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
python3 -c "
import asyncio
import sys
sys.path.append('backend')
from shared.database import DatabaseManager
from shared.config import ProductionConfig
import yaml

async def test_db():
    with open('infrastructure/config/production.yaml', 'r') as f:
        config_data = yaml.safe_load(f)
    config = ProductionConfig(**config_data)
    db = DatabaseManager(config.database_url)
    await db.connect()
    await db.execute_query('SELECT 1')
    await db.disconnect()

asyncio.run(test_db())
"
```

#### API Server Issues
```bash
# Check API server health
curl -f https://your-api-domain.com/health

# Check API server logs
tail -f logs/api_server.log
```

#### Worker Issues
```bash
# Check worker status
python3 -c "
import sys
sys.path.append('backend')
from shared.worker import BaseWorker
from shared.config import ProductionConfig
import yaml

with open('infrastructure/config/production.yaml', 'r') as f:
    config_data = yaml.safe_load(f)
config = ProductionConfig(**config_data)
worker = BaseWorker(config)
print(f'Worker status: {worker.get_status()}')
"
```

### Debug Mode
Enable debug mode for troubleshooting:
```bash
# Set debug environment variable
export DEBUG=true

# Run deployment with debug logging
./scripts/deployment/deploy_production.sh --dry-run
```

## Performance Optimization

### Database Optimization
- Connection pooling configuration
- Query optimization
- Index management
- Performance monitoring

### Application Optimization
- Worker concurrency settings
- Cache configuration
- Async processing optimization
- Resource allocation

### Infrastructure Optimization
- Auto-scaling configuration
- Load balancing
- Resource monitoring
- Cost optimization

## Security Considerations

### Access Control
- API key management
- JWT token configuration
- Role-based access control
- IP whitelisting

### Data Protection
- Encryption at rest and in transit
- Secure credential storage
- Audit logging
- Data retention policies

### Compliance
- HIPAA compliance measures
- GDPR compliance
- SOC2 compliance
- Regular security audits

## Compliance and Auditing

### HIPAA Compliance
- Data encryption
- Access logging
- Audit trails
- Data retention policies

### GDPR Compliance
- Data processing transparency
- Right to be forgotten
- Data portability
- Consent management

### Audit Requirements
- Comprehensive logging
- Audit trail maintenance
- Compliance reporting
- Regular audits

## Cost Management

### Resource Monitoring
- CPU and memory usage
- Storage utilization
- Network bandwidth
- External API costs

### Optimization Strategies
- Auto-scaling policies
- Resource scheduling
- Cost allocation
- Performance optimization

### Budget Controls
- Cost alerts
- Usage limits
- Resource quotas
- Cost reporting

## Documentation and Training

### Runbooks
- Deployment procedures
- Troubleshooting guides
- Maintenance procedures
- Emergency procedures

### Training Materials
- System architecture overview
- Operational procedures
- Troubleshooting techniques
- Best practices

### Knowledge Transfer
- Team training sessions
- Documentation reviews
- Procedure walkthroughs
- Incident post-mortems

## Future Considerations

### Scalability Planning
- Performance monitoring
- Capacity planning
- Scaling strategies
- Resource optimization

### Technology Evolution
- Framework updates
- Dependency management
- Security updates
- Performance improvements

### Operational Excellence
- Process improvement
- Automation opportunities
- Monitoring enhancements
- Incident prevention

## Support and Maintenance

### Ongoing Support
- 24/7 monitoring
- Incident response
- Performance optimization
- Security updates

### Maintenance Schedule
- Regular backups
- Security patches
- Performance tuning
- Compliance audits

### Continuous Improvement
- Process optimization
- Tool enhancement
- Automation improvement
- Best practice updates

## Conclusion

This production deployment guide provides comprehensive coverage of deploying the 003 Worker Refactor to production. The local-first development approach ensures reliable deployments, while comprehensive validation and monitoring provide operational confidence.

Key success factors:
1. **Thorough preparation**: Complete local validation and production preparation
2. **Comprehensive validation**: Extensive testing against local baseline
3. **Robust monitoring**: Real-time monitoring and alerting
4. **Automated rollback**: Quick recovery from deployment issues
5. **Ongoing optimization**: Continuous improvement and monitoring

For additional support or questions, refer to the project documentation or contact the development team.
