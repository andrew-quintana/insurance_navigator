# PHASE 1 PROMPT: Local Docker Environment Setup

**Objective**: Implement Docker-based local testing environment with production Supabase integration

## Task Overview
Set up a containerized local development environment that integrates with production Supabase while maintaining isolation and testing safety. This phase establishes the foundation for comprehensive workflow testing.

## Key Documents to Reference
- **Primary Spec**: `@docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/001/workflow_testing_spec.md`
- **Implementation TODO**: `@docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/001/TODO_workflow_testing.md` (Phase 1 sections)
- **Existing Docker Config**: `@docker-compose.yml` 
- **Integration Example**: `@tests/initiatives/system/upload_refactor/integration/frontend/docker-compose.full.yml`
- **Context**: `@docs/initiatives/system/upload_refactor/003/CONTEXT003.md`

## Specific Implementation Tasks

### 1. Docker Compose Configuration
Create `docker-compose.workflow-testing.yml` that:
- Extends existing `@docker-compose.yml` structure
- Configures API service from `@api/upload_pipeline/Dockerfile`
- Configures Worker service from `@backend/workers/Dockerfile`  
- Configures Frontend service from `@ui/Dockerfile.test`
- Integrates production Supabase credentials from `@.env.production` structure

### 2. Production Supabase Integration
- Use production Supabase URL and keys from environment variables
- Implement test schema isolation (avoid affecting production data)
- Configure all services to connect to production Supabase instance
- Add connection validation and health checks

### 3. Service Health Monitoring
- Add `/health` endpoints to API service
- Implement worker service health checks
- Create frontend service readiness indicators
- Configure service dependencies and startup order

## Environment Variables Required
Reference production credentials structure but create testing-specific configuration:
```bash
# Production Supabase Connection
SUPABASE_URL=https://[PROJECT_ID].supabase.co
SUPABASE_ANON_KEY=[from .env.production]
SUPABASE_SERVICE_ROLE_KEY=[from .env.production]

# Database Connection  
DATABASE_URL=postgresql://postgres:[PROD_PASSWORD]@[PROD_HOST]:5432/postgres

# Service Configuration
UPLOAD_PIPELINE_ENVIRONMENT=workflow_testing
SERVICE_MODE=HYBRID
```

## Success Criteria
- All Docker services build successfully
- Services can connect to production Supabase
- Health checks pass for all services
- No interference with production data
- Services communicate internally via Docker network

## Testing Validation
- Run `docker-compose -f docker-compose.workflow-testing.yml up`
- Verify all services are healthy
- Test basic API endpoints respond
- Confirm Supabase connectivity without data corruption
- Validate service-to-service communication

## Safety Considerations
- Use dedicated test schemas in production Supabase
- Implement data isolation and cleanup procedures
- Monitor external service usage costs
- Document rollback procedures for any issues

## Output Deliverables
1. `docker-compose.workflow-testing.yml` configuration file
2. Updated Dockerfile health checks in relevant services
3. Environment variable template and documentation
4. Service health monitoring implementation
5. Basic integration validation scripts