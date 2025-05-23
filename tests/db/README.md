# Database Tests

This directory contains tests for the database infrastructure, including Supabase integration and storage service functionality.

## Structure

```
tests/db/
├── unit/                     # Unit tests
│   ├── test_supabase_config.py  # Configuration validation tests
│   └── test_storage_service.py  # Storage service unit tests
├── integration/             # Integration tests
│   ├── test_supabase_connection.py  # Supabase connection tests
│   └── test_storage_service.py      # Storage service integration tests
└── conftest.py             # Shared test fixtures
```

## Test Categories

### Unit Tests
- **Configuration Tests**: Validate Supabase configuration handling and environment variable loading
- **Storage Service Tests**: Test storage service functionality with mocked dependencies

### Integration Tests
- **Connection Tests**: Test actual Supabase connection handling and error scenarios
- **Storage Service Tests**: Test real storage operations with Supabase

## Setup

1. Environment Variables
```bash
# Required for all tests
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key
SUPABASE_STORAGE_BUCKET=your_bucket_name

# Optional
SUPABASE_SIGNED_URL_EXPIRY=3600  # Default: 1 hour
```

2. Install Dependencies
```bash
pip install -r requirements.txt
```

## Running Tests

### Run All Tests
```bash
pytest tests/db
```

### Run Only Unit Tests
```bash
pytest tests/db/unit
```

### Run Only Integration Tests
```bash
pytest tests/db/integration -m integration
```

### Run Specific Test File
```bash
pytest tests/db/unit/test_storage_service.py
```

## Test Markers

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.asyncio`: Asynchronous tests

## Best Practices

1. **Test Independence**
   - Each test should be independent and not rely on state from other tests
   - Use fixtures for setup and teardown
   - Clean up any created resources after tests

2. **Mocking**
   - Use mocks for external dependencies in unit tests
   - Use real Supabase client in integration tests
   - Keep mock complexity to a minimum

3. **Error Handling**
   - Test both success and error scenarios
   - Verify error messages and types
   - Test rate limiting and timeout scenarios

4. **Resource Management**
   - Use fixtures for resource cleanup
   - Handle concurrent operations carefully
   - Be mindful of rate limits in integration tests

## Common Issues

1. **Rate Limiting**
   - Integration tests may hit rate limits
   - Use `asyncio.sleep()` between operations
   - Consider using test markers to skip rate-limited tests

2. **Connection Issues**
   - Ensure Supabase credentials are correct
   - Check network connectivity
   - Verify bucket permissions

3. **Test Failures**
   - Check environment variables
   - Verify Supabase service status
   - Look for rate limiting errors

## Contributing

When adding new tests:
1. Follow the existing directory structure
2. Add appropriate test markers
3. Update this README if adding new test categories
4. Ensure all tests are properly documented
5. Add necessary fixtures to conftest.py if shared 