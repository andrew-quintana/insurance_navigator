# Research Stage - Agent Prompts

## Phase 1 Prompt: Environment Variable Discovery
```
Conduct a comprehensive scan of the insurance_navigator codebase to identify all environment variable usage patterns. Focus on:

1. All .env* files and their contents
2. All instances of process.env usage in TypeScript/JavaScript files
3. Hardcoded values that should be environment variables
4. Current environment variable naming conventions

Document findings in: docs/initiatives/devops/environment_management/research_stage/codebase_analysis/

Reference the phased todos in: docs/initiatives/devops/environment_management/research_stage/phased_planning/RESEARCH_PHASE_TODOS.md
```

## Phase 2 Prompt: Configuration File Analysis
```
Analyze all configuration-related files in the insurance_navigator project to understand current environment handling patterns. Focus on:

1. Configuration files in config/, shared/, and other relevant directories
2. Configuration loading and initialization patterns
3. Environment-specific configuration mechanisms
4. Dependencies between configuration files

Document findings in: docs/initiatives/devops/environment_management/research_stage/module_identification/

Reference the phased todos in: docs/initiatives/devops/environment_management/research_stage/phased_planning/RESEARCH_PHASE_TODOS.md
```

## Phase 3 Prompt: Module Environment Dependencies
```
Examine each major module/component in the insurance_navigator codebase for environment-specific behavior. Focus on:

1. Frontend components with environment-dependent logic
2. Backend services requiring environment switches
3. Database configurations and connections
4. API endpoint and service configurations
5. Authentication and authorization environment dependencies

Document findings in: docs/initiatives/devops/environment_management/research_stage/module_identification/

Reference the phased todos in: docs/initiatives/devops/environment_management/research_stage/phased_planning/RESEARCH_PHASE_TODOS.md
```

## Phase 4 Prompt: Build and Deployment Analysis
```
Review all build, test, and deployment-related configurations to identify environment dependencies. Focus on:

1. Build scripts and configurations (package.json, webpack, etc.)
2. Testing environment requirements and configurations
3. CI/CD pipeline environment dependencies
4. Deployment scripts and environment-specific settings

Document findings in: docs/initiatives/devops/environment_management/research_stage/workflow_mapping/

Reference the phased todos in: docs/initiatives/devops/environment_management/research_stage/phased_planning/RESEARCH_PHASE_TODOS.md
```

## Phase 5 Prompt: Third-Party Service Integration Analysis
```
Audit all third-party service integrations for environment-specific configurations. Focus on:

1. External API configurations and endpoints
2. Cloud service environment settings (AWS, Azure, etc.)
3. Logging and monitoring service configurations
4. Payment processors and other integration services
5. Development vs production service endpoints

Document findings in: docs/initiatives/devops/environment_management/research_stage/codebase_analysis/

Reference the phased todos in: docs/initiatives/devops/environment_management/research_stage/phased_planning/RESEARCH_PHASE_TODOS.md
```

## Phase 6 Prompt: Documentation and Validation
```
Consolidate all research findings and create comprehensive documentation for the execution stage. Focus on:

1. Creating environment dependency maps
2. Validating findings through code testing
3. Documenting specific transition requirements
4. Preparing actionable recommendations for execution stage

Document findings in: docs/initiatives/devops/environment_management/research_stage/workflow_mapping/

Reference completed todos and create final research summary.
```