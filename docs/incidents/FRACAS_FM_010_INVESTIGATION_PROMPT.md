# FRACAS FM-010 Investigation Prompt: Chat Configuration Error

## 🎯 **MISSION**
Investigate and resolve the chat interface configuration error that causes generic error messages when users interact with the Insurance Navigator system.

## 🚨 **CURRENT SITUATION**

### **Critical Issue**
- **Status**: P1 - High Priority
- **Impact**: Chat interface completely non-functional
- **User Experience**: Generic error message "I apologize, but I encountered an error processing your request. Please try again in a moment."
- **Root Cause**: Configuration validation failure for missing translation service API keys
- **Error Code**: `Configuration validation errors: - At least one translation service API key is required (ELEVENLABS_API_KEY or FLASH_API_KEY)`

### **Evidence Summary**
```
Error Location: /chat endpoint
Configuration File: agents/patient_navigator/input_processing/config.py
Validation Method: InputProcessingConfig.validate()
Error Handler: main.py line 1287 (generic exception handler)
Missing Variables: ELEVENLABS_API_KEY or FLASH_API_KEY
```

## 🔍 **INVESTIGATION TASKS**

### **Task 1: Environment Configuration Audit (P0 - Critical)**
**Time Estimate**: 15 minutes

**Objective**: Determine what translation service API keys are missing and why.

**Investigation Steps**:
1. Check current environment variables in `.env.development`
2. Verify if `ELEVENLABS_API_KEY` or `FLASH_API_KEY` are present
3. Check if these keys are required for basic chat functionality
4. Determine if translation services are actually needed for plan overview requests

**Expected Output**:
- List of missing environment variables
- Assessment of whether translation services are required for basic chat
- Recommendation for immediate fix

### **Task 2: Configuration Dependency Analysis (P1 - High)**
**Time Estimate**: 20 minutes

**Objective**: Understand why chat interface depends on translation service configuration.

**Investigation Steps**:
1. Trace the dependency chain from chat endpoint to input processing config
2. Examine `agents/patient_navigator/input_processing/config.py` validation logic
3. Check if translation services can be made optional for basic chat
4. Review the configuration loading flow in chat interface

**Expected Output**:
- Dependency chain documentation
- Assessment of whether translation services are truly required
- Recommendation for making translation services optional

### **Task 3: Error Message Improvement (P1 - High)**
**Time Estimate**: 15 minutes

**Objective**: Replace generic error messages with helpful, specific guidance.

**Investigation Steps**:
1. Identify all generic error handlers in chat interface
2. Review error message patterns in `main.py` and `chat_interface.py`
3. Design specific error messages for configuration issues
4. Implement better error handling for missing API keys

**Expected Output**:
- Specific error messages for configuration issues
- Improved error handling implementation
- User-friendly guidance for missing configuration

### **Task 4: Configuration Validation Review (P2 - Medium)**
**Time Estimate**: 10 minutes

**Objective**: Review and potentially modify configuration validation logic.

**Investigation Steps**:
1. Examine `InputProcessingConfig.validate()` method
2. Determine if translation services should be optional
3. Check if there are different validation levels needed
4. Review configuration documentation

**Expected Output**:
- Modified validation logic if needed
- Clear documentation of required vs optional services
- Configuration best practices

## 🧪 **TEST COMMANDS**

```bash
# Test 1: Check current environment variables
cd /Users/aq_home/1Projects/accessa/insurance_navigator
cat .env.development | grep -E "(ELEVENLABS|FLASH)"

# Test 2: Test chat endpoint directly
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Give a plan overview", "conversation_id": "test"}'

# Test 3: Check configuration loading
python -c "
from agents.patient_navigator.input_processing.config import get_config
try:
    config = get_config()
    print('✅ Configuration loaded successfully')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"

# Test 4: Test with missing API keys
python -c "
import os
os.environ.pop('ELEVENLABS_API_KEY', None)
os.environ.pop('FLASH_API_KEY', None)
from agents.patient_navigator.input_processing.config import InputProcessingConfig
try:
    config = InputProcessingConfig.from_environment()
    config.validate()
    print('✅ Validation passed')
except Exception as e:
    print(f'❌ Validation failed: {e}')
"
```

## 📋 **EXPECTED OUTPUT**

### **Immediate Fix (P0)**
1. **Environment Variables**: Add missing `ELEVENLABS_API_KEY` or `FLASH_API_KEY` to `.env.development`
2. **Chat Functionality**: Verify chat interface works with basic requests
3. **Error Resolution**: Confirm specific error is resolved

### **Short-term Improvements (P1)**
1. **Better Error Messages**: Replace generic errors with specific guidance
2. **Optional Dependencies**: Make translation services optional for basic chat
3. **Configuration Documentation**: Document required vs optional services

### **Success Metrics**
- ✅ Chat interface responds to "Give a plan overview" without errors
- ✅ Users receive helpful error messages instead of generic ones
- ✅ Configuration validation provides clear guidance
- ✅ Translation services are optional for basic chat functionality

## 📄 **DELIVERABLES**

1. **FRACAS Update**: Update `FRACAS_FM_010_CHAT_CONFIGURATION_ERROR.md` with findings
2. **Configuration Fix**: Implement immediate fix for missing API keys
3. **Error Handling**: Implement improved error messages
4. **Documentation**: Update configuration documentation
5. **Test Results**: Provide test results showing resolution

## ⚠️ **CRITICAL NOTES**

- **Do Not Assume**: Don't assume translation services are required without investigation
- **User Impact**: This completely blocks chat functionality
- **Generic Errors**: The current error message provides no useful information to users
- **Configuration**: This appears to be a configuration issue, not a code bug

## 🚨 **ESCALATION CRITERIA**

- If translation services are truly required for basic chat functionality
- If configuration changes break other system components
- If API keys are not available or cannot be obtained
- If investigation reveals deeper architectural issues

## ⏱️ **ESTIMATED DURATION**
- **Total Time**: 60 minutes
- **Immediate Fix**: 15 minutes
- **Investigation**: 30 minutes
- **Implementation**: 15 minutes

---
**Reference**: See `docs/incidents/FRACAS_FM_010_CHAT_CONFIGURATION_ERROR.md` for complete failure details
