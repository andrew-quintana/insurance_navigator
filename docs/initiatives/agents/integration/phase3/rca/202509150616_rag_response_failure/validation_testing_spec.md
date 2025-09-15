# Testing Spec: RAG Response Failure Validation
## Phase 3 Integration - Post RCA Implementation

**Document ID**: `testing_spec_202509150616`  
**Date**: September 15, 2025  
**Based on**: RCA 001, 002, and isolated testing completion  
**Focus**: Mock services → External API services transition testing

---

## Scope

### What is being tested
- **RAG System**: Information retrieval with UUID consistency fixes
- **Upload Pipeline**: Document processing with deterministic UUID generation
- **Authentication Flow**: JWT token validation and user ID propagation  
- **Database Operations**: Normalized query patterns and data integrity
- **End-to-End Workflow**: Complete user journey from auth to response

### In Scope
✅ **Core Functionality**
- Document upload with proper user association
- Chunk processing and embedding generation
- RAG query execution with similarity threshold adjustments
- Response generation and output formatting

✅ **RCA Fix Validation**  
- UUID consistency across upload → processing → retrieval
- Similarity threshold adjustment (0.7 → 0.3) effectiveness
- User ID flow from authentication through RAG queries
- Normalized database query pattern validation

✅ **Service Integration**
- Mock service testing for isolated validation
- External API service testing for production readiness
- Service transition validation (mock → external)
- Error handling and fallback mechanisms

### Out of Scope
❌ **Performance Optimization** (beyond basic validation)
❌ **UI/UX Testing** (backend focus only)  
❌ **Load Testing** (covered in separate performance spec)
❌ **Security Penetration Testing** (covered in security spec)

---

## Test Types

### Unit Tests

#### **UUID Generation & Consistency**
```python
class TestUUIDConsistency:
    def test_deterministic_document_id_generation():
        # Verify UUID v5 generation with user_id + file_sha256
        
    def test_chunk_id_generation():
        # Verify UUID v5 with document_id + chunker + version + order
        
    def test_uuid_consistency_across_pipeline():
        # End-to-end UUID tracking from upload to retrieval
```

#### **Database Operations**  
```python
class TestDatabaseOperations:
    def test_normalized_query_pattern():
        # Verify JOIN between documents and document_chunks
        
    def test_user_isolation():
        # Ensure users can only access their own documents
        
    def test_embedding_storage_retrieval():
        # Vector operations and similarity calculations
```

#### **RAG Tool Functionality**
```python
class TestRAGTool:
    def test_similarity_threshold_adjustment():
        # Validate 0.3 threshold returns appropriate results
        
    def test_chunk_filtering_and_ranking():
        # Verify chunk selection and similarity scoring
        
    def test_query_processing():
        # Expert reframe and query optimization
```

### Integration Tests

#### **Upload Pipeline Integration**
```python
class TestUploadPipeline:
    def test_document_upload_to_chunking():
        # Complete flow: upload → parse → chunk → embed
        
    def test_user_authentication_to_storage():
        # JWT extraction → user validation → database storage
        
    def test_error_handling_and_recovery():
        # Failed uploads, processing errors, retry mechanisms
```

#### **RAG System Integration**
```python
class TestRAGSystem:
    def test_query_to_response_generation():
        # Complete RAG flow: query → retrieval → ranking → response
        
    def test_no_results_handling():
        # Graceful handling when no relevant chunks found
        
    def test_multi_document_scenarios():
        # Users with multiple documents and complex queries
```

#### **Mock Service Integration**
```python
class TestMockServices:
    def test_openai_embedding_mock():
        # Validate mock embedding service returns consistent results
        
    def test_anthropic_llm_mock():
        # Validate mock LLM service for query processing and response generation
        
    def test_service_configuration_switching():
        # Seamless transition between mock and external services
```

### End-to-End Tests

#### **Complete User Journey**
```python
class TestUserJourney:
    def test_new_user_complete_workflow():
        # Register → Login → Upload → Query → Response
        
    def test_returning_user_workflow():
        # Login → Query existing documents → Response
        
    def test_edge_case_scenarios():
        # Empty documents, large files, unsupported formats
```

#### **Service Transition Testing**
```python
class TestServiceTransition:
    def test_mock_to_external_api_transition():
        # Validate consistent results when switching services
        
    def test_external_api_failure_fallback():
        # Graceful degradation to mock services if external APIs fail
        
    def test_configuration_management():
        # Environment variable switches and service selection
```

### Load/Performance Tests

#### **Basic Performance Validation**
```python
class TestBasicPerformance:
    def test_response_time_thresholds():
        # RAG queries complete within 5 seconds
        
    def test_concurrent_user_handling():
        # 5-10 concurrent users without degradation
        
    def test_memory_usage_monitoring():
        # Embedding and vector operations within memory limits
```

---

## Coverage Goals

### Code Coverage
- **Target**: 85% overall code coverage
- **Critical Paths**: 95% coverage for RCA-fixed components
  - UUID generation utilities: 100%
  - Upload pipeline endpoints: 95%  
  - RAG tool core functionality: 95%
  - Database query operations: 90%

### Critical Path Scenarios

#### **Scenario 1: Successful Document Processing**
1. User uploads document with valid authentication
2. Document processed with deterministic UUID
3. Chunks created and embeddings generated  
4. RAG query retrieves relevant chunks
5. Response generated and returned to user
- **Coverage Goal**: 100% of happy path

#### **Scenario 2: UUID Consistency Validation**  
1. Document upload generates deterministic UUID
2. Processing workers find document using same UUID
3. Chunks created with proper document_id references
4. RAG queries match chunks to documents via UUID
5. Full UUID traceability maintained
- **Coverage Goal**: 100% of UUID flow

#### **Scenario 3: Error Handling & Recovery**
1. Invalid file upload → appropriate error message
2. Processing failure → retry mechanism triggered
3. No relevant chunks found → graceful "no information" response
4. External API failure → fallback to mock services
5. Database connection issues → proper error handling
- **Coverage Goal**: 90% of error scenarios

#### **Scenario 4: Service Configuration Switching**
1. Mock services configured for testing
2. All functionality validated with mock services
3. Switch to external APIs (OpenAI, Anthropic)  
4. Validate consistent results with external services
5. Test fallback mechanisms
- **Coverage Goal**: 95% of configuration scenarios

---

## Test Data & Environments

### Staging Setup

#### **Mock Services Environment**
```yaml
# docker-compose.test.yml
services:
  mock-openai:
    image: mock-openai-api:latest
    ports: ["8001:8000"]
    environment:
      - EMBEDDING_MODEL=text-embedding-3-small
      - MOCK_RESPONSES=true
      
  mock-anthropic:
    image: mock-anthropic-api:latest  
    ports: ["8002:8000"]
    environment:
      - MODEL=claude-sonnet-4
      - MOCK_RESPONSES=true
      
  insurance-api:
    build: .
    environment:
      - OPENAI_BASE_URL=http://mock-openai:8000
      - ANTHROPIC_BASE_URL=http://mock-anthropic:8000
      - SIMILARITY_THRESHOLD=0.3
```

#### **External Services Environment**
```yaml
# docker-compose.prod.yml  
services:
  insurance-api:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_BASE_URL=https://api.openai.com/v1
      - ANTHROPIC_BASE_URL=https://api.anthropic.com
      - SIMILARITY_THRESHOLD=0.3
```

### Mock Data vs Real Data

#### **Mock Data** (Phase 1 Testing)
```python
# Test data for isolated validation
MOCK_DOCUMENTS = {
    "insurance_policy_1": {
        "content": "Annual deductible: $500. Coverage limit: $100,000...",
        "file_type": "pdf",
        "user_id": "test-user-001"
    },
    "medical_record_1": {
        "content": "Patient diagnosis: Type 2 diabetes. Treatment plan...",
        "file_type": "txt", 
        "user_id": "test-user-001"
    }
}

MOCK_QUERIES = [
    "What is my annual deductible?",
    "What conditions are covered?", 
    "What is my coverage limit?"
]

EXPECTED_RESPONSES = {
    "What is my annual deductible?": "Your annual deductible is $500..."
}
```

#### **Real Data** (Phase 2 Testing)
```python
# Real insurance documents for production validation
REAL_TEST_USERS = [
    {
        "email": "testuseraq@example.com",
        "password": "zoqgoz-zinmim-4Sesnu",
        "user_id": "e5167bd7-849e-4d04-bd74-eef7c60402ce"
    },
    {
        "email": "testuser2@example.com", 
        "password": "generated-password-2",
        "user_id": "fbd836c6-ed55-4f18-a0a5-4ec1152b83ce"
    }
]

# Real insurance policy documents
REAL_DOCUMENTS = [
    "sample_health_insurance_policy.pdf",
    "medical_claims_history.pdf", 
    "prescription_coverage_details.pdf"
]
```

### Test Database Setup

#### **Schema Validation**
```sql
-- Verify schema matches expected structure
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'upload_pipeline'
ORDER BY table_name, ordinal_position;

-- Verify foreign key constraints
SELECT constraint_name, table_name, column_name, 
       foreign_table_name, foreign_column_name
FROM information_schema.referential_constraints rc
JOIN information_schema.key_column_usage kcu ON rc.constraint_name = kcu.constraint_name
WHERE rc.constraint_schema = 'upload_pipeline';
```

#### **Test Data Population**
```python
async def setup_test_data():
    # Create test users
    await create_test_users(REAL_TEST_USERS)
    
    # Upload test documents
    await upload_test_documents(REAL_DOCUMENTS)
    
    # Verify processing completion
    await verify_chunk_processing()
    
    # Validate embeddings generated
    await verify_embedding_coverage()
```

---

## Acceptance Criteria

### CI/CD Pipeline Passes
- [ ] **Unit Tests**: 100% pass rate with 85%+ coverage
- [ ] **Integration Tests**: 100% pass rate for critical paths
- [ ] **End-to-End Tests**: 90%+ pass rate (allowing for external API flakiness)
- [ ] **Mock Service Tests**: 100% pass rate (should be deterministic)
- [ ] **Service Transition Tests**: 95%+ pass rate

### Error Rate < Threshold
- [ ] **Upload Success Rate**: >99% for valid documents
- [ ] **Processing Success Rate**: >95% for uploaded documents  
- [ ] **RAG Query Success Rate**: >90% for queries with relevant content
- [ ] **Response Generation**: >95% success rate for found content
- [ ] **Service Availability**: >99% uptime during testing period

### Coverage Targets Met
- [ ] **Code Coverage**: 85%+ overall, 95%+ for RCA-fixed components
- [ ] **UUID Flow Coverage**: 100% of deterministic UUID generation paths
- [ ] **Error Scenarios**: 90%+ of identified error conditions
- [ ] **Service Configurations**: 95%+ of mock/external service combinations

### RCA Fix Validation
- [ ] **UUID Consistency**: 100% of uploads use deterministic UUIDs
- [ ] **Processing Pipeline**: 100% of uploaded documents get processed
- [ ] **Similarity Threshold**: RAG queries return results with 0.3 threshold  
- [ ] **User Association**: 100% of documents associated with correct users
- [ ] **End-to-End Workflow**: Complete user journey works for test users

### Mock vs External Service Validation  
- [ ] **Functional Parity**: Mock services provide equivalent functionality
- [ ] **Response Consistency**: Similar results between mock and external APIs
- [ ] **Configuration Switching**: Seamless transition between service types
- [ ] **Fallback Mechanisms**: Graceful degradation when external services unavailable
- [ ] **Performance Similarity**: Response times within acceptable variance

### Production Readiness Criteria
- [ ] **External API Integration**: All external services working correctly
- [ ] **Configuration Management**: Environment variables properly configured
- [ ] **Error Handling**: Graceful handling of all identified failure modes
- [ ] **Monitoring**: Proper logging and observability for production deployment
- [ ] **Documentation**: Complete setup and troubleshooting guides

---

## Test Execution Plan

### Phase 1: Mock Service Validation (Days 1-2)
```bash
# Set up mock services environment
docker-compose -f docker-compose.test.yml up -d

# Execute isolated testing
pytest tests/unit/ -v --cov=./ --cov-report=html
pytest tests/integration/mock/ -v
pytest tests/e2e/mock/ -v

# Validate all RCA fixes with mock services
pytest tests/rca_validation/ -v -m "mock_services"
```

### Phase 2: External API Integration (Days 3-4)  
```bash
# Set up external services environment
docker-compose -f docker-compose.prod.yml up -d

# Execute external API testing
pytest tests/integration/external/ -v
pytest tests/e2e/external/ -v  

# Validate service transition
pytest tests/service_transition/ -v

# Performance validation
pytest tests/performance/ -v -m "basic_validation"
```

### Phase 3: Production Readiness (Day 5)
```bash
# Full regression testing
pytest tests/ -v --cov=./ --cov-report=html

# Production environment validation  
pytest tests/production_readiness/ -v

# Final acceptance criteria verification
python scripts/validate_acceptance_criteria.py
```

---

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
    mock_services: Tests using mock services
    external_services: Tests using external APIs
    rca_validation: RCA fix validation tests
    performance: Performance validation tests
addopts = 
    --strict-markers
    --disable-warnings
    --tb=short
    -ra
```

### Mock Service Framework
```python
# Custom mock service utilities
class MockOpenAIService:
    def __init__(self, deterministic_responses=True):
        self.deterministic = deterministic_responses
        
    async def create_embedding(self, text: str, model: str):
        # Return deterministic embeddings for testing
        
class MockAnthropicService:
    def __init__(self, response_templates=None):
        self.templates = response_templates or DEFAULT_TEMPLATES
        
    async def generate_response(self, messages: list):
        # Return templated responses for testing
```

### Test Data Management
```python
# Test data fixtures
@pytest.fixture(scope="session")
async def test_database():
    # Set up clean test database
    
@pytest.fixture(scope="function")  
async def test_user():
    # Create isolated test user for each test
    
@pytest.fixture(scope="module")
async def sample_documents():
    # Load sample insurance documents
```

---

## Success Metrics

### Technical Metrics
- **Test Suite Execution Time**: <10 minutes for full suite
- **Test Reliability**: <2% flaky test rate  
- **Coverage Achievement**: 85%+ code coverage maintained
- **RCA Fix Validation**: 100% of identified issues resolved

### Quality Metrics  
- **Bug Detection Rate**: >90% of bugs caught before production
- **Regression Prevention**: 0 regressions introduced by fixes
- **Service Parity**: <10% variance between mock and external service results
- **Production Readiness Score**: 95%+ based on acceptance criteria

### Process Metrics
- **Test Development Velocity**: Test suite completion within 3 days
- **Issue Resolution Time**: Average <4 hours from detection to fix
- **Documentation Coverage**: 100% of test procedures documented
- **Knowledge Transfer**: Complete test suite runnable by any team member

---

**Document Status**: ✅ **ACTIVE**  
**Test Execution**: Ready to begin Phase 1  
**Dependencies**: Mock services deployment, test data preparation  
**Owner**: Development Team  
**Approval Required**: Technical Lead sign-off before Phase 2