# File Upload and LlamaParse Resolution Handoff - Coding Agent Prompt

## 🎯 **Mission Statement**

You are tasked with resolving the root cause of document processing failures in the Insurance Navigator. The issue is **NOT** with LlamaParse itself, but with the upstream file upload process that prevents files from being stored in Supabase storage, causing LlamaParse to generate mock content instead of parsing actual documents.

## 📋 **Current System State**

### **Root Cause Identified**
- **Primary Issue**: FM-023 - Raw file upload failure (files not stored in Supabase storage)
- **Secondary Issue**: FM-025 - LlamaParse generates mock content due to missing files
- **Impact**: RAG tool cannot retrieve relevant content because chunks contain generic test data
- **User Impact**: Queries like "what is my deductible" return no results despite document containing deductible information

### **Evidence of File Upload Failure**
```bash
# Document shows parsed status but file doesn't exist
Document: 7ff4ca89-0b1e-5bc3-880d-69a788401d89 - Status: parsed
Raw Path: files/user/61f1d766-14c7-4bbd-8dbe-0b32e7ca3ef0/raw/b78980ba_aa77e516.pdf

# File not found in storage
curl -X GET "http://127.0.0.1:54321/storage/v1/object/files/user/61f1d766-14c7-4bbd-8dbe-0b32e7ca3ef0/raw/b78980ba_aa77e516.pdf"
# Returns: {"statusCode":"404","error":"not_found","message":"Object not found"}

# Mock content generated due to missing file
"Mock parsed content from files/user/61f1d766-14c7-4bbd-8dbe-0b32e7ca3ef0/raw/b78980ba_aa77e516.pdf"
```

### **LlamaParse Status (Working Correctly)**
```bash
# API key is present and valid
✅ LlamaParse API key found: llx-<REDACTED>...

# Local PDF file exists and is readable
✅ PDF file exists: examples/simulated_insurance_document.pdf
📄 File size: 1782 bytes
📖 File readable, first 100 bytes: b'%PDF-1.3\n3 0 obj\n<</Type /Page\n/Parent 1 0 R\n/Reso'...
```

### **Real Document Content (What Should Be Parsed)**
```bash
# Actual PDF content contains deductible information
"Limited coverage for out-of-network services with higher co-pay and deductible requirements."
```

## 🔍 **Investigation Context**

### **Root Cause Analysis**
1. **File Upload Failure**: Frontend upload to Supabase storage is failing silently
2. **Signed URL Issues**: May be related to JWT authentication or CORS problems
3. **Mock Content Generation**: LlamaParse generates mock content when no file exists
4. **Pipeline Impact**: This prevents the entire document processing pipeline from working

### **System Architecture**
- **Frontend Upload**: Uses signed URLs to upload files to Supabase storage
- **Signed URL Generation**: `api/upload_pipeline/endpoints/upload.py` - `_generate_signed_url()`
- **Storage Manager**: `backend/shared/storage/storage_manager.py` - Handles Supabase storage operations
- **LlamaParse Service**: Working correctly but has no files to parse
- **Enhanced Worker**: Processes jobs but gets mock content due to missing files

### **Upload Flow**
1. Frontend requests signed URL from `/api/upload-pipeline/upload`
2. API generates signed URL for Supabase storage
3. Frontend uploads file to signed URL
4. **FAILURE POINT**: File upload fails silently
5. LlamaParse tries to parse non-existent file
6. Mock content is generated instead

## 🎯 **Resolution Objectives**

### **Primary Goals**
1. **Fix File Upload**: Resolve FM-023 - Raw file upload failure
2. **Test LlamaParse**: Verify LlamaParse works with actual files
3. **End-to-End Validation**: Confirm complete pipeline works
4. **Update Documentation**: Record findings and solutions

### **Secondary Goals**
1. **Improve Error Handling**: Better logging for upload failures
2. **Add Upload Monitoring**: Proactive detection of upload issues
3. **Create Test Suite**: Automated testing for file upload and parsing

## 🔧 **Resolution Steps**

### **Step 1: File Upload Investigation**
```bash
# Test signed URL generation
python -c "
import asyncio
from api.upload_pipeline.endpoints.upload import _generate_signed_url

async def test_signed_url():
    try:
        url = await _generate_signed_url('files/user/test/raw/test.pdf', 3600)
        print(f'Generated signed URL: {url}')
    except Exception as e:
        print(f'Error generating signed URL: {e}')

asyncio.run(test_signed_url())
"

# Test file upload to signed URL
curl -X PUT "http://127.0.0.1:54321/storage/v1/object/upload/files/user/test/raw/test.pdf" \
  -H "Authorization: Bearer ${SUPABASE_JWT_TOKEN}" \
  -F "file=@examples/simulated_insurance_document.pdf"
```

### **Step 2: Frontend Upload Testing**
```bash
# Test complete upload flow from frontend perspective
python test_production_upload_flow.py

# Check if file was actually uploaded
curl -X GET "http://127.0.0.1:54321/storage/v1/object/files/user/{user_id}/raw/{filename}.pdf" \
  -H "Authorization: Bearer ${SUPABASE_JWT_TOKEN}"
```

### **Step 3: LlamaParse Integration Testing**
```bash
# Test LlamaParse with actual file (once upload is fixed)
python -c "
import asyncio
from backend.shared.external.llamaparse_real import RealLlamaParseService
from backend.shared.config.worker_config import WorkerConfig

async def test_llamaparse_with_real_file():
    config = WorkerConfig.from_environment()
    service = RealLlamaParseService(api_key=config.llamaparse_api_key)
    
    # Test with local file first
    try:
        result = await service.parse_document(
            file_path='examples/simulated_insurance_document.pdf',
            webhook_url='http://localhost:8000/api/upload-pipeline/webhook/llamaparse/test-job',
            correlation_id='test-correlation'
        )
        print(f'Parse result: {result}')
    except Exception as e:
        print(f'Parse error: {e}')

asyncio.run(test_llamaparse_with_real_file())
"
```

### **Step 4: End-to-End Pipeline Testing**
```bash
# Test complete pipeline once both issues are fixed
python -c "
import asyncio
from agents.tooling.rag.core import RAGTool, RetrievalConfig

async def test_rag_with_real_content():
    user_id = 'bc3ca830-8806-4f6c-ab94-a0da85bf20b0'  # Test user
    config = RetrievalConfig(similarity_threshold=0.3, max_chunks=5)
    rag_tool = RAGTool(user_id=user_id, config=config)
    
    chunks = await rag_tool.retrieve_chunks_from_text('what is my deductible')
    print(f'Retrieved {len(chunks)} chunks')
    for chunk in chunks:
        print(f'Chunk: {chunk.content[:100]}... (similarity: {chunk.similarity:.4f})')

asyncio.run(test_rag_with_real_content())
"
```

## 🚨 **Potential Root Causes**

### **1. JWT Authentication Issues**
- **Symptom**: Frontend upload fails due to invalid JWT token
- **Investigation**: Check JWT token generation and validation
- **Solution**: Fix JWT token handling in upload process

### **2. CORS Configuration Problems**
- **Symptom**: Browser blocks file upload due to CORS policy
- **Investigation**: Check CORS headers in API responses
- **Solution**: Configure proper CORS headers for file upload

### **3. Signed URL Format Issues**
- **Symptom**: Generated signed URLs are malformed or invalid
- **Investigation**: Test signed URL generation and format
- **Solution**: Fix signed URL generation logic

### **4. Supabase Storage Configuration**
- **Symptom**: Storage bucket not properly configured for uploads
- **Investigation**: Check bucket permissions and policies
- **Solution**: Fix storage bucket configuration

### **5. Frontend Upload Implementation**
- **Symptom**: Frontend code has bugs in file upload logic
- **Investigation**: Review frontend upload implementation
- **Solution**: Fix frontend upload code

### **6. Network/Connectivity Issues**
- **Symptom**: File upload requests fail due to network issues
- **Investigation**: Test network connectivity to Supabase storage
- **Solution**: Fix network configuration or retry logic

## 📊 **Success Criteria**

### **Immediate Success**
- [ ] Files are successfully uploaded to Supabase storage
- [ ] Raw files are accessible via storage API (no 404 errors)
- [ ] LlamaParse processes actual PDF content instead of mock content
- [ ] Document chunks contain real insurance information
- [ ] RAG tool retrieves relevant chunks for "what is my deductible"

### **Validation Tests**
```bash
# Test 1: File Upload Success
curl -X GET "http://127.0.0.1:54321/storage/v1/object/files/user/{user_id}/raw/{filename}.pdf" \
  -H "Authorization: Bearer {service_role_key}"
# Should return: PDF content (not 404 error)

# Test 2: LlamaParse with Real File
python -c "
import asyncio
from backend.shared.external.llamaparse_real import RealLlamaParseService
from backend.shared.config.worker_config import WorkerConfig

async def test():
    config = WorkerConfig.from_environment()
    service = RealLlamaParseService(api_key=config.llamaparse_api_key)
    
    result = await service.parse_document('examples/simulated_insurance_document.pdf')
    print(f'Parse result: {result}')
    # Should contain actual PDF content, not mock content

asyncio.run(test())
"

# Test 3: RAG Tool with Real Content
python -c "
import asyncio
from agents.tooling.rag.core import RAGTool, RetrievalConfig

async def test():
    user_id = 'bc3ca830-8806-4f6c-ab94-a0da85bf20b0'  # Test user
    config = RetrievalConfig(similarity_threshold=0.3, max_chunks=5)
    rag_tool = RAGTool(user_id=user_id, config=config)
    
    chunks = await rag_tool.retrieve_chunks_from_text('what is my deductible')
    print(f'Retrieved {len(chunks)} chunks')
    for chunk in chunks:
        print(f'Chunk: {chunk.content[:100]}... (similarity: {chunk.similarity:.4f})')
    # Should retrieve chunks with high similarity scores (>0.3)

asyncio.run(test())
"
```

## 📝 **Documentation Requirements**

### **Failure Mode Update**
Update `FAILURE_MODES_LOG.md` with:
- Root cause analysis
- Solution implementation
- Evidence of resolution
- Prevention measures

### **Code Documentation**
- Add comments explaining LlamaParse integration
- Document API key requirements
- Add troubleshooting guide

### **Configuration Guide**
- Document required environment variables
- Provide setup instructions
- Include testing procedures

## 🔄 **Next Steps After Resolution**

1. **Test End-to-End Pipeline**: Upload document → Parse → Chunk → Embed → RAG
2. **Performance Monitoring**: Add metrics for LlamaParse API calls
3. **Error Handling**: Improve error messages for API failures
4. **Automated Testing**: Create tests for LlamaParse integration
5. **Documentation**: Update setup guides and troubleshooting docs

## 🚀 **Expected Outcome**

After successful resolution:
- Files are successfully uploaded to Supabase storage
- LlamaParse processes actual PDF documents instead of generating mock content
- Document chunks contain real insurance information
- RAG tool retrieves relevant chunks for insurance queries
- System provides accurate responses to user questions
- Complete upload pipeline works end-to-end with real document processing

## 📞 **Support Resources**

- **Supabase Storage Documentation**: https://supabase.com/docs/guides/storage
- **LlamaParse Documentation**: https://docs.llamaindex.ai/en/stable/llamaparse/
- **Current Codebase**: Insurance Navigator repository
- **Previous Investigation**: This document and `FAILURE_MODES_LOG.md`
- **Key Files**: 
  - `api/upload_pipeline/endpoints/upload.py` - Signed URL generation
  - `backend/shared/storage/storage_manager.py` - Storage operations
  - `test_production_upload_flow.py` - Upload testing

---

**Remember**: The primary issue is file upload failure (FM-023), not LlamaParse integration. Fix the upload process first, then verify LlamaParse works with actual files.
