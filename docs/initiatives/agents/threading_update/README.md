# Threading Update Initiative - MVP

## Overview

This MVP initiative addresses the critical hanging issue in the RAG system with a minimal, focused approach. The goal is to get the system working reliably under concurrent load without over-engineering the solution.

## Problem Statement

The RAG system's `_generate_embedding()` method in `agents/tooling/rag/core.py` causes:
- **Hanging failures** with 5+ concurrent requests
- **60+ second timeouts** 
- **Resource contention** and deadlocks
- **Poor user experience** under load

## MVP Solution

**Simple async/await conversion** - Replace the complex threading logic with basic async patterns:
- Convert `_generate_embedding()` to async method
- Use `httpx.AsyncClient` for HTTP requests  
- Remove threading and queue management
- Keep existing interfaces unchanged

## MVP Scope

**What we're doing:**
- ✅ Fix the hanging issue with minimal changes
- ✅ Convert threading to async/await
- ✅ Test with concurrent requests
- ✅ Deploy to production

**What we're NOT doing:**
- ❌ Complex architecture redesign
- ❌ Extensive connection pooling optimization
- ❌ Advanced circuit breaker patterns
- ❌ Comprehensive monitoring overhaul
- ❌ Performance optimization beyond fixing hangs

## Implementation Plan

### Step 1: Minimal Async Conversion
- Convert `_generate_embedding()` to async
- Replace threading with `httpx.AsyncClient`
- Remove queue and thread management code
- Test basic functionality

### Step 2: Concurrent Testing
- Test with 2-3 concurrent requests
- Test with 5+ concurrent requests (hanging scenario)
- Verify no timeouts or hangs
- Measure response times

### Step 3: Production Deployment
- Deploy MVP fix to production
- Monitor for hanging issues
- Validate concurrent request handling
- Confirm fix effectiveness

## Success Criteria

- ✅ No hanging with 5+ concurrent requests
- ✅ Response times under 10 seconds
- ✅ System remains stable under load
- ✅ Existing functionality preserved

## Files to Modify

- `agents/tooling/rag/core.py` - Main RAG implementation
- Test scripts for concurrent request validation

## Documentation

- [`prd.md`](./prd.md) - MVP requirements
- [`phased-todo.md`](./phased-todo.md) - MVP task tracking
- [`prompts.md`](./prompts.md) - Implementation prompts

## Related Issues

- **FM-038**: Original investigation into RAG system issues
- **Concurrent Request Hanging**: Reproduced locally with 5+ requests
- **Threading Deadlock**: Identified in `agents/tooling/rag/core.py`

## Team

- **Lead**: AI Assistant
- **Stakeholders**: Development Team
- **Reviewers**: Technical Architecture Team

## Timeline

- **Phase 1**: 1-2 days (Research & RFC)
- **Phase 2**: 3-5 days (Implementation)
- **Phase 3**: 1-2 days (Testing)
- **Phase 4**: 1 day (Deployment)

**Total Estimated Duration**: 6-10 days
