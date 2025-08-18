# Phase 6 Execution Prompt: Application Deployment and Verification

## Context
You are implementing Phase 6 of the 003 Worker Refactor iteration. This phase implements application deployment with comprehensive validation against local environment baseline, ensuring deployed application behavior matches local functionality to prevent the processing failures experienced in 002.

## Documentation References
Please review these documents before starting implementation:
- `@docs/initiatives/system/upload_refactor/003/CONTEXT003.md` - Application deployment strategy and verification framework
- `@docs/initiatives/system/upload_refactor/003/TODO003.md` - Detailed implementation checklist (Phase 6 section)
- `@docs/initiatives/system/upload_refactor/003/RFC003.md` - Technical design for application deployment and verification
- `@TODO003_phase5_notes.md` - Phase 5 infrastructure deployment details and validation results
- `@TODO003_phase5_decisions.md` - Infrastructure configuration decisions and trade-offs
- `@TODO003_phase5_handoff.md` - Application deployment requirements from Phase 5
- All previous phase outputs for complete deployment context
- `@docs/initiatives/system/upload_refactor/002/POSTMORTEM002.md` - Application deployment failures to prevent

## Primary Objective
Implement application deployment with comprehensive verification including:
1. Application deployment and configuration with validation against local baseline
2. Production functionality validation ensuring behavior matches local environment
3. Production monitoring and alerting with comprehensive observability
4. Production readiness validation with stakeholder approval and team training

## Key Implementation Requirements

### Application Deployment and Configuration
- Deploy BaseWorker and API applications to validated infrastructure with proper configuration
- Configure application environment and validate against local baseline performance and behavior
- Implement application health monitoring and status validation systems
- Create automated deployment verification and rollback procedures with safety measures

### Production Functionality Validation
- Validate deployed application behavior matches local environment baseline exactly
- Test complete processing pipeline in production environment with real workloads
- Verify external service integration and webhook functionality with comprehensive testing
- Validate performance and reliability against local benchmarks and requirements

### Production Monitoring and Alerting
- Implement comprehensive production monitoring and observability with real-time dashboards
- Create real-time alerting for processing failures and performance issues
- Develop production debugging and troubleshooting procedures with correlation ID tracking
- Build operational runbooks and incident response procedures for team use

### Production Readiness Validation
- Execute comprehensive production readiness testing with objective success criteria
- Validate rollback procedures and recovery capabilities with automated testing
- Create operational documentation and team training materials
- Obtain final stakeholder approval and production sign-off with clear success metrics

## Expected Outputs
Document your work in these files:
- `@TODO003_phase6_notes.md` - Application deployment details and verification results
- `@TODO003_phase6_decisions.md` - Deployment configuration decisions and trade-offs
- `@TODO003_phase6_handoff.md` - Production operation requirements for Phase 7
- `@TODO003_phase6_testing_summary.md` - Production validation results and performance comparison

## Success Criteria
- Application deployment completes successfully with all services operational and validated
- Deployed application behavior matches local environment baseline exactly
- Complete processing pipeline functions correctly in production with real external services
- Production monitoring provides comprehensive observability with real-time alerting
- Performance validation confirms production meets or exceeds local benchmarks
- Rollback procedures tested and validated with automated failure detection

## Implementation Notes
- Use the validated infrastructure from Phase 5 as your deployment foundation
- Ensure deployed application configuration exactly matches local environment settings
- Validate every aspect of processing pipeline against local baseline behavior
- Focus on preventing the processing disconnects and silent failures experienced in 002
- Implement comprehensive monitoring to detect any differences from local behavior
- Document all configuration decisions and operational procedures for team use

## Critical Validation Points
- **Deployment Completeness**: All application components deployed and operational (BaseWorker actually running)
- **Behavioral Validation**: Production behavior matches local environment baseline exactly
- **Processing Pipeline**: Complete pipeline processes documents successfully end-to-end
- **External Service Integration**: Real LlamaParse and OpenAI integration working correctly
- **Performance Validation**: Production performance meets or exceeds local benchmarks
- **Monitoring Integration**: Comprehensive monitoring operational with real-time status and alerting

Start by reading all referenced documentation and previous phase outputs, then implement application deployment following the detailed Phase 6 checklist and comprehensive verification requirements.