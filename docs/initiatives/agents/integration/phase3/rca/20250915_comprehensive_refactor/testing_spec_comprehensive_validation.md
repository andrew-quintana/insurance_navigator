# Testing Spec - Comprehensive System Refactor Validation

## Scope
- **What is being tested**: Complete system refactor addressing service integration, configuration management, database schema standardization, UUID generation consistency, and RAG system integration
- **In scope**: End-to-end user workflows, service integration, configuration loading, database operations, UUID consistency, error handling, performance validation
- **Out of scope**: UI/UX changes, new feature development, external API modifications, infrastructure changes beyond service configuration

## Test Types

### Unit Tests
- **Service Component Testing**: Individual service components and their methods
- **Configuration Management Testing**: Configuration loading, validation, and environment handling
- **Database Operation Testing**: Individual database queries and operations
- **UUID Generation Testing**: UUID generation consistency and validation
- **Error Handling Testing**: Error handling and recovery mechanisms

### Integration Tests
- **Service Integration Testing**: Service-to-service communication and dependencies
- **Configuration Integration Testing**: Configuration loading across all services
- **Database Integration Testing**: Database operations and schema consistency
- **Pipeline Integration Testing**: Complete upload → processing → retrieval pipeline
- **RAG Integration Testing**: RAG system integration with chat endpoints

### End-to-End Tests
- **User Workflow Testing**: Complete user journeys from upload to chat
- **Error Scenario Testing**: Error handling and recovery across the system
- **Performance Testing**: System performance under normal and load conditions
- **Security Testing**: Authentication, authorization, and data protection
- **Configuration Testing**: Environment-specific configuration validation

### Load/Performance Tests
- **Concurrent User Testing**: Multiple users uploading and chatting simultaneously
- **Data Volume Testing**: Large volumes of documents and chunks
- **Performance Benchmarking**: Response time and throughput validation
- **Resource Utilization Testing**: Memory, CPU, and database usage
- **Scalability Testing**: System behavior under increasing load

## Coverage Goals
- **Code Coverage**: 90%+ overall code coverage
- **Critical Paths**: 100% coverage for refactored components
  - Service initialization and dependency injection: 100%
  - Configuration management: 100%
  - Database schema operations: 100%
  - UUID generation and validation: 100%
  - RAG system integration: 100%

### Critical Path Scenarios

#### **Scenario 1: Complete User Workflow**
1. User authenticates and receives JWT token
2. User uploads document via /api/v2/upload endpoint
3. Document processed with deterministic UUID generation
4. Chunks created and embeddings generated
5. User queries document via /chat endpoint
6. RAG system retrieves relevant chunks and generates response
- **Coverage Goal**: 100% of happy path

#### **Scenario 2: Service Integration Validation**
1. All services initialize correctly with proper dependencies
2. Configuration loads correctly from environment variables
3. Database connections established and validated
4. RAG tool available and functional in chat endpoints
5. Error handling works correctly across all services
- **Coverage Goal**: 100% of service integration

#### **Scenario 3: Configuration Management Validation**
1. Environment-specific configurations load correctly
2. Similarity threshold set to 0.3 for production
3. Database connection settings load from environment
4. Service endpoints resolve correctly
5. Configuration validation fails fast with clear errors
- **Coverage Goal**: 100% of configuration scenarios

#### **Scenario 4: Database Schema Consistency**
1. All code references correct table names (document_chunks)
2. Foreign key relationships maintained correctly
3. Queries use proper JOIN operations
4. Data integrity maintained across operations
5. Migration scripts work correctly
- **Coverage Goal**: 100% of database operations

#### **Scenario 5: UUID Generation Consistency**
1. Upload endpoints use deterministic UUID generation
2. Processing workers find documents using matching UUIDs
3. Chunks created with proper document_id references
4. RAG queries retrieve chunks using consistent UUIDs
5. UUID validation and consistency checks pass
- **Coverage Goal**: 100% of UUID operations

## Test Data & Environments

### Development Environment
```yaml
# docker-compose.dev.yml
services:
  main-api:
    build: .
    environment:
      - ENVIRONMENT=development
      - RAG_SIMILARITY_THRESHOLD=0.3
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/insurance_navigator
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    ports: ["8001:8001"]
    
  database:
    image: postgres:15
    environment:
      - POSTGRES_DB=insurance_navigator
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports: ["5432:5432"]
```

### Staging Environment
```yaml
# docker-compose.staging.yml
services:
  main-api:
    build: .
    environment:
      - ENVIRONMENT=staging
      - RAG_SIMILARITY_THRESHOLD=0.3
      - DATABASE_URL=${STAGING_DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    ports: ["8001:8001"]
```

### Production Environment
```yaml
# docker-compose.prod.yml
services:
  main-api:
    build: .
    environment:
      - ENVIRONMENT=production
      - RAG_SIMILARITY_THRESHOLD=0.3
      - DATABASE_URL=${PRODUCTION_DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    ports: ["8001:8001"]
```

### Test Data Sets
```python
# Unit test data
UNIT_TEST_DOCUMENTS = [
    {
        "filename": "test_policy_1.pdf",
        "content": "Annual deductible: $500. Coverage limit: $100,000...",
        "user_id": "test-user-001"
    },
    {
        "filename": "test_policy_2.pdf", 
        "content": "Co-pay: $25. Prescription coverage included...",
        "user_id": "test-user-002"
    }
]

# Integration test data
INTEGRATION_TEST_USERS = [
    {
        "email": "integration-test-1@example.com",
        "password": "TestPassword123!",
        "user_id": "integration-user-001"
    },
    {
        "email": "integration-test-2@example.com",
        "password": "TestPassword456!",
        "user_id": "integration-user-002"
    }
]

# End-to-end test data
E2E_TEST_SCENARIOS = [
    {
        "user": "e2e-user-001",
        "documents": ["health_insurance_policy.pdf", "dental_coverage.pdf"],
        "queries": ["What is my deductible?", "What dental procedures are covered?"],
        "expected_responses": ["Your annual deductible is $500", "Dental cleanings and fillings are covered"]
    }
]
```

## Acceptance Criteria

### Functional Requirements
- [ ] **Service Integration**: All services initialize correctly with proper dependencies
- [ ] **Configuration Management**: Environment-specific configurations load correctly
- [ ] **Database Operations**: All database operations use correct schema and queries
- [ ] **UUID Consistency**: Deterministic UUID generation works across all pipeline stages
- [ ] **RAG Integration**: RAG system works correctly with chat endpoints
- [ ] **Error Handling**: Comprehensive error handling and recovery mechanisms

### Performance Requirements
- [ ] **Response Times**: Document upload < 500ms, RAG query < 2s, complete workflow < 10s
- [ ] **Throughput**: Support 10+ concurrent users without degradation
- [ ] **Resource Usage**: Memory usage < 2GB, CPU usage < 80% under normal load
- [ ] **Database Performance**: Query response times < 100ms for standard operations

### Reliability Requirements
- [ ] **Uptime**: 99%+ uptime during testing period
- [ ] **Error Rate**: < 1% error rate for critical user workflows
- [ ] **Recovery Time**: < 5 seconds mean time to recovery from failures
- [ ] **Data Integrity**: 100% data consistency and referential integrity

### Security Requirements
- [ ] **Authentication**: JWT token validation works correctly
- [ ] **Authorization**: Users can only access their own documents
- [ ] **Data Protection**: Sensitive data properly encrypted and protected
- [ ] **API Security**: All endpoints properly secured and validated

## Test Execution Plan

### Phase 1: Unit Testing (Days 1-2)
```bash
# Run unit tests for all refactored components
pytest tests/unit/service_integration/ -v --cov=./ --cov-report=html
pytest tests/unit/configuration_management/ -v --cov=./ --cov-report=html
pytest tests/unit/database_schema/ -v --cov=./ --cov-report=html
pytest tests/unit/uuid_generation/ -v --cov=./ --cov-report=html
pytest tests/unit/rag_integration/ -v --cov=./ --cov-report=html
```

### Phase 2: Integration Testing (Days 3-4)
```bash
# Run integration tests for service communication
pytest tests/integration/service_integration/ -v
pytest tests/integration/configuration_integration/ -v
pytest tests/integration/database_integration/ -v
pytest tests/integration/pipeline_integration/ -v
pytest tests/integration/rag_integration/ -v
```

### Phase 3: End-to-End Testing (Days 5-6)
```bash
# Run end-to-end tests for complete workflows
pytest tests/e2e/user_workflows/ -v
pytest tests/e2e/error_scenarios/ -v
pytest tests/e2e/performance/ -v
pytest tests/e2e/security/ -v
pytest tests/e2e/configuration/ -v
```

### Phase 4: Load Testing (Days 7-8)
```bash
# Run load tests for performance validation
pytest tests/load/concurrent_users/ -v
pytest tests/load/data_volume/ -v
pytest tests/load/performance_benchmarking/ -v
pytest tests/load/resource_utilization/ -v
pytest tests/load/scalability/ -v
```

## Test Tools & Framework

### Testing Framework
```python
# pytest configuration (pytest.ini)
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers = 
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    load: Load/performance tests
    service_integration: Service integration tests
    configuration: Configuration management tests
    database: Database schema tests
    uuid: UUID generation tests
    rag: RAG system tests
addopts = 
    --strict-markers
    --disable-warnings
    --tb=short
    -ra
```

### Test Utilities
```python
# Test configuration utilities
class TestConfigurationManager:
    def __init__(self, environment: str = "test"):
        self.environment = environment
        self.config = self._load_test_config()
    
    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
    
    def _load_test_config(self) -> Dict[str, Any]:
        return {
            "rag.similarity_threshold": 0.3,
            "database.url": "postgresql://test:test@localhost:5432/test_db",
            "environment": self.environment
        }

# Test database utilities
class TestDatabaseManager:
    def __init__(self):
        self.connection = self._create_test_connection()
    
    def setup_test_data(self, test_data: List[Dict]) -> None:
        # Setup test data in database
        pass
    
    def cleanup_test_data(self) -> None:
        # Clean up test data after tests
        pass

# Test service utilities
class TestServiceManager:
    def __init__(self):
        self.services = {}
    
    def start_service(self, service_name: str) -> None:
        # Start test service
        pass
    
    def stop_service(self, service_name: str) -> None:
        # Stop test service
        pass
```

## Success Metrics

### Technical Metrics
- **Test Suite Execution Time**: < 30 minutes for full suite
- **Test Reliability**: < 1% flaky test rate
- **Coverage Achievement**: 90%+ code coverage maintained
- **Performance Targets**: All performance targets met or exceeded

### Quality Metrics
- **Bug Detection Rate**: > 95% of bugs caught before production
- **Regression Prevention**: 0 regressions introduced by refactor
- **System Stability**: 99%+ uptime during testing period
- **Production Readiness Score**: 100% based on acceptance criteria

### Process Metrics
- **Test Development Velocity**: Test suite completion within 8 days
- **Issue Resolution Time**: Average < 2 hours from detection to fix
- **Documentation Coverage**: 100% of test procedures documented
- **Knowledge Transfer**: Complete test suite runnable by any team member

---

**Document Status**: ✅ **ACTIVE**  
**Test Execution**: Ready to begin Phase 1  
**Dependencies**: Refactored components, test environment setup  
**Owner**: QA Team  
**Approval Required**: Technical Lead sign-off before production deployment
