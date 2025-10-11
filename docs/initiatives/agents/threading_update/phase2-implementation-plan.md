# Threading Update Initiative - Implementation Plan

## Phase 2: Implementation

### Overview
Replace the complex threading logic in the RAG system with a simpler async/await approach, including connection pooling and concurrency limits.

### Implementation Tasks

#### Task 1: Async HTTP Client Setup
- [ ] Replace manual threading with async HTTP client
- [ ] Implement connection pooling
- [ ] Add timeout and retry logic
- [ ] Configure rate limiting

#### Task 2: Concurrency Control
- [ ] Implement semaphores for request limiting
- [ ] Add circuit breaker pattern
- [ ] Configure resource limits
- [ ] Add monitoring and metrics

#### Task 3: RAG System Refactor
- [ ] Update `_generate_embedding()` method
- [ ] Remove threading and queue logic
- [ ] Implement async/await pattern
- [ ] Update error handling

#### Task 4: Service Integration
- [ ] Update service manager integration
- [ ] Ensure async compatibility
- [ ] Update health checks
- [ ] Add performance monitoring

### Technical Specifications

#### Current Implementation Issues
```python
# Current problematic code in agents/tooling/rag/core.py
def api_call():
    # Complex threading logic
    thread = threading.Thread(target=api_call)
    thread.daemon = True
    thread.start()
    thread.join(timeout=25.0)
```

#### Proposed Async Implementation
```python
# Proposed async implementation
async def _generate_embedding(self, text: str) -> List[float]:
    async with self.http_client.post(...) as response:
        return await response.json()
```

### Dependencies

- **HTTP Client**: `httpx` or `aiohttp` for async HTTP
- **Connection Pool**: Built-in connection pooling
- **Concurrency**: `asyncio.Semaphore` for limiting
- **Monitoring**: Existing observability system

### Risk Mitigation

- **Backward Compatibility**: Ensure existing interfaces work
- **Performance**: Maintain or improve response times
- **Error Handling**: Robust async error handling
- **Testing**: Comprehensive async testing

### Timeline

- **Day 1-2**: HTTP client and connection pooling
- **Day 3-4**: Concurrency control and RAG refactor
- **Day 5**: Service integration and testing
- **Total**: 5 days
