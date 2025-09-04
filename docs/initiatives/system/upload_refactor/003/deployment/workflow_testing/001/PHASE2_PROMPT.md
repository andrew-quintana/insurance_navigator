# PHASE 2 PROMPT: Cloud Deployment Testing

**Objective**: Implement and validate cloud deployment on Render.com and Vercel with production Supabase integration

**Prerequisites**: Phase 1 local Docker environment successfully implemented and validated

## Task Overview
Deploy services to cloud platforms (Render for API/Worker, Vercel for Frontend) and establish cross-platform integration testing. Validate that cloud deployment matches local Docker baseline performance and functionality.

## Key Documents to Reference
- **Primary Spec**: `@docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/001/workflow_testing_spec.md` (Phase 2 sections)
- **Implementation TODO**: `@docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/001/TODO_workflow_testing.md` (Phase 3 sections)
- **Phase 1 Results**: Local Docker configuration and baselines from Phase 1
- **Context**: `@docs/initiatives/system/upload_refactor/003/CONTEXT003.md` (deployment requirements)
- **Existing Configs**: Any existing deployment configurations in `@config/` directory

## Specific Implementation Tasks

### 1. Render.com API Service Deployment
Configure API service deployment:
- Create `render.yaml` or equivalent deployment configuration
- Map production environment variables from Phase 1 setup
- Configure health checks and auto-scaling policies
- Implement deployment automation scripts
- Reference existing `@api/upload_pipeline/Dockerfile`

### 2. Render.com Worker Service Deployment  
Configure Worker service deployment:
- Create worker service deployment configuration
- Configure background job processing and queue management
- Map worker-specific environment variables
- Implement monitoring and restart policies
- Reference existing `@backend/workers/Dockerfile`

### 3. Vercel Frontend Deployment
Configure Frontend deployment:
- Create `vercel.json` deployment configuration
- Configure build settings and environment variables
- Implement preview deployment automation
- Configure custom domains and routing
- Reference existing `@ui/` frontend structure

### 4. Cross-Platform Integration Validation
- Configure API endpoint routing between platforms
- Implement CORS and security header policies  
- Validate authentication flows across platforms
- Test service discovery and communication
- Monitor network latency and reliability

## Environment Configuration
Extend Phase 1 environment variables for cloud deployment:
```bash
# Render API Service
RENDER_API_URL=https://[API_SERVICE].onrender.com
RENDER_WORKER_URL=https://[WORKER_SERVICE].onrender.com

# Vercel Frontend
VERCEL_URL=https://[PROJECT].vercel.app
NEXT_PUBLIC_API_URL=https://[API_SERVICE].onrender.com

# Production Supabase (same as Phase 1)
SUPABASE_URL=https://[PROJECT_ID].supabase.co
SUPABASE_ANON_KEY=[from production]
SUPABASE_SERVICE_ROLE_KEY=[from production]

# Cross-Platform Configuration
CORS_ORIGINS=https://[PROJECT].vercel.app
API_BASE_URL=https://[API_SERVICE].onrender.com
```

## Success Criteria
- All services deploy successfully to respective platforms
- Services maintain connectivity to production Supabase
- Cross-platform communication functions correctly
- Performance metrics meet or exceed Phase 1 baselines
- Error rates stay within acceptable thresholds (<1% API, <2% Worker, <0.5% Frontend)

## Testing Validation
- Execute end-to-end workflows on deployed services
- Compare performance against Phase 1 local Docker baselines  
- Validate service health monitoring and alerting
- Test rollback and recovery procedures
- Confirm external service integrations (LlamaParse, OpenAI)

## Monitoring and Observability
- Configure service health monitoring across platforms
- Implement error tracking and alerting systems
- Set up performance metrics collection
- Create dashboards for service status visibility
- Document incident response procedures

## Risk Mitigation
- Implement staged deployment procedures
- Configure automated rollback mechanisms
- Monitor external service usage and costs
- Establish communication protocols between platforms
- Document troubleshooting procedures for each platform

## Output Deliverables
1. Render.com deployment configurations for API and Worker services
2. Vercel deployment configuration for Frontend service
3. Cross-platform integration validation scripts
4. Performance comparison analysis vs Phase 1 baselines
5. Monitoring and alerting system implementation
6. Deployment automation scripts and rollback procedures
7. Documentation for cloud deployment procedures

## Phase Transition Criteria
Before proceeding to Phase 3:
- All cloud services operational and healthy
- Cross-platform integration validated
- Performance baselines maintained or improved
- Monitoring systems operational
- Rollback procedures tested and verified