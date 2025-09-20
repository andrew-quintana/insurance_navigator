# Infrastructure Setup Stage - Agent Prompts

## Phase 1 Prompt: Production Service Discovery and Documentation
```
Conduct a comprehensive audit of the current Render services for the insurance_navigator project to prepare for staging infrastructure replication. Focus on:

1. Complete documentation of insurance-navigator-api service configuration
2. Complete documentation of insurance-navigator-worker service configuration
3. Inventory of all environment variables used by both services
4. Service dependencies and external integrations mapping
5. Resource allocations and current performance metrics

Document findings in: docs/initiatives/devops/environment_management/infrastructure_setup/service_replication/

Reference the infrastructure specification: docs/initiatives/devops/environment_management/infrastructure_setup/refactor_specification/STAGING_INFRASTRUCTURE_SPEC.md

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 2 Prompt: Staging Environment Planning
```
Plan the staging environment configuration based on production service audit findings. Focus on:

1. Define staging-specific environment variable adaptations
2. Plan staging database and external service configurations
3. Design staging domain and networking requirements
4. Define appropriate resource allocations for staging workload
5. Create staging service naming and organizational strategy

Document findings in: docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/

Reference the infrastructure specification and production service documentation.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 3 Prompt: Staging API Service Creation
```
Create and configure the insurance-navigator-staging-api service using Render MCP based on production service specifications. Focus on:

1. Create staging API service with identical production configurations
2. Apply staging-specific environment variables and settings
3. Configure staging database connections and dependencies
4. Set up staging domain and networking configurations
5. Validate staging API service health and basic functionality

Reference the infrastructure specification: docs/initiatives/devops/environment_management/infrastructure_setup/refactor_specification/STAGING_INFRASTRUCTURE_SPEC.md

Reference production service documentation from Phase 1.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 4 Prompt: Staging Worker Service Creation
```
Create and configure the insurance-navigator-staging-worker service using Render MCP based on production worker specifications. Focus on:

1. Create staging worker service with identical production configurations
2. Apply staging-specific environment variables and worker settings
3. Configure staging database and queue connections
4. Set up staging external service integrations
5. Validate staging worker service health and job processing capabilities

Reference the infrastructure specification and production worker documentation.

Reference staging environment planning from Phase 2.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 5 Prompt: Service Integration and Communication
```
Configure and validate communication between staging services to ensure proper integration. Focus on:

1. Configure inter-service communication between staging API and worker
2. Validate service-to-service networking and communication
3. Test job queuing and processing workflows between services
4. Configure shared staging environment variables and settings
5. Validate staging service security and access configurations

Reference the infrastructure specification and individual service configurations.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 6 Prompt: Comprehensive Testing and Validation
```
Perform comprehensive testing and validation of the staging infrastructure to ensure readiness for subsequent phases. Focus on:

1. Run complete health checks on all staging services
2. Test core API and worker functionality in staging environment
3. Validate environment variable loading and configuration access
4. Establish performance baselines for staging services
5. Validate logging, monitoring, and alerting configurations

Document findings in: docs/initiatives/devops/environment_management/infrastructure_setup/validation_procedures/

Reference all previous phase configurations and specifications.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 7 Prompt: Configuration Documentation and Handoff
```
Create comprehensive documentation and prepare handoff materials for the research phase. Focus on:

1. Document all staging service configurations and settings
2. Create staging environment variable reference documentation
3. Document staging service endpoints and access information
4. Create troubleshooting guide for staging infrastructure
5. Prepare complete handoff documentation for research phase

Document findings in: docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/

Create handoff documentation that will be referenced by the research phase.

Complete final validation of todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase Handoff Documentation
Each phase must create handoff documentation that subsequent phases can reference without requiring knowledge of implementation details. Focus on:

- Service endpoints and access information
- Environment variable configurations
- Dependency mappings and external service connections
- Performance baselines and monitoring configurations
- Troubleshooting and maintenance procedures