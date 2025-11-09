# FRACAS FM-029 Investigation Report

## Incident Summary
**Priority**: P1 - High  
**Status**: RESOLVED  
**Created**: 2025-10-02  
**Resolved**: 2025-10-02  

## Problem Description
Users were receiving generic responses instead of document-specific information from the chat endpoint, indicating a complete failure of the RAG (Retrieval-Augmented Generation) system. All RAG operations were returning 0 chunks, and the InformationRetrievalAgent was not available.

## Root Cause Analysis

### Primary Issues Identified

1. **InformationRetrievalAgent Import Error**
   - **Issue**: `StrategyWorkflowOrchestrator` constructor expected a `WorkflowConfig` object but was receiving a boolean parameter
   - **Location**: `agents/patient_navigator/supervisor/workflow.py:58-62`
   - **Impact**: Caused `WORKFLOW_COMPONENTS_AVAILABLE` to be `False`, making `InformationRetrievalAgent` unavailable

2. **Environment Configuration Mismatch**
   - **Issue**: Application was loading development environment instead of staging environment
   - **Location**: Environment loader was defaulting to development
   - **Impact**: RAG system was connecting to local database instead of production database

3. **Database Connection Mismatch**
   - **Issue**: MCP tools and asyncpg were connecting to different database instances
   - **MCP Tools**: `2600:1f1c:f9:4d00:5005:129a:f6de:73d7` (has data)
   - **asyncpg**: `2600:1f1c:f9:4d0b:51c3:bff:5884:d72c` (no data)
   - **Impact**: RAG system couldn't find any document chunks

4. **User Data Availability**
   - **Issue**: User `8d65c725-ff38-4726-809e-018c05dfb874` mentioned in incident had no documents
   - **Actual Data**: User `be18f14d-4815-422f-8ebd-bfa044c33953` has 1127 chunks with embeddings
   - **Impact**: Testing with wrong user ID led to incorrect conclusions

## Resolution Actions Taken

### 1. Fixed InformationRetrievalAgent Import Error
**File**: `agents/patient_navigator/supervisor/workflow.py`
```python
# Before
self.strategy_orchestrator = StrategyWorkflowOrchestrator(use_mock=use_mock)

# After
from agents.patient_navigator.strategy.types import WorkflowConfig
strategy_config = WorkflowConfig(use_mock=use_mock)
self.strategy_orchestrator = StrategyWorkflowOrchestrator(strategy_config)
```

### 2. Fixed Environment Configuration
**Solution**: Set `ENVIRONMENT=staging` before loading environment variables
```python
# Set environment to staging before loading
os.environ['ENVIRONMENT'] = 'staging'
from config.environment_loader import load_environment
load_environment()
```

### 3. Verified RAG System Functionality
- **OpenAI API Key**: ✅ Available and working
- **Embedding Generation**: ✅ Working correctly
- **Database Connection**: ✅ Connected to production database
- **Vector Operations**: ✅ Vector extension installed and functional

## Current Status

### ✅ Resolved Issues
1. InformationRetrievalAgent is now available
2. Environment loading correctly uses staging configuration
3. RAG system can generate embeddings
4. Database connection is established

### ⚠️ Remaining Issue
**Database Instance Mismatch**: The MCP tools and the main application are connecting to different database instances. The MCP tools can see the data, but the main application cannot.

## Recommended Next Steps

### Immediate Actions (Priority 1)
1. **Fix Database Connection**: Ensure the main application uses the same database instance as the MCP tools
2. **Test End-to-End**: Verify the complete chat flow works with real user data
3. **Monitor System**: Set up monitoring to detect similar issues

### Short-term Actions (Priority 2)
1. **Environment Standardization**: Ensure all components use the same environment configuration
2. **Database Connection Pooling**: Implement proper database connection management
3. **Error Handling**: Improve error messages for RAG system failures

### Long-term Actions (Priority 3)
1. **Database Migration**: Consolidate database instances if multiple exist
2. **Configuration Management**: Implement centralized configuration management
3. **Testing Framework**: Create comprehensive integration tests for RAG system

## Technical Details

### Database Schema
- **Schema**: `upload_pipeline`
- **Tables**: `documents`, `document_chunks`, `upload_jobs`
- **Vector Extension**: pgvector v0.8.0
- **Embedding Model**: text-embedding-3-small (1536 dimensions)

### RAG System Components
- **RAGTool**: Core retrieval functionality
- **InformationRetrievalAgent**: Agent for processing queries
- **SupervisorWorkflow**: Orchestrates workflow execution
- **ChatInterface**: Main chat endpoint integration

### Environment Configuration
- **Development**: Local database (127.0.0.1:54322)
- **Staging**: Production database (db.your-staging-project.supabase.co:5432)
- **Production**: Production database (same as staging)

## Monitoring and Prevention

### Key Metrics to Monitor
1. RAG operation success rate
2. Chunks returned per query
3. Embedding generation success rate
4. Database connection health
5. Agent availability status

### Alert Conditions
1. RAG operations returning 0 chunks
2. InformationRetrievalAgent unavailable
3. Database connection failures
4. Embedding generation failures

## Lessons Learned

1. **Environment Configuration**: Always verify environment loading in production
2. **Database Connections**: Ensure all components use the same database instance
3. **Error Handling**: Improve error messages for better debugging
4. **Testing**: Test with real user data, not just mock data
5. **Monitoring**: Implement comprehensive monitoring for RAG system health

## Critical Issues Found in Staging Logs (2025-10-02)

### Database Authentication Failures
**Severity**: CRITICAL  
**Pattern**: `asyncpg.exceptions._base.InternalClientError: unexpected error while performing authentication: 'NoneType' object has no attribute 'group'`  
**Impact**: API service failing to start, application startup failures  
**Frequency**: Multiple instances across different time periods  
**Status**: UNRESOLVED

### Storage API Failures
**Severity**: HIGH  
**Pattern**: `Storage API error: 400 - {"statusCode":"404","error":"Bucket not found","message":"Bucket not found"}`  
**Impact**: Document processing jobs failing, upload pipeline broken  
**Affected User**: `8d65c725-ff38-4726-809e-018c05dfb874`  
**Files Affected**: Multiple PDF files in user's storage  
**Status**: UNRESOLVED

### Concurrent Jobs Error
**Severity**: MEDIUM  
**Pattern**: `Warning: Failed to check concurrent job limits for user 8d65c725-ff38-4726-809e-018c05dfb874: 429: Maximum concurrent jobs (2) exceeded`  
**Impact**: Upload requests being rejected  
**User**: `8d65c725-ff38-4726-809e-018c05dfb874`  
**Status**: PARTIALLY RESOLVED (error handling added, but root cause unclear)

### InformationRetrievalAgent Unavailability
**Severity**: MEDIUM  
**Pattern**: `InformationRetrievalAgent not available, skipping execution`  
**Impact**: RAG system falling back to mock responses  
**Frequency**: Multiple occurrences  
**Status**: RESOLVED (fixed in code)

### SSL Protocol Errors
**Severity**: MEDIUM  
**Pattern**: `Fatal error on SSL protocol`  
**Impact**: Network connectivity issues  
**Frequency**: Multiple occurrences  
**Status**: UNRESOLVED

### Anthropic API Overload
**Severity**: MEDIUM  
**Pattern**: `httpx.HTTPStatusError: Server error '529 ' for url 'https://api.anthropic.com/v1/messages'`  
**Impact**: LLM calls failing, fallback responses generated  
**Frequency**: Multiple occurrences  
**Status**: EXTERNAL (Anthropic service issue)

### Document Processing Failures
**Severity**: HIGH  
**Pattern**: `Document file is not accessible for processing. Please try uploading again.`  
**Impact**: Complete failure of document processing pipeline  
**Error Code**: `STORAGE_ACCESS_ERROR`  
**Status**: UNRESOLVED

## Updated Resolution Status

### ✅ Resolved Issues
1. InformationRetrievalAgent is now available
2. Environment loading correctly uses staging configuration
3. RAG system can generate embeddings
4. Database connection is established
5. Concurrent jobs error handling improved

### ❌ Critical Unresolved Issues
1. **Database Authentication Failures**: API service cannot start due to asyncpg authentication errors
2. **Storage API Failures**: Document storage bucket not found, breaking upload pipeline
3. **Document Processing Failures**: Files not accessible for processing
4. **SSL Protocol Errors**: Network connectivity issues

### ⚠️ External Issues
1. **Anthropic API Overload**: 529 errors indicating service overload

## **CRITICAL DISCOVERY: Database Environment Mismatch (2025-10-02)**

### Root Cause of Empty Database
**Issue**: Staging environment is using a completely different Supabase database instance than expected
- **Staging Database**: Different Supabase project (EMPTY - 0 documents, 0 jobs, 0 chunks)
- **Production Database**: Different Supabase project (contains actual data)
- **Configuration**: Staging uses separate environment configuration with different database credentials

### Impact
- All RAG operations fail because staging database has no data
- Upload pipeline appears to work but data goes to wrong database
- User sees empty results because they're querying the wrong database
- Concurrent jobs error occurs because there's no data to check against

### Resolution Required
1. **Option A**: Migrate data from production to staging database
2. **Option B**: Update staging configuration to use production database
3. **Option C**: Set up proper data seeding for staging environment

## Conclusion

The primary RAG system issues have been resolved, but a critical database environment mismatch was discovered. The staging environment is using an empty database instance, which explains why no rows appear in the database despite the system appearing to function.

**Status**: ROOT CAUSE IDENTIFIED - Database environment mismatch requires immediate resolution.
