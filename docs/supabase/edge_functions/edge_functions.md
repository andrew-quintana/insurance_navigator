# Edge Function Testing Guide

## Overview

This guide outlines best practices for testing edge functions in the Insurance Navigator project, with a focus on proper environment handling, test organization, and comprehensive test coverage.

## Environment Setup

### Environment Hierarchy

The testing framework follows a strict environment variable hierarchy:

1. **Runtime Overrides** (`ENV_FILE_OVERRIDE`)
   - Highest priority
   - Used for specific test scenarios
   - Example: `ENV_FILE_OVERRIDE=tests/fixtures/special_test.env`

2. **Test Environment** (`.env.test`)
   - Test-specific configuration
   - Contains test credentials and endpoints
   - Example: `SUPABASE_URL=http://127.0.0.1:54321`

3. **Base Environment** (`.env`)
   - Shared configuration across environments
   - Fallback values
   - Example: `LOG_LEVEL=DEBUG`

### Required Variables

Every test environment must include:
```env
SUPABASE_URL=<url>
SUPABASE_SERVICE_ROLE_KEY=<key>
OPENAI_API_KEY=<key>
NODE_ENV=test
```

### Optional Variables

Enhance testing capabilities with:
```env
LLAMAPARSE_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
DEBUG=true
```

### Feature Flags

Control test behavior with:
```env
ENABLE_VECTOR_PROCESSING=true
ENABLE_REGULATORY_PROCESSING=true
```

## Test Organization

### Directory Structure

```
tests/
├── edge-functions/
│   ├── templates/
│   │   ├── edge_function.env.test    # Environment template
│   │   ├── test_helpers.ts           # Shared utilities
│   │   └── sample_edge_function.test.ts  # Example test
│   ├── your_function/
│   │   ├── .env.test                 # Function-specific env
│   │   └── your_function.test.ts     # Function tests
│   └── README.md                     # Testing documentation
```

### Test Categories

1. **Unit Tests**
   - Mock Supabase client
   - Test business logic
   - Fast and isolated

2. **Integration Tests**
   - Real Supabase instance
   - End-to-end workflows
   - Can be skipped in mock mode

3. **Security Tests**
   - Authorization checks
   - Data sanitization
   - Security boundaries

4. **Resource Management**
   - Cleanup verification
   - Concurrent processing
   - Resource limits

## Writing Tests

### Test Setup

```typescript
// 1. Load environment
const config = await loadTestEnvironment();

// 2. Initialize clients
const supabase = createClient(config.supabaseUrl, config.supabaseKey);

// 3. Set up test data
await setupTestUser(supabase);
```

### Test Helpers

```typescript
// Assert successful operation
assertSuccess(result);

// Assert error with status
assertError(result, 404, "Should return not found");

// Wait for async condition
await waitForCondition(async () => {
  const { data } = await checkStatus();
  return data.status === "completed";
});
```

### Mock Client Usage

```typescript
const mockClient = createMockClient({
  dbData: { /* mock data */ },
  dbError: { /* mock error */ },
  storageError: { /* storage error */ }
});
```

## Best Practices

### Environment Handling

1. **Use Environment Template**
   - Copy `edge_function.env.test` to your function's directory
   - Customize for specific needs
   - Document any additions

2. **Environment Validation**
   - Validate required variables
   - Type-check configurations
   - Fail fast on missing values

3. **Feature Flags**
   - Use flags to control test behavior
   - Skip tests based on configuration
   - Document flag dependencies

### Test Implementation

1. **Isolation**
   - Clean up after each test
   - Use unique test data
   - Avoid test interdependencies

2. **Comprehensive Coverage**
   - Test success paths
   - Test error conditions
   - Test edge cases
   - Test security boundaries

3. **Resource Management**
   - Clean up temporary files
   - Release database connections
   - Handle concurrent operations

### Security Considerations

1. **Authentication**
   - Test unauthorized access
   - Verify role-based access
   - Check token validation

2. **Data Protection**
   - Test data sanitization
   - Verify sensitive data handling
   - Check audit logging

3. **Resource Limits**
   - Test rate limiting
   - Verify quota enforcement
   - Check timeout handling

## Common Pitfalls

1. **Environment Issues**
   - Missing required variables
   - Incorrect endpoint URLs
   - Invalid credentials

2. **Resource Leaks**
   - Unclosed connections
   - Temporary files
   - Database records

3. **Race Conditions**
   - Concurrent operations
   - Async timing issues
   - State dependencies

## Testing Checklist

- [ ] Environment properly configured
- [ ] Required variables validated
- [ ] Unit tests implemented
- [ ] Integration tests implemented
- [ ] Security tests implemented
- [ ] Resource cleanup verified
- [ ] Error cases covered
- [ ] Documentation updated
- [ ] Test data isolated
- [ ] Performance acceptable

## References

- [Environment Handling Guide](../environment_handling.md)
- [Security Guidelines](../../security/env_management_rules.md)
- [Deployment Guide](../../deployment/deploy-guide.md) 