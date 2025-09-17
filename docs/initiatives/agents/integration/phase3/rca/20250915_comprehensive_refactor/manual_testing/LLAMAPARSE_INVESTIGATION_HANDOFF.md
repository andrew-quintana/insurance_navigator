# LlamaParse Investigation Handoff - Coding Agent Prompt

## 🎯 **Mission Statement**

You are tasked with investigating and resolving LlamaParse integration issues that are preventing the Insurance Navigator from processing real document content. The system is currently falling back to mock services, generating generic test content instead of parsing actual PDF documents, which severely impacts the RAG tool's ability to provide relevant responses.

## 📋 **Current System State**

### **Critical Issue Summary**
- **Problem**: Enhanced worker falls back to mock LlamaParse service instead of real API
- **Impact**: Documents contain generic test content instead of actual PDF content
- **Consequence**: RAG tool similarity scores are very low (0.001-0.047) because chunks don't contain relevant information
- **User Impact**: Queries like "what is my deductible" return no results despite document containing deductible information

### **Evidence of Mock Service Usage**
```bash
# Enhanced worker logs show mock service fallback
"Real service 'llamaparse' unavailable, using mock service"
"LlamaParse job submitted successfully"
"parse_job_id": "mock_parse_3ba00e4a-8afa-4213-b910-9ac48e672a94"

# Generated chunks contain generic content
Chunk 0: "# Test Document"
Chunk 1: "This is a test document with some content."
Chunk 2: "Some more content here."
```

### **Real Document Content (What Should Be Parsed)**
```bash
# Actual PDF content contains deductible information
"Limited coverage for out-of-network services with higher co-pay and deductible requirements."
```

### **RAG Tool Results (Correctly Working)**
```bash
# Similarity scores are very low due to irrelevant content
Similarity scores: 0.001-0.047 (all below 0.3 threshold)
Retrieved 0 chunks (correctly - no relevant content)
```

## 🔍 **Investigation Context**

### **Previous Investigation Findings**
1. **LlamaParse API Key**: Not set in environment variables (`LLAMAPARSE_API_KEY` is empty)
2. **Service Router**: Falls back to mock service when real service is unavailable
3. **Document Processing**: PDF contains actual insurance information but chunks contain generic test content
4. **User Query**: "what is my deductible" should match content about "deductible requirements" in section 3.2

### **System Architecture**
- **Service Router**: `backend/shared/external/service_router.py` - Manages real vs mock service selection
- **LlamaParse Real Service**: `backend/shared/external/llamaparse_real.py` - Real API implementation
- **Worker Config**: `backend/shared/config/worker_config.py` - Loads environment variables
- **Enhanced Worker**: `backend/workers/enhanced_base_worker.py` - Uses service router

### **Configuration Flow**
1. `WorkerConfig.from_environment()` loads `LLAMACLOUD_API_KEY` or `LLAMAPARSE_API_KEY`
2. Service router checks `real_service.is_available()` 
3. If unavailable, falls back to mock service in development mode
4. Mock service generates generic test content

## 🎯 **Investigation Objectives**

### **Primary Goals**
1. **Identify Root Cause**: Why is LlamaParse real service unavailable?
2. **Fix Authentication**: Ensure proper API key configuration
3. **Verify API Connectivity**: Test actual LlamaParse API calls
4. **Validate Document Processing**: Confirm real PDF content is parsed
5. **Update Documentation**: Record findings and solutions

### **Secondary Goals**
1. **Improve Error Handling**: Better logging for service availability issues
2. **Add Health Monitoring**: Proactive detection of service failures
3. **Create Test Suite**: Automated testing for LlamaParse integration

## 🔧 **Investigation Steps**

### **Step 1: Environment Configuration Audit**
```bash
# Check current environment variables
echo "LLAMAPARSE_API_KEY: $LLAMAPARSE_API_KEY"
echo "LLAMACLOUD_API_KEY: $LLAMACLOUD_API_KEY"

# Verify .env.development file
cat .env.development | grep -i llama

# Check worker config loading
python -c "
from backend.shared.config.worker_config import WorkerConfig
config = WorkerConfig.from_environment()
print(f'LlamaParse API Key: {config.llamaparse_api_key[:10]}...' if config.llamaparse_api_key else 'LlamaParse API Key: NOT SET')
"
```

### **Step 2: Service Router Debugging**
```bash
# Test service router directly
python -c "
import asyncio
from backend.shared.external.service_router import ServiceRouter
from backend.shared.config.worker_config import WorkerConfig

async def test_service_router():
    config = WorkerConfig.from_environment()
    router = ServiceRouter(config={
        'llamaparse_config': {
            'api_key': config.llamaparse_api_key,
            'api_url': config.llamaparse_api_url
        }
    })
    
    # Test service availability
    service = await router.get_service('llamaparse')
    print(f'Service type: {type(service).__name__}')
    print(f'Is available: {await service.is_available()}')
    
    # Test health check
    health = await service.get_health()
    print(f'Health status: {health}')

asyncio.run(test_service_router())
"
```

### **Step 3: LlamaParse API Direct Testing**
```bash
# Test LlamaParse API directly
python -c "
import asyncio
import httpx
import os

async def test_llamaparse_api():
    api_key = os.getenv('LLAMAPARSE_API_KEY') or os.getenv('LLAMACLOUD_API_KEY')
    if not api_key:
        print('❌ No LlamaParse API key found')
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        try:
            response = await client.post('https://api.cloud.llamaindex.ai/api/v1/parsing/upload', 
                                       json={}, headers=headers, timeout=10)
            print(f'API Response: {response.status_code} - {response.text[:200]}')
        except Exception as e:
            print(f'API Error: {e}')

asyncio.run(test_llamaparse_api())
"
```

### **Step 4: Real Service Integration Testing**
```bash
# Test real service with actual document
python -c "
import asyncio
from backend.shared.external.llamaparse_real import RealLlamaParseService
from backend.shared.config.worker_config import WorkerConfig

async def test_real_service():
    config = WorkerConfig.from_environment()
    service = RealLlamaParseService(api_key=config.llamaparse_api_key)
    
    # Test availability
    print(f'Service available: {await service.is_available()}')
    
    # Test health check
    health = await service.get_health()
    print(f'Health: {health}')
    
    # Test with actual document
    if await service.is_available():
        try:
            result = await service.parse_document(
                file_path='examples/simulated_insurance_document.pdf',
                webhook_url='http://localhost:8000/api/upload-pipeline/webhook/llamaparse/test-job',
                correlation_id='test-correlation'
            )
            print(f'Parse result: {result}')
        except Exception as e:
            print(f'Parse error: {e}')

asyncio.run(test_real_service())
"
```

## 🚨 **Potential Root Causes**

### **1. Missing API Key**
- **Symptom**: `LLAMAPARSE_API_KEY` environment variable not set
- **Investigation**: Check `.env.development` file and environment loading
- **Solution**: Set proper API key in environment

### **2. Incorrect API Key Format**
- **Symptom**: API key exists but authentication fails
- **Investigation**: Verify key format and permissions
- **Solution**: Update key format or regenerate

### **3. API Endpoint Issues**
- **Symptom**: API key valid but endpoints return errors
- **Investigation**: Test different API endpoints and versions
- **Solution**: Update endpoint URLs or API version

### **4. Network/Connectivity Issues**
- **Symptom**: API calls timeout or fail
- **Investigation**: Test network connectivity and firewall rules
- **Solution**: Fix network configuration

### **5. Service Health Check Logic**
- **Symptom**: Service reports as unavailable when it should be available
- **Investigation**: Review `is_available()` and `get_health()` methods
- **Solution**: Fix health check logic

### **6. Configuration Loading Issues**
- **Symptom**: Environment variables not loaded correctly
- **Investigation**: Check `WorkerConfig.from_environment()` method
- **Solution**: Fix configuration loading

## 📊 **Success Criteria**

### **Immediate Success**
- [ ] LlamaParse real service reports as available
- [ ] Enhanced worker uses real service instead of mock
- [ ] Document chunks contain actual PDF content
- [ ] RAG tool retrieves relevant chunks for "what is my deductible"

### **Validation Tests**
```bash
# Test 1: Service Availability
python -c "
import asyncio
from backend.shared.external.service_router import ServiceRouter
from backend.shared.config.worker_config import WorkerConfig

async def test():
    config = WorkerConfig.from_environment()
    router = ServiceRouter(config={'llamaparse_config': config.get_llamaparse_config()})
    service = await router.get_service('llamaparse')
    print(f'Service type: {type(service).__name__}')
    print(f'Is available: {await service.is_available()}')

asyncio.run(test())
"

# Test 2: Document Processing
python -c "
import asyncio
from backend.shared.external.service_router import ServiceRouter
from backend.shared.config.worker_config import WorkerConfig

async def test():
    config = WorkerConfig.from_environment()
    router = ServiceRouter(config={'llamaparse_config': config.get_llamaparse_config()})
    service = await router.get_service('llamaparse')
    
    result = await service.parse_document('examples/simulated_insurance_document.pdf')
    print(f'Parse result: {result}')

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

After successful investigation and resolution:
- Enhanced worker uses real LlamaParse service
- Documents are parsed with actual content
- RAG tool retrieves relevant chunks for insurance queries
- System provides accurate responses to user questions
- Upload pipeline works end-to-end with real document processing

## 📞 **Support Resources**

- **LlamaParse Documentation**: https://docs.llamaindex.ai/en/stable/llamaparse/
- **API Reference**: https://api.cloud.llamaindex.ai/docs
- **Current Codebase**: Insurance Navigator repository
- **Previous Investigation**: This document and `FAILURE_MODES_LOG.md`

---

**Remember**: The goal is not just to fix the immediate issue, but to create a robust, reliable LlamaParse integration that will work consistently in both development and production environments.
