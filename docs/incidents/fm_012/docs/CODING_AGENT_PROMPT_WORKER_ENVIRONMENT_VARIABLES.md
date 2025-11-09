# Coding Agent Prompt: Worker Environment Variable Loading Issue

## 🎯 **Mission**
Investigate and resolve the document parsing failure that's causing non-retryable errors in the worker process.

## 🚨 **Problem Statement**
Document parsing pipeline is failing with non-retryable error: "Document file is not accessible for processing. Please try uploading again." The failure appears to be related to storage access issues, but the root cause requires investigation.

## 📋 **Specific Tasks**

### **Task 1: Investigate Document Processing Failure**
**Priority**: P0 - Critical  
**Time Estimate**: 45 minutes

**Investigation Steps**:
1. Analyze the complete error flow from document upload to parsing failure
2. Verify environment variable loading and propagation in the worker process
3. Examine storage access and authentication mechanisms
4. Identify the specific point of failure in the processing pipeline

**Code to Examine**:
- `backend/workers/enhanced_runner.py` (environment loading)
- `backend/workers/enhanced_base_worker.py` (processing logic)
- `backend/shared/storage/storage_manager.py` (storage access)
- `backend/shared/config/worker_config.py` (configuration)
- `backend/shared/storage/storage_manager.py` (lines 24-33)

**Expected Output**:
- Clear identification of where environment variable loading fails
- Evidence of whether variables are loaded in runner but not worker
- Root cause analysis of the propagation issue

### **Task 2: Fix Environment Variable Loading**
**Priority**: P0 - Critical  
**Time Estimate**: 45 minutes

**Implementation Requirements**:
1. Ensure `SUPABASE_SERVICE_ROLE_KEY` is available in worker process
2. Add environment variable validation at worker startup
3. Implement fail-fast behavior for missing critical variables
4. Maintain backward compatibility with existing configuration

**Code Changes Needed**:
- Modify `enhanced_runner.py` to validate environment variables after loading
- Fix `StorageManager` environment variable loading logic
- Add proper error handling and logging

**Success Criteria**:
- Worker can access `SUPABASE_SERVICE_ROLE_KEY` environment variable
- Clear error messages if environment variables are missing
- Document processing pipeline works end-to-end

### **Task 3: Test and Validate Fix**
**Priority**: P1 - High  
**Time Estimate**: 30 minutes

**Testing Steps**:
1. Test worker startup with correct environment variables
2. Test worker startup with missing environment variables (should fail gracefully)
3. Test end-to-end document processing
4. Verify error messages are user-friendly

**Test Commands**:
```bash
# Test 1: Normal startup
export ENVIRONMENT=development
python backend/workers/enhanced_runner.py

# Test 2: Missing environment variable
unset SUPABASE_SERVICE_ROLE_KEY
export ENVIRONMENT=development
python backend/workers/enhanced_runner.py  # Should fail with clear error

# Test 3: End-to-end processing
# Upload a document through the frontend and verify processing
```

## 🔍 **Key Investigation Areas**

### **Environment Variable Loading Chain**
1. **Runner Level**: `enhanced_runner.py` loads `.env.development`
2. **Worker Level**: `EnhancedBaseWorker` should have access to variables
3. **Storage Level**: `StorageManager` needs `SUPABASE_SERVICE_ROLE_KEY`

### **Potential Issues**
1. **Process Isolation**: Environment variables not propagating between processes
2. **Timing Issues**: Variables loaded after `StorageManager` initialization
3. **Configuration Mismatch**: Different environment variable names in different classes
4. **Fallback Logic**: `StorageManager` fallback not working correctly

### **Existing Patterns to Follow**
- `backend/shared/config/worker_config.py` has good environment variable handling
- `backend/shared/storage/storage_manager.py` has fallback logic (but it's not working)
- `enhanced_runner.py` has proper environment file loading

## 📚 **Reference Documentation**

### **Similar Issues Resolved**
- **FM-011**: Worker Storage and Fallback Failure (2025-09-18) - Similar storage access issue
- **FRACAS-001**: Service Connectivity Failures - Environment variable issues
- **Environment Variables Fix Plan**: Comprehensive environment variable management

### **Configuration Patterns**
- `WorkerConfig.from_environment()` - Good pattern for environment variable loading
- `StorageManager.__init__()` - Has fallback logic that needs fixing
- `enhanced_runner.py` - Proper environment file loading

## 🎯 **Expected Deliverables**

### **Code Changes**
1. **Fixed `enhanced_runner.py`**: Add environment variable validation
2. **Fixed `StorageManager`**: Improve environment variable loading logic
3. **Added validation**: Environment variable checks at startup

### **Documentation**
1. **Root cause analysis**: Clear explanation of why the issue occurred
2. **Solution documentation**: How the fix works
3. **Testing results**: Evidence that the fix works

### **Testing Evidence**
1. **Before fix**: Worker fails with "SUPABASE_SERVICE_ROLE_KEY environment variable not set"
2. **After fix**: Worker starts successfully and processes documents
3. **Error handling**: Clear error messages for missing environment variables

## 🚀 **Success Metrics**

### **Immediate Success**
- [ ] Worker can access `SUPABASE_SERVICE_ROLE_KEY` environment variable
- [ ] No more "SUPABASE_SERVICE_ROLE_KEY environment variable not set" errors
- [ ] Document processing pipeline works end-to-end

### **Quality Improvements**
- [ ] Clear error messages for missing environment variables
- [ ] Fail-fast behavior for configuration issues
- [ ] Consistent environment variable handling across services

## 🔧 **Implementation Guidelines**

### **Code Quality**
- Follow existing patterns in the codebase
- Add comprehensive error handling
- Include clear logging for debugging
- Maintain backward compatibility

### **Error Handling**
- Fail fast with clear error messages
- Provide actionable guidance for fixing issues
- Log environment variable loading status
- Include context in error messages

### **Testing**
- Test both success and failure scenarios
- Verify error messages are user-friendly
- Test environment variable validation
- Ensure end-to-end functionality

## 📞 **Support Information**

### **Related Files**
- `backend/workers/enhanced_runner.py` - Main runner script
- `backend/workers/enhanced_base_worker.py` - Worker implementation
- `backend/shared/storage/storage_manager.py` - Storage manager
- `backend/shared/config/worker_config.py` - Configuration management

### **Environment Files**
- `.env.development` - Development environment variables
- `scripts/start-dev.sh` - Development startup script

### **Logs to Check**
- Worker startup logs for environment variable loading
- Storage manager logs for service role key access
- Document processing logs for end-to-end functionality

---

**Created**: 2025-09-24  
**Priority**: P0 - Critical  
**Estimated Time**: 2 hours  
**Dependencies**: None  
**Blockers**: None
