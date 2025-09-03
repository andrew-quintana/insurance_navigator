# Phase 1 Prompt: Cloud Environment Setup & Validation

## Context for Claude Code Agent

**IMPORTANT**: You are implementing Phase 1 of cloud deployment testing for the integrated Upload Pipeline + Agent Workflow system. This phase establishes cloud infrastructure and validates basic connectivity across Vercel (frontend), Render (backend), and Supabase (database) platforms.

## Required Reading Before Starting

**Essential Documents (READ THESE FIRST):**
1. `docs/initiatives/system/upload_refactor/003/deployment/001/TODO001.md` - Main implementation guide with detailed Phase 1 tasks
2. `docs/initiatives/system/upload_refactor/003/deployment/001/RFC001.md` - Technical design and interface contracts
3. `docs/initiatives/system/upload_refactor/003/deployment/001/CONTEXT001.md` - Complete testing strategy and background

**Foundation Documents (For Reference):**
4. `docs/initiatives/system/upload_refactor/003/integration/001/` - Local integration baseline (100% success rate achieved)
5. Any existing Vercel, Render, or Supabase configuration files in the project

## Your Primary Objectives

1. **Deploy Frontend to Vercel**: Set up Next.js application with production configuration
2. **Deploy Backend to Render**: Configure Docker-based API server and BaseWorker processes
3. **Configure Supabase Database**: Set up production database with vector extensions and proper security
4. **Validate Basic Connectivity**: Implement and execute autonomous tests for service communication
5. **Document Everything**: Create comprehensive notes and handoff materials for Phase 2

## Key Implementation Guidelines

### Working with the Developer
- **Collaborative Approach**: You're working WITH the developer, not replacing them
- **Autonomous Tasks**: Handle technical implementation and automated testing
- **Developer Tasks**: The developer will handle visual validation, log analysis, and initial UX testing
- **Communication**: Clearly document what you've implemented so the developer knows what to test

### Success Criteria (Must Achieve 100%)
- All services deployed and responding to health checks
- Basic connectivity between frontend ↔ backend ↔ database working
- Environment variables properly configured across all platforms
- Autonomous validation tests achieve 100% pass rate

### Implementation Priority Order
1. **Start with Supabase**: Database and authentication foundation
2. **Deploy Backend to Render**: API server and worker processes
3. **Deploy Frontend to Vercel**: Next.js application with proper configuration
4. **Implement Testing**: Autonomous validation framework
5. **Execute Validation**: Run all tests and achieve 100% pass rate

## Autonomous Testing Framework to Implement

Create these classes based on the interface contracts in RFC001.md:

```python
class CloudEnvironmentValidator:
    async def validate_vercel_deployment(self) -> ValidationResult
    async def validate_render_deployment(self) -> ValidationResult  
    async def validate_supabase_connectivity(self) -> ValidationResult
```

## Critical Files to Create/Update

### Configuration Files
- Vercel deployment configuration (vercel.json or equivalent)
- Render service configuration (render.yaml or Dockerfile updates)
- Supabase project configuration and environment variables
- Production environment variable files for each platform

### Testing Framework
- `backend/testing/cloud_deployment/phase1_validator.py` - Main validation logic
- `scripts/cloud_deployment/phase1_test.py` - Test execution script
- Environment-specific test configurations

### Documentation (Required Outputs)
- `TODO001_phase1_notes.md` - Implementation details and decisions
- `TODO001_phase1_decisions.md` - Configuration choices and trade-offs
- `TODO001_phase1_handoff.md` - Requirements for Phase 2 integration testing
- `TODO001_phase1_testing_summary.md` - Validation results and metrics

## Integration with Local Baseline

**CRITICAL**: The cloud environment must replicate the local integration behavior exactly. Reference these local integration achievements:
- 100% processing success rate
- Average response time: 322.2ms (from Artillery.js testing)
- Cross-browser compatibility (Chrome, Firefox, Safari)
- Complete document upload → processing → conversation workflow

## Common Pitfalls to Avoid

1. **Environment Configuration Mismatches**: Ensure all environment variables match between services
2. **Service Discovery Issues**: Validate that services can actually communicate in cloud environment
3. **Security Configuration**: Don't compromise security for convenience during setup
4. **Performance Regression**: Cloud performance should meet/exceed local baselines
5. **Incomplete Testing**: All autonomous tests must achieve 100% pass rate before proceeding

## Developer Handoff Points

After you complete the autonomous implementation, the developer will:
- Visually validate deployments in browser
- Analyze deployment logs and identify issues
- Test initial user experience and navigation
- Validate responsive design across devices
- Review environment configuration completeness

Document your progress clearly so they know exactly what to test and validate.

## Success Validation Checklist

Before considering Phase 1 complete:
- [ ] Vercel deployment accessible and loading correctly
- [ ] Render services responding to health checks
- [ ] Supabase database connectivity and authentication working
- [ ] All environment variables properly configured
- [ ] Autonomous validation tests achieving 100% pass rate
- [ ] All required documentation created and completed
- [ ] Clear handoff materials prepared for developer validation

## Next Steps After Phase 1

Upon successful completion with 100% autonomous test pass rate, proceed to Phase 2 (Integration & Performance Testing) using `PHASE2_PROMPT.md`.

---

**Remember**: You are building upon a proven local integration foundation. The cloud deployment must match or exceed that baseline performance and reliability. Focus on systematic validation and comprehensive documentation for successful handoff to Phase 2.