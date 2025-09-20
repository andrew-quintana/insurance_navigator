# DevOps Environment Management Initiative

## Project Overview
This initiative establishes a comprehensive environment management system for the insurance_navigator application, enabling smooth transitions between development, staging, and production environments with rigid deployment controls and consistent configuration management.

## Project Structure

### Infrastructure Setup Stage (`./infrastructure_setup/`)
**Purpose**: Establish staging infrastructure by replicating production Render services to create staging-specific services before code analysis begins.

**Deliverables**:
- Staging API service replication (insurance-navigator-staging-api)
- Staging worker service replication (insurance-navigator-staging-worker) 
- Service configuration management procedures
- Infrastructure validation and testing procedures
- Staging environment foundation for subsequent phases

**Sub-directories**:
- `refactor_specification/` - Technical specifications for staging service replication
- `phased_planning/` - Structured infrastructure setup execution plans and prompts
- `service_replication/` - Documentation and procedures for service replication
- `configuration_management/` - Staging service configuration management
- `validation_procedures/` - Infrastructure testing and validation procedures

### Research Stage (`./research_stage/`)
**Purpose**: Systematic investigation of the current codebase to identify all environment dependencies and transition requirements.

**Deliverables**:
- Comprehensive environment dependency audit
- Module-specific transition requirements  
- Workflow environment mapping
- Phased research execution plan

**Sub-directories**:
- `codebase_analysis/` - Systematic codebase scanning results
- `module_identification/` - Module-specific environment dependency analysis
- `workflow_mapping/` - Workflow and process environment requirements
- `phased_planning/` - Structured research execution plans and prompts

### Execution Stage (`./execution_stage/`)
**Purpose**: Implementation of environment-agnostic system based on research findings.

**Deliverables**:
- Environment management refactor specification
- RFC for environment handling standards
- Phased implementation plan
- Testing and validation procedures
- Deployment automation and procedures

**Sub-directories**:
- `refactor_specification/` - Technical implementation specifications
- `rfc_documentation/` - Architectural decisions and standards
- `implementation_phases/` - Phased execution plans and prompts
- `testing_strategy/` - Comprehensive testing frameworks
- `deployment_procedures/` - Standardized deployment workflows

## Key Principles

### Environment Workflow
1. **Infrastructure First**: Staging infrastructure established before code changes
2. **Development First**: All changes begin in development environment
3. **Staging Validation**: Mandatory staging environment testing and approval using replicated infrastructure
4. **Production Promotion**: Only staging-validated changes deploy to production
5. **No Direct Production**: Strict prohibition of development-to-production deployments

### Configuration Management
1. **Environment Agnosticism**: Code works consistently across all environments
2. **Configuration Isolation**: Environment-specific values only in .env files
3. **Centralized Loading**: Single configuration system for all modules
4. **Validation Required**: Automated validation of all environment configurations

### Agent Guidelines
1. **Infrastructure Setup Prompts**: Focus on Render service replication and staging infrastructure creation
2. **Research Prompts**: Focus on discovery and documentation, no implementation
3. **Execution Prompts**: Focus on implementation based on research findings and staging infrastructure
4. **Phased Approach**: Each stage has clear phases with specific deliverables
5. **Documentation Reference**: All prompts reference specific documentation locations
6. **Render MCP Integration**: Use Render MCP for infrastructure setup and maintenance tasks

## Usage Instructions

### For Infrastructure Setup Phase
1. Use prompts from `infrastructure_setup/phased_planning/INFRASTRUCTURE_PROMPTS.md`
2. Document staging service configurations in appropriate `infrastructure_setup/` subdirectories
3. Update todos in `infrastructure_setup/phased_planning/INFRASTRUCTURE_PHASE_TODOS.md`
4. Complete staging infrastructure setup before beginning research phase

### For Research Phase
1. Use prompts from `research_stage/phased_planning/RESEARCH_PROMPTS.md`
2. Document findings in appropriate `research_stage/` subdirectories
3. Update todos in `research_stage/phased_planning/RESEARCH_PHASE_TODOS.md`
4. Reference staging infrastructure documentation from infrastructure setup stage
5. Complete all research phases before beginning execution

### For Execution Phase
1. Reference staging infrastructure setup and research findings from completed phases
2. Use prompts from `execution_stage/implementation_phases/EXECUTION_PROMPTS.md`
3. Follow specifications in `execution_stage/refactor_specification/`
4. Update todos in `execution_stage/implementation_phases/EXECUTION_PHASE_TODOS.md`
5. Adhere to RFC standards in `execution_stage/rfc_documentation/`
6. Use Render MCP for staging infrastructure maintenance and optimization

## Success Criteria
- [ ] Staging infrastructure successfully replicated and operational
- [ ] insurance-navigator-staging-api service functional and accessible
- [ ] insurance-navigator-staging-worker service processing jobs correctly
- [ ] Complete codebase environment dependency audit
- [ ] Zero hardcoded environment values in codebase
- [ ] Consistent environment variable patterns across all modules
- [ ] Automated testing validates environment configurations
- [ ] Seamless development → staging → production workflow using staging infrastructure
- [ ] Comprehensive deployment procedures with safety checks
- [ ] 100% configuration test coverage
- [ ] Successful automated environment promotions
- [ ] Staging infrastructure properly maintained via Render MCP

## Project Timeline
The project is designed to be executed in sequential phases, with each stage completion required before beginning the next stage.

**Estimated Duration**: 
- Infrastructure Setup Stage: 3-5 days
- Research Stage: 1-2 weeks
- Execution Stage: 3-4 weeks
- Total Project: 4-7 weeks

## Documentation Standards
All documentation follows a consistent structure with clear separation between research findings and implementation specifications. Prompts are designed to be execution-detail-free, focusing agents on the appropriate phase objectives and referencing relevant documentation for context.