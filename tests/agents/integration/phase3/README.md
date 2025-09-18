# Phase 3 Integration Tests

**Location**: `/tests/agents/integration/phase3/`  
**Source**: Moved from `/docs/initiatives/agents/integration/phase3/tests/`  
**Purpose**: Cloud infrastructure and production integration testing

## Test Categories

### Cloud Infrastructure Tests
- `cloud_infrastructure_test.py` - Cloud infrastructure validation
- `service_deployment_test.py` - Service deployment validation  
- `render_deployment_test.py` - Render deployment testing
- `cloud_performance_test.py` - Cloud performance benchmarking
- `cloud_chat_endpoint_test.py` - Cloud /chat endpoint testing

### Production Integration Tests
- `phase3_production_deployment_test.py` - Production deployment validation
- `phase3_production_pipeline_test.py` - Production pipeline testing
- `phase3_production_real_user_test.py` - Real user scenario testing
- `phase3_production_full_workflow_test.py` - Complete workflow validation

### RAG and Worker Tests
- `test_production_worker_real_apis.py` - Production worker API testing
- `test_worker_real_apis_simple.py` - Simplified worker API tests
- `test_worker_config_verification.py` - Worker configuration testing
- `test_uploaded_document_rag.py` - Document RAG integration testing

### Comprehensive Testing
- `phase3_complete_integration_test.py` - Complete integration validation
- `phase3_complete_workflow_test.py` - Complete workflow testing
- `phase3_comprehensive_validation_test.py` - Comprehensive validation
- `phase3_upload_pipeline_integration_test.py` - Upload pipeline integration
- `phase3_rag_deep_dive_test.py` - Deep RAG system testing

### Debug and Utility Scripts
- `debug_rag_system.py` - RAG system debugging
- `debug_similarity_search.py` - Similarity search debugging
- `fix_mock_content.py` - Mock content fixes
- `regenerate_embeddings.py` - Embedding regeneration
- `test_psutil_fix.py` - PSUtil configuration testing

## Usage

Run tests from the project root:

```bash
# Run all phase3 tests
python -m pytest tests/agents/integration/phase3/

# Run specific test category
python -m pytest tests/agents/integration/phase3/cloud_*

# Run production tests
python -m pytest tests/agents/integration/phase3/phase3_production_*
```

## Related Documentation

- **Planning**: `/docs/initiatives/agents/integration/phase3/planning/`
- **Execution**: `/docs/initiatives/agents/integration/phase3/execution/`
- **Documentation**: `/docs/initiatives/agents/integration/phase3/documentation/`
- **Main README**: `/docs/initiatives/agents/integration/phase3/README.md`

## Test Results

Test results and reports are stored in:
- `/docs/initiatives/agents/integration/phase3/results/`
- `/docs/initiatives/agents/integration/phase3/reports/`