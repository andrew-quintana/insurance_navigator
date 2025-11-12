# Phase 1 Implementation Prompt: Emergency Stabilization

**Initiative**: Agent Concurrency Remediation  
**Phase**: 1 - Emergency Stabilization  
**Timeline**: Week 1  
**Priority**: P0 - Critical  

## 🎯 **Objective**
Implement critical fixes to eliminate immediate resource exhaustion risks from unbounded concurrency patterns identified in FM-043.

## 📋 **Context & References**

**Read these documents first for complete context:**
- **FRACAS Analysis**: `@docs/incidents/fm_043/FRACAS_FM_043_UNBOUNDED_CONCURRENCY_AGENTS.md`
- **RFC Specification**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/rfc.md`  
- **Implementation TODO**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/todo.md`

## 🚨 **Critical Tasks**

### **Task 1: Fix Unbounded asyncio.gather()**
**File**: `agents/patient_navigator/strategy/workflow/performance_benchmark.py:200-202`

**Current Issue**:
```python
tasks = [run_single_workflow() for _ in range(concurrent_requests)]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Required Fix**: Add semaphore controls to limit concurrent operations to maximum 10.

**Implementation Pattern**:
```python
semaphore = asyncio.Semaphore(10)  # Configurable limit

async def limited_workflow():
    async with semaphore:
        return await run_single_workflow()

tasks = [limited_workflow() for _ in range(concurrent_requests)]  
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### **Task 2: Implement Database Connection Pooling**
**File**: `agents/tooling/rag/core.py:129-214`

**Current Issue**: New database connections created per operation without pooling.

**Required Fix**: Create `DatabasePoolManager` with connection pooling (min_size=5, max_size=20).

**Files to Create/Modify**:
- `agents/tooling/rag/database_manager.py` (new)
- Modify `agents/tooling/rag/core.py` to use pooled connections

### **Task 3: Replace Daemon Threading**
**File**: `agents/patient_navigator/information_retrieval/agent.py:614-639`

**Current Issue**: Unmanaged daemon threads without lifecycle management.

**Required Fix**: Replace with `asyncio.timeout()` and proper async patterns.

### **Task 4: Add Basic Monitoring**
**File**: `agents/shared/monitoring/concurrency_monitor.py` (new)

**Required Implementation**: Basic resource usage monitoring with logging alerts at 80% usage.

## ✅ **Success Criteria**
- [ ] Resource usage remains bounded during stress testing
- [ ] Database connections stay within configured limits  
- [ ] No daemon threads created
- [ ] Basic resource monitoring active
- [ ] All changes include proper error handling

## 🔧 **Implementation Guidelines**

1. **Commit Message Format**: Use `Addresses: FM-043` in all commits
2. **Testing**: Include unit tests for all concurrency controls
3. **Configuration**: Make all limits configurable via environment variables
4. **Logging**: Add detailed logging for resource usage
5. **Error Handling**: Ensure graceful degradation when limits reached

## 🧪 **Testing Requirements**

Create tests to verify:
- Semaphore limits enforced under stress
- Connection pools work correctly
- No resource leakage in error scenarios
- Monitoring captures accurate metrics

## 📊 **Verification Steps**

1. Run stress tests with 50+ concurrent operations
2. Monitor resource usage during testing
3. Verify connection counts never exceed limits
4. Check that no daemon threads are created
5. Confirm monitoring dashboards show real-time data

## 🚀 **Ready to Start**
All information needed for Phase 1 implementation is provided. Refer to the FRACAS document for detailed evidence and the RFC for architectural context.

**Next Phase**: Phase 2 begins after all Phase 1 success criteria are met.