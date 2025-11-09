# MVP Async Fix - Concurrent Request Testing

This directory contains comprehensive testing scripts for validating the MVP async conversion of the RAG system.

## Overview

The MVP async fix converts the RAG system's `_generate_embedding()` method from threading to async/await using `httpx.AsyncClient`. This testing suite validates that the conversion successfully prevents hanging issues with concurrent requests.

## Test Scripts

### 1. `tests/validate_mvp_async.py` - Basic Validation
**Purpose**: Quick validation before running full concurrent tests
**Usage**: `python tests/validate_mvp_async.py`

**Tests**:
- Environment variable setup
- RAG tool creation
- Single request functionality
- Basic async operation

### 2. `tests/test_concurrent_rag_mvp.py` - Full Concurrent Testing
**Purpose**: Comprehensive concurrent request testing
**Usage**: `python tests/test_concurrent_rag_mvp.py`

**Test Scenarios**:
- **Test 1**: Basic Concurrent Test (3 requests)
- **Test 2**: Hanging Scenario Test (7 requests) 
- **Test 3**: Stress Test (10 requests)

## MVP Success Criteria

The tests validate against these MVP success criteria:

### Performance Requirements
- ✅ **No hanging**: No requests taking > 60 seconds
- ✅ **Response times**: All requests complete < 10 seconds
- ✅ **System stability**: Success rate >= 90%

### Reliability Requirements
- ✅ **No deadlocks**: System remains responsive under load
- ✅ **Error handling**: Proper error handling and recovery
- ✅ **Resource efficiency**: No resource exhaustion

## Test Execution

### Step 1: Basic Validation
```bash
python tests/validate_mvp_async.py
```

**Expected Output**:
```
🔍 MVP Async Fix - Basic Validation
==================================================
📋 Checking environment setup...
  ✅ OPENAI_API_KEY: Set
  ✅ DATABASE_URL: Set
  ✅ SUPABASE_URL: Set
  ✅ SUPABASE_SERVICE_ROLE_KEY: Set
  ✅ All required environment variables are set

🔧 Testing RAG tool creation...
  ✅ RAG tool created successfully

🧪 Testing single request...
  📝 Query: What does my insurance cover?
  ⏱️  Duration: 2.34s
  📊 Chunks returned: 3
  ✅ First chunk preview: Your insurance plan covers preventive care services...
  ✅ Single request test passed

🔄 Testing async operation...
  ✅ Async operations completed: 3 tasks

🎉 Basic validation PASSED!
   Ready to run full concurrent test suite.

🚀 Proceeding to run full concurrent test suite...
   Execute: python tests/test_concurrent_rag_mvp.py
```

### Step 2: Concurrent Testing
```bash
python tests/test_concurrent_rag_mvp.py
```

**Expected Output**:
```
🧪 MVP Async Fix - Concurrent Request Testing
============================================================
🎯 Testing MVP async conversion with concurrent requests
⏱️  Timeout threshold: 10.0s
🚫 Hanging threshold: 60.0s
👤 Test user: f0cfcc46-5fdb-48c4-af13-51c6cf53e408
============================================================

🔬 Test 1: Basic Concurrent Test (3 requests)
============================================================
📊 TEST RESULTS: Basic Concurrent Test
============================================================
🕐 Timestamp: 2025-01-10T17:30:45.123456
🔢 Concurrent Requests: 3
⏱️  Total Duration: 3.45s
✅ Success Rate: 100.0%
📈 Response Times:
   • Average: 2.12s
   • Median:  2.15s
   • Min:     1.98s
   • Max:     2.23s
❌ Failures:
   • Timeouts: 0
   • Errors:   0
   • Hanging:  0

🎯 MVP SUCCESS CRITERIA CHECK:
   • No hanging (5+ requests): ✅ PASS
   • Response times < 10s: ✅ PASS
   • System stability: ✅ PASS

🏆 OVERALL MVP STATUS: ✅ PASS
```

## Test Results

### Output Files
- `concurrent_test_results_YYYYMMDD_HHMMSS.json` - Individual test results
- `test-results/mvp_concurrent_test_summary_YYYYMMDD_HHMMSS.json` - Complete test suite summary

### Result Interpretation

#### ✅ PASS Criteria
- **No hanging**: `hanging_count = 0`
- **Response times**: `max_response_time < 10.0s`
- **System stability**: `success_rate >= 90.0%`

#### ❌ FAIL Criteria
- **Hanging detected**: Any request taking > 60 seconds
- **Timeout issues**: Requests timing out at 10 seconds
- **Low success rate**: Success rate < 90%

## Troubleshooting

### Common Issues

#### 1. Environment Variables Missing
```
❌ Missing environment variables: ['OPENAI_API_KEY', 'DATABASE_URL']
```
**Solution**: Ensure `.env.development` file exists with required variables

#### 2. Database Connection Issues
```
❌ Failed to create RAG tool: connection refused
```
**Solution**: Verify database is running and accessible

#### 3. API Key Issues
```
❌ Single request test failed: OpenAI API error: 401 - Unauthorized
```
**Solution**: Verify `OPENAI_API_KEY` is valid and has sufficient credits

#### 4. Timeout Issues
```
⚠️ Warning: Request took 12.34s (exceeds 10s threshold)
```
**Solution**: Check network connectivity and API response times

### Debug Mode
For detailed debugging, set logging level:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Expectations

### Before MVP Fix (Threading)
- ❌ Hanging with 5+ concurrent requests
- ❌ Requests taking 60+ seconds
- ❌ System instability under load

### After MVP Fix (Async)
- ✅ No hanging with 10+ concurrent requests
- ✅ All requests complete < 10 seconds
- ✅ Stable system performance under load

## Integration with CI/CD

### Exit Codes
- `0`: All tests passed MVP criteria
- `1`: One or more tests failed MVP criteria

### Usage in CI/CD
```bash
# Run validation
python tests/validate_mvp_async.py && python tests/test_concurrent_rag_mvp.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "MVP async fix validation PASSED"
else
    echo "MVP async fix validation FAILED"
    exit 1
fi
```

## Reference Documents

- [Threading Update Initiative README](../docs/initiatives/agents/threading_update/README.md)
- [MVP Implementation Plan](../docs/initiatives/agents/threading_update/phased-todo.md)
- [MVP Prompts](../docs/initiatives/agents/threading_update/prompts.md)

## Next Steps

After successful testing:
1. **Deploy to production** (Step 3 of MVP plan)
2. **Monitor for 24 hours** for hanging issues
3. **Validate fix effectiveness** in production environment
4. **Document performance improvements**

---

**Note**: This testing suite is designed for the MVP async fix validation. For comprehensive performance testing beyond MVP scope, refer to the full performance testing documentation.
