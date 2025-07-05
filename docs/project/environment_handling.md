# Environment Handling Guide

## Overview

The Insurance Navigator project implements a robust environment handling system that provides flexibility, security, and reliability across different deployment contexts. This document outlines the core concepts, implementation details, and best practices for working with environment configurations.

## Environment System Architecture

### 1. Environment Hierarchy

The system follows a strict hierarchy for resolving environment variables:

1. **Runtime Overrides** (`ENV_FILE_OVERRIDE`)
   - Highest priority
   - Used primarily for testing and local development
   - Can completely override other sources

2. **Environment-Specific Files**
   - `.env.development` for development
   - `.env.test` for testing
   - `.env.staging` for staging (can't use yet - needs supabase pro)
   - `.env.production` for production

3. **Base Environment**
   - `.env` file for shared configurations
   - Contains common settings across environments

4. **Default Values**
   - Hardcoded defaults for non-critical settings
   - Lowest priority in the resolution chain

### 2. Variable Categories

#### Required Variables
These must be present in all environments:
```
SUPABASE_URL=<url>
SUPABASE_SERVICE_ROLE_KEY=<key>
OPENAI_API_KEY=<key>
NODE_ENV=<environment>
```

#### Optional Variables
These enhance functionality but aren't required:
```
LLAMAPARSE_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
DEBUG=<true/false>
```

#### Boolean Variables
These are parsed from strings with specific rules:
```
ENABLE_VECTOR_PROCESSING=<true/false>
ENABLE_REGULATORY_PROCESSING=<true/false>
```

## Implementation Details

### 1. Environment Loading Process

```typescript
// Pseudo-code of the loading process
function loadEnvironment() {
  // 1. Check for override
  if (process.env.ENV_FILE_OVERRIDE) {
    loadEnvFile(process.env.ENV_FILE_OVERRIDE)
    return
  }

  // 2. Load environment-specific file
  const envFile = `.env.${process.env.NODE_ENV}`
  if (fileExists(envFile)) {
    loadEnvFile(envFile)
  }

  // 3. Load base environment
  loadEnvFile('.env')

  // 4. Apply defaults
  applyDefaultValues()
}
```

### 2. Type Safety

The system enforces type safety through TypeScript interfaces:

```typescript
interface EnvironmentConfig {
  // Required variables
  SUPABASE_URL: string;
  SUPABASE_SERVICE_ROLE_KEY: string;
  OPENAI_API_KEY: string;
  
  // Optional variables
  LLAMAPARSE_API_KEY?: string;
  ANTHROPIC_API_KEY?: string;
  
  // Boolean variables
  ENABLE_VECTOR_PROCESSING: boolean;
  ENABLE_REGULATORY_PROCESSING: boolean;
}
```

## Best Practices

### 1. Environment File Management

✅ **Do**:
- Keep sensitive values in environment-specific files
- Use descriptive variable names
- Document all environment variables
- Use consistent naming conventions
- Include validation for critical values

❌ **Don't**:
- Commit sensitive values to version control
- Use ambiguous variable names
- Mix environment-specific and shared variables
- Hardcode environment-specific values

### 2. Security Considerations

1. **Sensitive Data Handling**
   - Store API keys only in environment files
   - Use different keys for different environments
   - Rotate keys regularly
   - Monitor environment variable access

2. **Access Control**
   - Restrict environment file access
   - Use separate keys for different service levels
   - Implement role-based access control
   - Log environment variable changes

### 3. Development Workflow

1. **Local Development**
   ```bash
   # Create local environment file
   cp .env.example .env.development
   # Edit with local values
   nano .env.development
   ```

2. **Testing**
   ```bash
   # Use override for specific tests
   ENV_FILE_OVERRIDE=tests/fixtures/env.test npm test
   ```

3. **Deployment**
   ```bash
   # Verify environment before deploy
   npm run verify-env
   # Deploy with correct environment
   NODE_ENV=production npm run deploy
   ```

### 4. Debugging and Troubleshooting

1. **Enable Debug Mode**
   ```bash
   DEBUG=true npm start
   ```

2. **Environment Validation**
   ```bash
   npm run validate-env
   ```

3. **Common Issues**
   - Missing required variables
   - Type mismatches
   - Invalid boolean values
   - Environment file loading failures

## Maintenance and Updates

### 1. Adding New Variables

1. Update TypeScript interfaces
2. Add to validation logic
3. Update documentation
4. Add to example environment files
5. Update tests

### 2. Removing Variables

1. Check for all usages
2. Update TypeScript interfaces
3. Remove from validation
4. Update documentation
5. Clean up tests

### 3. Changing Variable Types

1. Update TypeScript interfaces
2. Update validation logic
3. Update all usage locations
4. Update tests
5. Document migration process

## Monitoring and Logging

### 1. Environment Events

Log important environment events:
- Environment file loading
- Variable access attempts
- Configuration changes
- Validation failures

### 2. Metrics

Track environment-related metrics:
- Missing variable frequency
- Invalid value attempts
- Environment load times
- Variable access patterns

## References

- [Environment Testing Guide](../tests/docs/environment_testing.md)
- [Security Guidelines](../security/env_management_rules.md)
- [Deployment Guide](../deployment/deploy-guide.md) 