# FRACAS FM-013 Investigation Prompt: Environment Configuration Inconsistencies

## 🎯 **INVESTIGATION MISSION**

**Objective**: Investigate and resolve environment configuration inconsistencies across the codebase that create maintenance challenges and deployment risks.

**Reference Document**: `docs/incidents/failure_modes/configuration/FRACAS_FM_013_ENVIRONMENT_CONFIGURATION_INCONSISTENCIES.md`

## 🚨 **CURRENT SITUATION**

### **Critical Issue**
- **Status**: High Priority
- **Impact**: Maintenance difficulties, deployment risks, debugging challenges
- **Root Cause**: Multiple different approaches for loading environment variables and configuration
- **Scope**: All environments (development, staging, production)

### **Evidence Summary**
```
Problem: Multiple different approaches for environment variable loading
Impact: Inconsistent behavior across components
Maintenance: Difficult to update configuration logic
Deployment: Different fallback behaviors create risks
```

## 🔍 **INVESTIGATION TASKS**

### **Task 1: Configuration Pattern Analysis (P0 - Critical)**
**Time Estimate**: 30 minutes

**Objective**: Analyze all different configuration loading approaches in the codebase.

**Investigation Steps**:
1. Identify all files using different environment variable loading approaches
2. Document the four main approaches (A, B, C, D)
3. Analyze inconsistencies in default values and error handling
4. Create comprehensive mapping of configuration patterns

**Expected Output**:
- Complete inventory of configuration approaches
- Detailed analysis of inconsistencies
- Mapping of files to configuration patterns

### **Task 2: Environment File Analysis (P0 - Critical)**
**Time Estimate**: 20 minutes

**Objective**: Analyze environment file structure and identify missing files.

**Investigation Steps**:
1. Check existing environment files (`.env.development`, `.env.staging`, `.env.production`)
2. Verify YAML configuration files in `config/environment/`
3. Identify missing configuration files
4. Analyze environment detection inconsistencies

**Expected Output**:
- Environment file inventory
- Missing file identification
- Environment detection method analysis

### **Task 3: Centralized Configuration Design (P1 - High)**
**Time Estimate**: 45 minutes

**Objective**: Design a centralized configuration system to replace inconsistent approaches.

**Implementation Requirements**:
1. Create centralized storage configuration module
2. Design environment validation system
3. Plan migration strategy from old patterns
4. Create configuration best practices

**Code Changes Needed**:
- Create `config/storage_config.py` for centralized storage configuration
- Implement environment validation functions
- Design migration tools
- Create configuration documentation

**Success Criteria**:
- Centralized configuration system designed
- Migration strategy planned
- Best practices documented

### **Task 4: Production Configuration Analysis (P1 - High)**
**Time Estimate**: 20 minutes

**Objective**: Understand how production works without `production.yaml` file.

**Investigation Steps**:
1. Analyze `config/render/render.yaml` as production configuration
2. Understand Render environment variable injection
3. Review cloud deployment detection logic
4. Document production configuration approach

**Expected Output**:
- Production configuration understanding
- Render YAML analysis
- Cloud deployment detection documentation

### **Task 5: Implementation Plan (P2 - Medium)**
**Time Estimate**: 30 minutes

**Objective**: Create detailed implementation plan for configuration standardization.

**Implementation Requirements**:
1. Phase 1: Create missing production configuration
2. Phase 2: Implement centralized storage configuration
3. Phase 3: Migrate all files to use centralized approach
4. Phase 4: Create validation and testing tools

**Success Criteria**:
- Detailed implementation plan
- Phase-by-phase breakdown
- Success criteria for each phase

## 🧪 **TEST COMMANDS**

```bash
# Test 1: Analyze configuration patterns
find . -name "*.py" -exec grep -l "os.getenv" {} \; | head -10

# Test 2: Check environment files
ls -la .env.*
ls -la config/environment/

# Test 3: Test current configuration loading
python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.development')
print('Environment variables loaded:')
for key in ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'ENVIRONMENT']:
    print(f'{key}: {os.getenv(key, \"NOT_SET\")}')
"

# Test 4: Test configuration manager
python -c "
from config.configuration_manager import get_config
try:
    config = get_config()
    print('✅ Configuration manager works')
    print(f'Environment: {config.environment}')
except Exception as e:
    print(f'❌ Configuration manager failed: {e}')
"
```

## 📋 **EXPECTED OUTPUT**

### **Immediate Fix (P0)**
1. **Configuration Analysis**: Complete inventory of all configuration approaches
2. **Missing Files**: Identify and create missing configuration files
3. **Pattern Documentation**: Document all configuration patterns and inconsistencies

### **Short-term Improvements (P1)**
1. **Centralized System**: Implement centralized storage configuration
2. **Environment Validation**: Create validation tools for all environments
3. **Migration Tools**: Create tools to migrate from old patterns

### **Long-term Improvements (P2)**
1. **Standardization**: All components use centralized configuration
2. **Documentation**: Comprehensive configuration documentation
3. **Testing**: Automated configuration validation

### **Success Metrics**
- ✅ All storage operations use centralized configuration
- ✅ All environments have complete configuration files
- ✅ Environment validation script passes for all environments
- ✅ No hardcoded environment-specific logic in business logic files
- ✅ Consistent error handling and fallback behavior

## 📄 **DELIVERABLES**

1. **FRACAS Update**: Update `docs/incidents/failure_modes/configuration/FRACAS_FM_013_ENVIRONMENT_CONFIGURATION_INCONSISTENCIES.md` with findings
2. **Configuration Analysis**: Complete analysis of all configuration patterns
3. **Centralized System**: Implement centralized storage configuration
4. **Migration Plan**: Detailed plan for migrating to centralized approach
5. **Documentation**: Update configuration documentation

## ⚠️ **CRITICAL NOTES**

- **High Impact**: Configuration inconsistencies create maintenance and deployment risks
- **Multiple Approaches**: Four different approaches need to be standardized
- **Production Working**: Production works without `production.yaml` due to Render configuration
- **Migration Complexity**: Need to migrate all files without breaking functionality

## 🚨 **ESCALATION CRITERIA**

- If centralized configuration breaks existing functionality
- If migration requires significant architectural changes
- If environment validation reveals critical missing configurations
- If standardization conflicts with platform-specific requirements

## ⏱️ **ESTIMATED DURATION**
- **Total Time**: 145 minutes
- **Investigation**: 50 minutes
- **Design**: 45 minutes
- **Implementation**: 50 minutes

---

**Reference**: See `docs/incidents/failure_modes/configuration/FRACAS_FM_013_ENVIRONMENT_CONFIGURATION_INCONSISTENCIES.md` for complete failure details
