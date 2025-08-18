# Phase 2 Execution Prompt: Infrastructure Validation Framework

## Context
You are implementing Phase 2 of the 003 Worker Refactor iteration. This phase implements infrastructure validation framework to prevent the deployment configuration failures experienced in 002, with automated validation of deployment infrastructure against local environment baseline.

## Documentation References
Please review these documents before starting implementation:
- `@docs/initiatives/system/upload_refactor/003/CONTEXT003.md` - Infrastructure validation strategy and framework architecture
- `@docs/initiatives/system/upload_refactor/003/TODO003.md` - Detailed implementation checklist (Phase 2 section)
- `@docs/initiatives/system/upload_refactor/003/RFC003.md` - Technical design for infrastructure validation framework
- `@TODO003_phase1_notes.md` - Phase 1 local environment implementation details
- `@TODO003_phase1_decisions.md` - Previous technical choices and baseline configuration
- `@TODO003_phase1_handoff.md` - Infrastructure validation requirements from Phase 1

## Primary Objective
Implement infrastructure validation framework including:
1. Deployment configuration management and automated validation scripts
2. Comprehensive infrastructure health check framework
3. Environment configuration management and secrets validation
4. Deployment health monitoring and automated rollback procedures

## Key Implementation Requirements

### Deployment Configuration Management
- Implement infrastructure as code for version-controlled deployment configuration
- Create automated deployment configuration validation scripts
- Develop configuration drift detection and remediation procedures
- Build deployment rollback and recovery automation with safety measures

### Automated Infrastructure Validation
- Create comprehensive infrastructure health check framework
- Implement service connectivity and functionality validation against local baseline
- Develop database schema and performance validation procedures
- Build external service integration validation and monitoring systems

### Environment Configuration Management
- Implement environment variable validation and management framework
- Create secrets management and security configuration validation
- Develop configuration consistency checking between local and deployment environments
- Build automated configuration deployment and verification procedures

### Deployment Health Monitoring
- Set up comprehensive deployment health monitoring and alerting
- Implement real-time service status validation and failure detection
- Create deployment success verification and automated failure detection
- Develop automated rollback triggers and recovery procedures

## Expected Outputs
Document your work in these files:
- `@TODO003_phase2_notes.md` - Infrastructure validation implementation details and framework architecture
- `@TODO003_phase2_decisions.md` - Validation strategy decisions and technical trade-offs
- `@TODO003_phase2_handoff.md` - BaseWorker implementation requirements for Phase 3
- `@TODO003_phase2_testing_summary.md` - Infrastructure testing results and validation coverage

## Success Criteria
- Infrastructure validation framework successfully validates local environment configuration
- Automated validation scripts detect configuration drift and inconsistencies
- Deployment health checks validate all service connectivity and functionality
- Rollback procedures tested and validated with automated trigger mechanisms
- Configuration management ensures consistency between local and deployment environments
- All validation procedures documented and executable by operations team

## Implementation Notes
- Use the infrastructure validation framework design from RFC003.md as your implementation guide
- Build upon the local environment configuration established in Phase 1
- Implement comprehensive validation against local baseline for deployment verification
- Focus on preventing the infrastructure configuration failures experienced in 002
- Ensure all validation procedures are automated and objective
- Document validation criteria and success measures for each component

## Critical Validation Points
- **Configuration Validation**: Deployment configuration matches local environment baseline
- **Health Check Coverage**: All services and dependencies validated with comprehensive checks
- **Rollback Capability**: Automated rollback procedures tested and validated
- **Environment Consistency**: Configuration consistency validated between environments
- **Monitoring Integration**: Infrastructure health monitoring operational and alerting
- **Documentation Completeness**: All procedures documented and validated by team

Start by reading all referenced documentation and previous phase outputs, then implement the infrastructure validation framework following the detailed Phase 2 checklist and validation requirements.