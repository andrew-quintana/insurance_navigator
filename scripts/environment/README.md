# Environment Configuration Scripts

## Overview

This directory contains scripts for enforcing the three-environment configuration system rules and validating compliance.

## Scripts

### `enforce-environment-rules.sh`
- **Purpose**: Full codebase environment compliance check
- **Scope**: All files in the project
- **Usage**: Manual execution or CI/CD
- **Features**:
  - Comprehensive violation detection
  - Detailed reporting with color-coded output
  - Fix suggestions
  - Success metrics
  - Violation count tracking

**Usage:**
```bash
./scripts/environment/enforce-environment-rules.sh
```

**Output:**
- ✅ Success messages for compliant code
- ❌ Violation messages for non-compliant code
- ⚠️ Warning messages for potential issues
- Summary with total violations and success rate

### `enforce-environment-rules-new-code.sh`
- **Purpose**: New/modified code compliance check
- **Scope**: Git staged files only
- **Usage**: Pre-commit hook (automated)
- **Features**:
  - Targeted violation detection
  - Modified file analysis
  - Performance optimized
  - Fix suggestions
  - Git integration

**Usage:**
```bash
# Automatically run by pre-commit hooks
# Manual execution:
./scripts/environment/enforce-environment-rules-new-code.sh
```

**Output:**
- Focused on modified files only
- Faster execution than full codebase check
- Git-aware violation detection
- Pre-commit integration

## What These Scripts Check

### 1. Direct Environment Variable Access
- **Violation**: Direct `os.getenv()` usage outside `configuration_manager.py`
- **Fix**: Use `config.get_config()` or specific config methods
- **Example**:
  ```python
  # ❌ WRONG
  db_url = os.getenv("DATABASE_URL")
  
  # ✅ CORRECT
  config = initialize_config(environment)
  db_url = config.get_database_url()
  ```

### 2. Hardcoded Environment-Specific Values
- **Violation**: Hardcoded values like `NODE_ENV`, `DEBUG`, `LOG_LEVEL`
- **Fix**: Use configuration manager methods
- **Example**:
  ```python
  # ❌ WRONG
  if os.getenv("NODE_ENV") == "development":
      debug = True
  
  # ✅ CORRECT
  if config.is_development():
      debug = config.service.debug
  ```

### 3. Configuration Manager Usage
- **Check**: Presence of configuration manager imports and usage
- **Validation**: Ensures proper configuration patterns

### 4. Environment-Specific Testing
- **Check**: Test file structure and environment validation
- **Validation**: Ensures all environments are tested

### 5. Staging Environment References
- **Violation**: Any references to "staging" environment
- **Fix**: Remove staging references (use testing instead)

### 6. Environment-Specific Documentation
- **Check**: Presence of environment-specific documentation
- **Validation**: Ensures proper documentation patterns

## Integration

### Pre-commit Hooks
The `enforce-environment-rules-new-code.sh` script is integrated with pre-commit hooks:

```yaml
# .pre-commit-config.yaml
- id: environment-configuration-enforcement
  name: Environment Configuration Enforcement
  entry: ./scripts/environment/enforce-environment-rules-new-code.sh
  language: system
  stages: [pre-commit]
  always_run: true
```

### CI/CD Pipeline
The `enforce-environment-rules.sh` script can be integrated into CI/CD pipelines:

```yaml
# Example CI/CD integration
- name: Check Environment Configuration Compliance
  run: ./scripts/environment/enforce-environment-rules.sh
```

## Exit Codes

- **0**: All checks passed, no violations found
- **1**: Violations found, compliance check failed

## Dependencies

- `bash` - Shell script execution
- `git` - Git integration for modified file detection
- `grep` - Pattern matching for violation detection
- `find` - File system searching for test structure validation

## Customization

### Adding New Checks
To add new violation checks, modify the scripts to include additional `grep` patterns:

```bash
# Example: Check for new violation pattern
NEW_VIOLATIONS=$(grep -r "NEW_PATTERN" --exclude-dir=.git . | wc -l)
if [ "$NEW_VIOLATIONS" -gt 0 ]; then
    report_violation "Found $NEW_VIOLATIONS instances of new violation pattern"
fi
```

### Modifying Output
The scripts use color-coded output functions that can be customized:

```bash
# Color functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
```

## Troubleshooting

### Common Issues

1. **Script not executable**
   ```bash
   chmod +x scripts/environment/enforce-environment-rules*.sh
   ```

2. **Git not available**
   - Ensure git is installed and accessible
   - Check if running in a git repository

3. **Permission denied**
   - Check file permissions
   - Ensure script is executable

4. **False positives**
   - Review exclusion patterns in scripts
   - Update patterns as needed

### Debug Mode
Add debug output to scripts for troubleshooting:

```bash
# Add to script for debugging
set -x  # Enable debug mode
echo "Debug: Checking file $file"
```

## Maintenance

### Regular Updates
- Update violation patterns as needed
- Add new checks for emerging patterns
- Improve detection accuracy
- Update documentation

### Performance Optimization
- Optimize grep patterns for better performance
- Reduce false positives
- Improve execution speed
- Streamline checks

## Related Files

- [Environment Configuration Documentation](../../docs/environment-configuration/)
- [Enforcement Documentation](../../docs/enforcement/)
- [Configuration Manager](../../config/configuration_manager.py)
- [Pre-commit Configuration](../../.pre-commit-config.yaml)
- [Cursor Rules](../../.cursor/rules/)
