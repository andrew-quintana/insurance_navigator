# Environment Configuration Enforcement - File Organization

## Overview

This directory contains all documentation and resources related to the enforcement system for the three-environment configuration system.

## Directory Structure

```
docs/enforcement/
├── INDEX.md                                    # This file - directory index
└── ENVIRONMENT_ENFORCEMENT_SUMMARY.md         # Complete enforcement system overview
```

## Files in This Directory

### `ENVIRONMENT_ENFORCEMENT_SUMMARY.md`
- **Purpose**: Comprehensive overview of the enforcement system
- **Audience**: Developers, code reviewers, and CI/CD maintainers
- **Content**:
  - Enforcement mechanisms overview
  - Cursor rules documentation
  - Pre-commit hooks configuration
  - Enforcement scripts documentation
  - Violation consequences
  - Success metrics
  - Usage instructions

## Related Files

### Cursor Rules
- `.cursor/rules/environment_configuration_enforcement.mdc` - Core enforcement rules
- `.cursor/rules/testing_enforcement.mdc` - Testing enforcement rules
- `.cursor/rules/agent_environment_prompt.mdc` - Agent behavior rules

### Scripts
- `scripts/environment/enforce-environment-rules.sh` - Full codebase compliance check
- `scripts/environment/enforce-environment-rules-new-code.sh` - New/modified code check

### Git Configuration
- `.pre-commit-config.yaml` - Pre-commit hooks for enforcement

### Configuration Files
- `config/configuration_manager.py` - Core configuration manager implementation
- `config/ENVIRONMENT_CONFIGURATION_GUIDE.md` - Technical implementation guide

## Enforcement Levels

### Level 1: Agent Behavior (Immediate)
- **Mechanism**: Cursor rules and agent prompts
- **Scope**: All agent interactions
- **Enforcement**: Agent instruction compliance
- **Result**: Agent automatically follows rules

### Level 2: Pre-commit Hooks (Before Commit)
- **Mechanism**: Git pre-commit hooks
- **Scope**: Modified files
- **Enforcement**: Commit blocking
- **Result**: Violations prevent commits

### Level 3: Code Review (Before Merge)
- **Mechanism**: Manual review + automated checks
- **Scope**: All changes
- **Enforcement**: Merge rejection
- **Result**: Violations prevent merges

### Level 4: CI/CD Pipeline (Before Deployment)
- **Mechanism**: Automated testing and validation
- **Scope**: All environments
- **Enforcement**: Deployment blocking
- **Result**: Violations prevent deployments

## Key Enforcement Rules

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

### Multi-Environment Testing (MANDATORY)
```python
# ✅ CORRECT
@pytest.mark.parametrize("environment", ["development", "testing", "production"])
def test_feature(environment):
    config = initialize_config(environment)
    # Test implementation
```

### Environment-Specific Behavior (MANDATORY)
- **Development**: Local database, debug logging, standard RAG settings
- **Testing**: Production database + test schema, warning logging, reduced RAG settings
- **Production**: Production database, error logging, optimized RAG settings

## Quick Start

1. **Read the enforcement summary**: `ENVIRONMENT_ENFORCEMENT_SUMMARY.md`
2. **Review cursor rules**: `../../.cursor/rules/`
3. **Check pre-commit hooks**: `../../.pre-commit-config.yaml`
4. **Run enforcement script**: `../../scripts/environment/enforce-environment-rules-new-code.sh`

## Success Metrics

- **100%** of new code uses configuration manager
- **0%** direct environment variable access in new code
- **100%** environment-specific testing coverage
- **All features** tested in all three environments
- **All violations** caught and fixed before deployment

## Maintenance

This directory should be updated when:
- New enforcement rules are added
- Violation patterns change
- Enforcement scripts are modified
- New documentation is needed

## Related Documentation

- [Environment Configuration](../environment-configuration/ENVIRONMENT_CONFIGURATION_README.md)
- [Configuration Manager](../../config/configuration_manager.py)
- [Cursor Rules](../../.cursor/rules/)
- [Pre-commit Hooks](../../.pre-commit-config.yaml)
