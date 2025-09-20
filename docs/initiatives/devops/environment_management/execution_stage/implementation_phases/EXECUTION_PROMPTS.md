# Execution Stage - Agent Prompts

## Phase 1 Prompt: Core Infrastructure Implementation
```
Implement the core environment management infrastructure for the insurance_navigator project. Focus on:

1. Create central configuration system in shared/config/ directory
2. Implement EnvironmentConfig class with validation capabilities
3. Create TypeScript interfaces for all configuration types
4. Set up environment variable validation schema
5. Implement comprehensive error handling and logging

Reference the refactor specification: docs/initiatives/devops/environment_management/execution_stage/refactor_specification/ENVIRONMENT_REFACTOR_SPEC.md

Update todos in: docs/initiatives/devops/environment_management/execution_stage/implementation_phases/EXECUTION_PHASE_TODOS.md
```

## Phase 2 Prompt: Environment File Setup
```
Create and configure environment files for the insurance_navigator project based on research findings. Focus on:

1. Create comprehensive .env.development with all development values
2. Create .env.staging with staging-specific configurations
3. Create .env.production template for production deployment
4. Implement validation for environment file completeness
5. Document all environment variables and their purposes

Reference research findings in: docs/initiatives/devops/environment_management/research_stage/

Update todos in: docs/initiatives/devops/environment_management/execution_stage/implementation_phases/EXECUTION_PHASE_TODOS.md
```

## Phase 3 Prompt: Shared Utilities Refactoring
```
Refactor shared utilities in the insurance_navigator project to use the new environment management system. Focus on:

1. Update shared/environment.ts to use new configuration system
2. Refactor database connection handling for environment awareness
3. Implement environment-aware logging configuration
4. Create utility functions for environment detection
5. Update shared type definitions for environment configurations

Reference the refactor specification: docs/initiatives/devops/environment_management/execution_stage/refactor_specification/ENVIRONMENT_REFACTOR_SPEC.md

Update todos in: docs/initiatives/devops/environment_management/execution_stage/implementation_phases/EXECUTION_PHASE_TODOS.md
```

## Phase 4 Prompt: Frontend Module Refactoring
```
Refactor frontend components in the insurance_navigator project to remove environment dependencies. Focus on:

1. Remove all hardcoded API endpoints from frontend components
2. Implement configuration service for frontend environment handling
3. Update build process to inject environment configurations
4. Refactor feature flags to use environment configuration
5. Update error handling for configuration issues

Reference research findings for frontend modules and refactor specification.

Update todos in: docs/initiatives/devops/environment_management/execution_stage/implementation_phases/EXECUTION_PHASE_TODOS.md
```

## Phase 5 Prompt: Backend Service Refactoring
```
Refactor backend services in the insurance_navigator project for environment-agnostic operation. Focus on:

1. Update API endpoint configurations to use environment variables
2. Refactor authentication services for environment-specific settings
3. Update third-party service integrations (payment processors, external APIs)
4. Implement environment-aware service discovery
5. Update middleware for environment-specific behavior

Reference research findings for backend services and API configurations.

Update todos in: docs/initiatives/devops/environment_management/execution_stage/implementation_phases/EXECUTION_PHASE_TODOS.md
```

## Phase 6 Prompt: Build System Integration
```
Update the build system for the insurance_navigator project to support environment-aware builds. Focus on:

1. Update package.json scripts for environment-specific builds
2. Implement build-time configuration validation
3. Create environment-specific build optimizations
4. Update CI/CD pipeline for environment awareness
5. Implement automated environment variable validation

Reference the refactor specification and existing build configurations.

Update todos in: docs/initiatives/devops/environment_management/execution_stage/implementation_phases/EXECUTION_PHASE_TODOS.md
```

## Phase 7 Prompt: Testing and Validation Implementation
```
Implement comprehensive testing for the environment management system in the insurance_navigator project. Focus on:

1. Create unit tests for configuration system functionality
2. Implement integration tests for environment transitions
3. Create end-to-end tests for each environment
4. Validate configuration loading across all environments
5. Test error handling for missing or invalid configurations

Reference testing strategy: docs/initiatives/devops/environment_management/execution_stage/testing_strategy/

Update todos in: docs/initiatives/devops/environment_management/execution_stage/implementation_phases/EXECUTION_PHASE_TODOS.md
```

## Phase 8 Prompt: Deployment Procedures Implementation
```
Create automated deployment procedures for the insurance_navigator project environment management. Focus on:

1. Create automated deployment scripts for each environment
2. Implement environment promotion validation procedures
3. Create comprehensive rollback procedures for each environment
4. Document deployment procedures and safety checks
5. Set up monitoring for environment-specific metrics

Reference deployment procedures: docs/initiatives/devops/environment_management/execution_stage/deployment_procedures/

Update todos in: docs/initiatives/devops/environment_management/execution_stage/implementation_phases/EXECUTION_PHASE_TODOS.md
```

## Phase 9 Prompt: Documentation and Training
```
Create comprehensive documentation and training materials for the environment management system. Focus on:

1. Update developer setup documentation for new environment handling
2. Create troubleshooting guide for environment configuration issues
3. Document deployment and promotion procedures thoroughly
4. Create best practices guide for environment management
5. Prepare training materials for the development team

Consolidate all documentation and ensure consistency across all environment management documentation.

Update todos in: docs/initiatives/devops/environment_management/execution_stage/implementation_phases/EXECUTION_PHASE_TODOS.md
```