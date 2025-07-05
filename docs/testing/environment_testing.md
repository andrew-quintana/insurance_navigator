# Environment Testing Guide

## Overview

The Insurance Navigator project includes a flexible environment configuration system that supports different deployment contexts (development, test, staging, production) while maintaining strong testability. This document outlines how to use and test environment configurations.

## Core Features

### Environment Override System

The system allows overriding environment configurations using the `ENV_FILE_OVERRIDE` variable:

```bash
ENV_FILE_OVERRIDE=tests/fixtures/env.bogey deno test
```

This feature is particularly useful for:
- Testing environment loading functionality
- Isolating tests that need specific environment configurations
- Verifying behavior with different environment setups

### Environment Hierarchy

1. **Override File** (if `ENV_FILE_OVERRIDE` is set)
2. **Environment-Specific File** (`.env.[environment]`)
3. **Default Values** (for non-required fields)

## Testing Best Practices

### 1. Using Environment Overrides

```typescript
// Example test with environment override
Deno.test({
  name: "test with custom environment",
  async fn() {
    // Set up temporary environment file
    const envPath = "tests/fixtures/env.custom";
    await Deno.writeTextFile(envPath, `
      NODE_ENV=test
      CUSTOM_VAR=test_value
    `);

    try {
      Deno.env.set("ENV_FILE_OVERRIDE", envPath);
      // Run your test
    } finally {
      await Deno.remove(envPath);
    }
  }
});
```

### 2. Creating Bogey Environments

For testing environment loading functionality:

```typescript
// tests/fixtures/env.bogey
NODE_ENV=test
ENV_LEVEL=test
SUPABASE_URL=https://bogey.supabase.co
SUPABASE_SERVICE_ROLE_KEY=bogey-key-123
// ... other test values
```

### 3. Environment Reset

Always reset the environment between tests:

```typescript
function resetEnvironment() {
  Object.keys(originalEnv).forEach(key => {
    try {
      Deno.env.delete(key);
    } catch (error) {
      console.warn(`Failed to delete ${key}:`, error);
    }
  });
}
```

## Environment Variable Types

### Required Variables
These must be present in all environments:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`

### Optional Variables
These can be undefined:
- `LLAMAPARSE_API_KEY`
- `ANTHROPIC_API_KEY`

### Boolean Variables
These are parsed from strings:
- `ENABLE_VECTOR_PROCESSING`
- `ENABLE_REGULATORY_PROCESSING`

Values of `"false"` or `"0"` are interpreted as `false`, all other non-empty values as `true`.

## Running Tests

### Basic Test Run
```bash
deno test
```

### With Environment Override
```bash
ENV_FILE_OVERRIDE=path/to/env/file deno test
```

### Testing Specific Environment Functionality
```bash
ENV_FILE_OVERRIDE=tests/fixtures/env.bogey deno test tests/unit/environment-override.test.ts
```

## Debugging

The system includes detailed logging:
- Environment file loading
- Variable setting
- Override detection
- Error conditions

Enable debug output in tests:
```typescript
console.log('Loading environment from:', envPath);
console.log('Set env var:', key, value);
```

## Security Considerations

1. Never commit real credentials in test environment files
2. Use bogey/dummy values for sensitive information in tests
3. Clean up temporary environment files after tests
4. Preserve critical system variables during environment resets

## Common Issues and Solutions

1. **Test Interference**
   - Use `resetEnvironment()` between tests
   - Isolate tests with custom environment files

2. **Boolean Parsing**
   - Use explicit `"false"` or `"0"` for false values
   - Any other non-empty value is true

3. **Missing Variables**
   - Required variables throw clear error messages
   - Optional variables return undefined

## Best Practices

1. **Isolation**: Use separate environment files for different test scenarios
2. **Cleanup**: Always clean up temporary files in `finally` blocks
3. **Verification**: Log environment loading for debugging
4. **Documentation**: Comment non-obvious environment requirements
5. **Security**: Use dummy values in test environments 