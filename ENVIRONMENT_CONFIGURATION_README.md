# Environment Configuration System

## Overview

This project uses a **three-environment configuration system** that provides a streamlined approach to development, testing, and production deployment. The testing environment serves as a **bridge between development and production** by using the production database while maintaining test-specific settings.

## Environment Structure

### 1. Development Environment
- **Purpose**: Local development and testing
- **Database**: Local development database
- **Schema**: `upload_pipeline`
- **Port**: 8000
- **Debug**: `true`
- **Log Level**: `DEBUG`
- **RAG Settings**: Standard (10 chunks, 4000 tokens)

### 2. Testing Environment (Bridge)
- **Purpose**: Bridge between development and production
- **Database**: **Production database** (same as production)
- **Schema**: `upload_pipeline_test` (isolated test schema)
- **Port**: 8001 (different port to avoid conflicts)
- **Debug**: `false`
- **Log Level**: `WARNING`
- **RAG Settings**: Reduced limits (8 chunks, 3000 tokens)
- **API Keys**: Production keys (same as production)

### 3. Production Environment
- **Purpose**: Live production deployment
- **Database**: Production database
- **Schema**: `upload_pipeline`
- **Port**: 8000
- **Debug**: `false`
- **Log Level**: `ERROR`
- **RAG Settings**: Optimized (10 chunks, 4000 tokens)

## Configuration Manager Usage

### Basic Usage
```python
from config.configuration_manager import initialize_config, Environment

# Initialize for specific environment
config = initialize_config("testing")  # or "development", "production"

# Check environment
if config.is_development():
    # Development-specific logic
elif config.is_testing():
    # Testing-specific logic (bridge environment)
elif config.is_production():
    # Production-specific logic
```

### Configuration Access
```python
# Database configuration
db_url = config.get_database_url()
schema = config.database.schema

# RAG configuration
similarity_threshold = config.get_rag_similarity_threshold()
max_chunks = config.rag.max_chunks
token_budget = config.rag.token_budget

# Service configuration
port = config.service.port
debug = config.service.debug
log_level = config.service.log_level
```

## Testing Requirements

### Multi-Environment Testing
Every feature MUST be tested in all three environments:

```python
# tests/integration/test_all_environments_feature.py
import pytest
from config.configuration_manager import initialize_config

@pytest.mark.parametrize("environment", ["development", "testing", "production"])
def test_feature_across_environments(environment):
    config = initialize_config(environment)
    
    # Test that feature works in all environments
    result = test_feature(config)
    assert result is not None
    
    # Test environment-specific behavior
    if environment == "development":
        assert config.service.debug == True
    elif environment == "testing":
        assert config.database.schema == "upload_pipeline_test"
    elif environment == "production":
        assert config.service.log_level == "ERROR"
```

### Test File Structure
```
tests/
├── development/
│   ├── test_development_*.py
│   └── test_dev_*.py
├── testing/
│   ├── test_testing_*.py
│   └── test_bridge_*.py
├── production/
│   ├── test_production_*.py
│   └── test_prod_*.py
└── integration/
    ├── test_all_environments_*.py
    └── test_cross_environment_*.py
```

## Environment Files

### Development Environment
```bash
# .env.development
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

### Testing Environment (Bridge)
```bash
# .env.testing
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

### Production Environment
```bash
# .env.production
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

## Enforcement Rules

### Code Patterns (ENFORCED)
```python
# ✅ CORRECT: Use configuration manager
config = initialize_config(environment)
if config.is_development():
    # Development logic

# ❌ WRONG: Direct environment variable access
if os.getenv("NODE_ENV") == "development":
    # Development logic

# ❌ WRONG: Hardcoded values
similarity_threshold = 0.3
max_chunks = 10
```

### Testing Patterns (ENFORCED)
```python
# ✅ CORRECT: Test all environments
@pytest.mark.parametrize("environment", ["development", "testing", "production"])
def test_feature(environment):
    config = initialize_config(environment)
    # Test implementation

# ❌ WRONG: Test only one environment
def test_feature():
    config = initialize_config("development")
    # Test implementation
```

## Pre-commit Hooks

### Installation
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Hook Checks
1. **Environment Configuration Enforcement**: Checks for rule violations
2. **Python Environment Tests**: Runs environment-specific tests
3. **Configuration Manager Usage**: Checks for direct env access
4. **Environment-Specific Tests**: Validates test file structure

## Manual Enforcement

### Run Enforcement Script
```bash
# Run environment rules enforcement
./scripts/enforce-environment-rules.sh
```

### Check for Violations
```bash
# Check for direct os.getenv usage
grep -r "os\.getenv" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude="*.example" --exclude="config/configuration_manager.py" --exclude="test_*.py" .

# Check for hardcoded values
grep -r "NODE_ENV\|DEBUG.*true\|DEBUG.*false\|LOG_LEVEL.*DEBUG\|LOG_LEVEL.*WARNING\|LOG_LEVEL.*ERROR" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude="*.example" --exclude="config/configuration_manager.py" --exclude="test_*.py" .
```

## Benefits

### Testing Environment as Bridge
1. **Realistic Testing**: Tests run against production-like infrastructure
2. **Data Isolation**: Test schema prevents conflicts with production data
3. **API Consistency**: Same API keys ensure consistent behavior
4. **Performance Testing**: Can test with production database performance
5. **Deployment Confidence**: Higher confidence in production deployments

### Configuration Management
1. **Centralized Configuration**: Single source of truth for all settings
2. **Environment Isolation**: Clear separation between environments
3. **Type Safety**: Type-safe access to configuration values
4. **Validation**: Automatic configuration validation
5. **Hot Reloading**: Configuration can be reloaded without restart

## Migration Guide

### From Staging Environment
1. Remove any staging environment references
2. Update testing environment to use production database
3. Update CI/CD pipelines to use testing instead of staging
4. Update documentation to reflect new structure

### From Direct Environment Access
1. Replace `os.getenv()` calls with `config.get_config()`
2. Replace hardcoded values with configuration manager access
3. Add environment-specific tests
4. Update documentation

## Troubleshooting

### Common Issues
1. **Configuration not loading**: Check environment file exists and is valid
2. **Tests failing**: Ensure all environments are tested
3. **Environment detection wrong**: Use `config.is_*()` methods
4. **Hardcoded values**: Replace with configuration manager access

### Debug Configuration
```python
# Debug configuration values
config = initialize_config("testing")
print(f"Environment: {config.get_environment().value}")
print(f"Port: {config.service.port}")
print(f"Debug: {config.service.debug}")
print(f"Log Level: {config.service.log_level}")
print(f"Schema: {config.database.schema}")
```

## Support

For questions or issues with the environment configuration system:
1. Check the enforcement rules in `.cursor/rules/`
2. Run the enforcement script: `./scripts/enforce-environment-rules.sh`
3. Review the configuration manager: `config/configuration_manager.py`
4. Check example environment files in `config/`

## Success Metrics

- 100% of code uses configuration manager
- 0% direct environment variable access
- 100% environment-specific testing coverage
- All features tested in all three environments
- Environment-specific behavior validated
