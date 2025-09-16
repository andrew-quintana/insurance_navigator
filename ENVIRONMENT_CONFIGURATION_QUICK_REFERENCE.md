# Environment Configuration System - Quick Reference

## Overview

This project uses a **three-environment configuration system** with comprehensive enforcement to ensure consistent, reliable, and maintainable code across all deployment environments.

## Environments

### 1. Development Environment
- **Database**: Local development database
- **Schema**: `upload_pipeline`
- **Port**: 8000
- **Debug**: `true`
- **Log Level**: `DEBUG`
- **RAG Settings**: Standard (10 chunks, 4000 tokens)

### 2. Testing Environment (Bridge)
- **Database**: **Production database** (same as production)
- **Schema**: `upload_pipeline_test` (isolated test schema)
- **Port**: 8001 (different port to avoid conflicts)
- **Debug**: `false`
- **Log Level**: `WARNING`
- **RAG Settings**: Reduced limits (8 chunks, 3000 tokens)
- **API Keys**: Production keys (same as production)

### 3. Production Environment
- **Database**: Production database
- **Schema**: `upload_pipeline`
- **Port**: 8000
- **Debug**: `false`
- **Log Level**: `ERROR`
- **RAG Settings**: Optimized (10 chunks, 4000 tokens)

## Quick Start

### Basic Usage
```python
from config.configuration_manager import initialize_config

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

### Multi-Environment Testing (MANDATORY)
Every feature MUST be tested in all three environments:

```python
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

## Enforcement Rules

### Configuration Manager Usage (MANDATORY)
```python
# ✅ CORRECT
from config.configuration_manager import initialize_config
config = initialize_config("testing")
if config.is_development():
    # Development logic

# ❌ WRONG
import os
if os.getenv("NODE_ENV") == "development":
    # Development logic
```

### Environment-Specific Behavior (MANDATORY)
- **Development**: Local database, debug logging, standard RAG settings
- **Testing**: Production database + test schema, warning logging, reduced RAG settings
- **Production**: Production database, error logging, optimized RAG settings

## Documentation

### Complete Guides
- [Environment Configuration Guide](docs/environment-configuration/ENVIRONMENT_CONFIGURATION_README.md) - Complete user guide
- [Enforcement System](docs/enforcement/ENVIRONMENT_ENFORCEMENT_SUMMARY.md) - Enforcement mechanisms overview
- [Configuration Scripts](scripts/environment/README.md) - Compliance checking scripts

### Configuration Files
- `config/configuration_manager.py` - Core configuration manager implementation
- `config/ENVIRONMENT_CONFIGURATION_GUIDE.md` - Technical implementation guide
- `config/env.*.example` - Example environment files

### Enforcement Files
- `.cursor/rules/environment_configuration_enforcement.mdc` - Core enforcement rules
- `.cursor/rules/testing_enforcement.mdc` - Testing enforcement rules
- `.cursor/rules/agent_environment_prompt.mdc` - Agent behavior rules

## Scripts

### Compliance Checking
```bash
# Check new/modified code (pre-commit hook)
./scripts/environment/enforce-environment-rules-new-code.sh

# Check entire codebase
./scripts/environment/enforce-environment-rules.sh
```

### Pre-commit Hooks
The system includes pre-commit hooks that automatically check for compliance:
- Environment configuration enforcement
- Multi-environment testing
- Configuration manager usage
- Environment-specific test structure

## Key Benefits

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

## Success Metrics

- **100%** of new code uses configuration manager
- **0%** direct environment variable access in new code
- **100%** environment-specific testing coverage
- **All features** tested in all three environments
- **All violations** caught and fixed before deployment

## Support

For questions or issues with the environment configuration system:
1. Check the [complete guide](docs/environment-configuration/ENVIRONMENT_CONFIGURATION_README.md)
2. Review the [enforcement system](docs/enforcement/ENVIRONMENT_ENFORCEMENT_SUMMARY.md)
3. Run the [enforcement script](scripts/environment/enforce-environment-rules-new-code.sh)
4. Check the [configuration manager](config/configuration_manager.py)
