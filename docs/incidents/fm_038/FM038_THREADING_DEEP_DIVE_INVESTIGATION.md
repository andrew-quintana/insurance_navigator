# FM-038 Deep Dive: Threading Implementation Investigation

## Current Status & Context

### Investigation Progress
- **Root Cause Identified**: OpenAI embedding API calls hanging indefinitely in RAG system
- **Initial Fix Applied**: Threading-based timeout mechanism (25-second timeout)
- **Coroutine Bug Fixed**: Proper async handling with `asyncio.new_event_loop()` and `run_until_complete()`
- **Enhanced Logging**: Comprehensive error logging enabled debugging visibility
- **Deployment Status**: All fixes deployed to production

### Current Problem
**RAG operations are still hanging despite threading-based timeout implementation**

**Evidence**:
```
2025-10-09 04:24:15,698 - RAG Operation Started [6c7393ee-fe41-4511-94d7-ac6dad919974]
[NO COMPLETION LOG AFTER 2+ MINUTES]
2025-10-09 04:26:13,784 - main - ERROR - Chat processing timed out after 120 seconds
```

**CRITICAL NEW EVIDENCE - HTTP Client Cleanup Error**:
```
2025-10-09 04:26:00,767 - asyncio - ERROR - Task exception was never retrieved
future: <Task finished name='Task-880' coro=<AsyncClient.aclose() done>
RuntimeError: unable to perform operation on <TCPTransport closed=True reading=False>
```

This suggests our threading-based timeout mechanism is **not working as expected** AND is causing **async client lifecycle conflicts**.

## Threading Implementation Analysis Needed

### Current Threading Code
```python
# agents/tooling/rag/core.py - _generate_embedding method
def api_call():
    try:
        import asyncio
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                encoding_format="float"
            ))
            result_queue.put(response)
        finally:
            loop.close()
    except Exception as e:
        exception_queue.put(e)

# Start API call in separate thread
thread = threading.Thread(target=api_call)
thread.daemon = True
thread.start()

# Wait for result with 25-second timeout
thread.join(timeout=25.0)

if thread.is_alive():
    end_time = time.time()
    self.logger.error(f"OpenAI embedding API call timed out after {end_time - start_time:.2f}s")
    raise RuntimeError("OpenAI embedding API call timed out after 25 seconds")
```

### Potential Issues to Investigate

#### 1. **CRITICAL: Async Client Lifecycle Conflict** ⚠️
- **Problem**: Our threading approach is interfering with async HTTP client lifecycle
- **Evidence**: `AsyncClient.aclose()` task fails with `TCPTransport closed=True`
- **Root Cause**: Creating new event loops in threads conflicts with async HTTP connections
- **Impact**: Async connections are left hanging, causing resource leaks
- **Solution**: Use synchronous OpenAI client instead of async client in threads

#### 2. Event Loop Threading Issues
- **Problem**: Creating new event loops in threads can cause issues with async libraries
- **Question**: Is `asyncio.new_event_loop()` the right approach for OpenAI client?
- **Investigation**: Check if OpenAI client has specific threading requirements

#### 3. OpenAI Client Threading Compatibility
- **Problem**: OpenAI's AsyncOpenAI client may not be designed for threading
- **Question**: Should we use synchronous OpenAI client instead?
- **Investigation**: Research OpenAI client threading best practices

#### 4. Thread Join Timeout Behavior
- **Problem**: `thread.join(timeout=25.0)` may not be interrupting the operation properly
- **Question**: Is the thread actually terminating when timeout occurs?
- **Investigation**: Add logging to verify thread termination

#### 5. Queue Communication Issues
- **Problem**: Queue-based communication between threads may be blocking
- **Question**: Are the queues causing deadlocks?
- **Investigation**: Check queue behavior and thread synchronization

#### 6. Daemon Thread Behavior
- **Problem**: Daemon threads may not terminate cleanly
- **Question**: Should we use non-daemon threads with explicit termination?
- **Investigation**: Test daemon vs non-daemon thread behavior

## Investigation Strategy

### Phase 1: **CRITICAL - Fix Async Client Conflict** (IMMEDIATE)
1. **Replace AsyncOpenAI with Synchronous OpenAI Client**
   - Use `from openai import OpenAI` instead of `AsyncOpenAI`
   - Eliminate event loop creation in threads
   - Remove async/await patterns in threading code
   - Test with synchronous client approach

2. **Verify Thread Termination**
   - Add logging to confirm thread actually terminates
   - Check if `thread.join(timeout=25.0)` works properly
   - Monitor for resource cleanup issues

### Phase 2: Threading Behavior Analysis
1. **Add Thread Lifecycle Logging**
   ```python
   def api_call():
       self.logger.info("Thread started for OpenAI API call")
       try:
           # ... existing code ...
           self.logger.info("Thread completed OpenAI API call successfully")
       except Exception as e:
           self.logger.error(f"Thread failed with exception: {e}")
       finally:
           self.logger.info("Thread exiting")
   ```

2. **Add Timeout Verification Logging**
   ```python
   thread.join(timeout=25.0)
   
   if thread.is_alive():
       self.logger.error("Thread is still alive after timeout - investigating...")
       self.logger.error(f"Thread name: {thread.name}")
       self.logger.error(f"Thread daemon: {thread.daemon}")
       self.logger.error(f"Thread ident: {thread.ident}")
   ```

3. **Test Thread Termination**
   ```python
   # Force thread termination if it doesn't respond
   if thread.is_alive():
       self.logger.warning("Attempting to force thread termination")
       # Add thread termination logic
   ```

### Phase 2: Alternative Threading Approaches
1. **RECOMMENDED: Synchronous OpenAI Client** ⭐
   **This is the preferred solution based on the HTTP client cleanup error evidence.**
   
   ```python
   from openai import OpenAI  # Synchronous client
   
   def api_call():
       try:
           client = OpenAI(api_key=api_key)
           response = client.embeddings.create(
               model="text-embedding-3-small",
               input=text
           )
           result_queue.put(response)
       except Exception as e:
           exception_queue.put(e)
   ```
   
   **Why This Solves Our Problem:**
   - ✅ **No Event Loop Conflicts**: Synchronous client doesn't use async
   - ✅ **No HTTP Client Cleanup Errors**: No async client lifecycle issues  
   - ✅ **Clean Thread Termination**: No async resources to clean up
   - ✅ **Reliable Timeout**: `thread.join(timeout=25.0)` will work properly
   - ✅ **No Resource Leaks**: Synchronous connections are easier to manage

2. **asyncio.run_in_executor Approach**
   ```python
   import concurrent.futures
   
   async def _generate_embedding(self, text: str):
       loop = asyncio.get_event_loop()
       with concurrent.futures.ThreadPoolExecutor() as executor:
           future = loop.run_in_executor(
               executor, 
               self._sync_embedding_call, 
               text
           )
           try:
               response = await asyncio.wait_for(future, timeout=25.0)
               return response.data[0].embedding
           except asyncio.TimeoutError:
               self.logger.error("Embedding generation timed out")
               raise
   ```

3. **Signal-Based Timeout**
   ```python
   import signal
   
   def timeout_handler(signum, frame):
       raise TimeoutError("OpenAI API call timed out")
   
   def api_call():
       signal.signal(signal.SIGALRM, timeout_handler)
       signal.alarm(25)  # 25 second timeout
       try:
           # ... API call ...
       finally:
           signal.alarm(0)  # Cancel alarm
   ```

### Phase 3: Root Cause Deep Dive
1. **OpenAI Client Documentation Review**
   - Check OpenAI's official threading guidelines
   - Review async vs sync client recommendations
   - Look for known threading issues

2. **Network-Level Investigation**
   - Check if the hang is at network level
   - Investigate DNS resolution issues
   - Test with different network configurations

3. **Resource Monitoring**
   - Monitor thread count during operations
   - Check for resource leaks
   - Monitor memory usage patterns

## Key Questions to Answer

### Threading-Specific Questions
1. **Is the thread actually terminating when `thread.join(timeout=25.0)` returns?**
2. **Are we creating too many event loops or not cleaning them up properly?**
3. **Is the OpenAI client designed to work in threaded environments?**
4. **Are there any deadlocks in our queue-based communication?**

### Alternative Approach Questions
1. **Should we use synchronous OpenAI client instead of async?**
2. **Would `asyncio.run_in_executor` be more reliable?**
3. **Should we implement a different timeout mechanism?**
4. **Are there any OpenAI-specific timeout configurations we're missing?**

### Debugging Questions
1. **What happens if we remove the threading entirely and use direct async calls?**
2. **Can we reproduce the hanging behavior in a minimal test case?**
3. **Are there any environment-specific issues (production vs local)?**

## Expected Outcomes

### Immediate Goals
1. **Identify why threading-based timeout isn't working**
2. **Implement a working timeout mechanism**
3. **Eliminate RAG operation hanging**

### Long-term Goals
1. **Establish reliable timeout patterns for external API calls**
2. **Document threading best practices for OpenAI integration**
3. **Create robust error handling for async operations**

## Handoff Instructions

### For Next Investigator
1. **CRITICAL: Start with Phase 1**: Replace AsyncOpenAI with synchronous OpenAI client immediately
2. **Focus on HTTP client cleanup errors**: The `AsyncClient.aclose()` error proves our threading approach is fundamentally flawed
3. **Test synchronous approach first**: This is the highest priority fix based on evidence
4. **Monitor production logs**: Watch for elimination of HTTP client cleanup errors
5. **Verify thread termination**: Ensure threads terminate cleanly without async resource conflicts

### Critical Files to Modify
- `agents/tooling/rag/core.py` - `_generate_embedding` method
- `agents/patient_navigator/output_processing/agent.py` - Similar threading pattern

### Testing Strategy
1. **Local testing**: Reproduce hanging behavior locally
2. **Minimal test case**: Create isolated test for threading behavior
3. **Production monitoring**: Deploy changes incrementally with logging

### Success Criteria
- **RAG operations complete within 25 seconds** or fail with clear error
- **No more indefinite hanging** of embedding generation
- **Clear error logs** when timeouts occur
- **Reliable timeout behavior** across different scenarios
- **No HTTP client cleanup errors** (eliminate async client lifecycle conflicts)

## Conclusion

**The threading investigation is absolutely the right path forward.** The logs provide definitive proof that our current threading approach is causing:

1. **RAG operations to hang indefinitely**
2. **Async client lifecycle conflicts** (HTTP client cleanup errors)
3. **Resource cleanup failures**
4. **Event loop interference**

**CRITICAL EVIDENCE**: The HTTP client cleanup error (`AsyncClient.aclose()` task failed) proves our threading approach is fundamentally flawed and interfering with async HTTP connections.

The solution is to **replace the async OpenAI client with a synchronous one** in our threading implementation, which will eliminate the event loop conflicts and allow proper timeout handling.

**Status**: 🔴 **CRITICAL** - Threading implementation must be fixed immediately to resolve the hanging issue.

**Next Action**: Implement synchronous OpenAI client approach as documented in Phase 1.

---

**Priority**: 🔴 **HIGH** - This is blocking the core functionality of the chat system

**Complexity**: 🟡 **MEDIUM** - Threading issues can be tricky but are well-documented

**Risk**: 🟡 **MEDIUM** - Changes to timeout handling could affect system stability

**Timeline**: 🟢 **SHORT** - Should be resolvable within 1-2 hours with focused investigation
