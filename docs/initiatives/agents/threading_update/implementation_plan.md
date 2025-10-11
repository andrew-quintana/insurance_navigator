# Threading Update Implementation Plan

## Overview

This document provides the detailed implementation plan for the Threading Update Initiative, following the RFC outlined in `rfc.md`.

## Phase 1: Scope Update and Research ✅

### 1.1 Current State Analysis ✅

**Completed Analysis:**
- **File**: `agents/tooling/rag/core.py` (lines 300-690)
- **Method**: `_generate_embedding()` 
- **Issues Identified**:
  - Manual thread management with 20+ heartbeat logs
  - Queue-based communication between threads
  - No connection pooling
  - Complex timeout handling
  - Hanging failures with 5+ concurrent requests

### 1.2 Best Practices Research ✅

**Key Findings:**
- Use `asyncio` instead of manual threading for I/O-bound operations
- Implement connection pooling with `aiohttp`
- Use `asyncio.Semaphore` for concurrency control
- Replace manual thread management with `async/await` patterns
- Use `asyncio.wait_for()` for timeout handling

## Phase 2: Implementation Plan

### 2.1 Architecture Changes

**Current Architecture:**
```
Request → Thread Creation → Queue Communication → Manual Timeout → Response
```

**Proposed Architecture:**
```
Request → Async Function → Connection Pool → Semaphore Control → Response
```

### 2.2 Implementation Steps

#### Step 1: Create Async HTTP Client with Connection Pooling

**File**: `agents/tooling/rag/core.py`

**Changes:**
```python
import aiohttp
import asyncio
from typing import Optional

class RAGTool:
    def __init__(self, ...):
        # ... existing initialization ...
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.semaphore: Optional[asyncio.Semaphore] = None
        self.max_concurrent_requests = 10  # Configurable limit
    
    async def _initialize_async_resources(self):
        """Initialize async HTTP client and semaphore"""
        if self.http_session is None:
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=30,  # Per-host connection limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
            )
            timeout = aiohttp.ClientTimeout(total=30.0)
            self.http_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
    
    async def _cleanup_async_resources(self):
        """Clean up async resources"""
        if self.http_session:
            await self.http_session.close()
            self.http_session = None
        self.semaphore = None
```

#### Step 2: Replace Threading with Async/Await

**Current Implementation (to be replaced):**
```python
def _generate_embedding(self, text: str) -> List[float]:
    # 20+ heartbeat logs
    # Manual thread creation
    # Queue-based communication
    # Complex timeout handling
```

**New Implementation:**
```python
async def _generate_embedding(self, text: str) -> List[float]:
    """Generate embedding using async OpenAI API call"""
    await self._initialize_async_resources()
    
    async with self.semaphore:  # Concurrency control
        try:
            # Prepare request data
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "text-embedding-3-small",
                "input": text,
                "encoding_format": "float"
            }
            
            # Make async API call with timeout
            async with asyncio.wait_for(
                self.http_session.post(
                    "https://api.openai.com/v1/embeddings",
                    headers=headers,
                    json=data
                ),
                timeout=30.0
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    embedding = result["data"][0]["embedding"]
                    self.logger.info(f"Successfully generated embedding: {len(embedding)} dimensions")
                    return embedding
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"OpenAI API error {response.status}: {error_text}")
                    
        except asyncio.TimeoutError:
            self.logger.error("OpenAI embedding API call timed out after 30 seconds")
            raise RuntimeError("OpenAI embedding API call timed out")
        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {e}")
            raise
```

#### Step 3: Update Calling Methods

**Update `retrieve_chunks_from_text` method:**
```python
async def retrieve_chunks_from_text(self, query: str, operation_metrics: Optional[RAGOperationMetrics] = None) -> List[ChunkWithContext]:
    """Retrieve chunks using async embedding generation"""
    try:
        # Generate embedding asynchronously
        query_embedding = await self._generate_embedding(query)
        
        # Rest of the method remains the same (database operations)
        chunks = await self.retrieve_chunks(query_embedding, operation_metrics)
        
        return chunks
        
    except Exception as e:
        self.logger.error(f"RAG retrieval failed: {e}")
        raise
```

#### Step 4: Update Service Initialization

**Update service manager initialization:**
```python
# In main.py or service manager
async def initialize_rag_service():
    """Initialize RAG service with async resources"""
    rag_tool = RAGTool(user_id="system", config=RetrievalConfig.default())
    await rag_tool._initialize_async_resources()
    return rag_tool

async def cleanup_rag_service(rag_tool):
    """Clean up RAG service async resources"""
    await rag_tool._cleanup_async_resources()
```

### 2.3 Configuration Updates

**Add to environment configuration:**
```python
# In config files
RAG_MAX_CONCURRENT_REQUESTS = 10
RAG_CONNECTION_POOL_SIZE = 100
RAG_CONNECTION_TIMEOUT = 30.0
```

## Phase 3: Validation Plan

### 3.1 Development Environment Testing

**Prerequisites:**
- Development environment already deployed
- Supabase containers running
- Database accessible

**Test Script:**
```python
# test_concurrent_async.py
import asyncio
import aiohttp
import time

async def test_concurrent_requests():
    """Test concurrent requests to verify no hanging"""
    
    # Get auth token
    async with aiohttp.ClientSession() as session:
        login_data = {
            "email": "sendaqmail@gmail.com",
            "password": "xasdez-katjuc-zyttI2"
        }
        
        async with session.post("http://localhost:8000/auth/login", json=login_data) as response:
            if response.status == 200:
                token_data = await response.json()
                token = token_data["access_token"]
            else:
                print(f"Login failed: {response.status}")
                return
    
    # Test concurrent requests
    async def make_request(session, token, request_id):
        headers = {"Authorization": f"Bearer {token}"}
        data = {"message": f"Test request {request_id}: What is my deductible?"}
        
        start_time = time.time()
        try:
            async with session.post("http://localhost:8000/chat", headers=headers, json=data) as response:
                end_time = time.time()
                if response.status == 200:
                    result = await response.json()
                    print(f"Request {request_id}: SUCCESS ({end_time - start_time:.2f}s)")
                    return True
                else:
                    print(f"Request {request_id}: FAILED ({response.status})")
                    return False
        except Exception as e:
            end_time = time.time()
            print(f"Request {request_id}: ERROR ({end_time - start_time:.2f}s) - {e}")
            return False
    
    # Test with increasing concurrency
    for num_requests in [1, 2, 3, 5, 10]:
        print(f"\n=== Testing {num_requests} concurrent requests ===")
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                make_request(session, token, i+1) 
                for i in range(num_requests)
            ]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            success_count = sum(1 for r in results if r is True)
            print(f"Results: {success_count}/{num_requests} successful in {end_time - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_concurrent_requests())
```

### 3.2 Performance Metrics

**Key Metrics to Track:**
- **Response Time**: Average response time per request
- **Concurrency**: Maximum concurrent requests without hanging
- **Resource Usage**: Memory and CPU usage
- **Error Rate**: Timeout and connection errors
- **Success Rate**: Percentage of successful requests

**Success Criteria:**
- ✅ No hanging failures with 5+ concurrent requests
- ✅ Response times < 30 seconds for all requests
- ✅ Success rate > 95% for concurrent requests
- ✅ Memory usage stable under load

### 3.3 Validation Checklist

**Development Testing:**
- [ ] Single request works (baseline)
- [ ] 2-3 concurrent requests work (current working range)
- [ ] 5+ concurrent requests work (current failure point)
- [ ] 10+ concurrent requests work (stress test)
- [ ] Error handling works correctly
- [ ] Timeout handling works correctly
- [ ] Resource cleanup works correctly

## Phase 4: Production Deployment

### 4.1 Pre-deployment Checklist

- [ ] All development tests pass
- [ ] Performance metrics meet criteria
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Rollback plan prepared

### 4.2 Deployment Strategy

**Branch**: `feature/threading-update`
**Testing**: Deploy to staging environment first
**Monitoring**: Watch for hanging failures and performance issues
**Rollback Plan**: Keep current implementation as fallback

### 4.3 Production Validation

**Health Checks:**
- [ ] `/health` endpoint responds correctly
- [ ] RAG service health check passes
- [ ] Database health check passes

**Load Testing:**
- [ ] Test with production-like load
- [ ] Monitor response times
- [ ] Check for hanging failures
- [ ] Verify error handling

**User Testing:**
- [ ] Chat endpoint functionality
- [ ] RAG chunk retrieval
- [ ] Response quality
- [ ] User experience

## Implementation Timeline

### Week 1: Research and Design ✅
- [x] Complete current state analysis
- [x] Research async/await best practices
- [x] Design new architecture
- [x] Create detailed implementation plan

### Week 2: Implementation
- [ ] Create async HTTP client with connection pooling
- [ ] Replace threading with async/await
- [ ] Update calling methods
- [ ] Update service initialization

### Week 3: Testing and Validation
- [ ] Unit tests for async functions
- [ ] Integration testing in development
- [ ] Performance testing with concurrent requests
- [ ] Fix any issues found during testing

### Week 4: Deployment
- [ ] Deploy to staging environment
- [ ] Production deployment
- [ ] Monitor system performance
- [ ] Document lessons learned

## Risk Assessment

### High Risk
- **Breaking Changes**: Async conversion might break existing functionality
- **Performance Regression**: New implementation might be slower
- **Production Issues**: Deployment might cause service disruption

### Mitigation Strategies
- **Incremental Changes**: Implement changes gradually
- **Comprehensive Testing**: Test thoroughly in development
- **Rollback Plan**: Keep current implementation as backup
- **Monitoring**: Watch production metrics closely

## Success Criteria

### Technical Success
- ✅ No hanging failures with 5+ concurrent requests
- ✅ Response times improved or maintained
- ✅ Reduced code complexity
- ✅ Better error handling

### Business Success
- ✅ Improved system reliability
- ✅ Better user experience
- ✅ Reduced maintenance burden
- ✅ Foundation for future scalability

## Next Steps

1. **Start Implementation**: Begin with Step 1 (Create Async HTTP Client)
2. **Test Incrementally**: Test each step before moving to the next
3. **Monitor Performance**: Track metrics throughout implementation
4. **Prepare Rollback**: Keep current implementation as fallback
5. **Document Changes**: Update documentation as changes are made
