# Phase 5 Execution Prompt: Development End-to-End Testing

## Context
You are implementing Phase 5 of the upload refactor 003 file testing initiative. This phase focuses on development end-to-end testing with development configuration, including updating development-level servers similar to mock servers, building upon the successful pipeline validation from Phase 4.

## Documentation References
Please review these documents before starting implementation:
- `docs/initiatives/system/upload_refactor/003/file_testing/TODO001.md` - Phase 5 requirements and tasks
- `docs/initiatives/system/upload_refactor/003/file_testing/TEST_METHOD001.md` - Testing methodology and procedures
- `docs/initiatives/system/upload_refactor/003/file_testing/TODO001_phase4_handoff.md` - **REQUIRED**: Phase 4 handoff notes and requirements
- `docs/initiatives/system/upload_refactor/003/file_testing/PHASE3_SCOPE_UPDATE.md` - Phase 3 scope and objectives

## Primary Objective
**TEST** the complete system in a development environment with realistic services by implementing development-level external service configurations, validating end-to-end workflows, and ensuring production readiness through comprehensive development testing.

## Expected Outputs
Document your work in these files:
- `TODO001_phase5_notes.md` - Phase 5 implementation details and development testing results
- `TODO001_phase5_decisions.md` - Technical decisions and development service integration approaches
- `TODO001_phase5_handoff.md` - **REQUIRED**: Comprehensive handoff notes for Phase 6 transition
- `TODO001_phase5_testing_summary.md` - Phase 5 testing results and development environment validation

## Implementation Approach
1. **Review Phase 4 Handoff**: **REQUIRED**: Read and understand all Phase 4 handoff requirements
2. **Verify Current System State**: Confirm end-to-end pipeline completion and database state from Phase 4
3. **Development Service Setup**: Configure development-level external services (LlamaParse, OpenAI development endpoints)
4. **Service Router Configuration**: Update service router to use development services instead of mocks
5. **End-to-End Development Testing**: Test complete workflows with development external services
6. **Performance and Reliability Validation**: Validate system performance under development service constraints
7. **Create Handoff Notes**: **REQUIRED**: Document complete development testing results for Phase 6

## Phase 5 Requirements

### Core Tasks
- [ ] **REQUIRED**: Review and understand Phase 4 handoff notes completely
- [ ] Verify current system state matches Phase 4 handoff expectations
- [ ] Configure development-level external service integrations
- [ ] Update service router to use development services instead of mocks
- [ ] Implement development service authentication and configuration
- [ ] Validate complete end-to-end workflows with development services
- [ ] Test error handling and service resilience with development services
- [ ] **REQUIRED**: Create comprehensive handoff notes for Phase 6

### Success Criteria
- ✅ Development external services configured and operational
- ✅ Service router updated to use development services
- ✅ End-to-end workflows validated with development services
- ✅ Error handling and service resilience tested
- ✅ Performance validated under development service constraints
- ✅ System ready for production API integration
- ✅ **REQUIRED**: Complete handoff documentation ready for Phase 6

### Dependencies from Phase 4
- **End-to-End Pipeline**: ✅ Confirmed working from Phase 4 handoff
- **All Processing Stages**: ✅ All stages validated and working correctly
- **Database Infrastructure**: ✅ PostgreSQL operational with correct schema
- **BaseWorker Implementation**: ✅ Enhanced with comprehensive monitoring
- **Environment Configuration**: ✅ Docker Compose stack fully operational

## Technical Focus Areas

### 1. Development Service Configuration
- Configure development LlamaParse API endpoints and authentication
- Set up OpenAI development API keys and usage tracking
- Implement development service rate limiting and quotas
- Configure development service error handling and timeouts

### 2. Service Router Enhancement
- Update ServiceRouter to support development mode
- Implement development service selection and configuration
- Add development service health checks and monitoring
- Ensure seamless switching between mock and development services

### 3. End-to-End Development Testing
- Test complete document processing with development services
- Validate service integration reliability and performance
- Test concurrent processing with development service limits
- Validate error scenarios and recovery with development services

### 4. Development Environment Validation
- Verify development service authentication and authorization
- Test development service rate limits and usage patterns
- Validate development service error handling and resilience
- Ensure development environment production readiness

## Testing Procedures

### Step 1: Phase 4 Handoff Review
```bash
# REQUIRED: Review Phase 4 handoff notes
cat docs/initiatives/system/upload_refactor/003/file_testing/TODO001_phase4_handoff.md

# Verify current system state matches handoff expectations
docker-compose ps
docker-compose logs base-worker --tail=20
```

### Step 2: Development Service Setup
```bash
# Configure development service endpoints
python scripts/configure-development-services.py

# Set up development API credentials
python scripts/setup-development-credentials.py

# Validate development service connectivity
python scripts/validate-development-services.py
```

### Step 3: Service Router Configuration
```bash
# Update service router for development mode
python scripts/update-service-router-development.py

# Test service router development mode switching
python scripts/test-service-router-modes.py

# Validate service router development configuration
python scripts/validate-service-router-development.py
```

### Step 4: End-to-End Development Testing
```bash
# Test complete workflow with development services
python scripts/test-development-end-to-end.py

# Monitor development service performance
python scripts/monitor-development-services.py

# Test concurrent processing with development services
python scripts/test-development-concurrency.py
```

### Step 5: Development Service Resilience Testing
```bash
# Test development service error scenarios
python scripts/test-development-service-errors.py

# Test development service rate limiting
python scripts/test-development-rate-limits.py

# Validate development service recovery mechanisms
python scripts/test-development-service-recovery.py
```

### Step 6: Development Environment Validation
```sql
-- Monitor development service integration status
SELECT 
    service_name,
    mode,
    status,
    last_successful_call,
    error_count,
    avg_response_time
FROM service_router_status 
WHERE mode = 'development'
ORDER BY service_name;

-- Check development service call success rates
SELECT 
    service_endpoint,
    COUNT(*) as total_calls,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_calls,
    ROUND(100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM service_call_logs 
WHERE service_mode = 'development'
  AND created_at >= NOW() - INTERVAL '24 hours'
GROUP BY service_endpoint;

-- Verify development end-to-end processing
SELECT d.document_id, d.filename, uj.stage, uj.updated_at,
       dc.chunk_count, dc.embedding_count
FROM upload_pipeline.documents d
JOIN upload_pipeline.upload_jobs uj ON d.document_id = uj.document_id
LEFT JOIN (
    SELECT document_id, 
           COUNT(*) as chunk_count,
           COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as embedding_count
    FROM upload_pipeline.document_chunks
    GROUP BY document_id
) dc ON d.document_id = dc.document_id
WHERE d.created_at >= NOW() - INTERVAL '1 hour'
ORDER BY uj.updated_at DESC;
```

## Expected Outcomes

### Success Scenario
- Development external services configured and operational
- Service router updated to use development services
- End-to-end workflows validated with development services
- Error handling and service resilience tested
- Performance validated under development service constraints
- System ready for production API integration
- **REQUIRED**: Complete handoff documentation ready for Phase 6

### Failure Scenarios
- Development services not properly configured or accessible
- Service router fails to switch to development mode
- End-to-end workflows fail with development services
- Development service error handling inadequate
- Performance degradation with development services
- System not ready for production API integration

## Risk Assessment

### High Risk
- **Development Service Integration Failures**: Critical development services not accessible
  - *Mitigation*: Comprehensive service validation and fallback procedures
- **Service Authentication Issues**: Development API authentication failures
  - *Mitigation*: Thorough credential validation and secure management

### Medium Risk
- **Development Service Rate Limiting**: Exceeding development API rate limits
  - *Mitigation*: Implement proper throttling and usage monitoring
- **Performance Degradation**: Development services slower than mocks
  - *Mitigation*: Performance testing and optimization strategies

### Low Risk
- **Service Configuration Changes**: Development service endpoints or formats change
  - *Mitigation*: Robust service configuration and validation
- **Documentation Gaps**: Incomplete development service integration documentation
  - *Mitigation*: Comprehensive documentation review and validation

## Phase 6 Readiness

### Phase 6 Dependencies
- ✅ Development external services configured and tested
- ✅ Service router supporting development and production modes
- ✅ End-to-end workflows validated with realistic service constraints
- ✅ Error handling and service resilience tested
- ✅ **REQUIRED**: Complete handoff documentation provided

### Handoff Requirements
- **REQUIRED**: Complete Phase 5 development testing results
- **REQUIRED**: Development service integration status and configuration
- **REQUIRED**: End-to-end validation results with development services
- **REQUIRED**: Performance benchmarks and service usage metrics
- **REQUIRED**: Comprehensive handoff notes for Phase 6 production API integration

## Success Metrics

### Phase 5 Completion Criteria
- [ ] Development external services configured and operational
- [ ] Service router updated to use development services
- [ ] End-to-end workflows validated with development services
- [ ] Error handling and service resilience tested
- [ ] Performance validated under development service constraints
- [ ] System ready for production API integration
- [ ] **REQUIRED**: Complete handoff documentation ready for Phase 6

## Handoff Documentation Requirements

### **MANDATORY**: Phase 5 → Phase 6 Handoff Notes
The handoff document (`TODO001_phase5_handoff.md`) must include:

1. **Phase 5 Completion Summary**
   - What was accomplished with development service integration
   - Technical implementation details
   - Success criteria achievement status

2. **Current System State**
   - Database status and job distribution
   - Worker service health and operational status
   - Development service integration status and health
   - Service router configuration and mode support

3. **Phase 6 Requirements**
   - Primary objective and success criteria for production API integration
   - Technical focus areas and implementation procedures
   - Dependencies and prerequisites for production services

4. **Risk Assessment**
   - Current risk profile and mitigation strategies
   - Known issues and workarounds from development testing
   - Recommendations for production API integration

5. **Knowledge Transfer**
   - Key learnings from Phase 5 development testing
   - Service integration patterns established
   - Best practices and architectural decisions for production readiness

6. **Handoff Checklist**
   - Phase 5 deliverables completed
   - Phase 6 readiness confirmed
   - Documentation handoff status

7. **Production Readiness Assessment**
   - Development testing completion status
   - Service integration validation results
   - Performance expectations and production preparation

---

**Phase 5 Status**: 🔄 IN PROGRESS  
**Focus**: Development End-to-End Testing  
**Environment**: postgres database, development service-integrated processing pipeline  
**Success Criteria**: Complete development service integration and validation  
**Next Phase**: Phase 6 (Production API Integration)  
**Handoff Requirement**: ✅ MANDATORY - Complete handoff documentation for Phase 6  
**Phase 4 Dependency**: ✅ REQUIRED - Review and understand Phase 4 handoff notes