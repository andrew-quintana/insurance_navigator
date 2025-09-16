# Environment Configuration Guide

## Overview

The Insurance Navigator system uses a **three-environment configuration system** that provides a streamlined approach to development, testing, and production deployment. The testing environment serves as a **bridge between development and production** by using the production database while maintaining test-specific settings.

## Environment Architecture

### **Environment Hierarchy** (Priority Order)
1. **Runtime Overrides** (`ENV_FILE_OVERRIDE`) - Highest priority
2. **Environment-Specific Files** (`.env.{environment}`) - Environment-specific settings
3. **Base Environment** (`.env`) - Shared settings
4. **Default Values** - Hardcoded fallbacks

### **Supported Environments**
- **`development`** - Local development and testing
- **`testing`** - Bridge environment using production database with test settings
- **`production`** - Live production deployment

## Environment-Specific Configurations

### **1. Development Environment**
**Purpose**: Local development and testing
**File**: `.env.development`
**Database**: Local development database
**Characteristics**:
- Debug mode enabled
- Verbose logging (DEBUG level)
- Local database connections
- Development API keys
- Standard RAG settings

```bash
NODE_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Local Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/insurance_navigator_dev
DATABASE_SCHEMA=upload_pipeline

# Development API Keys
OPENAI_API_KEY=sk-dev-...
SUPABASE_URL=https://dev-project.supabase.co

# Service Configuration
SERVICE_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### **2. Testing Environment**
**Purpose**: Bridge between development and production
**File**: `.env.testing`
**Database**: **Production database with test schema**
**Characteristics**:
- Production database access
- Test-specific schema (`upload_pipeline_test`)
- Production API keys
- Reduced RAG limits for faster testing
- Different port (8001) to avoid conflicts
- Warning-level logging

```bash
NODE_ENV=testing
DEBUG=false
LOG_LEVEL=WARNING

# Production Database with Test Schema
DATABASE_URL=postgresql://postgres:password@prod-db.example.com:5432/insurance_navigator_prod
TEST_DATABASE_SCHEMA=upload_pipeline_test

# Production API Keys (same as production)
OPENAI_API_KEY=sk-prod-...
SUPABASE_URL=https://prod-project.supabase.co

# Service Configuration
SERVICE_PORT=8001
CORS_ORIGINS=http://localhost:3000

# RAG Configuration - Reduced limits for faster testing
RAG_MAX_CHUNKS=8
RAG_TOKEN_BUDGET=3000
```

### **3. Production Environment**
**Purpose**: Live production deployment
**File**: `.env.production`
**Database**: Production database
**Characteristics**:
- Production database
- Optimized performance settings
- Error-level logging
- Production API keys
- Full RAG limits

```bash
NODE_ENV=production
DEBUG=false
LOG_LEVEL=ERROR

# Production Database
DATABASE_URL=postgresql://postgres:password@prod-db.example.com:5432/insurance_navigator_prod
DATABASE_SCHEMA=upload_pipeline

# Production API Keys
OPENAI_API_KEY=sk-prod-...
SUPABASE_URL=https://prod-project.supabase.co

# Service Configuration
SERVICE_PORT=8000
CORS_ORIGINS=https://insurance-navigator.com,https://www.insurance-navigator.com

# RAG Configuration - Optimized
RAG_MAX_CHUNKS=10
RAG_TOKEN_BUDGET=4000
```

## Key Differences Between Environments

| Aspect | Development | Testing | Production |
|--------|-------------|---------|------------|
| **Database** | Local dev DB | **Production DB + test schema** | Production DB |
| **Schema** | `upload_pipeline` | `upload_pipeline_test` | `upload_pipeline` |
| **API Keys** | Development keys | **Production keys** | Production keys |
| **Debug Mode** | `true` | `false` | `false` |
| **Log Level** | `DEBUG` | `WARNING` | `ERROR` |
| **Port** | 8000 | **8001** | 8000 |
| **RAG Max Chunks** | 10 | **8** | 10 |
| **RAG Token Budget** | 4000 | **3000** | 4000 |
| **CORS Origins** | `localhost:3000` | `localhost:3000` | Production domains |

## Testing Environment as Bridge

The testing environment serves as a **bridge between development and production** by:

1. **Using Production Database**: Tests run against the same database as production
2. **Test Schema Isolation**: Uses `upload_pipeline_test` schema to avoid data conflicts
3. **Production API Keys**: Uses the same API keys as production for realistic testing
4. **Reduced Limits**: Uses smaller RAG limits for faster test execution
5. **Different Port**: Runs on port 8001 to avoid conflicts with development

### Benefits of This Approach:
- **Realistic Testing**: Tests run against production-like infrastructure
- **Data Isolation**: Test schema prevents conflicts with production data
- **API Consistency**: Same API keys ensure consistent behavior
- **Performance Testing**: Can test with production database performance
- **Deployment Confidence**: Higher confidence in production deployments

## Configuration Loading Process

1. **Base Configuration**: Load `.env` file
2. **Environment-Specific**: Load `.env.{environment}` file (overrides base)
3. **Production Override**: If production or testing, also load `.env.production`
4. **Schema Override**: If testing, override schema to `upload_pipeline_test`
5. **Validation**: Validate all configuration sections
6. **Caching**: Cache configuration for performance

## Usage Examples

### Initialize Configuration
```python
from config.configuration_manager import initialize_config

# Initialize for specific environment
config = initialize_config("testing")  # Uses production DB + test schema
config = initialize_config("development")  # Uses local DB
config = initialize_config("production")  # Uses production DB

# Initialize for current environment (from NODE_ENV)
config = initialize_config()
```

### Access Configuration
```python
# Get environment-specific values
similarity_threshold = config.get_rag_similarity_threshold()
database_url = config.get_database_url()
is_testing = config.is_testing()

# Get nested values
max_chunks = config.get_config("rag.max_chunks", 10)
debug_mode = config.get_config("service.debug", False)

# Check environment
is_production = config.is_production()
is_development = config.is_development()
is_testing = config.is_testing()
```

### Environment-Specific Logic
```python
if config.is_testing():
    # Testing-specific logic
    print("Running tests against production database with test schema")
elif config.is_development():
    # Development-specific logic
    print("Running in development mode with local database")
elif config.is_production():
    # Production-specific logic
    print("Running in production mode")
```

## Database Schema Management

### Development Schema
- **Schema**: `upload_pipeline`
- **Database**: Local development database
- **Purpose**: Development and local testing

### Testing Schema
- **Schema**: `upload_pipeline_test`
- **Database**: Production database
- **Purpose**: Testing against production infrastructure

### Production Schema
- **Schema**: `upload_pipeline`
- **Database**: Production database
- **Purpose**: Live production data

## Security Considerations

1. **Environment Files**: Never commit `.env.*` files to version control
2. **API Keys**: Use different keys for development, same keys for testing and production
3. **Database Access**: Testing has production database access but uses test schema
4. **CORS**: Restrict CORS origins to appropriate domains
5. **Logging**: Avoid logging sensitive information in production

## Best Practices

1. **Environment Isolation**: Keep environments separate but testing bridges to production
2. **Configuration Validation**: Always validate configuration on startup
3. **Default Values**: Provide sensible defaults for all settings
4. **Documentation**: Document all configuration options
5. **Testing**: Test configuration loading in all environments
6. **Schema Management**: Use test schema for testing to avoid data conflicts

## Migration from Staging

If migrating from a previous staging environment:

1. **Remove Staging**: Delete `.env.staging` file
2. **Update Testing**: Configure testing to use production database
3. **Update CI/CD**: Update deployment pipelines to use testing instead of staging
4. **Update Documentation**: Update all references to staging environment

## Troubleshooting

### Common Issues

1. **Testing Environment Not Using Production DB**
   - Check that `.env.production` is loaded
   - Verify `TEST_DATABASE_SCHEMA` is set

2. **Port Conflicts**
   - Development uses port 8000
   - Testing uses port 8001
   - Production uses port 8000

3. **Schema Conflicts**
   - Testing uses `upload_pipeline_test` schema
   - Development and production use `upload_pipeline` schema

4. **API Key Issues**
   - Testing and production use the same API keys
   - Development uses different API keys
