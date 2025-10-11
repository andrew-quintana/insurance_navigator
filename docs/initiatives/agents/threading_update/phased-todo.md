# Threading Update Initiative - MVP Todo List

## MVP Implementation Plan

### Step 1: Minimal Async Conversion
- [ ] Convert `_generate_embedding()` method to async
- [ ] Replace threading with `httpx.AsyncClient`
- [ ] Remove queue and thread management code
- [ ] Remove manual thread creation and management
- [ ] Test basic functionality (single request)

### Step 2: Concurrent Testing
- [ ] Test with 2-3 concurrent requests
- [ ] Test with 5+ concurrent requests (hanging scenario)
- [ ] Verify no timeouts or hangs
- [ ] Measure response times
- [ ] Validate system stability

### Step 3: Production Deployment
- [ ] Deploy MVP fix to production
- [ ] Monitor for hanging issues
- [ ] Validate concurrent request handling
- [ ] Confirm fix effectiveness
- [ ] Monitor for 24 hours

## Success Criteria

### Performance Requirements
- [ ] No hanging with 5+ concurrent requests
- [ ] Response times under 10 seconds
- [ ] System remains stable under load
- [ ] Existing functionality preserved

### Reliability Requirements
- [ ] No deadlocks or resource exhaustion
- [ ] Proper error handling
- [ ] System stability under stress
- [ ] Graceful degradation if needed

## Files to Modify

### Primary Files
- [ ] `agents/tooling/rag/core.py` - Main RAG implementation
  - Convert `_generate_embedding()` to async
  - Replace threading with async/await
  - Remove queue management
  - Update error handling

### Test Files
- [ ] Create concurrent request test script
- [ ] Test with various load levels
- [ ] Validate fix effectiveness

## Implementation Notes

### What We're Doing (MVP)
- ✅ Fix the hanging issue with minimal changes
- ✅ Convert threading to async/await
- ✅ Test with concurrent requests
- ✅ Deploy to production

### What We're NOT Doing (Out of Scope)
- ❌ Complex architecture redesign
- ❌ Extensive connection pooling optimization
- ❌ Advanced circuit breaker patterns
- ❌ Comprehensive monitoring overhaul
- ❌ Performance optimization beyond fixing hangs

## Timeline

- **Step 1**: 1-2 hours (Async conversion)
- **Step 2**: 1 hour (Testing)
- **Step 3**: 1 hour (Deployment)

**Total Estimated Duration**: 3-4 hours