# Workflow Testing Spec - Phase-Based Service Integration

## Scope

### In Scope
- **Phase 1**: Local Docker-based testing with production Supabase
  - API service containerized testing
  - Worker service containerized testing
  - Frontend service containerized testing
  - Integration with production Supabase instance
  - End-to-end workflow validation in local environment
- **Phase 2**: Cloud deployment testing
  - Render.com API and worker service deployment
  - Vercel frontend deployment
  - Production Supabase integration
  - Cross-platform service communication validation

### Out of Scope
- Local Supabase instance testing (production instance required)
- Performance benchmarking (covered in separate performance testing)
- Security penetration testing
- Database migration testing

## Test Types

### Unit Tests
- **API Service Components**
  - Upload pipeline handlers: `api/upload_pipeline/`
  - Document processing modules
  - Authentication service integration
  - Storage service integration
- **Worker Service Components**  
  - Enhanced base worker: `backend/workers/enhanced_base_worker.py`
  - Job queue processing
  - External API integrations (LlamaParse, OpenAI)
  - State management and persistence
- **Frontend Components**
  - Upload interface components
  - Document viewer components
  - Authentication flows
  - State management (Redux/Context)

### Integration Tests
- **Service-to-Service Communication**
  - API → Worker job dispatching
  - Worker → API status reporting
  - Frontend → API authenticated requests
  - All services → Supabase data persistence
- **External Service Integration**
  - Supabase auth, storage, and database operations
  - LlamaParse document processing
  - OpenAI content analysis
- **Data Flow Validation**
  - Document upload → processing → storage → retrieval workflow
  - User authentication → authorization → resource access

### End-to-End Tests
- **Phase 1: Local Docker Environment**
  - Complete user workflow from upload to processed document retrieval
  - Multi-user concurrent access testing
  - Error handling and recovery scenarios
  - Cross-service health monitoring
- **Phase 2: Cloud Deployment Environment**
  - Production-like user workflows
  - Network latency and reliability testing
  - Service scaling and load distribution
  - Disaster recovery scenarios

### Load/Performance Tests
- **Concurrent User Simulation**
  - Multiple simultaneous document uploads
  - High-frequency API requests
  - Worker queue saturation testing
- **Resource Utilization Monitoring**
  - Container resource consumption
  - Database connection pooling
  - Memory and CPU usage patterns

## Coverage Goals

### Code Coverage
- **Minimum Acceptable**: 80% overall code coverage
- **Critical Path Target**: 95% coverage for core workflows
  - Document upload and processing pipeline
  - User authentication and authorization
  - Error handling and recovery mechanisms

### Critical Path Scenarios
1. **Happy Path Workflows**
   - New user registration → document upload → processing → retrieval
   - Existing user authentication → bulk upload → status monitoring
2. **Error Recovery Scenarios**
   - Network failures during upload/processing
   - External service outages (LlamaParse, OpenAI)
   - Database connection failures
   - Worker service crashes and restart
3. **Edge Cases**
   - Large file uploads (>100MB)
   - Unsupported file formats
   - Rate limiting scenarios
   - Concurrent access to same resources

## Test Data & Environments

### Phase 1: Local Docker + Production Supabase
- **Environment Setup**
  - Docker Compose configuration: `docker-compose.yml`
  - Production Supabase connection: Environment variables from `.env.production`
  - Mock external services where needed (LlamaParse, OpenAI for cost control)
- **Test Data Sources**
  - Synthetic insurance documents (PDF, DOC, images)
  - User personas with varying permission levels  
  - Edge case files (corrupted, oversized, unsupported formats)
- **Infrastructure**
  - Containerized API service: `api/upload_pipeline/Dockerfile`
  - Containerized Worker service: `backend/workers/Dockerfile`
  - Containerized Frontend: `ui/Dockerfile.test`
  - Shared volumes for document storage testing

### Phase 2: Cloud Deployment + Production Supabase  
- **Environment Setup**
  - Render.com deployment configurations
  - Vercel deployment configurations
  - Production Supabase integration
  - Real external service integration
- **Staging Environment**
  - Render.com staging instances
  - Vercel preview deployments
  - Production Supabase with dedicated test schemas
- **Test Data Management**
  - Automated test data provisioning
  - Data cleanup and isolation procedures
  - Production data anonymization for testing

## Docker Configuration Details

### Phase 1 Docker Services

#### API Service
```yaml
api-server:
  build:
    context: .
    dockerfile: api/upload_pipeline/Dockerfile
  environment:
    DATABASE_URL: postgresql://postgres:[PRODUCTION_PASSWORD]@[PRODUCTION_HOST]:5432/postgres
    UPLOAD_PIPELINE_SUPABASE_URL: https://[PROJECT_ID].supabase.co
    UPLOAD_PIPELINE_SUPABASE_ANON_KEY: [PRODUCTION_ANON_KEY]
    UPLOAD_PIPELINE_SUPABASE_SERVICE_ROLE_KEY: [PRODUCTION_SERVICE_ROLE_KEY]
```

#### Worker Service  
```yaml
enhanced-base-worker:
  build:
    context: .
    dockerfile: backend/workers/Dockerfile
  environment:
    DATABASE_URL: postgresql://postgres:[PRODUCTION_PASSWORD]@[PRODUCTION_HOST]:5432/postgres
    SUPABASE_URL: https://[PROJECT_ID].supabase.co
    SUPABASE_ANON_KEY: [PRODUCTION_ANON_KEY]
    SUPABASE_SERVICE_ROLE_KEY: [PRODUCTION_SERVICE_ROLE_KEY]
    SERVICE_MODE: HYBRID
```

#### Frontend Service
```yaml
frontend:
  build:
    context: ui
    dockerfile: Dockerfile.test
  environment:
    NEXT_PUBLIC_API_URL: http://api-server:8000
    NEXT_PUBLIC_SUPABASE_URL: https://[PROJECT_ID].supabase.co
    NEXT_PUBLIC_SUPABASE_ANON_KEY: [PRODUCTION_ANON_KEY]
```

### Service Dependencies
- All services depend on production Supabase availability
- API service must be healthy before worker and frontend start
- Health checks ensure service readiness before test execution
- Network isolation for security while maintaining external connectivity

## Acceptance Criteria

### Phase 1 Acceptance Criteria
- **CI/CD Pipeline Passes**
  - All unit tests pass: `npm test`
  - Integration tests complete successfully
  - Docker services build and start without errors
  - Health checks pass for all containerized services
- **Error Rate Thresholds**
  - API endpoint error rate < 1%
  - Worker job processing error rate < 2%
  - Frontend navigation/interaction error rate < 0.5%
- **Coverage Targets Met**
  - Overall code coverage ≥ 80%
  - Critical path coverage ≥ 95%
  - All defined test scenarios executed successfully
- **Performance Baselines Established**
  - Average document processing time documented
  - API response times measured and recorded
  - Resource utilization patterns documented

### Phase 2 Acceptance Criteria  
- **Cloud Deployment Validation**
  - Render.com services deploy successfully
  - Vercel frontend deployment accessible
  - All services communicate across cloud platforms
  - Production Supabase integration confirmed
- **Production-Like Performance**
  - End-to-end workflow completion within acceptable time limits
  - No degradation from Phase 1 baseline performance
  - External service integrations function reliably
- **Monitoring and Alerting**
  - Service health monitoring operational
  - Error tracking and notification systems active
  - Performance metrics collection functional
- **Rollback Procedures Tested**
  - Automated rollback mechanisms validated
  - Recovery time objectives met
  - Data consistency maintained during rollback scenarios

## Test Execution Strategy

### Phase 1: Local Docker Testing
1. **Environment Preparation**
   - Pull latest production environment variables
   - Build and start all Docker services
   - Verify connectivity to production Supabase
   - Execute service health checks

2. **Test Execution Order**
   - Unit tests (parallel execution)
   - Integration tests (service-by-service)
   - End-to-end scenarios (sequential)
   - Load testing (controlled concurrency)

3. **Validation Checkpoints**
   - Each test suite completion triggers validation
   - Performance metrics captured and compared
   - Error logs analyzed and categorized
   - Coverage reports generated and reviewed

### Phase 2: Cloud Deployment Testing
1. **Deployment Sequence**
   - Infrastructure provisioning (Render, Vercel)
   - Service deployment and configuration
   - External service integration verification
   - Production readiness validation

2. **Testing Progression**
   - Smoke tests on newly deployed services
   - Integration testing across cloud platforms
   - End-to-end user workflow validation
   - Performance and scalability verification

3. **Go/No-Go Decision Points**
   - Pre-defined metrics must be met before progression
   - Manual validation checkpoints for critical functionality
   - Stakeholder approval for production readiness
   - Automated monitoring threshold validation

## Risk Mitigation

### Phase 1 Risks
- **Production Supabase Impact**: Use dedicated test schemas and careful data isolation
- **External Service Costs**: Implement request throttling and cost monitoring
- **Docker Environment Consistency**: Standardized base images and dependency management
- **Local Resource Limitations**: Optimize container resource allocation and implement cleanup procedures

### Phase 2 Risks
- **Cloud Platform Outages**: Multi-region deployment strategies and fallback procedures
- **Service Integration Failures**: Comprehensive retry logic and error handling
- **Production Data Exposure**: Strict access controls and data anonymization
- **Deployment Rollback Complexity**: Automated rollback procedures and state management

## Success Metrics

### Quantitative Metrics
- Test execution time reduction compared to manual testing
- Code coverage percentage achievement
- Error detection rate in pre-production environment
- Mean time to resolution for identified issues

### Qualitative Metrics
- Developer confidence in deployment process
- Stakeholder satisfaction with testing thoroughness
- Reduction in production incidents post-deployment
- Improved system reliability and user experience

## Maintenance and Evolution

### Continuous Improvement
- Regular review and update of test scenarios
- Performance baseline adjustments based on system evolution
- Testing infrastructure optimization and cost management
- Integration of new services and features into testing pipeline

### Documentation and Knowledge Transfer
- Maintain comprehensive test execution documentation
- Regular training sessions for development team
- Incident response procedures and runbook maintenance
- Best practices documentation and sharing