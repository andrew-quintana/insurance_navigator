# Frontend Simulation Testing

This directory contains testing scripts that simulate frontend behavior for testing the upload pipeline without requiring a full frontend server.

## Testing Philosophy

### Why Frontend Simulation?

Instead of running a full Next.js frontend server for testing, we use **frontend simulation** which:

- **Fast & Reliable**: No frontend dependencies or build processes
- **Focused Testing**: Tests the core API functionality directly
- **Easy Automation**: Simple to run in CI/CD pipelines
- **Resource Efficient**: Minimal resource usage for testing
- **Comprehensive Coverage**: Tests all frontend integration points

### What We Simulate

1. **Upload Requests**: Frontend file upload API calls
2. **Job Status Polling**: Real-time progress updates
3. **Job Management**: Listing, retry, and error handling
4. **User Authentication**: JWT token handling
5. **Error Scenarios**: Validation errors and edge cases
6. **Rate Limiting**: Abuse prevention testing
7. **Concurrent Processing**: User job limits

## Testing Scripts

### 1. Bash Script: `test-frontend-simulation.sh`

**Features:**
- Simple shell script with colored output
- No Python dependencies required
- Fast execution for quick testing
- Good for CI/CD and automation

**Usage:**
```bash
# Make executable
chmod +x scripts/testing/test-frontend-simulation.sh

# Run with default settings
./scripts/testing/test-frontend-simulation.sh

# Run from project root
scripts/testing/test-frontend-simulation.sh
```

**Requirements:**
- `curl` command available
- Bash shell
- Local services running (API, Worker, Database)

### 2. Python Script: `test-frontend-simulation.py`

**Features:**
- Async HTTP requests for better performance
- Structured logging and error handling
- Configurable API endpoints
- Better error reporting and debugging
- Exit codes for CI/CD integration

**Usage:**
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

**Requirements:**
- Python 3.7+
- `aiohttp` package
- Local services running

## Test Coverage

### Service Health Tests
- ✅ API Server health check
- ✅ BaseWorker health check  
- ✅ Database connectivity validation

### Upload Workflow Tests
- ✅ File upload request simulation
- ✅ Job creation and ID generation
- ✅ Document metadata validation
- ✅ SHA256 deduplication testing

### Job Management Tests
- ✅ Job status polling simulation
- ✅ Progress tracking and updates
- ✅ Job listing and filtering
- ✅ Error state handling

### Validation Tests
- ✅ File size limits (25MB max)
- ✅ MIME type validation (PDF only)
- ✅ Filename sanitization
- ✅ Concurrent job limits (2 per user)

### Performance Tests
- ✅ Rate limiting enforcement
- ✅ Concurrent processing limits
- ✅ Error handling performance
- ✅ Response time validation

## Testing Scenarios

### Happy Path Testing
1. **Upload Document**: Create new document with valid metadata
2. **Job Processing**: Monitor job through all stages
3. **Completion**: Verify job reaches "done" state
4. **Data Integrity**: Validate document and chunk creation

### Error Path Testing
1. **Invalid Inputs**: Test validation error handling
2. **Rate Limiting**: Verify abuse prevention
3. **Concurrent Limits**: Test user job limits
4. **Service Failures**: Test error recovery

### Edge Case Testing
1. **Large Files**: Test file size boundaries
2. **Duplicate Uploads**: Test deduplication logic
3. **Rapid Requests**: Test rate limiting
4. **Service Restarts**: Test recovery mechanisms

## Integration with CI/CD

### Exit Codes
- **0**: All tests passed
- **1**: One or more tests failed

### Environment Variables
```bash
# Customize test configuration
export API_BASE_URL="http://localhost:8000"
export WORKER_BASE_URL="http://localhost:8002"
export TEST_USER_ID="ci-test-user"
```

### CI/CD Example
```yaml
# GitHub Actions example
- name: Run Frontend Simulation Tests
  run: |
    chmod +x scripts/testing/test-frontend-simulation.sh
    ./scripts/testing/test-frontend-simulation.sh
  
- name: Run Python Frontend Tests
  run: |
    pip install aiohttp
    python scripts/testing/test-frontend-simulation.py
```

## When to Use Each Approach

### Use Bash Script For:
- **Quick Testing**: Fast validation during development
- **CI/CD Pipelines**: Simple automation without Python setup
- **Debugging**: Quick service health checks
- **Basic Validation**: Core functionality testing

### Use Python Script For:
- **Comprehensive Testing**: Full test suite execution
- **Debugging**: Detailed error reporting and logging
- **Custom Scenarios**: Configurable testing parameters
- **Performance Testing**: Async request handling

## Future Enhancements

### Phase 7: Real Frontend Testing
When we move to Phase 7 (production deployment), we can add:

1. **Local Frontend Server**: Run actual Next.js app for integration testing
2. **Browser Automation**: Selenium/Playwright for end-to-end testing
3. **Visual Testing**: Screenshot comparison and UI validation
4. **User Experience Testing**: Real user workflow validation

### Current Benefits
- **Fast Development**: No frontend build delays
- **Reliable Testing**: Consistent test results
- **Easy Debugging**: Direct API interaction
- **Comprehensive Coverage**: All integration points tested

## Troubleshooting

### Common Issues

1. **Services Not Running**
   ```bash
   # Check if services are healthy
   curl -f http://localhost:8000/health
   curl -f http://localhost:8002/health
   ```

2. **Database Connection Issues**
   ```bash
   # Verify PostgreSQL is running
   docker-compose ps postgres
   ```

3. **Port Conflicts**
   ```bash
   # Check port usage
   lsof -i :8000
   lsof -i :8002
   ```

4. **Authentication Issues**
   - Verify JWT token format
   - Check service role keys
   - Validate RLS policies

### Debug Mode
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
python scripts/testing/test-frontend-simulation.py
```

## Conclusion

Frontend simulation testing provides a robust, efficient way to validate the upload pipeline without the complexity of running a full frontend server. This approach:

- **Accelerates Development**: Fast feedback loops
- **Improves Reliability**: Consistent test results
- **Enables Automation**: Easy CI/CD integration
- **Maintains Quality**: Comprehensive test coverage

For Phase 6 local testing, this approach is ideal. As we move to Phase 7 production deployment, we can enhance with real frontend testing while maintaining these simulation tests for rapid development and debugging.
