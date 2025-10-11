# RFC: Threading Update for RAG System

## Status: COMPLETED (Phase 1 - Research Complete)

## Summary

This RFC proposes replacing the complex threading logic in the RAG system with a modern async/await approach using httpx, connection pooling, and proper concurrency control to resolve hanging failures under concurrent load.

## Problem Statement

### Current Issues
- **Hanging Failure**: System hangs completely with 5+ concurrent requests
- **Resource Contention**: Multiple threads competing for HTTP connections
- **Thread Pool Exhaustion**: No limits on concurrent threads
- **Complex Threading Logic**: Manual thread management with queues and heartbeat logging
- **Blocking Operations**: Synchronous OpenAI client wrapped in threads within async context

### Current Implementation Analysis
The current `_generate_embedding()` method in `agents/tooling/rag/core.py` (lines 279-690) uses a problematic pattern:

```python
# Current problematic implementation
async def _generate_embedding(self, text: str) -> List[float]:
    # Creates new thread for each request
    thread = threading.Thread(target=api_call)
    thread.daemon = True
    thread.start()
    thread.join(timeout=25.0)  # Blocking wait
    
    # Complex queue-based result handling
    result_queue = queue.Queue()
    exception_queue = queue.Queue()
    # ... extensive heartbeat logging and error handling
```

**Problems Identified:**
1. **Thread-per-request**: Creates new thread for each embedding request
2. **No connection pooling**: Each thread creates new HTTP connections
3. **Resource exhaustion**: No limits on concurrent threads
4. **Complex error handling**: Manual queue-based exception handling
5. **Blocking in async context**: `thread.join()` blocks the event loop
6. **No circuit breaker**: No protection against cascading failures

### Impact
- **Production Failure**: Complete system failure under concurrent load
- **User Experience**: Requests timeout after 60 seconds
- **Scalability**: System cannot handle multiple users simultaneously
- **Resource Waste**: Excessive thread creation and HTTP connection overhead

## Proposed Solution

### Architecture Overview
Replace threading with async/await using:
- **httpx**: Modern async HTTP client with connection pooling
- **asyncio.Semaphore**: Concurrency control
- **Circuit Breaker**: Failure protection
- **Proper error handling**: Async exception management

### Key Components

#### 1. Async HTTP Client with Connection Pooling
```python
import httpx
from typing import Optional

class AsyncOpenAIClient:
    def __init__(self, api_key: str, max_connections: int = 10):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(
                max_keepalive_connections=max_connections,
                max_connections=max_connections
            )
        )
        self.api_key = api_key
        self.semaphore = asyncio.Semaphore(max_connections)
    
    async def generate_embedding(self, text: str) -> List[float]:
        async with self.semaphore:
            response = await self.client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "text-embedding-3-small",
                    "input": text,
                    "encoding_format": "float"
                }
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
```

#### 2. Circuit Breaker Pattern
```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        return (self.last_failure_time and 
                datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout))
    
    def _on_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

#### 3. Refactored RAG Embedding Method
```python
async def _generate_embedding(self, text: str) -> List[float]:
    """Generate embedding using async OpenAI client with proper error handling."""
    if not text or not text.strip():
        raise ValueError("Empty text cannot be embedded")
    
    try:
        # Use circuit breaker for resilience
        embedding = await self.circuit_breaker.call(
            self.openai_client.generate_embedding, text
        )
        
        # Validate embedding
        if not self._validate_embedding(embedding, "query"):
            raise ValueError("Generated embedding failed validation")
        
        return embedding
        
    except Exception as e:
        self.logger.error(f"Embedding generation failed: {e}")
        raise
```

### Performance Benefits
- **Connection Reuse**: HTTP connection pooling reduces overhead
- **Resource Control**: Semaphore limits concurrent requests
- **Non-blocking**: No thread.join() blocking the event loop
- **Failure Resilience**: Circuit breaker prevents cascading failures
- **Simplified Code**: Removes complex threading and queue logic

## Implementation Plan

### Phase 2: Implementation (4-5 days)
1. **Day 1**: Implement AsyncOpenAIClient with httpx
2. **Day 2**: Add CircuitBreaker implementation
3. **Day 3**: Refactor _generate_embedding() method
4. **Day 4**: Update service integration and error handling
5. **Day 5**: Testing and validation

### Phase 3: Testing (2-3 days)
1. **Unit Tests**: Test async embedding generation
2. **Load Tests**: Test concurrent request handling
3. **Integration Tests**: Test with service manager

### Phase 4: Deployment (1 day)
1. **Production Deployment**: Deploy with monitoring
2. **Validation**: Verify fix effectiveness

## Risks and Mitigation

### Risks
1. **Breaking Changes**: Async interface changes
2. **Performance Regression**: New implementation slower
3. **Error Handling**: Different exception patterns

### Mitigation
1. **Backward Compatibility**: Maintain existing interfaces
2. **Performance Testing**: Benchmark before/after
3. **Comprehensive Testing**: Unit, integration, and load tests
4. **Gradual Rollout**: Deploy with feature flags
5. **Monitoring**: Enhanced observability during transition

## Success Criteria

### Functional Requirements
- [ ] System handles 5+ concurrent requests without hanging
- [ ] Response times < 5 seconds for single requests
- [ ] Response times < 10 seconds for 5 concurrent requests
- [ ] Error rate < 1% under normal load
- [ ] Circuit breaker activates on API failures

### Non-Functional Requirements
- [ ] Code complexity reduced by 50%
- [ ] Memory usage reduced by 30%
- [ ] Thread count remains stable under load
- [ ] HTTP connection reuse > 80%

### Monitoring Metrics
- [ ] Request latency percentiles (p50, p95, p99)
- [ ] Concurrent request handling
- [ ] Error rates and types
- [ ] Circuit breaker state changes
- [ ] Resource utilization (CPU, memory, connections)

## Timeline

- **Phase 1 (Research)**: ✅ Completed (2 days)
- **Phase 2 (Implementation)**: 4-5 days
- **Phase 3 (Testing)**: 2-3 days  
- **Phase 4 (Deployment)**: 1 day
- **Total**: 9-11 days

## Code Examples

### Before (Current Threading Implementation)
```python
# Complex threading with queues and heartbeat logging
async def _generate_embedding(self, text: str) -> List[float]:
    result_queue = queue.Queue()
    exception_queue = queue.Queue()
    
    def api_call():
        try:
            sync_client = OpenAI(api_key=api_key, timeout=30.0)
            response = sync_client.embeddings.create(...)
            result_queue.put(response)
        except Exception as e:
            exception_queue.put(e)
    
    thread = threading.Thread(target=api_call)
    thread.daemon = True
    thread.start()
    thread.join(timeout=25.0)  # BLOCKING!
    
    if thread.is_alive():
        raise RuntimeError("Timeout")
    
    # Complex queue checking...
```

### After (Proposed Async Implementation)
```python
# Clean async implementation with connection pooling
async def _generate_embedding(self, text: str) -> List[float]:
    try:
        embedding = await self.circuit_breaker.call(
            self.openai_client.generate_embedding, text
        )
        return embedding
    except Exception as e:
        self.logger.error(f"Embedding generation failed: {e}")
        raise
```

---

**Next Steps**: Proceed to Phase 2 implementation with the detailed architecture and code examples provided above.
