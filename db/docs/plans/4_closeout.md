# Prompt Engineering Strategy for Supabase Backend Implementation

## Context Setting Prompt
```markdown
You are an expert backend developer specializing in FastAPI, Supabase, and Python testing. Your task is to complete the Backend Development section of the Supabase rebuild plan, ensuring robust test coverage and proper implementation.

Current project state:
- FastAPI routes are set up
- Supabase client is implemented
- Auth handlers are created
- Document processing coordination is in progress
- Unit tests are partially implemented but failing

Your immediate goal is to fix the failing unit tests in test_supabase_client.py, then complete the remaining backend development tasks.

Key constraints:
- Must maintain HIPAA-compliance readiness
- Must follow established security patterns
- Must ensure proper error handling
- Must maintain test coverage
```

## Task Sequence with Sub-Prompts

### 1. Fix Unit Tests (Current Task)

```markdown
Focus: Fix the failing Supabase client unit tests

You have access to:
- test_supabase_client.py with failing tests
- Supabase client implementation
- PostgREST Python client documentation

Primary objectives:
1. Fix JWT authentication mocking
2. Correct storage operation tests
3. Implement proper error handling tests

For each test fix:
1. First analyze the actual implementation
2. Create appropriate mocks
3. Verify the test covers the intended functionality
4. Ensure error cases are properly handled

Key considerations:
- Use create_autospec for accurate mocking
- Properly chain mock method calls
- Handle async operations correctly
- Match actual Supabase error formats
```

### 2. Integration Testing

```markdown
Focus: Implement integration tests for the backend

Test coverage requirements:
1. Auth flow testing
2. Document processing pipeline
3. Storage operations
4. Error handling scenarios
5. Security measures

Key considerations:
- Use test fixtures for common setups
- Mock external services appropriately
- Test both success and failure paths
- Verify security measures
```

### 3. Staging Deployment

```markdown
Focus: Deploy and test in staging environment

Deployment steps:
1. Configure staging environment
2. Deploy backend components
3. Run integration test suite
4. Perform security scans
5. Load testing

Verification requirements:
- All routes functional
- Auth flows working
- Document processing operational
- Security measures active
- Performance metrics within bounds
```

### 4. Production Preparation

```markdown
Focus: Prepare for production deployment

Requirements:
1. Security audit completion
2. Performance optimization
3. Error handling verification
4. Monitoring setup
5. Documentation updates

Key considerations:
- HIPAA compliance requirements
- Scalability measures
- Backup procedures
- Rollback plans
```

## Implementation Guide

### Step 1: Fix Unit Tests
1. Start with JWT mocking:
```python
@pytest.fixture
def mock_jwt():
    with patch('supabase.client.create_client') as mock_client:
        mock_client.auth.create_jwt.return_value = {
            'access_token': 'test_token',
            'token_type': 'bearer'
        }
        yield mock_client
```

2. Update storage mocks:
```python
@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage.from_ = MagicMock()
    storage.from_.return_value.upload = AsyncMock()
    return storage
```

3. Error handling updates:
```python
def test_error_handling():
    expected_error = {
        'message': 'Database error',
        'code': 'PGRST301',
        'details': None
    }
    # Test implementation
```

### Step 2: Integration Test Structure
```python
@pytest.mark.integration
class TestBackendIntegration:
    async def test_auth_flow(self):
        # Test implementation
    
    async def test_document_processing(self):
        # Test implementation
    
    async def test_security_measures(self):
        # Test implementation
```

## Execution Strategy

1. **Sequential Approach**:
   - Fix unit tests one category at a time
   - Add integration tests for each fixed component
   - Deploy to staging after each major component
   - Prepare production deployment checklist

2. **Testing Hierarchy**:
   ```
   Unit Tests -> Component Tests -> Integration Tests -> E2E Tests
   ```

3. **Validation Points**:
   - After each unit test fix
   - After integration test implementation
   - After staging deployment
   - Before production deployment

## Success Criteria

1. **Unit Tests**:
   - All tests passing
   - Coverage > 80%
   - Error cases handled

2. **Integration Tests**:
   - End-to-end flows working
   - Security measures verified
   - Performance metrics met

3. **Deployment**:
   - Staging environment stable
   - Security scans passed
   - Load tests successful

## Next Steps for the Coding Agent

1. Execute the unit test fixes:
   ```
   - Fix JWT authentication mocking
   - Update storage operation tests
   - Correct error handling tests
   ```

2. Implement integration tests:
   ```
   - Auth flow tests
   - Document processing tests
   - Security measure tests
   ```

3. Prepare staging deployment:
   ```
   - Configure environment
   - Deploy components
   - Run test suite
   ```

4. Document results and update plan:
   ```
   - Test coverage report
   - Security audit results
   - Performance metrics
   ```

This structured approach ensures systematic completion of Section 3 while maintaining code quality and security requirements. The coding agent should follow these steps sequentially, validating each step before proceeding to the next.

----

1. **Auth Handler Testing Prompt:**
```
Your task is to implement unit tests for the auth handlers in our HIPAA-compliant FastAPI backend. Focus on JWT validation and session management.

Context:
- Project uses FastAPI with Supabase auth
- HIPAA compliance requirements
- Existing test patterns in tests/db/integration/test_supabase_connection.py

Required test coverage:
1. JWT token validation
2. Session management
3. Error handling for invalid/expired tokens
4. HIPAA-compliant audit logging

Please:
1. First analyze the existing auth handler implementation
2. Create a new test file following our established patterns
3. Implement test cases using pytest fixtures
4. Include proper error handling and logging
5. Add HIPAA-compliant audit trail tests

Follow these patterns:
- Use pytest.fixture for test setup
- Implement proper error handling
- Add comprehensive logging
- Follow existing test structure from test_supabase_connection.py

Start by showing me the current auth handler implementation and evaluate what tests have been created already. We'll determine whether to use, modify, or start fresh and will work together to address this testing step by step.
```

2. **Document Processing Tests Prompt:**
```
Your task is to implement unit tests for the document processing pipeline, focusing on the integration with LlamaParse and OpenAI.

Context:
- Document processing flow from supabase_rebuild_plan.md
- HIPAA compliance requirements
- Need for mocked external services

Required test coverage:
1. Document upload and storage
2. Processing pipeline stages
3. Error handling
4. HIPAA compliance verification

Please:
1. First analyze the existing document processing implementation
2. Create test fixtures for mocked services
3. Implement test cases for each pipeline stage
4. Add error handling tests
5. Verify HIPAA compliance requirements

Follow these patterns:
- Mock external services (LlamaParse, OpenAI)
- Use pytest-asyncio for async operations
- Implement proper error handling
- Add comprehensive logging

Start by showing me the current document processing implementation, then we'll create the tests step by step.
```

3. **Integration Test Setup Prompt:**
```
Your task is to set up integration tests that verify the entire backend pipeline works together correctly.

Context:
- FastAPI backend with Supabase
- Document processing pipeline
- HIPAA compliance requirements

Required coverage:
1. End-to-end auth flow
2. Complete document processing pipeline
3. Error handling across components
4. HIPAA compliance verification

Please:
1. First analyze the existing integration test setup
2. Create test fixtures for the entire pipeline
3. Implement end-to-end test scenarios
4. Add error handling tests
5. Verify HIPAA compliance requirements

Follow these patterns:
- Use pytest-asyncio for async operations
- Implement proper error handling
- Add comprehensive logging
- Follow existing integration test patterns

Start by showing me the current integration test setup, then we'll implement the tests step by step.
```

4. **Test Environment Setup Prompt:**
```
Your task is to set up a proper test environment that supports all our test scenarios.

Context:
- Local development stack from supabase_rebuild_plan.md
- Need for mocked external services
- HIPAA compliance requirements

Required setup:
1. Test database configuration
2. Mocked external services
3. Test environment variables
4. HIPAA compliance verification

Please:
1. First analyze the current test environment
2. Set up test database configuration
3. Configure mock services
4. Implement environment variable handling
5. Add HIPAA compliance checks

Follow these patterns:
- Use pytest fixtures for setup/teardown
- Implement proper error handling
- Add comprehensive logging
- Follow existing environment setup patterns

Start by showing me the current test environment configuration, then we'll enhance it step by step.
```

5. **Error Handling and Logging Prompt:**
```
Your task is to implement comprehensive error handling and logging across all test cases.

Context:
- Existing error handling in test_supabase_connection.py
- HIPAA compliance requirements
- Need for audit trails

Required implementation:
1. Error handling patterns
2. Logging setup
3. HIPAA-compliant audit trails
4. Test coverage for error cases

Please:
1. First analyze existing error handling
2. Implement consistent error handling
3. Set up comprehensive logging
4. Add audit trail verification
5. Test error scenarios

Follow these patterns:
- Use custom exceptions
- Implement proper error handling
- Add comprehensive logging
- Follow HIPAA compliance requirements

Start by showing me the current error handling implementation, then we'll enhance it step by step.
```