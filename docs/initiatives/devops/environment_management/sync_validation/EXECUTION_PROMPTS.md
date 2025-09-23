# Environment Sync Validation - Execution Prompts

**Created:** 2025-09-23 15:00:02 PDT

## Overview
This document provides specialized prompts for each phase of the environment sync validation initiative. Each prompt references the specific documentation needed for execution and provides clear context for autonomous testing agents.

---

## Phase 1: Unit Testing Execution Prompt

### Primary Prompt
```
Execute comprehensive unit testing for the Insurance Navigator application across development and staging environments. Focus on individual component validation to ensure core functionality works in isolation.

Required Reading:
- @docs/initiatives/devops/environment_management/sync_validation/CONTEXT.md
- @docs/initiatives/devops/environment_management/sync_validation/TESTING_SPECIFICATION.md  
- @docs/initiatives/devops/environment_management/sync_validation/PHASE_1_UNIT_TESTING.md

Key Tasks:
1. Set up test environments for both development and staging
2. Execute unit tests for all core components listed in the phase document
3. Generate comprehensive test coverage reports (target: 90%+)
4. Compare test results between environments
5. Document and track any issues found
6. Validate test consistency across environments

Success Criteria:
- All unit tests pass in both environments
- Test coverage exceeds 90% on core modules
- No critical issues remain unresolved
- Environment comparison complete

Deliverables:
- Test execution reports
- Coverage analysis
- Issue tracking document
- Environment comparison report
```

---

## Phase 2: Component Testing Execution Prompt

### Primary Prompt
```
Execute comprehensive component testing for the Insurance Navigator application to validate service-level functionality across Render backend and Vercel frontend platforms in development and staging environments.

Required Reading:
- @docs/initiatives/devops/environment_management/sync_validation/CONTEXT.md
- @docs/initiatives/devops/environment_management/sync_validation/TESTING_SPECIFICATION.md
- @docs/initiatives/devops/environment_management/sync_validation/PHASE_2_COMPONENT_TESTING.md

Prerequisites:
- Phase 1 (Unit Testing) must be completed successfully
- Render Web Service and Workers deployed to staging
- Vercel staging deployment configured
- Test databases configured for both environments
- External API mock services available
- Vercel CLI configured for local development

Key Tasks:
1. Test Render Web Service API endpoints and FastAPI application functionality
2. Validate Render Workers background processes and job handling
3. Test database integration and external API connectivity from Render
4. Validate AI service components and LangChain integration on Render
5. Test Vercel frontend integration and React/Next.js functionality
6. Test cross-platform communication between Vercel and Render
7. Validate security components and authentication flows across platforms
8. Test monitoring, logging, and configuration management for both platforms
9. Assess performance and resource utilization across Render and Vercel
10. Test Vercel CLI local development environment

Success Criteria:
- All components start successfully on both Render and Vercel platforms
- Cross-platform communication works correctly
- External API integrations work correctly from Render
- Database connections establish without errors from Render
- Render Workers handle jobs without failures
- Vercel deployments function correctly in staging and development
- Performance metrics meet acceptable thresholds across platforms

Deliverables:
- Component test suite results for both platforms
- Cross-platform integration test reports
- Performance benchmark analysis for Render and Vercel
- Security validation report across platforms
- Configuration validation summary for both platforms
```

---

## Phase 3: Integration Testing Execution Prompt

### Primary Prompt
```
Execute comprehensive end-to-end integration testing for the Insurance Navigator application to validate complete workflows across Render backend and Vercel frontend platforms in both development and staging environments.

Required Reading:
- @docs/initiatives/devops/environment_management/sync_validation/CONTEXT.md
- @docs/initiatives/devops/environment_management/sync_validation/TESTING_SPECIFICATION.md
- @docs/initiatives/devops/environment_management/sync_validation/PHASE_3_INTEGRATION_TESTING.md

Prerequisites:
- Phase 1 (Unit Testing) completed successfully
- Phase 2 (Component Testing) completed successfully
- All services running on both Render and Vercel platforms
- Test data prepared and validated
- Cross-platform communication established

Key Tasks:
1. Test complete user authentication and authorization workflows across Vercel and Render
2. Validate end-to-end document processing pipeline from Vercel to Render Workers
3. Test AI chat interface integration with full conversation flows between platforms
4. Validate administrative operations and system management across platforms
5. Test cross-platform communication and data flow integrity between Vercel and Render
6. Validate performance under realistic load conditions across both platforms
7. Test security integration across all touchpoints between Vercel and Render
8. Validate error handling and recovery procedures across platforms
9. Test environment synchronization and consistency between Render and Vercel

Success Criteria:
- All end-to-end workflows complete successfully across platforms
- Data flows correctly between Vercel frontend and Render backend services
- Error handling works at all integration points between platforms
- Performance meets acceptable thresholds on both Render and Vercel
- Security measures function across all cross-platform touchpoints
- Environment synchronization is validated between Render and Vercel

Deliverables:
- End-to-end workflow test results across platforms
- Cross-platform performance integration analysis
- Security integration validation between Render and Vercel
- Environment synchronization report for both platforms
- Cross-platform communication analysis
- Error handling validation report across platforms
```

---

## Phase 4: Environment Validation Execution Prompt

### Primary Prompt
```
Execute comprehensive environment validation and deployment readiness assessment for the Insurance Navigator application across Render and Vercel platforms, preparing for manual testing handoff.

Required Reading:
- @docs/initiatives/devops/environment_management/sync_validation/CONTEXT.md
- @docs/initiatives/devops/environment_management/sync_validation/TESTING_SPECIFICATION.md
- @docs/initiatives/devops/environment_management/sync_validation/PHASE_4_ENVIRONMENT_VALIDATION.md

Prerequisites:
- Phase 1 (Unit Testing) completed successfully
- Phase 2 (Component Testing) completed successfully  
- Phase 3 (Integration Testing) completed successfully
- All services deployed to both Render and Vercel platforms
- Cross-platform communication validated

Key Tasks:
1. Validate all environment configurations and variables across Render and Vercel
2. Test Render Web Service and Workers deployment configuration
3. Test Vercel deployment builds and staging environment
4. Validate Vercel CLI local development environment setup
5. Validate database environments and migration procedures from Render
6. Test external service integrations and connectivity from Render backend
7. Validate cross-platform network security and performance configurations
8. Test monitoring, observability, and alerting systems for both platforms
9. Validate deployment and CI/CD pipeline functionality across platforms
10. Prepare comprehensive manual testing package for multi-platform setup
11. Create detailed handoff documentation for Render/Vercel architecture
12. Validate environment synchronization and consistency between platforms

Success Criteria:
- All environment configurations validated successfully across both platforms
- Services deploy and start without errors on both Render and Vercel
- Health checks pass consistently across all services on both platforms
- Performance metrics meet baseline requirements across Render and Vercel
- Security validations pass all checks for cross-platform setup
- Vercel CLI development environment fully functional
- Manual testing preparation complete for multi-platform testing
- Handoff documentation ready for Render/Vercel architecture

Deliverables:
- Environment validation report for both platforms
- Configuration comparison analysis between Render and Vercel
- Performance baseline documentation across platforms
- Security validation summary for cross-platform setup
- Manual testing preparation package for Render/Vercel testing
- Complete handoff documentation bundle for multi-platform architecture
- Environment monitoring setup guide for both platforms
- Issue tracking and resolution log across platforms
```

---

## General Execution Guidelines

### For All Phases
1. **Documentation First**: Always read the referenced documents thoroughly before beginning execution
2. **Environment Awareness**: Execute tests in both development and staging environments
3. **Issue Tracking**: Document all issues found with severity levels and resolution status
4. **Progress Reporting**: Provide regular updates on test execution progress
5. **Evidence Collection**: Capture screenshots, logs, and test outputs as evidence
6. **Cleanup**: Ensure test environments are clean after execution

### Error Handling
- Document all errors with context and reproduction steps
- Categorize errors by severity (Critical, High, Medium, Low)
- Provide recommended resolution approaches
- Track resolution status and validation

### Reporting Requirements
- Executive summary of test results
- Detailed findings with evidence
- Performance metrics and benchmarks
- Security validation results
- Environment comparison analysis
- Recommendations for improvement

### Communication Protocol
- Provide status updates at key milestones
- Escalate critical issues immediately
- Share preliminary findings for early feedback
- Coordinate with other testing agents as needed

---

## Phase Dependencies and Execution Order

### Sequential Execution Required
Each phase must be completed successfully before proceeding to the next:

1. **Phase 1** → **Phase 2** → **Phase 3** → **Phase 4**

### Success Gate Criteria
Each phase has specific success criteria that must be met before advancement:
- All tests in current phase pass
- No critical or high-severity issues remain unresolved
- Required deliverables are complete and validated
- Environment consistency is confirmed

### Rollback Procedures
If a phase fails to meet success criteria:
1. Document failure reasons and evidence
2. Implement necessary fixes or mitigations
3. Re-execute failed components
4. Validate success criteria before proceeding

---

## Final Handoff Preparation

### Manual Testing Package Components
- Comprehensive test environment access
- Pre-configured test data and user accounts
- Detailed testing scenarios and expected outcomes
- Issue reporting and escalation procedures
- Performance monitoring and analysis tools
- Security guidelines and compliance checklists
- Environment troubleshooting and support guides

### Success Validation
The initiative is complete when:
- All four phases pass their success criteria
- Environment synchronization is validated
- Manual testing package is prepared and verified
- Handoff documentation is complete and accessible
- All critical and high-severity issues are resolved
- Performance and security baselines are established