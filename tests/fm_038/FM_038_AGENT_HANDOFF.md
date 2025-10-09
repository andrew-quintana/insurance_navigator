# FM-038: Agent Handoff - Zero Chunks Retrieved Investigation

**Date:** 2025-10-09  
**Status:** 🔴 **CRITICAL - INVESTIGATION REQUIRED**  
**Priority:** P0 - Blocking all RAG functionality  
**Handoff From:** Previous AI Agent  
**Handoff To:** Next AI Agent

---

## Executive Summary

**Current Problem:** RAG operations are completing successfully but returning **0 chunks** in all cases, despite users having uploaded documents. This suggests either:
1. A fundamental issue with the chunk retrieval logic
2. Threading issues affecting database queries
3. Embedding generation silently failing
4. Database connection or query problems

**Latest Production Evidence (2025-10-09 05:26:15 - 05:26:18):**
```
RAG Operation Started [f287de61-81be-4e4d-99a1-486e29849b1f]
RAG Operation SUCCESS - Duration:3140.0ms Chunks:0/0 Tokens:0
```

**Key Observation:** Operations complete in ~3 seconds (not hanging), but retrieve 0 chunks every time.

---

## Context You Need

### 1. What We've Been Working On
- **Original Issue**: RAG operations hanging indefinitely (120 seconds timeout)
- **Root Cause Found**: OpenAI SDK network layer hangs when making embedding API calls
- **Threading Fix Applied**: Implemented 25-second timeout with synchronous OpenAI client
- **Current Status**: No longer hanging, BUT now returning 0 chunks

### 2. Key Files
- `agents/tooling/rag/core.py` - Main RAG implementation
  - `retrieve_chunks_from_text()` - Method being called by agents (line 216)
  - `_generate_embedding()` - Embedding generation with threading (line 269)
  - `retrieve_chunks()` - Database query for similar chunks (line 78)
- `agents/tooling/rag/observability.py` - Performance monitoring
- `tests/fm_038/` - All investigation documentation

### 3. Recent Changes
- **Commit `8ddd6afd`**: Added comprehensive checkpoint logging (CHECKPOINT A-H)
- **Commit `3c11a9fe`**: Fixed duplicate RAG logs with propagate=False
- **Commit `20d8dc57`**: Added PRE/POST-EMBEDDING checkpoints
- **Commit `274b16cd`**: Replaced AsyncOpenAI with synchronous OpenAI client

---

## The Problem: Zero Chunks Retrieved

### Evidence from Production Logs

**Request 1 (05:26:15):**
```
RAG Operation Started [f287de61-81be-4e4d-99a1-486e29849b1f]
user_id: cae3b3ec-b355-4509-bd4e-0f7da8cb2858
query_text: "To access mental health services..."
RAG Operation SUCCESS - Duration:3140.0ms Chunks:0/0 Tokens:0
```

**Request 2 (05:26:55):**
```
RAG Operation Started [d0e71573-eb15-43d3-885c-8b9cc520c3a1]
user_id: cae3b3ec-b355-4509-bd4e-0f7da8cb2858
query_text: "Does the policy provide coverage for ambulance..."
[No completion log yet - may have started hanging again]
```

### Critical Questions to Answer

1. **Is embedding generation working?**
   - Are we successfully generating embeddings?
   - Are embeddings the correct dimension (1536)?
   - Are they valid float arrays?

2. **Is the database query working?**
   - Are there actually chunks in the database for this user?
   - Is the SQL query correct?
   - Are embeddings stored correctly in the database?

3. **Is the similarity threshold too high?**
   - Current threshold: 0.5
   - Are there chunks below threshold that would match?
   - What's the actual similarity distribution?

4. **Is threading interfering with database queries?**
   - Are async database queries working correctly?
   - Is the connection pool healthy?
   - Are queries timing out silently?

---

## What We Know Works

✅ **Performance Monitoring**: `RAG Operation Started` logs appear correctly  
✅ **Database Connection**: Service starts successfully, connection pool initialized  
✅ **Fast Execution**: Operations complete in ~3 seconds (not hanging on all requests)  
✅ **User ID**: Valid user ID being passed (`cae3b3ec-b355-4509-bd4e-0f7da8cb2858`)

---

## What We DON'T Know

❓ **Are there chunks in the database for this user?**  
❓ **Is embedding generation succeeding silently?**  
❓ **Are the new CHECKPOINT logs appearing?** (No evidence yet)  
❓ **Is the database query returning results?**  
❓ **What are the actual similarity scores?**

---

## Your Investigation Tasks

### Task 1: Verify Database Has Chunks ⭐ **START HERE**

**Why:** If there are no chunks, we can't retrieve anything!

**How:**
```sql
-- Check if user has any documents
SELECT COUNT(*) FROM documents WHERE user_id = 'cae3b3ec-b355-4509-bd4e-0f7da8cb2858';

-- Check if user has any chunks with embeddings
SELECT COUNT(*) 
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.document_id
WHERE d.user_id = 'cae3b3ec-b355-4509-bd4e-0f7da8cb2858'
AND dc.embedding IS NOT NULL;

-- Check sample similarity scores
SELECT 1 - (dc.embedding <=> '[0.1,0.2,...]'::vector(1536)) as similarity
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.document_id
WHERE d.user_id = 'cae3b3ec-b355-4509-bd4e-0f7da8cb2858'
AND dc.embedding IS NOT NULL
ORDER BY dc.embedding <=> '[0.1,0.2,...]'::vector(1536)
LIMIT 5;
```

**Expected Outcome:**
- If COUNT = 0: User has no documents/chunks → Need to investigate upload pipeline
- If COUNT > 0: Chunks exist → Continue to Task 2

### Task 2: Check If CHECKPOINT Logs Are Appearing

**Why:** Our new checkpoint logging should show execution flow, but we haven't seen them yet.

**What to Look For in Production Logs:**
```
CHECKPOINT A: retrieve_chunks_from_text() method ENTRY
CHECKPOINT B: Query text validation passed
CHECKPOINT C: About to call performance_monitor.start_operation()
CHECKPOINT D: performance_monitor.start_operation() returned successfully
CHECKPOINT E: About to enter try block
CHECKPOINT F: Inside try block, before embedding generation
CHECKPOINT G: About to await self._generate_embedding()
CHECKPOINT H: await self._generate_embedding() returned!
```

**Expected Outcome:**
- If no checkpoints appear: Code is hanging before method entry (investigate caller)
- If checkpoints appear up to G: Hanging at embedding generation
- If all checkpoints appear: Embedding works, problem is in retrieval

### Task 3: Add Embedding Validation Logging

**Why:** We need to know if embeddings are being generated correctly.

**What to Add:**
```python
# In _generate_embedding() after getting response
embedding = response.data[0].embedding
self.logger.info(f"EMBEDDING VALIDATION: Generated embedding with {len(embedding)} dimensions")
self.logger.info(f"EMBEDDING VALIDATION: First 5 values: {embedding[:5]}")
self.logger.info(f"EMBEDDING VALIDATION: All values are floats: {all(isinstance(x, (int, float)) for x in embedding)}")
self.logger.info(f"EMBEDDING VALIDATION: No NaN values: {not any(math.isnan(x) for x in embedding)}")
```

**Expected Outcome:**
- Should see 1536 dimensions
- First 5 values should be floats (e.g., [0.123, -0.456, ...])
- All checks should pass

### Task 4: Add Database Query Logging

**Why:** We need to see what the SQL query is actually doing.

**What to Add in `retrieve_chunks()` method:**
```python
# Before the SQL query
self.logger.info(f"DATABASE QUERY: Starting similarity search")
self.logger.info(f"DATABASE QUERY: user_id={self.user_id}")
self.logger.info(f"DATABASE QUERY: embedding dimension={len(query_embedding)}")
self.logger.info(f"DATABASE QUERY: similarity_threshold={self.config.similarity_threshold}")
self.logger.info(f"DATABASE QUERY: max_chunks={self.config.max_chunks}")

# After fetching all_similarity_rows
self.logger.info(f"DATABASE QUERY: Found {len(all_similarity_rows)} total chunks")
if all_similarities:
    self.logger.info(f"DATABASE QUERY: Similarity range: {min(all_similarities):.3f} to {max(all_similarities):.3f}")

# After fetching filtered rows
self.logger.info(f"DATABASE QUERY: Found {len(rows)} chunks above threshold {self.config.similarity_threshold}")
```

**Expected Outcome:**
- Should see how many chunks exist for the user
- Should see the actual similarity scores
- Should identify if threshold is too high

### Task 5: Investigate Threading Impact on Async Queries

**Why:** The threading for embedding generation might be interfering with async database queries.

**What to Check:**
1. Are database connections being reused correctly?
2. Is the async context being maintained?
3. Are there any connection pool exhaustion issues?

**What to Add:**
```python
# In retrieve_chunks_from_text() before calling retrieve_chunks()
self.logger.info(f"THREAD CHECK: Current thread: {threading.current_thread().name}")
self.logger.info(f"THREAD CHECK: Thread is main: {threading.current_thread() == threading.main_thread()}")

# Check database connection status
import asyncpg
self.logger.info(f"DB CONNECTION: Pool size before query")
```

### Task 6: Test with Lower Similarity Threshold

**Why:** The default threshold (0.5) might be too high, filtering out all results.

**What to Try:**
```python
# Temporarily lower threshold for testing
self.config.similarity_threshold = 0.1  # or even 0.0

# Or add a diagnostic query that ignores threshold
diagnostic_sql = f"""
    SELECT COUNT(*) as total_chunks,
           COUNT(CASE WHEN 1 - (dc.embedding <=> $1::vector(1536)) > 0.5 THEN 1 END) as above_50,
           COUNT(CASE WHEN 1 - (dc.embedding <=> $1::vector(1536)) > 0.3 THEN 1 END) as above_30,
           COUNT(CASE WHEN 1 - (dc.embedding <=> $1::vector(1536)) > 0.1 THEN 1 END) as above_10,
           MAX(1 - (dc.embedding <=> $1::vector(1536))) as max_similarity
    FROM {schema}.document_chunks dc
    JOIN {schema}.documents d ON dc.document_id = d.document_id
    WHERE d.user_id = $2 AND dc.embedding IS NOT NULL
"""
```

---

## Potential Root Causes (Ranked by Likelihood)

### 1. 🔥 **No Documents/Chunks for User** (MOST LIKELY)
- **Symptom**: Always returns 0 chunks
- **Check**: Query database directly for user's chunks
- **Fix**: Investigate upload pipeline, ensure documents are being processed

### 2. 🔥 **Embedding Generation Silently Failing**
- **Symptom**: No error logs, but embeddings might be invalid
- **Check**: Add embedding validation logging
- **Fix**: Ensure OpenAI API is returning valid embeddings

### 3. 🔥 **Similarity Threshold Too High**
- **Symptom**: Chunks exist but don't meet 0.5 threshold
- **Check**: Query for similarity distribution
- **Fix**: Lower threshold or investigate embedding quality

### 4. ⚠️ **Database Query Issue**
- **Symptom**: Query not returning results despite data existing
- **Check**: Log SQL queries and results
- **Fix**: Debug SQL, check vector extension, verify indexes

### 5. ⚠️ **Threading Affecting Database Queries**
- **Symptom**: Async queries not working correctly in threaded context
- **Check**: Log thread information, check connection pool
- **Fix**: Refactor to avoid threading or ensure proper async handling

### 6. ⚠️ **Vector Embedding Dimension Mismatch**
- **Symptom**: Embeddings generated with wrong dimensions
- **Check**: Log embedding dimensions (should be 1536)
- **Fix**: Ensure correct model and dimension in queries

---

## Critical Files to Check

### Main RAG Implementation
```
agents/tooling/rag/core.py
├── retrieve_chunks_from_text() - Line 216 (Entry point)
├── _generate_embedding()       - Line 269 (Embedding generation)
└── retrieve_chunks()           - Line 78  (Database query)
```

### Observability
```
agents/tooling/rag/observability.py
├── RAGPerformanceMonitor.start_operation()  - Line 232
└── RAGObservabilityLogger                   - Line 60
```

### Configuration
```
agents/tooling/rag/config.py (if exists)
├── similarity_threshold  - Default 0.5
├── max_chunks           - Default 5
└── token_budget         - Default 4000
```

---

## Expected Success Criteria

✅ **Chunks Retrieved**: Operations return > 0 chunks when user has documents  
✅ **Diagnostic Logs**: CHECKPOINT logs appear in production  
✅ **Embedding Validation**: Embeddings are valid 1536-dimension float arrays  
✅ **Database Query**: SQL queries return results when chunks exist  
✅ **Performance**: Operations complete in < 5 seconds  
✅ **No Hangs**: No requests timeout after 120 seconds

---

## Quick Start Checklist

**Before You Start:**
- [ ] Read `FM_038_CRITICAL_DISCOVERY.md` for context on threading issue
- [ ] Read `FM_038_INVESTIGATION_SUMMARY.md` for quick overview
- [ ] Check production logs for CHECKPOINT messages
- [ ] Verify current deployment commit: `8ddd6afd`

**Investigation Order:**
1. [ ] Check database for user's chunks (Task 1) ⭐ **START HERE**
2. [ ] Look for CHECKPOINT logs in production (Task 2)
3. [ ] Add embedding validation logging (Task 3)
4. [ ] Add database query logging (Task 4)
5. [ ] Test with lower threshold if needed (Task 6)
6. [ ] Investigate threading impact (Task 5) - Only if above don't solve it

---

## Key Contacts & Resources

### Repository
- **Repo**: `andrew-quintana/insurance_navigator`
- **Branch**: `main`
- **Latest Commit**: `8ddd6afd`

### Environment
- **Platform**: Render
- **Service**: `srv-d0v2nqvdiees73cejf0g`
- **Database**: PostgreSQL with pgvector extension
- **Production URL**: `${PRODUCTION_API_URL}` (see .env)

### Documentation
- `tests/fm_038/FM_038_CRITICAL_DISCOVERY.md` - Root cause analysis
- `tests/fm_038/FM_038_INVESTIGATION_SUMMARY.md` - Quick reference
- `tests/fm_038/FM_038_DEPLOYMENT_LOGS_ANALYSIS.md` - Deployment comparison
- `tests/fm_038/FM_038_THREADING_FIX_COMPLETE.md` - Threading implementation
- `docs/technical/rag_system.md` - RAG system architecture (if exists)

### Test User
- **User ID**: `cae3b3ec-b355-4509-bd4e-0f7da8cb2858`
- **Test Queries**: Mental health services, ambulance coverage, etc.

---

## Communication Protocol

**When You Find Something:**
1. Document findings in a new `FM_038_FINDING_*.md` file
2. Add logging to confirm hypothesis
3. Test locally if possible
4. Deploy to production with clear commit message
5. Monitor production logs for 5-10 minutes
6. Report back with results

**When You're Stuck:**
1. Document what you tried in `FM_038_ATTEMPTS.md`
2. Include error logs and observations
3. List what you've ruled out
4. Ask specific questions about next steps

---

## Previous Agent Notes

**What Worked:**
- Identified OpenAI SDK network hang as root cause of original timeout
- Added comprehensive checkpoint logging
- Fixed duplicate log entries (propagate=False)
- Documented complete timeline of changes

**What Didn't Work:**
- Threading timeout doesn't prevent underlying network hang
- AsyncOpenAI in threads caused TCP transport errors
- Synchronous client helped but didn't solve core issue

**Current Theory:**
Either we're not successfully generating embeddings (and failing silently), OR we're generating embeddings but the database has no chunks to compare against, OR the similarity threshold is too high and filtering everything out.

**High Priority:**
Need to determine if this is a "no data" problem or an "embeddings broken" problem ASAP.

---

## Final Notes

This is a **CRITICAL blocker** for all RAG functionality. Users cannot get personalized insurance information without working chunk retrieval.

The investigation has been thorough on the threading/timeout side, but we haven't looked deeply enough at the retrieval logic itself. Focus there first.

Good luck! 🚀

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-09 05:30:00  
**Handoff Status:** Ready for next agent

