# Edge Function Testing Prompt

## Overview
This prompt will guide you through testing a new edge function in our pipeline. Follow these steps and reference the provided files for detailed implementation guidance.

## Step 1: Environment Setup
1. Copy the environment template to your function's test directory:
   ```bash
   cp @docs/development/testing/templates/edge_function.env.test your-function/.env.test
   ```
   Update variables as needed for your specific function.

2. Import test helpers:
   ```typescript
   // Reference: @docs/development/testing/templates/test_helpers.ts
   import { 
     loadTestEnvironment,
     createMockClient,
     setupTestUser,
     cleanup,
     assertSuccess,
     assertError
   } from "../helpers/test_helpers.ts";
   ```

## Step 2: Test Structure
Follow the test organization pattern from our document processor example:
```typescript
// Reference: @supabase/functions/tests/upload_handler.test.ts

// 1. Unit tests with mocked client
Deno.test("unit tests", async (t) => {
  await t.step("should handle success case", async () => {
    // Test with mock client
  });
  
  await t.step("should handle error case", async () => {
    // Test error scenarios
  });
});

// 2. Integration tests with local Supabase
Deno.test("integration tests", async (t) => {
  // Use real Supabase client
});
```

## Step 3: Test Cases Checklist
Reference: @docs/development/testing/edge_functions.md

- [ ] Success path
  - Normal operation
  - Expected data transformations
  - Proper status codes (200/201)

- [ ] Error handling
  - Invalid input (400)
  - Not found resources (404)
  - Server errors (500)
  - Permission denied (403)

- [ ] Resource management
  - Memory usage
  - File cleanup
  - Connection handling

- [ ] State management
  - Database updates
  - Storage operations
  - Cache interactions

## Step 4: Mock Client Setup
Create function-specific mock client based on our template:
```typescript
// Reference: @supabase/functions/tests/upload_handler.test.ts
const mockClient = createMockClient({
  // Add your function-specific mock data and handlers
  storageError: null,
  dbData: { /* your test data */ },
  updateHandler: (table, data, field, value) => {
    // Custom update logic
  }
});
```

## Step 5: Test Implementation

### Unit Tests
```typescript
// Example based on @supabase/functions/tests/upload_handler.test.ts
Deno.test("your function name", async (t) => {
  await t.step("should process successfully", async () => {
    const mockClient = createMockClient({
      // Configure mock for success case
    });
    
    const result = await yourFunction(params, mockClient);
    assertSuccess(result);
    // Add specific assertions
  });

  await t.step("should handle errors", async () => {
    const mockClient = createMockClient({
      // Configure mock for error case
    });
    
    const result = await yourFunction(params, mockClient);
    assertError(result, 404, "Should return not found");
  });
});
```

### Integration Tests
```typescript
// Example based on @supabase/functions/tests/upload_handler.test.ts
Deno.test("integration", async (t) => {
  const config = await loadTestEnvironment();
  const supabase = createClient(config.supabaseUrl, config.serviceKey);
  
  try {
    await setupTestUser(supabase);
    
    // Your test implementation
    
  } finally {
    await cleanup(supabase);
  }
});
```

## Step 6: Error Handling
Ensure proper error propagation:
```typescript
// Reference: @supabase/functions/upload-handler/types.ts
// Define your error types
export class YourFunctionError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: any
  ) {
    super(message);
    this.name = "YourFunctionError";
  }
}

// Handle errors consistently
try {
  // Your code
} catch (error) {
  if (error instanceof YourFunctionError) {
    throw error;
  }
  throw new YourFunctionError(
    error.message || "Unknown error",
    error.statusCode || 500,
    error
  );
}
```

## Step 7: Resource Cleanup
Implement cleanup in your tests:
```typescript
// Reference: @supabase/functions/tests/upload_handler.test.ts
Deno.test("cleanup", async () => {
  try {
    // Your cleanup logic
    await cleanup(supabase);
  } catch (error) {
    console.error("Cleanup failed:", error);
    throw error;
  }
});
```

## References
For detailed implementation guidance, refer to:
- @docs/development/testing/edge_functions.md - Testing best practices
- @docs/development/testing/templates/edge_function.env.test - Environment configuration
- @docs/development/testing/templates/test_helpers.ts - Test utilities
- @supabase/functions/tests/upload_handler.test.ts - Working example
- @supabase/functions/upload-handler/types.ts - Error types example
- @supabase/functions/upload-handler/storage.ts - Storage operations example
- @supabase/functions/upload-handler/processor.ts - Main function example

## Common Pitfalls
1. Not properly mocking all required client methods
2. Missing error cases in tests
3. Not cleaning up resources
4. Inconsistent error handling
5. Not maintaining mock client state

## Next Steps
1. Copy the environment template
2. Set up test directory structure
3. Implement mock client
4. Write unit tests
5. Write integration tests
6. Verify error handling
7. Run tests and debug
8. Document any special considerations 