# Staging Environment Configuration Management

**Date**: January 21, 2025  
**Purpose**: Centralized configuration management for staging environment setup  
**Status**: Phase 2 Complete - Ready for Phase 3  

## Overview

This directory contains comprehensive configuration management documentation for the staging environment setup, based on production service audit findings and existing staging database configuration. All configurations are designed to replicate production functionality while maintaining appropriate staging-specific adaptations.

## Documentation Structure

### Core Configuration Documents

1. **STAGING_ENVIRONMENT_CONFIGURATION.md**
   - Complete staging environment configuration plan
   - Environment variable adaptations for Render services
   - External service configurations (excluding database)
   - Domain and networking requirements
   - Resource allocations and service naming strategy

2. **STAGING_SERVICE_SPECIFICATIONS.md**
   - Detailed specifications for staging service creation
   - API and Worker service configurations
   - Build and runtime specifications
   - Health checks and monitoring requirements
   - Security and deployment procedures

3. **STAGING_ENVIRONMENT_VARIABLES_TEMPLATE.md**
   - Complete template for staging environment variables
   - Service-specific variable configurations
   - Environment-specific variations
   - Security considerations and validation
   - Implementation and troubleshooting guides

## Key Configuration Highlights

### Staging Database Configuration
- **Schema**: `upload_pipeline` (same as production)
- **Connection Pool**: 10 connections with 15 max overflow
- **Timeout**: 30 seconds with 3600s recycle
- **Environment**: Staging-specific database instance
- **Isolation**: Separate from production database

### Staging Service Specifications
- **API Service**: `insurance-navigator-staging-api`
- **Worker Service**: `insurance-navigator-staging-worker`
- **Runtime**: Docker with Python 3.11-slim
- **Region**: Oregon (us-west-2)
- **Plan**: Starter (same as production)

### Staging Environment Variables
- **Total Variables**: 25+ environment variables
- **Categories**: Core, Database, API, Service, RAG, Worker-specific
- **Security**: Staging-specific API keys and database isolation
- **Validation**: Comprehensive validation logic

### Staging External Services
- **Supabase**: Staging project for database, auth, storage, realtime
- **OpenAI**: Staging API key for embeddings and chat completions
- **LlamaParse**: Staging API key for document processing
- **Anthropic**: Staging API key for alternative chat completions (optional)

## Configuration Management Principles

### 1. Production Parity
- Maintain identical service configurations where possible
- Preserve build and runtime specifications
- Keep same health check configurations
- Maintain same port configurations

### 2. Staging Adaptations
- Use staging-specific database connections
- Implement staging API key management
- Configure staging-specific CORS origins
- Set appropriate logging levels for staging

### 3. Security Isolation
- Staging-specific API keys with limited scope
- Staging database isolation from production
- Staging-specific CORS origins
- Staging monitoring and alerting

### 4. Monitoring and Observability
- Staging-specific monitoring
- Staging health check alerts
- Staging log aggregation
- Staging performance monitoring

## Implementation Guidelines

### Phase 3: Staging API Service Creation
1. Create `insurance-navigator-staging-api` service via Render MCP
2. Apply production API service configuration to staging service
3. Configure staging-specific environment variables for API service
4. Connect API service to existing staging database
5. Configure staging domain and networking for API service
6. Validate staging API service health and basic functionality

### Phase 4: Staging Worker Service Creation
1. Create `insurance-navigator-staging-worker` service via Render MCP
2. Apply production worker service configuration to staging service
3. Configure staging-specific environment variables for worker service
4. Connect worker service to existing staging database
5. Configure staging external service integrations for worker
6. Validate staging worker service health and job processing

### Phase 5: Service Integration and Communication
1. Configure communication between staging API and worker services
2. Validate inter-service communication in staging environment
3. Test job queuing and processing between staging services
4. Configure shared staging environment variables and configurations
5. Validate staging service networking and security configurations

## Configuration Validation

### Required Validations
- [ ] Staging API service responds to health checks
- [ ] Staging worker service processes test jobs successfully
- [ ] All environment variables properly loaded and accessible
- [ ] Service logs indicate proper startup and configuration

### Functionality Validation
- [ ] API endpoints respond correctly in staging environment
- [ ] Worker processes handle test workloads appropriately
- [ ] Database connections established and functional
- [ ] External service integrations working with staging endpoints

### Configuration Parity
- [ ] Staging service configurations match production specifications
- [ ] Resource allocations appropriate for staging workload
- [ ] Build and deployment processes functional
- [ ] Monitoring and alerting configured for staging context

## Security Considerations

### Staging Security
- **API Keys**: Staging-specific keys with limited scope
- **Database**: Isolated staging database
- **CORS**: Staging-specific origins only
- **SSL**: Automatic SSL via Render
- **Monitoring**: Staging-specific monitoring

### Data Isolation
- **Database**: Separate staging database instance
- **Storage**: Staging-specific storage buckets
- **API Keys**: Staging-specific API keys
- **Logs**: Staging-specific log aggregation

## Monitoring and Alerting

### Staging Monitoring
- **Health Checks**: Service health monitoring
- **Performance**: Response time monitoring
- **Errors**: Error rate monitoring
- **Dependencies**: External service monitoring

### Staging Alerting
- **Service Down**: Immediate alerts
- **High Error Rate**: Threshold-based alerts
- **Performance Degradation**: Response time alerts
- **Dependency Failures**: External service alerts

## Troubleshooting

### Common Issues
- **Service Startup Failures**: Check environment variables and dependencies
- **Database Connection Issues**: Verify database configuration and connectivity
- **External API Issues**: Check API keys and service availability
- **Performance Issues**: Monitor resource usage and optimize configuration

### Debug Procedures
- **Log Analysis**: Review service logs for errors
- **Health Check Analysis**: Analyze health check responses
- **Performance Analysis**: Monitor performance metrics
- **Dependency Analysis**: Check external service dependencies

## Next Steps

### Immediate Actions
1. **Phase 3**: Create staging API service using Render MCP
2. **Phase 4**: Create staging worker service using Render MCP
3. **Phase 5**: Configure service integration and communication
4. **Phase 6**: Run comprehensive testing and validation
5. **Phase 7**: Create configuration documentation and handoff

### Long-term Considerations
1. **Configuration Drift Prevention**: Automated comparison of staging vs production
2. **Regular Audits**: Service configuration consistency checks
3. **Version Control**: Service configuration template management
4. **Emergency Procedures**: Infrastructure issue response procedures

## Conclusion

This configuration management directory provides a complete foundation for staging environment setup. All configurations are based on production service audit findings and existing staging database setup, ensuring staging services replicate production functionality while maintaining appropriate staging-specific adaptations.

**Phase 2 Status**: ✅ COMPLETED  
**Ready for Phase 3**: Staging API Service Creation  

---

**Document Status**: Complete  
**Last Updated**: January 21, 2025  
**Next Review**: After Phase 3 completion
