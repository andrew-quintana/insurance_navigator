# Infrastructure Validation Framework

## Overview

The Infrastructure Validation Framework for the 003 Worker Refactor provides comprehensive validation of deployment infrastructure against local environment baseline to prevent deployment configuration failures experienced in previous iterations.

This framework implements the infrastructure validation approach outlined in RFC003.md section 7, with automated validation, health checks, and rollback procedures.

## Architecture

```
infrastructure/
├── config/                 # Configuration files for different environments
│   ├── local.yaml         # Local environment baseline
│   ├── staging.yaml       # Staging deployment configuration
│   ├── production.yaml    # Production deployment configuration
│   └── rollback.yaml      # Rollback configuration
├── validation/            # Validation framework components
│   ├── deployment_validator.py    # Main deployment validator
│   └── config_validator.py        # Configuration validation
├── monitoring/            # Health monitoring and observability
│   └── health_checker.py  # Comprehensive health checker
├── scripts/               # Deployment and automation scripts
│   ├── deploy_and_verify.sh       # Main deployment script
│   └── automated_rollback.py      # Automated rollback system
└── requirements.txt       # Python dependencies
```

## Key Components

### 1. Deployment Validator (`validation/deployment_validator.py`)

Comprehensive validation of deployment infrastructure including:
- Database connectivity and schema validation
- API server health and endpoint validation
- Worker process health and functionality
- External service connectivity
- Storage configuration and accessibility
- Environment configuration validation
- Performance and security validation

**Usage:**
```bash
python validation/deployment_validator.py config/production.yaml
```

### 2. Configuration Validator (`validation/config_validator.py`)

Validates deployment configuration against local environment baseline:
- Configuration structure validation
- Environment variable validation
- Deployment-specific settings validation
- Configuration consistency checking
- Drift detection

**Usage:**
```bash
python validation/config_validator.py config/local.yaml config/production.yaml
```

### 3. Health Checker (`monitoring/health_checker.py`)

Continuous health monitoring for all infrastructure components:
- Real-time health status monitoring
- Performance bottleneck detection
- System health assessment
- Continuous monitoring mode

**Usage:**
```bash
# Single health check
python monitoring/health_checker.py config/production.yaml

# Continuous monitoring
python -c "
import asyncio
from monitoring.health_checker import HealthChecker
checker = HealthChecker('config/production.yaml')
asyncio.run(checker.start_continuous_monitoring())
"
```

### 4. Automated Rollback (`scripts/automated_rollback.py`)

Automated rollback system for failed deployments:
- Infrastructure rollback
- Application rollback
- Database rollback
- Monitoring rollback
- Rollback verification

**Usage:**
```bash
python scripts/automated_rollback.py config/production.yaml config/rollback.yaml
```

### 5. Deployment Script (`scripts/deploy_and_verify.sh`)

Main deployment and verification script implementing the workflow from RFC003.md:
- Local environment validation
- Infrastructure deployment
- Infrastructure validation
- Application deployment
- Application validation
- Smoke testing
- Continuous monitoring

**Usage:**
```bash
# Deploy to staging
./scripts/deploy_and_verify.sh staging

# Deploy to production with monitoring
./scripts/deploy_and_verify.sh -m production

# Validate only (no deployment)
./scripts/deploy_and_verify.sh -v staging

# Rollback
./scripts/deploy_and_verify.sh -r production
```

## Configuration

### Environment Configuration

Each environment has its own configuration file:

- **`local.yaml`**: Local development environment baseline
- **`staging.yaml`**: Staging deployment configuration
- **`production.yaml`**: Production deployment configuration

### Rollback Configuration

The `rollback.yaml` file defines rollback procedures and strategies for different failure scenarios.

## Quick Start

### 1. Install Dependencies

```bash
cd infrastructure
pip install -r requirements.txt
```

### 2. Validate Local Environment

```bash
# Validate local configuration
python validation/config_validator.py config/local.yaml config/local.yaml

# Run health checks on local environment
python monitoring/health_checker.py config/local.yaml
```

### 3. Validate Deployment Configuration

```bash
# Compare staging configuration with local baseline
python validation/config_validator.py config/local.yaml config/staging.yaml

# Compare production configuration with local baseline
python validation/config_validator.py config/local.yaml config/production.yaml
```

### 4. Run Complete Deployment Validation

```bash
# Deploy and validate staging
./scripts/deploy_and_verify.sh staging

# Deploy and validate production with monitoring
./scripts/deploy_and_verify.sh -m production
```

## Validation Workflow

The framework implements the validation workflow from RFC003.md:

1. **Local Environment Validation**: Ensure local environment is operational
2. **Infrastructure Deployment**: Deploy infrastructure components
3. **Infrastructure Validation**: Validate against local baseline
4. **Application Deployment**: Deploy application services
5. **Application Validation**: Validate functionality against local baseline
6. **Smoke Testing**: Run production smoke tests
7. **Continuous Monitoring**: Start health monitoring

## Health Checks

The health checker validates:

- **Database Health**: Connectivity, schema, performance, activity
- **API Server Health**: Endpoints, response times, functionality
- **Worker Process Health**: Process status, job processing, activity patterns
- **Storage Health**: Connectivity, configuration, accessibility
- **External Services**: LlamaParse, OpenAI connectivity
- **Performance Health**: Response times, bottlenecks
- **Monitoring Health**: Metrics endpoints, configuration
- **System Overall Health**: Error patterns, bottlenecks, systemic issues

## Rollback Procedures

The automated rollback system handles:

- **Infrastructure Failures**: Platform-specific rollback (Render, Docker)
- **Application Failures**: Git-based or Docker-based rollback
- **Database Failures**: Backup restoration or migration rollback
- **Monitoring Failures**: Configuration restoration
- **Complete Failures**: Full system rollback

## Monitoring and Alerting

The framework provides:

- **Real-time Health Monitoring**: Continuous health status monitoring
- **Performance Metrics**: Response time tracking and bottleneck detection
- **Alerting**: Configurable alerting for health check failures
- **Reporting**: Comprehensive health and validation reports

## Testing

### Unit Tests

```bash
# Run validation framework tests
pytest validation/ -v

# Run monitoring tests
pytest monitoring/ -v
```

### Integration Tests

```bash
# Test complete validation workflow
python -m pytest tests/integration/test_validation_workflow.py -v
```

## Configuration Examples

### Production Configuration

```yaml
database:
  url: "${DATABASE_URL}"
  pool_size: 20
  max_overflow: 30

api:
  url: "${API_BASE_URL}"
  workers: 4
  timeout: 30

worker:
  health_url: "${WORKER_HEALTH_URL}"
  max_concurrent_jobs: 10

deployment:
  platform: "render"
  environment: "production"
  auto_scaling:
    enabled: true
    min_instances: 1
    max_instances: 10
```

### Rollback Configuration

```yaml
rollback:
  timeout: 300
  max_attempts: 3
  delay: 10

render:
  services:
    - "accessa-api"
    - "accessa-worker"

verification:
  health_checks:
    - "database_connectivity"
    - "api_health"
    - "worker_health"
```

## Troubleshooting

### Common Issues

1. **Configuration Validation Failures**
   - Check environment variable configuration
   - Verify configuration file structure
   - Compare with local baseline

2. **Health Check Failures**
   - Verify service connectivity
   - Check service configuration
   - Review service logs

3. **Rollback Failures**
   - Check rollback configuration
   - Verify backup availability
   - Review rollback logs

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
export LOG_LEVEL=DEBUG
python validation/deployment_validator.py config/production.yaml
```

## Security Considerations

- **Environment Variables**: Sensitive configuration stored in environment variables
- **Access Control**: Validation scripts require appropriate access permissions
- **Audit Logging**: All validation and rollback actions are logged
- **Rollback Security**: Rollback procedures require proper authentication

## Performance

- **Validation Time**: Complete validation completes in <15 minutes
- **Health Check Interval**: Configurable health check intervals (default: 30s)
- **Response Time Thresholds**: Configurable performance thresholds
- **Resource Usage**: Minimal resource overhead for validation processes

## Contributing

When contributing to the infrastructure validation framework:

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new functionality
3. Update documentation for new features
4. Ensure backward compatibility
5. Follow security best practices

## References

- **RFC003.md**: Technical design and architecture
- **TODO003.md**: Implementation checklist and requirements
- **CONTEXT003.md**: Infrastructure validation strategy
- **POSTMORTEM002.md**: Lessons learned from previous failures

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review validation logs and reports
3. Consult the reference documentation
4. Contact the development team

---

**Note**: This framework is designed to prevent the deployment configuration failures experienced in previous iterations by ensuring comprehensive validation before deployment and providing automated rollback capabilities for failed deployments.
