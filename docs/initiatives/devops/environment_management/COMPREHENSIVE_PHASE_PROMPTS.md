# Environment Management Project - Comprehensive Phase Prompts

## Phase 5 Prompt: Service Integration and Communication Validation
```
Complete the validation of staging infrastructure and ensure proper inter-service communication. Focus on:

1. Configure communication between staging API and worker services
2. Validate inter-service communication in staging environment
3. Test job queuing and processing between staging services
4. Configure shared staging environment variables and configurations
5. Validate staging service networking and security configurations
6. Complete staging API service health and basic functionality validation
7. Complete staging worker service health and job processing validation

Document findings in: docs/initiatives/devops/environment_management/infrastructure_setup/validation_procedures/

Reference staging service configurations from completed infrastructure setup phases.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 6 Prompt: Codebase Environment Dependency Research
```
Conduct comprehensive investigation of the insurance_navigator codebase to identify all environment dependencies. Focus on:

1. Scan all .env* files in the project and document their contents
2. Search for process.env usage across all TypeScript/JavaScript files
3. Identify hardcoded environment-specific values throughout the codebase
4. Document current environment variable patterns and usage
5. Analyze all configuration files (config/, shared/, etc.)
6. Identify environment-specific configuration patterns
7. Document configuration loading mechanisms
8. Map configuration dependencies across modules

Document findings in: docs/initiatives/devops/environment_management/research_stage/codebase_analysis/

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 7 Prompt: Module-Level Environment Analysis
```
Examine each major module and workflow in the insurance_navigator codebase for environment-specific behavior. Focus on:

1. Audit frontend components for environment-specific behavior
2. Analyze backend services for environment switches and dependencies
3. Review database connection configurations and patterns
4. Examine API endpoint configurations across the application
5. Check authentication/authorization environment dependencies
6. Review build scripts and configurations for environment handling
7. Analyze deployment-related files and CI/CD configurations
8. Identify CI/CD environment dependencies and requirements

Document findings in: docs/initiatives/devops/environment_management/research_stage/module_identification/

Reference codebase analysis from Phase 6.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 8 Prompt: Core Environment Management Infrastructure
```
Implement the central environment management infrastructure for the insurance_navigator project based on research findings. Focus on:

1. Create central configuration system in shared/config/ directory
2. Implement EnvironmentConfig class with comprehensive validation capabilities
3. Create TypeScript interfaces for all configuration types identified in research
4. Set up environment variable validation schema based on findings
5. Create .env.example template with all required variables from research
6. Implement comprehensive error handling and logging for configuration issues

Reference research findings from Phases 6-7 for implementation requirements.

Reference the refactor specification: docs/initiatives/devops/environment_management/execution_stage/refactor_specification/ENVIRONMENT_REFACTOR_SPEC.md

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 9 Prompt: Environment File Updates and Validation
```
Update and validate existing environment files for the insurance_navigator project based on staging infrastructure and research findings. Focus on:

1. Update .env.staging with new staging service URLs (insurance-navigator-staging-api endpoint)
2. Validate environment file completeness and consistency across all environments
3. Document all environment variables and their purposes based on existing configurations
4. Ensure staging service URLs are properly configured for new infrastructure
5. Validate that all required environment variables are present across environments

Note: .env.development.template, .env.staging, and .env.production already exist and are well-structured.

Reference staging infrastructure configuration from completed setup phases.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 10 Prompt: Shared Utilities and Core Module Refactoring
```
Refactor shared utilities in the insurance_navigator project to use the new environment management system. Focus on:

1. Refactor shared/environment.ts to use new configuration system
2. Update database connection handling for environment awareness
3. Implement environment-aware logging configuration
4. Create utility functions for environment detection
5. Update shared type definitions for environment configurations

Reference the core environment management infrastructure from Phase 8.

Reference module analysis findings from Phase 7.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 11 Prompt: Frontend Module Environment Integration
```
Refactor frontend components in the insurance_navigator project to remove environment dependencies. Focus on:

1. Remove all hardcoded API endpoints from frontend components
2. Implement configuration service for frontend environment handling
3. Update build process to inject environment configurations
4. Refactor feature flags to use environment configuration
5. Update frontend error handling for configuration issues

Reference frontend analysis findings from Phase 7.

Reference environment files and configuration system from Phases 8-9.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 12 Prompt: Backend Service Environment Integration
```
Refactor backend services in the insurance_navigator project for environment-agnostic operation. Focus on:

1. Update API endpoint configurations to use environment variables
2. Refactor authentication services for environment-specific settings
3. Update third-party service integrations (payment processors, external APIs)
4. Implement environment-aware service discovery
5. Update middleware for environment-specific behavior

Reference backend analysis findings from Phase 7.

Reference staging service configurations and environment management system.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 13 Prompt: Build System and CI/CD Integration
```
Update the build system for the insurance_navigator project to support environment-aware builds. Focus on:

1. Update package.json scripts for environment-specific builds
2. Implement build-time configuration validation
3. Create environment-specific build optimizations
4. Update CI/CD pipeline for environment awareness
5. Implement automated environment variable validation

Reference build system analysis from Phase 7.

Reference environment configuration system and validation from previous phases.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 14 Prompt: Comprehensive Testing and Validation
```
Implement comprehensive testing for the environment management system in the insurance_navigator project. Focus on:

1. Create unit tests for configuration system functionality
2. Implement integration tests for environment transitions
3. Create end-to-end tests for each environment (development, staging, production)
4. Validate configuration loading across all environments
5. Test error handling for missing or invalid configurations

Reference testing strategy: docs/initiatives/devops/environment_management/execution_stage/testing_strategy/

Reference all previous implementation phases for testing requirements.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 15 Prompt: Staging Infrastructure Optimization
```
Optimize and maintain the staging infrastructure for the insurance_navigator project based on usage patterns and performance data. Focus on:

1. Optimize staging service configurations based on usage patterns
2. Update staging service environment variables via Render MCP as needed
3. Monitor staging service performance and resource utilization
4. Implement staging service scaling and resource management procedures
5. Document staging service maintenance and optimization procedures

Reference staging infrastructure setup and validation from completed phases.

Reference performance data and monitoring configurations.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 16 Prompt: Deployment Procedures and Automation
```
Create automated deployment procedures for the insurance_navigator project environment management. Focus on:

1. Create automated deployment scripts for each environment
2. Implement environment promotion validation procedures
3. Create comprehensive rollback procedures for each environment
4. Document deployment procedures and safety checks
5. Set up monitoring for environment-specific metrics

Reference deployment procedures: docs/initiatives/devops/environment_management/execution_stage/deployment_procedures/

Reference all previous implementation phases for deployment requirements.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 17 Prompt: Documentation and Training
```
Create comprehensive documentation and training materials for the environment management system. Focus on:

1. Update developer setup documentation for new environment handling
2. Create troubleshooting guide for environment configuration issues
3. Document deployment and promotion procedures thoroughly
4. Create best practices guide for environment management
5. Prepare training materials for the development team

Consolidate all documentation from previous phases and ensure consistency.

Reference all completed implementation work for comprehensive documentation.

Complete final validation of todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Usage Instructions
Each phase builds upon the previous phases. Start with Phase 5 since Phases 1-4 (infrastructure setup) are already completed. Each prompt references specific documentation and previous phase findings to ensure continuity and comprehensive implementation.