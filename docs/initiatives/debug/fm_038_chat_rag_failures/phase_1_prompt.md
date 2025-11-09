# Phase 1 Prompt: Comprehensive Investigation Script

**Phase:** 1 - Comprehensive Investigation Script  
**Objective:** Build a script that simulates the complete chat endpoint flow with detailed logging  
**Status:** 🔴 **START HERE**  

---

## Context

You are implementing Phase 1 of the Comprehensive Chat Flow Investigation. The goal is to build a comprehensive script that orchestrates the entire chat process with detailed logging to understand every step from authentication to response, including all function inputs/outputs.

## Key Context

- **Scope**: Complete chat flow analysis, not just RAG issues
- **Focus**: Function input/output analysis and comprehensive logging
- **Goal**: Complete visibility into entire system behavior
- **Priority**: Understanding all components, not just zero-chunk issue

## Investigation Scope

### Complete Chat Flow Analysis
1. **Authentication Flow** - Login, JWT tokens, session management
2. **Request Processing** - Endpoint handling, validation, parsing
3. **Agent Orchestration** - Agent selection, function calls, coordination
4. **RAG Operations** - Embedding generation, database queries, similarity
5. **Response Generation** - LLM processing, formatting, delivery

### Function Input/Output Investigation
- **Parameter Logging**: All function inputs with types and values
- **Return Value Analysis**: All function outputs with validation
- **State Tracking**: Function state changes and side effects
- **Dependency Analysis**: Function call chains and dependencies
- **Error Propagation**: How errors flow through the system

## Authentication Credentials

- **User:** `sendaqmail@gmail.com`
- **Password:** `xasdez-katjuc-zyttI2`
- **Test User ID:** `cae3b3ec-b355-4509-bd4e-0f7da8cb2858`

## References

### Primary Documentation
- **Main Handoff:** `tests/fm_038/FM_038_AGENT_HANDOFF.md` - Complete investigation context and Task 1 details
- **Phased TODO:** `docs/initiatives/debug/fm_038_chat_rag_failures/TODO.md` - Phase 1 detailed tasks
- **RFC:** `docs/initiatives/debug/fm_038_chat_rag_failures/RFC.md` - Overall initiative context

### Supporting Documents
- **FRACAS Report:** `tests/fm_038/FM_038_FRACAS_REPORT.md` - Detailed investigation history
- **Investigation Summary:** `tests/fm_038/FM_038_INVESTIGATION_SUMMARY.md` - Quick reference
- **Database Check:** `tests/fm_038/check_database_chunks.py` - Database verification script

## Expected Deliverable

- `tests/fm_038/chat_flow_investigation.py` - Complete script with:
  - Authentication flow analysis
  - Request processing investigation
  - Agent orchestration monitoring
  - Complete function analysis
  - RAG operations deep dive
  - Response generation tracking
  - Error detection & handling
  - Detailed logs showing every step of the chat flow
  - Function input/output analysis with types and values
  - Performance timing analysis for each component
  - Error detection and silent failure identification

## Success Criteria

- Script successfully authenticates and processes chat requests
- All function calls are logged with detailed inputs/outputs
- Complete visibility into every step of the chat flow
- Clear identification of any issues or bottlenecks
- Performance metrics for all major operations
- Silent failures detected and logged

---

**Next Phase:** Phase 2 - Interactive Debugging Notebook (after Phase 1 completion)
