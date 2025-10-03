# Phase C Local Backend + Production Supabase Testing Guide

## Overview

This guide explains how to run Phase C UUID standardization tests using your local backend with the production Supabase database. This configuration allows you to test the complete UUID pipeline with real production data while using local backend services for easier debugging and development.

## Configuration

### Backend: Local
- **API Base URL**: `http://localhost:8000`
- **Upload Endpoint**: `http://localhost:8000/upload`
- **Chat Endpoint**: `http://localhost:8000/chat`
- **Health Endpoint**: `http://localhost:8000/health`

### Database: Production Supabase
- **Supabase URL**: `https://znvwzkdblknkkztqyfnu.supabase.co`
- **Database URL**: `postgresql://postgres:<REDACTED>@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres`
- **Pooler URL**: `${DATABASE_URL}//localhost:8000/health
```

### 2. Required Python Packages
Install the required dependencies:

```bash
pip install aiohttp asyncpg
```

### 3. Production Supabase Access
The test script automatically configures the production Supabase connection using the credentials from your `.env.production` file.

## Running Tests

### Quick Start
```bash
# Run all Phase C tests with local backend + production Supabase
python run_phase_c_local_prod_tests.py
```

### Verbose Output
```bash
# Run with detailed output for debugging
python run_phase_c_local_prod_tests.py --verbose
```

### Help and Examples
```bash
# Show usage examples and troubleshooting
python run_phase_c_local_prod_tests.py --help-examples
```

## Test Coverage

The local backend + production Supabase tests cover:

### 1. Local Backend Health Check
- Verifies local backend is running and responding
- Tests health endpoint functionality
- Validates API availability

### 2. Production Supabase Connection
- Tests direct database connection to production Supabase
- Validates UUID generation functions in production database
- Checks upload_pipeline schema accessibility

### 3. UUID Generation with Production Database
- Tests deterministic UUID generation using production database
- Validates UUID storage and retrieval
- Tests chunk UUID generation
- Verifies database operations work correctly

### 4. End-to-End Upload Pipeline
- Tests complete upload workflow with local backend
- Validates document storage in production database
- Tests UUID consistency across upload process
- Simulates real upload scenarios

### 5. RAG Retrieval with Production Data
- Tests chat endpoint with local backend
- Validates RAG functionality with production data
- Tests query processing and response generation
- Verifies UUID references in responses

### 6. Multi-User UUID Isolation
- Tests user isolation with deterministic UUIDs
- Validates different users get different UUIDs for same content
- Tests database storage for multiple users
- Verifies UUID consistency per user

### 7. Performance with Production Database
- Tests UUID generation performance
- Validates database operation performance
- Tests query performance with production data
- Measures response times and throughput

### 8. Error Handling and Recovery
- Tests invalid UUID handling
- Validates database error handling
- Tests recovery from connection issues
- Verifies error handling robustness

## Expected Output

### Successful Test Run
```
🚀 Starting Phase C Tests - Local Backend + Production Supabase
================================================================================
Configuration:
  Backend: local (http://localhost:8000)
  Database: production_supabase (https://znvwzkdblknkkztqyfnu.supabase.co)
  Environment: hybrid_testing
================================================================================

🔍 Checking prerequisites...
✅ Prerequisites check passed

🏥 Testing local backend health...
✅ Local backend health: PASSED

🗄️ Testing production Supabase connection...
✅ Production Supabase connection: PASSED

🔧 Testing UUID generation with production database...
✅ UUID generation with production database: PASSED

📤 Testing end-to-end upload pipeline...
✅ End-to-end upload pipeline: PASSED

🔍 Testing RAG retrieval with production data...
✅ RAG retrieval with production data: PASSED

👥 Testing multi-user UUID isolation...
✅ Multi-user UUID isolation: PASSED

⚡ Testing performance with production database...
✅ Performance with production database: PASSED

🛡️ Testing error handling and recovery...
✅ Error handling and recovery: PASSED

================================================================================
📋 PHASE C: LOCAL BACKEND + PRODUCTION SUPABASE TEST REPORT
================================================================================
Configuration: Local Backend + Production Supabase
Total Tests: 8
Passed: 8
Failed: 0
Critical Failures: 0
Success Rate: 100.0%

✅ ALL TESTS PASSED
UUID standardization is working correctly with local backend and production Supabase.
Ready for Phase 3 cloud deployment.

📄 Detailed results saved to: phase_c_local_backend_production_supabase_1234567890.json
```

### Failed Test Run
```
❌ Local backend health: FAILED (Status: 500)
❌ Production Supabase connection: ERROR - Connection refused

================================================================================
📋 PHASE C: LOCAL BACKEND + PRODUCTION SUPABASE TEST REPORT
================================================================================
Configuration: Local Backend + Production Supabase
Total Tests: 8
Passed: 6
Failed: 2
Critical Failures: 2
Success Rate: 75.0%

🚨 CRITICAL FAILURES DETECTED: 2
UUID standardization may not be ready for production deployment.
Please resolve critical issues before proceeding.
```

## Troubleshooting

### Common Issues

#### 1. Local Backend Not Running
**Error**: `❌ Local backend health: FAILED (Status: 500)`

**Solution**:
```bash
# Start the local backend
python main.py

# Check if it's running
curl -f http://localhost:8000/health
```

#### 2. Database Connection Issues
**Error**: `❌ Production Supabase connection: ERROR - Connection refused`

**Solution**:
- Check internet connectivity
- Verify Supabase credentials in `.env.production`
- Test database connection manually:
```bash
python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://postgres:<REDACTED>@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres'))"
```

#### 3. Missing Dependencies
**Error**: `❌ Missing required dependencies: No module named 'aiohttp'`

**Solution**:
```bash
pip install aiohttp asyncpg
```

#### 4. Environment Variable Issues
**Error**: `❌ Missing required environment variables: SUPABASE_URL`

**Solution**:
The test script automatically sets environment variables, but you can verify:
```bash
python -c "import os; print('SUPABASE_URL:', os.getenv('SUPABASE_URL'))"
```

### Debug Mode

Run tests with verbose output to see detailed information:
```bash
python run_phase_c_local_prod_tests.py --verbose
```

This will show:
- Environment configuration details
- Detailed test execution steps
- Error stack traces
- Performance metrics

## Test Results

### Output Files

Each test run generates:
- **Detailed Results**: `phase_c_local_backend_production_supabase_{timestamp}.json`
- **Console Output**: Real-time test progress and results

### Exit Codes

- **0**: All tests passed - Ready for Phase 3
- **1**: Critical failures detected - Issues must be resolved
- **2**: Non-critical failures detected - Issues should be addressed

## Integration with Phase 3

### Success Criteria

The local backend + production Supabase tests validate:
- ✅ **UUID Generation**: Deterministic UUID generation working correctly
- ✅ **Database Operations**: Production database operations successful
- ✅ **End-to-End Pipeline**: Complete upload and retrieval pipeline working
- ✅ **User Isolation**: Multi-user UUID isolation working correctly
- ✅ **Performance**: Performance meets requirements
- ✅ **Error Handling**: Error handling and recovery working correctly

### Phase 3 Readiness

If all tests pass:
- UUID standardization is working correctly with production data
- Local backend can successfully interact with production Supabase
- Phase 3 cloud deployment can proceed with confidence
- All UUID-dependent functionality is validated

## Best Practices

### 1. Test Execution
- Run tests after making changes to UUID generation code
- Always verify local backend is running before testing
- Check production Supabase connectivity before testing
- Review test results carefully before proceeding

### 2. Development Workflow
- Use local backend for development and debugging
- Test with production Supabase to validate real-world scenarios
- Monitor test results for any regressions
- Document any issues or unexpected behavior

### 3. Production Deployment
- Ensure all tests pass before deploying to production
- Monitor UUID generation in production environment
- Have rollback procedures ready if issues arise
- Train support team on UUID troubleshooting

## Support

### Getting Help
- Check the troubleshooting section above
- Run tests with `--verbose` for detailed error information
- Review the generated JSON results file for specific error details
- Ensure all prerequisites are met before running tests

### Reporting Issues
- Document the exact error messages
- Include the test configuration used
- Provide the generated results file
- Describe the steps to reproduce the issue

## Conclusion

The local backend + production Supabase testing configuration provides a powerful way to validate UUID standardization with real production data while maintaining the flexibility of local development. This approach ensures that your UUID implementation works correctly in production scenarios before deploying to the cloud.

Follow this guide to run comprehensive tests and validate that your UUID standardization is ready for Phase 3 cloud deployment.
