# Testing Infrastructure for 003 Worker Refactor

## Overview

This document describes the comprehensive testing infrastructure implemented during Phase 6 of the 003 Worker Refactor. The testing approach uses **frontend simulation** to validate all frontend integration points without requiring a full frontend server deployment.

## Testing Philosophy

### Frontend Simulation Approach

Instead of deploying and running a full Next.js frontend server for testing, we use **frontend simulation** which:

- **Simulates Frontend Behavior**: Makes the same API calls a frontend would make
- **Tests All Integration Points**: Validates every frontend-backend interaction
- **Fast and Reliable**: No frontend build or startup delays
- **Easy Automation**: Simple scripts for CI/CD integration
- **Comprehensive Coverage**: Tests all scenarios including error conditions

### What Gets Tested

1. **Upload Workflow**: Complete document upload to processing completion
2. **Job Management**: Status polling, listing, retry, and error handling
3. **API Contracts**: Request/response validation and error handling
4. **Rate Limiting**: Abuse prevention and concurrent processing limits
5. **Error Scenarios**: Validation errors, service failures, and edge cases
6. **Performance**: Response times, throughput, and resource usage

## Testing Scripts

### 1. Bash Testing Script: `test-frontend-simulation.sh`

**Location**: `scripts/testing/test-frontend-simulation.sh`

**Features**:
- **Quick Testing**: Fast validation during development
- **No Dependencies**: Uses only `curl` and bash
- **CI/CD Ready**: Simple automation for pipelines
- **Colored Output**: Clear success/failure indication

**Usage**:
```bash
# Make executable
chmod +x scripts/testing/test-frontend-simulation.sh

# Run with default settings
./scripts/testing/test-frontend-simulation.sh

# Run from project root
scripts/testing/test-frontend-simulation.sh
```

**Test Coverage**:
- Service health checks (API, Worker, Database)
- Upload endpoint with validation and deduplication
- Job status polling and progress tracking
- Job listing and management
- Error handling and validation
- Rate limiting and concurrent processing

### 2. Python Testing Script: `test-frontend-simulation.py`

**Location**: `scripts/testing/test-frontend-simulation.py`

**Features**:
- **Comprehensive Testing**: Full test suite execution
- **Async Performance**: Efficient HTTP request handling with aiohttp
- **Configurable**: Custom API endpoints and parameters
- **Exit Codes**: Proper CI/CD integration
- **Structured Logging**: Detailed error reporting and debugging

**Usage**:
```bash
# Install dependencies
pip install aiohttp

# Run with default settings
python scripts/testing/test-frontend-simulation.py

# Run with custom API URLs
python scripts/testing/test-frontend-simulation.py \
  --api-url http://localhost:8000 \
  --worker-url http://localhost:8002
```

**Test Coverage**:
- All tests from bash script plus:
- Async request handling for better performance
- Configurable test parameters
- Better error reporting and debugging
- CI/CD integration with proper exit codes

## Test Scenarios

### Happy Path Testing

1. **Document Upload**
   - Create new document with valid metadata
   - Validate job creation and ID generation
   - Monitor job processing through all stages
   - Verify completion and data integrity

2. **Job Management**
   - Poll job status for real-time updates
   - List user's jobs with filtering
   - Retry failed jobs when appropriate
   - Handle job completion and cleanup

### Error Path Testing

1. **Input Validation**
   - File size limits (25MB max)
   - MIME type validation (PDF only)
   - Filename sanitization and security
   - SHA256 hash validation

2. **Rate Limiting**
   - Upload rate limits (30/day/user)
   - Polling rate limits (10/min/job)
   - Concurrent job limits (2 per user)
   - Abuse prevention and protection

3. **Service Failures**
   - External service timeouts
   - Database connection failures
   - Worker process failures
   - Recovery and retry mechanisms

### Edge Case Testing

1. **Boundary Conditions**
   - Maximum file sizes
   - Rapid request sequences
   - Concurrent user operations
   - Resource exhaustion scenarios

2. **Data Consistency**
   - Duplicate upload handling
   - Partial processing failures
   - State machine edge cases
   - Buffer operation validation

## Integration with CI/CD

### Exit Codes
- **0**: All tests passed successfully
- **1**: One or more tests failed

### Environment Variables
```bash
# Customize test configuration
export API_BASE_URL="http://localhost:8000"
export WORKER_BASE_URL="http://localhost:8002"
export TEST_USER_ID="ci-test-user"
export LOG_LEVEL="INFO"
```

### CI/CD Examples

#### GitHub Actions
```yaml
- name: Run Frontend Simulation Tests
  run: |
    chmod +x scripts/testing/test-frontend-simulation.sh
    ./scripts/testing/test-frontend-simulation.sh

- name: Run Python Frontend Tests
  run: |
    pip install aiohttp
    python scripts/testing/test-frontend-simulation.py
```

#### GitLab CI
```yaml
test_frontend:
  script:
    - chmod +x scripts/testing/test-frontend-simulation.sh
    - ./scripts/testing/test-frontend-simulation.sh
  artifacts:
    reports:
      junit: test-results.xml
```

#### Jenkins Pipeline
```groovy
stage('Frontend Testing') {
    steps {
        sh 'chmod +x scripts/testing/test-frontend-simulation.sh'
        sh './scripts/testing/test-frontend-simulation.sh'
    }
}
```

## Testing in Different Environments

### Local Development
```bash
# Quick validation during development
./scripts/testing/test-frontend-simulation.sh

# Comprehensive testing with Python
python scripts/testing/test-frontend-simulation.py
```

### Staging Environment
```bash
# Test against staging API
python scripts/testing/test-frontend-simulation.py \
  --api-url https://staging-api.accessa.ai \
  --worker-url https://staging-worker.accessa.ai
```

### Production Environment
```bash
# Test against production API
python scripts/testing/test-frontend-simulation.py \
  --api-url https://api.accessa.ai \
  --worker-url https://worker.accessa.ai
```

## Performance Testing

### Load Testing
```bash
# Run multiple concurrent tests
for i in {1..10}; do
  python scripts/testing/test-frontend-simulation.py &
done
wait
```

### Stress Testing
```bash
# Test with high request volumes
python scripts/testing/test-frontend-simulation.py --stress-test
```

### Benchmarking
```bash
# Measure response times and throughput
python scripts/testing/test-frontend-simulation.py --benchmark
```

## Monitoring and Observability

### Test Metrics
- **Test Success Rate**: Percentage of tests passing
- **Response Times**: API endpoint performance
- **Error Rates**: Failure patterns and frequencies
- **Resource Usage**: CPU, memory, and network utilization

### Health Checks
- **Service Health**: API, Worker, Database connectivity
- **Performance Health**: Response time thresholds
- **Error Health**: Error rate monitoring
- **Resource Health**: Resource usage monitoring

### Alerting
- **Test Failures**: Immediate notification of test failures
- **Performance Degradation**: Alert when response times exceed thresholds
- **Service Unavailability**: Alert when services become unresponsive
- **Resource Exhaustion**: Alert when resources approach limits

## Troubleshooting

### Common Issues

1. **Services Not Running**
   ```bash
   # Check service health
   curl -f http://localhost:8000/health
   curl -f http://localhost:8002/health
   ```

2. **Database Connection Issues**
   ```bash
   # Verify database connectivity
   docker-compose ps postgres
   docker-compose logs postgres
   ```

3. **Authentication Issues**
   ```bash
   # Check JWT token format
   # Verify service role keys
   # Validate RLS policies
   ```

4. **Rate Limiting Issues**
   ```bash
   # Check rate limit configuration
   # Verify concurrent job limits
   # Test rate limit enforcement
   ```

### Debug Mode
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
python scripts/testing/test-frontend-simulation.py

# Run with debug output
./scripts/testing/test-frontend-simulation.sh --debug
```

## Future Enhancements

### Phase 7: Production Deployment
- **Real Frontend Testing**: Add actual Next.js frontend testing
- **Browser Automation**: Selenium/Playwright for end-to-end testing
- **Visual Testing**: Screenshot comparison and UI validation
- **User Experience Testing**: Real user workflow validation

### Advanced Testing Features
- **Performance Profiling**: Detailed performance analysis
- **Memory Leak Detection**: Memory usage monitoring and analysis
- **Security Testing**: Vulnerability scanning and penetration testing
- **Compliance Testing**: HIPAA and security compliance validation

### Testing Infrastructure
- **Distributed Testing**: Multi-environment testing coordination
- **Test Data Management**: Automated test data generation and cleanup
- **Test Result Storage**: Persistent test result storage and analysis
- **Test Reporting**: Comprehensive test result reporting and trending

## Best Practices

### Test Execution
1. **Run Tests Early**: Test during development, not just before deployment
2. **Automate Everything**: Use CI/CD for consistent test execution
3. **Monitor Results**: Track test success rates and performance trends
4. **Fail Fast**: Stop deployment on test failures

### Test Maintenance
1. **Keep Tests Current**: Update tests when API contracts change
2. **Remove Obsolete Tests**: Clean up tests that no longer apply
3. **Document Changes**: Update test documentation with changes
4. **Version Control**: Track test script changes in version control

### Test Quality
1. **Comprehensive Coverage**: Test all critical paths and edge cases
2. **Realistic Scenarios**: Use realistic test data and scenarios
3. **Performance Validation**: Include performance testing in test suites
4. **Error Handling**: Test both success and failure scenarios

## Conclusion

The frontend simulation testing infrastructure provides a robust, efficient way to validate the upload pipeline without the complexity of running a full frontend server. This approach:

- **Accelerates Development**: Fast feedback loops during development
- **Ensures Quality**: Comprehensive API testing coverage
- **Enables Automation**: Simple CI/CD integration
- **Maintains Focus**: Tests core functionality without UI complexity
- **Provides Flexibility**: Easy to enhance with real frontend testing later

For Phase 6 and subsequent phases, this testing infrastructure provides the foundation for reliable, automated validation of all frontend integration points while maintaining fast development cycles and comprehensive quality assurance.
