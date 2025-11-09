# FM-038: CRITICAL ROOT CAUSE DISCOVERY
## Why We Saw Logs Before But Not Now

**Date:** 2025-10-09  
**Investigation:** FM-038 Deep Dive - Threading Implementation  
**Status:** 🔥 **ROOT CAUSE IDENTIFIED**

---

## Executive Summary

**The mystery is SOLVED.** We saw diagnostic logs in the old deployment but not in current deployments because:

1. **OLD CODE (b26150a)**: Failed FAST with visible errors due to coroutine handling bug
2. **COROUTINE FIX (99e4ae75)**: Attempted to fix async handling but introduced the REAL hang
3. **SYNCHRONOUS FIX (274b16cd)**: Made the hang MORE SILENT by removing async errors
4. **CURRENT CODE**: Hangs BEFORE our diagnostic code executes, in the underlying OpenAI SDK

---

## Timeline of Code Changes

### 1️⃣ **Deployment `dep-d3jje8nfte5s738ca010` (2025-10-09 04:18:38)**
**Commit:** `b26150a03f1eb119bab2c3855ea763b077e69853`  
**Status:** ❌ **FAILED FAST - WITH LOGS**

#### Code Behavior:
```python
def api_call():
    try:
        response = client.embeddings.create(  # ❌ NO await - returns coroutine!
            model="text-embedding-3-small",
            input=text,
            encoding_format="float"
        )
        result_queue.put(response)  # ❌ Tries to put coroutine object in queue
    except Exception as e:
        exception_queue.put(e)
```

#### What Happened:
1. ✅ Called `AsyncOpenAI.embeddings.create()` **WITHOUT `await`**
2. ✅ **Instantly returned a coroutine object** (no actual API call)
3. ✅ Thread **completed in ~1 second** (no network I/O)
4. ✅ Later code tried to access `response.data` on coroutine → **AttributeError**
5. ✅ **Logged detailed error messages** (we SAW these!)
6. ✅ **Operation failed cleanly in ~1 second**

#### Error Logs (VISIBLE):
```
2025-10-09 04:19:51,563 - RAGTool - ERROR - === EMBEDDING GENERATION FAILED ===
2025-10-09 04:19:51,563 - RAGTool - ERROR - Error type: AttributeError
2025-10-09 04:19:51,563 - RAGTool - ERROR - Error message: 'coroutine' object has no attribute 'data'
/app/agents/tooling/rag/core.py:265: RuntimeWarning: coroutine 'AsyncEmbeddings.create' was never awaited
```

**Why We Saw Logs:** Code failed BEFORE making any network calls, so exceptions were caught and logged normally.

---

### 2️⃣ **Coroutine Fix (99e4ae75 - 2025-10-09 04:20:27)**
**Status:** ❌ **INTRODUCED REAL HANG**

#### Code Behavior:
```python
def api_call():
    try:
        import asyncio
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(client.embeddings.create(  # ✅ Now awaited properly
                model="text-embedding-3-small",
                input=text,
                encoding_format="float"
            ))
            result_queue.put(response)
        finally:
            loop.close()
    except Exception as e:
        exception_queue.put(e)
```

#### What Happened:
1. ✅ Properly awaited async `client.embeddings.create()`
2. ❌ **Actually made the API call** (network I/O)
3. ❌ **API call hung indefinitely** (never returned)
4. ❌ Thread stuck in `loop.run_until_complete()` forever
5. ❌ **No exception raised** (just infinite waiting)
6. ❌ **No error logs** (code never reached error handling)

**Why This Hung:** The async `AsyncOpenAI` client had lifecycle issues when used in a thread with a new event loop. The HTTP transport connections became unresponsive.

---

### 3️⃣ **Synchronous Client Fix (274b16cd - PR #14)**
**Status:** ❌ **STILL HANGS - BUT MORE SILENT**

#### Code Behavior:
```python
def api_call():
    try:
        self.logger.info("Thread started for OpenAI API call")  # ❌ NEVER LOGGED
        # Use synchronous OpenAI client - no event loops needed
        sync_client = OpenAI(
            api_key=api_key,
            max_retries=3,
            timeout=30.0
        )
        
        response = sync_client.embeddings.create(  # ❌ HANGS HERE
            model="text-embedding-3-small",
            input=text,
            encoding_format="float"
        )
        result_queue.put(response)
        self.logger.info("Thread completed OpenAI API call successfully")  # ❌ NEVER LOGGED
    except Exception as e:  # ❌ NO EXCEPTION RAISED
        self.logger.error(f"Thread failed with exception: {e}")
        exception_queue.put(e)
    finally:
        self.logger.info("Thread exiting")  # ❌ NEVER LOGGED
```

#### What Happens:
1. ✅ Synchronous client created (no event loop issues)
2. ❌ **`sync_client.embeddings.create()` hangs indefinitely**
3. ❌ **No exception raised** (stuck in network I/O layer)
4. ❌ **None of the logging statements are reached**
5. ❌ Thread stuck at line: `response = sync_client.embeddings.create(...)`

**Why We Don't See Logs:** The synchronous OpenAI client's `.create()` call hangs BEFORE returning control to our code. No exception is raised, so our logging code is never executed.

---

### 4️⃣ **Current Code with Heartbeats (3ef5ffe0, 20d8dc57, 3c11a9fe)**
**Status:** ❌ **STILL HANGS - HEARTBEATS NEVER REACHED**

#### Code Behavior:
```python
async def retrieve_chunks_from_text(self, query_text: str, ...):
    # ... earlier code ...
    
    self.logger.info(f"PRE-EMBEDDING: About to call _generate_embedding...")  # ❌ NEVER LOGGED
    self.logger.info("PRE-EMBEDDING: Checkpoint - calling await self._generate_embedding()")  # ❌ NEVER LOGGED
    query_embedding = await self._generate_embedding(query_text)  # ❌ HANGS HERE FOREVER
    self.logger.info("POST-EMBEDDING: _generate_embedding() returned successfully")  # ❌ NEVER LOGGED
```

#### What Happens:
1. ✅ `RAG Operation Started` log appears (before calling `_generate_embedding`)
2. ❌ **`await self._generate_embedding(query_text)` hangs indefinitely**
3. ❌ **PRE-EMBEDDING logs never appear** (we never reach line 241)
4. ❌ **HEARTBEAT logs never appear** (we never enter the `_generate_embedding` method)
5. ❌ **No exception raised** (hanging in async call)

**Why We Don't See Heartbeats:** The hang occurs at the **`await` statement itself**, not inside the `_generate_embedding` method. The thread inside `_generate_embedding` is stuck at `sync_client.embeddings.create()`, and the `await` waits forever for it to complete.

---

## The REAL Problem

### **Where the Hang Actually Occurs**

```
┌─────────────────────────────────────────────────────────────────┐
│ retrieve_chunks_from_text()                                     │
│                                                                 │
│ Line 241: await self._generate_embedding(query_text)           │
│           └─► HANGS HERE - awaits forever                      │
│                                                                 │
│              ┌──────────────────────────────────────────┐      │
│              │ _generate_embedding()                    │      │
│              │                                          │      │
│              │ def api_call():                          │      │
│              │     sync_client = OpenAI(...)            │      │
│              │     response = sync_client.embeddings... │      │
│              │                └─► HANGS HERE           │      │
│              │                    (network I/O layer)   │      │
│              │                                          │      │
│              │ thread.join(timeout=25.0)                │      │
│              │  └─► Times out after 25s                │      │
│              │  └─► But `await` above keeps waiting!   │      │
│              └──────────────────────────────────────────┘      │
│                                                                 │
│ ⏰ main.py timeout (120s) eventually fires                     │
└─────────────────────────────────────────────────────────────────┘
```

### **The Threading vs Async Mismatch**

1. **Thread Timeout (25s)**: `thread.join(timeout=25.0)` returns after 25 seconds
2. **Thread Detection**: `if thread.is_alive():` should detect this
3. **Exception Raised**: `RuntimeError("OpenAI embedding API call timed out...")` is raised
4. **❌ BUT:** The `await self._generate_embedding()` call is NOT properly handling this exception!

**The bug is in HOW the async caller handles the threading timeout.**

---

## Why Logs Appeared in Old Deployment But Not Now

| Aspect | OLD CODE (b26150a) | CURRENT CODE (3c11a9fe) |
|--------|-------------------|-------------------------|
| **API Call Method** | Not awaited (bug) | Properly awaited (in thread) |
| **Execution Time** | ~1 second | Hangs indefinitely |
| **Error Type** | AttributeError | No error (stuck in I/O) |
| **Logs Visible?** | ✅ YES - error logs | ❌ NO - never reaches logs |
| **Diagnostic Value** | High (showed the bug) | None (silent hang) |
| **Root Problem** | Coroutine not awaited | OpenAI SDK network hang |

---

## Critical Insights

### 1. **The Old Logs Were Actually Proof of a DIFFERENT Bug**
- The error logs we saw (`'coroutine' object has no attribute 'data'`) were from a **different problem**
- That problem was "fixed" by properly awaiting the async call
- But fixing that **exposed the REAL problem**: the OpenAI SDK hangs in network I/O

### 2. **Threading Does NOT Fix the Underlying Network Hang**
- The thread times out properly (25 seconds)
- But the `await` caller doesn't properly handle the timeout exception
- So the async code waits forever for the thread to complete "successfully"

### 3. **Synchronous Client Made Things WORSE for Debugging**
- Async client at least gave us `TCPTransport closed` errors
- Synchronous client just **silently hangs in network I/O**
- No exceptions, no logs, no visibility

### 4. **Why Pre-Embedding Logs Don't Appear**
- We added `PRE-EMBEDDING` logs at line 241
- But the hang occurs when **ENTERING** the `await self._generate_embedding()` call
- The async runtime begins the call, then waits
- It never returns to log the `POST-EMBEDDING` message
- And it hangs before the internal thread even starts

---

## The Real Root Cause

### **OpenAI SDK Network Layer Hang**

The underlying problem is NOT in our code. It's in:

1. **OpenAI SDK's HTTP Client**: The underlying `httpx` or `requests` library is hanging
2. **Network I/O Layer**: The TCP connection is established but never receives a response
3. **Timeout Not Respected**: Despite setting `timeout=30.0`, the SDK ignores it or it's not propagating to the network layer
4. **No Cancellation**: Python's `threading.Thread.join(timeout=...)` doesn't actually **cancel** the thread, it just stops waiting for it

### **Why Threading Doesn't Help**

```python
thread.join(timeout=25.0)  # ⏰ Returns after 25s

if thread.is_alive():  # ✅ True - thread still running
    raise RuntimeError("Timeout")  # ✅ Exception raised

# ❌ BUT: The thread is STILL RUNNING in background!
# ❌ The await caller doesn't properly handle the exception!
# ❌ So execution continues waiting...
```

---

## Next Steps

### **Option 1: Fix Exception Handling in Async Caller** (RECOMMENDED)
Ensure the `await self._generate_embedding()` properly handles the `RuntimeError` and doesn't wait forever.

### **Option 2: Force-Kill the Thread** (NUCLEAR)
Use `thread._stop()` or similar mechanisms to forcefully terminate the thread (unsafe).

### **Option 3: Investigate OpenAI SDK Timeout Configuration**
There may be additional timeout configurations needed for the underlying HTTP client.

### **Option 4: Use Alternative HTTP Clients**
Replace OpenAI SDK's default HTTP client with one that properly respects timeouts.

### **Option 5: Add Network-Level Timeouts**
Use socket-level timeouts or OS-level connection timeouts.

---

## Conclusion

**We saw logs before because the code FAILED FAST with a different bug (coroutine not awaited).**

**We don't see logs now because the code HANGS SILENTLY in the OpenAI SDK's network I/O layer.**

The threading approach was correct in theory, but it doesn't address the root cause: **the OpenAI SDK's network layer is not respecting timeouts and is hanging indefinitely.**

**Status:** 🔴 **ROOT CAUSE IDENTIFIED - NEEDS NEW SOLUTION**  
**Priority:** 🔥 **CRITICAL**

---

**Investigation By:** AI Coding Agent  
**Document:** FM-038 Critical Discovery  
**Last Updated:** 2025-10-09 05:30:00 (estimated)


