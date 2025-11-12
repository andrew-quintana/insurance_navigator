# Phase 2 Implementation Prompt: Pattern Modernization

**Initiative**: Agent Concurrency Remediation  
**Phase**: 2 - Pattern Modernization  
**Timeline**: Week 2-3  
**Priority**: P1 - High  

## 🎯 **Objective**
Modernize async/await patterns and improve resource management across all agent workflows.

## 📋 **Context & References**

**Read these documents first for complete context:**
- **FRACAS Analysis**: `@docs/incidents/fm_043/FRACAS_FM_043_UNBOUNDED_CONCURRENCY_AGENTS.md`
- **RFC Specification**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/rfc.md`  
- **Implementation TODO**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/todo.md`

**Prerequisites**: Phase 1 must be completed and verified before starting Phase 2.

## 🔄 **Modernization Tasks**

### **Task 1: Replace Deprecated get_event_loop()**
**File**: `agents/patient_navigator/input_processing/handler.py:84`

**Current Issue**:
```python
loop = asyncio.get_event_loop()  # DEPRECATED
audio_data = await loop.run_in_executor(None, self._capture_audio_sync, timeout)
```

**Required Fix**: Replace with `asyncio.get_running_loop()`.

**Implementation Pattern**:
```python
loop = asyncio.get_running_loop()  # CURRENT
audio_data = await loop.run_in_executor(None, self._capture_audio_sync, timeout)
```

**Scope**: Search entire codebase for `get_event_loop()` usage and replace all instances.

### **Task 2: Migrate to Async HTTP Clients**
**File**: `agents/patient_navigator/information_retrieval/agent.py:98`

**Current Issue**: Synchronous HTTP calls inside threads.

**Required Fix**: Replace with `httpx.AsyncClient` for all external API calls.

**Implementation Pattern**:
```python
# OLD: Synchronous HTTP in threads
def api_call():
    resp = client.messages.create(...)  # Synchronous

# NEW: Async HTTP client
async def call_llm(self, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            json=payload,
            headers=headers
        )
        return response.json()
```

### **Task 3: Implement Async Context Managers**
**Files**: All components with resource management needs

**Required Implementation**: Add proper `__aenter__` and `__aexit__` methods for resource cleanup.

**Pattern**:
```python
class ResourceManager:
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
```

### **Task 4: Add Rate Limiting**
**File**: `agents/shared/rate_limiting/limiter.py` (new)

**Required Implementation**: Configurable rate limiting for external APIs.

**Configuration**:
- OpenAI: 60 requests/minute
- Anthropic: 50 requests/minute
- Configurable via environment variables

**Implementation Pattern**: Token bucket or sliding window rate limiter.

## ✅ **Success Criteria**
- [ ] Zero deprecated async API usage across codebase
- [ ] All external HTTP calls use async clients
- [ ] Proper resource cleanup in all error scenarios
- [ ] Rate limiting active for all external APIs
- [ ] No performance regression from changes

## 🔧 **Implementation Guidelines**

1. **Backward Compatibility**: Maintain existing interfaces during migration
2. **Error Handling**: Ensure all async patterns handle timeouts properly
3. **Testing**: Update all tests to use async patterns
4. **Configuration**: Make rate limits configurable
5. **Documentation**: Update API documentation for new patterns

## 🧪 **Testing Requirements**

### **Compatibility Tests**
- Verify all existing functionality works with new patterns
- Test error scenarios with proper async handling
- Validate timeout behavior with async clients

### **Performance Tests**  
- Ensure no regression in response times
- Validate rate limiting doesn't impact normal operations
- Test resource cleanup under load

### **Integration Tests**
- Test async HTTP clients with real external APIs
- Validate rate limiting with burst traffic
- Test context manager cleanup in error scenarios

## 📊 **Verification Steps**

1. **Code Review**: Verify no deprecated patterns remain
2. **Load Testing**: Test system under concurrent load
3. **Rate Limit Testing**: Verify external APIs respect limits
4. **Resource Testing**: Confirm proper cleanup in all scenarios
5. **Performance Baseline**: Compare against Phase 1 performance

## 🔍 **Migration Checklist**

### **Async Pattern Updates**
- [ ] Replace all `asyncio.get_event_loop()` with `get_running_loop()`
- [ ] Convert all synchronous HTTP calls to async clients
- [ ] Implement async context managers for resource management
- [ ] Add proper async error handling throughout

### **Resource Management**
- [ ] Implement rate limiting for OpenAI API calls
- [ ] Implement rate limiting for Anthropic API calls  
- [ ] Add configurable timeouts for all external calls
- [ ] Ensure proper resource cleanup in error paths

### **Testing Updates**
- [ ] Update unit tests for async patterns
- [ ] Add integration tests for HTTP clients
- [ ] Add performance regression tests
- [ ] Validate error handling in async context

## 🚀 **Ready to Start**
Phase 1 emergency fixes must be completed and validated before beginning Phase 2. This phase focuses on systematic modernization of async patterns.

**Next Phase**: Phase 3 begins after all Phase 2 success criteria are met and performance baselines are established.