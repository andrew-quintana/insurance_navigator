# FRACAS Investigation Prompt: FM-009 - LlamaParse API Invalid Token Format

## 🎯 **MISSION CRITICAL INVESTIGATION**

**Objective**: Resolve the LlamaParse API authentication failure causing 100% document processing failure rate.

**Reference Document**: `docs/incidents/FRACAS_FM_009_LLAMAPARSE_INVALID_TOKEN_FORMAT.md`

## 🚨 **CURRENT SITUATION**

### **Critical Issue**
- **Status**: P0 - Critical
- **Impact**: 100% failure rate for document processing
- **Root Cause**: Environment variable priority mismatch - worker expects `LLAMACLOUD_API_KEY` but development only has `LLAMAPARSE_API_KEY=sk-test-key`
- **Error Code**: `LLAMAPARSE_CLIENT_ERROR`
- **Affected Component**: Document Processing Pipeline

### **Evidence Summary**
```
API Response: 401 Unauthorized
Response Body: {"detail":"Invalid token format"}
Request Headers: {"Authorization": "Bearer sk-test-key"}
Current API Key: sk-test-key (from .env.development)
Worker Config Priority: LLAMACLOUD_API_KEY > LLAMAPARSE_API_KEY
Production Has: LLAMACLOUD_API_KEY=llx-CRtlURo7FT74ZMydik58KjPHC5aTpOSuGjWqOkTXjrPQucUS
Development Has: LLAMAPARSE_API_KEY=sk-test-key (missing LLAMACLOUD_API_KEY)
```

## 🔍 **INVESTIGATION TASKS**

### **Task 1: Environment Variable Configuration Fix (P0 - Critical)**
**Time Estimate**: 15 minutes

**Objective**: Fix the environment variable priority mismatch between development and production.

**Investigation Steps**:
1. Add `LLAMACLOUD_API_KEY` to `.env.development` with the production key value
2. Verify the worker configuration priority in `backend/shared/config/worker_config.py`
3. Test that the worker can now access the correct API key
4. Validate that document processing works end-to-end

**Expected Output**:
- `.env.development` updated with `LLAMACLOUD_API_KEY=llx-CRtlURo7FT74ZMydik58KjPHC5aTpOSuGjWqOkTXjrPQucUS`
- Worker successfully loads the correct API key
- Document processing pipeline functional

**Code to Examine**:
- `docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/upload_pipeline/phase2/reports/external_api_integration_report.md`
- `docs/initiatives/deployment/20250918_mvp_production_deployment/fracas/FM_006_llamaparse_api_error.md`
- `docs/technical/reference_working_llamaparse_integration.py`

### **Task 2: Environment Configuration Analysis (P0 - Critical)**
**Time Estimate**: 20 minutes

**Objective**: Analyze current environment configuration and identify configuration issues.

**Investigation Steps**:
1. Examine current `.env.development` configuration
2. Check for environment-specific API key settings
3. Identify any configuration inconsistencies
4. Document proper environment variable setup

**Expected Output**:
- Current environment configuration analysis
- Configuration issue identification
- Proper environment setup documentation

**Files to Examine**:
- `.env.development`
- `config/env.development.example`
- `backend/shared/config/worker_config.py`

### **Task 3: API Key Validation Implementation (P1 - High)**
**Time Estimate**: 45 minutes

**Objective**: Implement API key format validation to prevent future issues.

**Implementation Requirements**:
1. Add API key format validation to worker startup
2. Implement validation in `enhanced_runner.py`
3. Add validation to `WorkerConfig` class
4. Create clear error messages for invalid API keys

**Code Changes Needed**:
- Modify `backend/workers/enhanced_runner.py` to validate API key format
- Update `backend/shared/config/worker_config.py` to include API key validation
- Add validation methods for LlamaParse API key format

**Success Criteria**:
- API key format validation during startup
- Clear error messages for invalid API keys
- Prevention of processing with invalid keys

### **Task 4: LlamaParse API Integration Testing (P1 - High)**
**Time Estimate**: 60 minutes

**Objective**: Test LlamaParse API integration with correct API key format.

**Testing Steps**:
1. Obtain valid LlamaParse API key (if possible)
2. Test API key authentication with LlamaParse service
3. Test document parsing with valid API key
4. Verify end-to-end document processing pipeline

**Test Commands**:
```bash
# Test 1: Fix Development Environment
echo "LLAMACLOUD_API_KEY=llx-CRtlURo7FT74ZMydik58KjPHC5aTpOSuGjWqOkTXjrPQucUS" >> .env.development

# Test 2: Verify Environment Variable Loading
python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.development')
print(f'LLAMACLOUD_API_KEY: {os.getenv(\"LLAMACLOUD_API_KEY\", \"NOT_SET\")}')
print(f'LLAMAPARSE_API_KEY: {os.getenv(\"LLAMAPARSE_API_KEY\", \"NOT_SET\")}')
"

# Test 3: API Key Validation
python -c "
import os
import httpx
import asyncio
from dotenv import load_dotenv
load_dotenv('.env.development')

async def test_api_key():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://api.cloud.llamaindex.ai/api/v1/jobs',
            headers={'Authorization': f'Bearer {os.getenv(\"LLAMACLOUD_API_KEY\")}'}
        )
        print(f'API Key Test: {response.status_code}')
        print(f'Response: {response.text}')

asyncio.run(test_api_key())
"

# Test 4: Document Processing
python backend/workers/enhanced_runner.py
```

**Expected Output**:
- Successful API key authentication
- Document processing pipeline functionality
- End-to-end processing verification

### **Task 5: Error Handling Improvement (P2 - Medium)**
**Time Estimate**: 30 minutes

**Objective**: Improve error handling to provide more specific error messages.

**Implementation Requirements**:
1. Add specific error handling for 401 authentication errors
2. Provide actionable error messages for API key issues
3. Implement fallback mechanisms for invalid API keys
4. Add logging for API key validation failures

**Code Changes Needed**:
- Update `_direct_llamaparse_call` method in `enhanced_base_worker.py`
- Add specific error handling for 401 responses
- Implement user-friendly error messages
- Add API key validation logging

**Success Criteria**:
- Specific error messages for authentication failures
- Actionable feedback for users
- Proper error classification and handling

## 📋 **INVESTIGATION CHECKLIST**

### **Pre-Investigation**
- [ ] Read FRACAS document: `docs/incidents/FRACAS_FM_009_LLAMAPARSE_INVALID_TOKEN_FORMAT.md`
- [ ] Review historical LlamaParse issues in documentation
- [ ] Understand current error patterns and symptoms
- [ ] Set up investigation environment

### **During Investigation**
- [ ] Research LlamaParse API key format requirements
- [ ] Analyze current environment configuration
- [ ] Test API key validation with different formats
- [ ] Implement API key format validation
- [ ] Test end-to-end document processing
- [ ] Document findings and solutions

### **Post-Investigation**
- [ ] Update FRACAS document with findings
- [ ] Implement corrective actions
- [ ] Test complete solution
- [ ] Document lessons learned
- [ ] Create prevention measures

## 🔧 **TECHNICAL SPECIFICATIONS**

### **Current Configuration**
```bash
# Development Environment (Missing LLAMACLOUD_API_KEY)
LLAMAPARSE_API_KEY=sk-test-key

# Production Environment (Has Both)
LLAMACLOUD_API_KEY=llx-CRtlURo7FT74ZMydik58KjPHC5aTpOSuGjWqOkTXjrPQucUS
LLAMAPARSE_API_KEY=llx-CRtlURo7FT74ZMydik58KjPHC5aTpOSuGjWqOkTXjrPQucUS

# Worker Configuration Priority
llamaparse_api_key=os.getenv("LLAMACLOUD_API_KEY", os.getenv("LLAMAPARSE_API_KEY", ""))
```

### **API Endpoints**
- **Base URL**: `https://api.cloud.llamaindex.ai`
- **Jobs Endpoint**: `/api/v1/jobs` (GET)
- **Parsing Endpoint**: `/api/parsing/upload` (POST)
- **Authentication**: Bearer token

### **Error Patterns**
- **HTTP Status**: 401 Unauthorized
- **Response Body**: `{"detail":"Invalid token format"}`
- **Error Code**: `LLAMAPARSE_CLIENT_ERROR`
- **Retryable**: No (non-retryable error)

## 📊 **SUCCESS METRICS**

### **Resolution Metrics**
- [ ] `LLAMACLOUD_API_KEY` added to `.env.development` with valid `llx-...` format
- [ ] Worker successfully loads correct API key from environment
- [ ] Document processing pipeline functional (100% success rate)
- [ ] Error messages provide actionable feedback
- [ ] End-to-end document processing tested and verified

### **Prevention Metrics**
- [ ] API key validation during startup
- [ ] Comprehensive environment variable validation
- [ ] Clear documentation of API key requirements
- [ ] Monitoring for API key validation failures

## 🚀 **DELIVERABLES**

### **Immediate Deliverables**
1. **Environment Configuration Fix**: Add `LLAMACLOUD_API_KEY` to `.env.development`
2. **Configuration Documentation**: Document environment variable priority requirements
3. **Validation Implementation**: Add API key format validation to worker startup
4. **Testing Results**: Verify document processing pipeline functionality

### **Documentation Deliverables**
1. **Updated FRACAS Document**: Complete with findings and resolution
2. **API Key Management Guide**: Document API key acquisition and configuration
3. **Environment Setup Guide**: Document proper environment variable configuration
4. **Error Handling Guide**: Document improved error handling implementation

## ⚠️ **CRITICAL NOTES**

1. **Environment Variable Priority**: The worker configuration prioritizes `LLAMACLOUD_API_KEY` over `LLAMAPARSE_API_KEY` - ensure both are set in development
2. **API Key Security**: Ensure API keys are properly secured and not committed to version control
3. **Environment Consistency**: Maintain consistent environment variable naming between development and production
4. **Error Handling**: Implement proper error handling to prevent sensitive information exposure
5. **Testing**: Thoroughly test all changes before deploying to production
6. **Documentation**: Update all relevant documentation with environment variable priority requirements

## 📞 **ESCALATION CRITERIA**

**Escalate to Senior Developer if**:
- Environment variable priority changes are needed in worker configuration
- Multiple environment variable naming conventions need to be standardized
- Integration testing reveals additional issues beyond environment configuration

**Escalate to DevOps if**:
- Production environment access is needed to verify configuration
- Security concerns with API key management
- Infrastructure changes are required
- Environment variable synchronization between services is needed

---

**Investigation Prompt ID**: FM-009-INVESTIGATION  
**Created**: 2025-09-24  
**Priority**: P0 - Critical  
**Status**: Ready for Assignment  
**Estimated Duration**: 30-60 minutes  
**Dependencies**: Access to production environment variables and development environment configuration
