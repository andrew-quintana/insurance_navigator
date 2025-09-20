# Staging Infrastructure Replication Specification

## Overview
Technical specification for replicating production Render services to create staging environment infrastructure, ensuring consistent configurations while adapting for staging-specific requirements.

## Service Replication Requirements

### 1. API Service Replication
**Source Service**: `insurance-navigator-api`  
**Target Service**: `insurance-navigator-staging-api`

**Replication Strategy**:
- Clone all service configuration settings
- Preserve build and runtime specifications
- Maintain identical resource allocations
- Adapt environment variables for staging context

**Configuration Preservation**:
- Runtime environment (Node.js version, etc.)
- Build commands and start commands
- Health check configurations
- Auto-deploy settings (initially disabled for manual control)
- Region and resource plan specifications

**Environment Variable Adaptations**:
- Database connections → staging database instances
- API endpoints → staging-specific endpoints
- External service integrations → staging/test environments
- Domain configurations → staging domain settings

### 2. Worker Service Replication
**Source Service**: `insurance-navigator-worker`  
**Target Service**: `insurance-navigator-staging-worker`

**Replication Strategy**:
- Mirror worker configuration specifications
- Preserve job processing configurations
- Maintain resource and scaling settings
- Adapt for staging workload characteristics

**Configuration Preservation**:
- Worker runtime specifications
- Job queue configurations
- Processing timeout settings
- Resource allocation and scaling rules
- Background job handling configurations

**Environment Variable Adaptations**:
- Queue service connections → staging queue instances
- Database worker connections → staging database
- External API integrations → staging/test endpoints
- Logging and monitoring → staging-specific configurations

## Implementation Approach

### Phase 1: Service Discovery and Documentation
1. **Current Service Audit**: Document all current production service configurations
2. **Configuration Mapping**: Create detailed mapping of all settings to be replicated
3. **Environment Variable Inventory**: Complete inventory of all environment variables
4. **Dependency Analysis**: Identify all service dependencies and external integrations

### Phase 2: Staging Service Creation
1. **Service Replication**: Use Render MCP to create staging services with identical base configurations
2. **Configuration Application**: Apply staging-specific environment variables and settings
3. **Dependency Setup**: Configure staging-specific database and external service connections
4. **Network Configuration**: Set up staging-specific domain and networking configurations

### Phase 3: Validation and Testing
1. **Service Health Validation**: Verify staging services start and operate correctly
2. **Functionality Testing**: Test core functionality in staging environment
3. **Performance Baseline**: Establish performance baselines for staging services
4. **Integration Testing**: Validate service-to-service communication in staging

## Technical Implementation Details

### Render MCP Integration
**Required Tools**:
- Render MCP for service management
- Render CLI for configuration management
- Environment variable management tools

**Service Creation Commands**:
```typescript
// Example MCP usage structure - actual implementation will use research findings
await render.createWebService({
  name: 'insurance-navigator-staging-api',
  // Configuration based on production service settings
  runtime: productionService.runtime,
  buildCommand: productionService.buildCommand,
  startCommand: productionService.startCommand,
  envVars: stagingEnvironmentVariables
});
```

### Environment Variable Management
**Staging Environment Variables**:
- Database URLs → staging database instances
- API keys → staging/test API keys
- External service endpoints → staging service endpoints
- Feature flags → staging-specific feature configurations
- Logging levels → enhanced logging for staging debugging

**Security Considerations**:
- Staging-specific secrets management
- Test API keys with limited scope
- Staging database isolation from production
- Secure staging domain configurations

## Validation Criteria

### Service Health Checks
- [ ] Staging API service responds to health check endpoints
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

## Risk Mitigation

### Configuration Drift Prevention
- Automated comparison of staging vs production configurations
- Regular audits of service configuration consistency
- Documentation of all staging-specific adaptations
- Version control for service configuration templates

### Rollback Procedures
- Service configuration backup before modifications
- Ability to quickly recreate staging services if needed
- Clear rollback procedures for configuration changes
- Emergency contact procedures for infrastructure issues

## Dependencies and Prerequisites

### Required Access and Permissions
- Render dashboard admin access
- Render MCP integration configured
- Staging environment credentials and access
- Database and external service staging instances

### Infrastructure Dependencies
- Staging database instances available
- Staging domain and SSL configurations
- External service staging/test environments configured
- Monitoring and logging infrastructure for staging

## Success Metrics
- 100% configuration parity between production and staging services
- Sub-30-second service startup times in staging
- Zero configuration-related service failures
- Complete environment variable coverage for staging
- Successful staging service deployment and operation