# Environment Management Project - Comprehensive Phase Prompts

## Phase 4.5 Prompt: Vercel Frontend Deployment Setup
```
Set up comprehensive Vercel deployment infrastructure for the insurance_navigator frontend to establish consistent deployment across all environments. Focus on:

1. Set up Vercel development deployment via CLI for consistent development testing
2. Configure Vercel development deployment with .env.development variables
3. Set up Vercel preview deployment for staging environment testing
4. Configure Vercel preview deployment with .env.staging variables (connecting to staging backend services)
5. Set up Vercel production deployment configuration
6. Configure Vercel production deployment with .env.production variables
7. Test development Vercel deployment with staging backend services (insurance-navigator-staging-api and insurance-navigator-staging-worker)
8. Validate development frontend connects properly to staging API and worker services
9. Document Vercel deployment configurations and access methods for all environments
10. Create consistent frontend testing strategy using Vercel deployments instead of local hosting

Reference staging infrastructure configuration from completed setup phases.

Reference existing .env files for proper environment variable configuration.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

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
8. Test full-stack integration using Vercel development frontend with staging backend services

Document findings in: docs/initiatives/devops/environment_management/infrastructure_setup/validation_procedures/

Reference staging service configurations from completed infrastructure setup phases.

Reference Vercel deployment setup from Phase 4.5.

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

## Phase 7 Prompt: Docker Build Optimization and Acceleration
```
Investigate and implement comprehensive Docker build optimization strategies for the insurance_navigator project to accelerate builds and improve deployment efficiency. Focus on:

1. Investigate current Dockerfile configurations across the project and analyze performance bottlenecks
2. Research and implement Docker build acceleration best practices including:
   - Multi-stage Docker builds for optimal layer caching
   - Docker BuildKit configuration for enhanced build performance
   - Layer caching strategies for CI/CD pipelines
   - Build cache storage solutions (Registry caching, local cache, remote cache)
3. Optimize dependency installation and package management in Docker builds:
   - Node.js dependency caching strategies
   - Python package caching (if applicable)
   - Efficient package manager usage (npm ci, yarn, etc.)
4. Implement .dockerignore optimization to reduce build context size
5. Configure build secrets management for secure and efficient builds
6. Investigate and implement build acceleration techniques:
   - Parallel builds where applicable
   - Build context optimization
   - Layer reuse strategies
7. Test and validate optimized Docker builds across all environments (development, staging, production)
8. Measure and document performance improvements (build time reduction, cache hit rates)
9. Create best practices documentation for Docker build optimization
10. Integrate optimized builds with existing CI/CD pipelines (Render, Vercel)

Research industry best practices from Docker documentation, container registries (Docker Hub, ECR, GCR), and CI/CD platforms.

Document findings in: docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/

Reference existing Docker configurations and deployment setups.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 8 Prompt: Module-Level Environment Analysis
```
Examine each major module and workflow in the insurance_navigator codebase for environment-specific behavior. Focus on:

1. Audit frontend components for environment-specific behavior
2. Analyze backend services for environment switches and dependencies
3. Review database connection configurations and patterns
4. Examine API endpoint configurations across the application
5. Check authentication/authorization environment dependencies
6. Review build scripts and configurations for environment handling (including Vercel build configurations and Docker builds)
7. Analyze deployment-related files and CI/CD configurations (including Vercel deployment configurations and Docker configurations)
8. Identify CI/CD environment dependencies and requirements

Document findings in: docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/

Reference codebase analysis from Phase 6, Vercel deployment setup from Phase 4.5, and Docker optimization from Phase 7.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 9 Prompt: Core Environment Management Infrastructure
```
Implement the central environment management infrastructure for the insurance_navigator project based on research findings. Focus on:

1. Create central configuration system in shared/config/ directory
2. Implement EnvironmentConfig class with comprehensive validation capabilities
3. Create TypeScript interfaces for all configuration types identified in research
4. Set up environment variable validation schema based on findings
5. Create .env.example template with all required variables from research
6. Implement comprehensive error handling and logging for configuration issues

Reference research findings from Phases 6-8 for implementation requirements.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 10 Prompt: Environment File Updates and Validation
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

## Phase 11 Prompt: Shared Utilities and Core Module Refactoring
```
Refactor shared utilities in the insurance_navigator project to use the new environment management system. Focus on:

1. Refactor shared/environment.ts to use new configuration system
2. Update database connection handling for environment awareness
3. Implement environment-aware logging configuration
4. Create utility functions for environment detection
5. Update shared type definitions for environment configurations

Reference the core environment management infrastructure from Phase 9.

Reference module analysis findings from Phase 8.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 12 Prompt: Frontend Module Environment Integration
```
Refactor frontend components in the insurance_navigator project to remove environment dependencies. Focus on:

1. Remove all hardcoded API endpoints from frontend components
2. Implement configuration service for frontend environment handling
3. Update build process to inject environment configurations (including Vercel build process)
4. Refactor feature flags to use environment configuration
5. Update frontend error handling for configuration issues
6. Test frontend changes across all Vercel deployments (development, preview/staging, production)

Reference frontend analysis findings from Phase 8.

Reference environment files and configuration system from Phases 9-10.

Reference Vercel deployment setup from Phase 4.5.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 13 Prompt: Backend Service Environment Integration
```
Refactor backend services in the insurance_navigator project for environment-agnostic operation. Focus on:

1. Update API endpoint configurations to use environment variables
2. Refactor authentication services for environment-specific settings
3. Update third-party service integrations (payment processors, external APIs)
4. Implement environment-aware service discovery
5. Update middleware for environment-specific behavior

Reference backend analysis findings from Phase 8.

Reference staging service configurations and environment management system.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 14 Prompt: Build System and CI/CD Integration
```
Update the build system for the insurance_navigator project to support environment-aware builds. Focus on:

1. Update package.json scripts for environment-specific builds
2. Implement build-time configuration validation
3. Create environment-specific build optimizations
4. Update CI/CD pipeline for environment awareness (including Vercel deployments and optimized Docker builds)
5. Implement automated environment variable validation
6. Configure Vercel deployment automation and environment variable management
7. Integrate optimized Docker builds into CI/CD pipeline

Reference build system analysis from Phase 8.

Reference environment configuration system and validation from previous phases.

Reference Vercel deployment setup from Phase 4.5 and Docker optimization from Phase 7.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 15 Prompt: Comprehensive Testing and Validation
```
Implement comprehensive testing for the environment management system in the insurance_navigator project. Focus on:

1. Create unit tests for configuration system functionality
2. Implement integration tests for environment transitions
3. Create end-to-end tests for each environment (development, staging, production)
4. Validate configuration loading across all environments
5. Test error handling for missing or invalid configurations
6. Test full-stack integration across all environments using Vercel frontend deployments
7. Validate frontend-backend communication across all environment combinations
8. Test Docker build optimization performance and reliability

Reference all previous implementation phases for testing requirements.

Reference Vercel deployment setup from Phase 4.5 for full-stack testing and Docker optimization from Phase 7.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 16 Prompt: Staging Infrastructure Optimization
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

## Phase 17 Prompt: Deployment Procedures and Automation
```
Create automated deployment procedures for the insurance_navigator project environment management. Focus on:

1. Create automated deployment scripts for each environment
2. Implement environment promotion validation procedures
3. Create comprehensive rollback procedures for each environment
4. Document deployment procedures and safety checks
5. Set up monitoring for environment-specific metrics
6. Integrate optimized Docker builds into deployment procedures

Reference all previous implementation phases for deployment requirements.

Reference Docker optimization from Phase 7 for deployment integration.

Update todos in: docs/initiatives/devops/environment_management/infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md
```

## Phase 18 Prompt: Documentation and Training
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
Each phase builds upon the previous phases. Start with Phase 4.5 since Phases 1-4 (infrastructure setup) are already completed. Each prompt references specific documentation and previous phase findings to ensure continuity and comprehensive implementation.

**Updated Phase Count**: Now 18 total phases (added Phase 4.5 for Vercel deployment and Phase 7 for Docker optimization)