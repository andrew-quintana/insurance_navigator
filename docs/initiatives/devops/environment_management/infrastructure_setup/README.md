# Infrastructure Setup Stage

## Overview
This preliminary stage establishes the staging infrastructure by creating staging-specific Render services that mirror production configurations, ensuring consistent behavior and reducing deployment risks before implementing environment-agnostic code changes.

## Objectives
- Replicate existing production Render services for staging environment
- Preserve service configurations to minimize environmental differences
- Establish staging infrastructure foundation for subsequent environment management phases
- Create staging-specific service endpoints and worker configurations

## Directory Structure

### `/refactor_specification/`
Technical specifications for replicating and configuring staging infrastructure services.

### `/phased_planning/`
Structured todo lists and planning documents for systematic infrastructure setup execution.

### `/service_replication/`
Documentation and procedures for replicating Render services with staging-specific configurations.

### `/configuration_management/`
Management of staging service configurations, environment variables, and service settings.

### `/validation_procedures/`
Testing and validation procedures to ensure staging infrastructure matches production behavior.

## Key Deliverables
1. Staging API service replication specification
2. Staging worker service replication specification
3. Phased infrastructure setup execution plan
4. Service configuration management procedures
5. Infrastructure validation and testing procedures

## Service Replication Strategy
1. **insurance-navigator-api** → **insurance-navigator-staging-api**
   - Preserve all service configurations
   - Update environment variables for staging
   - Maintain identical service specifications

2. **insurance-navigator-worker** → **insurance-navigator-staging-worker**
   - Replicate worker configurations
   - Adapt for staging environment requirements
   - Ensure service compatibility

## Infrastructure Prerequisites
- Access to Render dashboard and CLI
- Render MCP integration available
- Current production service configurations documented
- Staging environment variable definitions prepared

## Success Criteria
- Staging API service operational and accessible
- Staging worker service functional and processing tasks
- Service configurations match production specifications
- Environment variables properly configured for staging
- Infrastructure ready for research and execution phases