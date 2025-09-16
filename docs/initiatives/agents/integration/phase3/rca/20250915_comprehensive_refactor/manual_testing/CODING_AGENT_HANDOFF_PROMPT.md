# Coding Agent Handoff: Upload Endpoint Consolidation Investigation

## 🎯 **Mission**
Investigate and consolidate the multiple upload endpoints in the Insurance Navigator system into a single, mature, production-ready upload endpoint.

## 📋 **Current System State**

### **Services Running:**
- **API Server**: `http://localhost:8000` (FastAPI with uvicorn)
- **Enhanced Worker**: Running and processing jobs successfully
- **Database**: Local Supabase (`127.0.0.1:54322`) with `upload_pipeline` schema
- **Frontend**: Next.js application (implied)

### **Critical Issue:**
The upload pipeline endpoints are returning "405 Method Not Allowed" errors despite being properly registered in FastAPI. This is blocking end-to-end testing and preventing the system from being production-ready.

## 🔍 **Investigation Required**

### **1. Upload Endpoint Audit**
The system currently has multiple upload endpoints that need investigation:

1. **`/upload-document-backend`** - Legacy endpoint with authentication
2. **`/upload-document-backend-no-auth`** - Legacy endpoint without authentication  
3. **`/api/upload-pipeline/upload`** - New upload pipeline endpoint (router-based)
4. **`/api/upload-pipeline/upload-file/{job_id}`** - Direct file upload endpoint (router-based)
5. **`/api/v2/upload`** - Removed conflicting endpoint

### **2. Frontend Integration Analysis**
- **File**: `ui/components/DocumentUpload.tsx`
- **File**: `ui/components/DocumentUploadServerless.tsx`
- **File**: `ui/app/chat/page.tsx`

**Questions to Answer:**
- Which endpoints are actually being called by the frontend?
- What is the expected flow: frontend → API → blob storage → worker?
- Are there any hardcoded endpoint URLs that need updating?

### **3. Endpoint Functionality Analysis**
For each endpoint, determine:
- **Purpose**: What does this endpoint do?
- **Authentication**: Does it require auth or not?
- **Input**: What parameters does it accept?
- **Output**: What does it return?
- **Storage**: How does it handle file storage?
- **Worker Integration**: How does it trigger worker processing?

## 🚨 **Critical Issues to Resolve**

### **FM-016: Upload-File Endpoint 405 Method Not Allowed**
- **Status**: ACTIVE
- **Severity**: HIGH
- **Issue**: All `/api/upload-pipeline/*` endpoints return "405 Method Not Allowed"
- **Evidence**: Endpoints are registered in FastAPI but not accessible
- **Blocking**: End-to-end upload flow testing

### **FM-017: Root Cause Analysis - Upload Endpoint Issues**
- **Status**: ACTIVE
- **Severity**: CRITICAL
- **Issue**: Router not actually loaded despite being included in main.py
- **Evidence**: Router imports work, routes show in FastAPI app, but endpoints return 405
- **Suspected Cause**: CORS middleware or route registration issue

## 📚 **Documentation References**

### **Key Files to Review:**
1. **`docs/initiatives/agents/integration/phase3/rca/20250915_comprehensive_refactor/manual_testing/FAILURE_MODES_LOG.md`**
   - Complete failure mode documentation
   - Root cause analysis of current issues
   - Evidence and investigation findings

2. **`docs/initiatives/agents/integration/phase3/rca/20250915_comprehensive_refactor/manual_testing/MANUAL_TESTING_GUIDE.md`**
   - Testing procedures and infrastructure
   - Known failure modes and workarounds
   - System health metrics

3. **`main.py`** (lines 88-95)
   - Router inclusion code
   - CORS middleware configuration
   - Current endpoint definitions

4. **`api/upload_pipeline/endpoints/upload.py`**
   - Upload router implementation
   - Upload-file endpoint logic
   - Database access patterns

## 🎯 **Success Criteria**

### **Immediate Goals:**
1. **Resolve 405 Errors**: Fix the "Method Not Allowed" errors for upload-pipeline endpoints
2. **Identify Canonical Endpoint**: Determine which endpoint should be the single upload endpoint
3. **Test End-to-End Flow**: Verify complete upload flow works (frontend → API → storage → worker)

### **Consolidation Goals:**
1. **Single Upload Endpoint**: Consolidate to one mature upload endpoint
2. **Clean Architecture**: Remove unused/duplicate endpoints
3. **Frontend Integration**: Update frontend to use consolidated endpoint
4. **Documentation**: Update all documentation to reflect new endpoint structure

## 🛠 **Technical Context**

### **Current Architecture:**
```
Frontend (Next.js) 
    ↓ POST /upload-document-backend-no-auth
API Server (FastAPI)
    ↓ Creates job + signed URL
Blob Storage (Supabase)
    ↓ File uploaded
Enhanced Worker
    ↓ Processes job
Database (PostgreSQL)
    ↓ Stores chunks/embeddings
```

### **Database Schema:**
- **`upload_pipeline.documents`** - Document metadata
- **`upload_pipeline.upload_jobs`** - Job processing queue
- **`upload_pipeline.document_chunks`** - Processed document chunks
- **`storage.objects`** - Blob storage metadata

### **Environment Variables:**
- **`ENVIRONMENT=development`**
- **`DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres?sslmode=disable`**
- **`SUPABASE_URL=http://localhost:54321`**
- **`SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`**

## 🔧 **Investigation Steps**

### **Step 1: Resolve 405 Errors**
1. Check if API server is running the latest code
2. Verify router imports and registration
3. Test with different HTTP methods and headers
4. Check CORS configuration and middleware
5. Consider implementing endpoint directly in main.py as workaround

### **Step 2: Frontend Analysis**
1. Search frontend code for upload endpoint calls
2. Identify which endpoints are actually used
3. Document the expected request/response format
4. Test frontend integration with working endpoints

### **Step 3: Endpoint Consolidation**
1. Compare functionality of all upload endpoints
2. Design single, mature upload endpoint
3. Plan migration strategy
4. Implement consolidated endpoint
5. Update frontend to use new endpoint
6. Remove deprecated endpoints

## 📝 **Expected Deliverables**

1. **Investigation Report**: Document findings about current upload endpoints
2. **Consolidated Endpoint**: Single, mature upload endpoint implementation
3. **Frontend Updates**: Updated frontend code to use consolidated endpoint
4. **Documentation**: Updated failure modes log and manual testing guide
5. **Testing**: Verified end-to-end upload flow working

## 🚀 **Getting Started**

1. **Read the documentation** in the referenced files
2. **Start the system** using the environment variables provided
3. **Reproduce the 405 errors** to understand the current state
4. **Investigate the root cause** using the evidence provided
5. **Implement the solution** following the success criteria

## ⚠️ **Important Notes**

- The enhanced worker is working correctly and processing jobs
- The database schema is properly set up
- The issue is specifically with the upload-pipeline endpoints returning 405
- CORS middleware is configured and may be interfering
- The system needs to be production-ready for manual testing

## 📞 **Support**

If you encounter issues or need clarification:
- Review the failure modes log for detailed investigation history
- Check the manual testing guide for system procedures
- All evidence and findings are documented in the referenced files

---

**Handoff Date**: 2025-09-16  
**Priority**: HIGH  
**Estimated Effort**: 2-4 hours  
**Dependencies**: None (all services running)
