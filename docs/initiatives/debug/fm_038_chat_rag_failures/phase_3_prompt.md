# Phase 3 Prompt: Analysis & Documentation

**Phase:** 3 - Analysis & Documentation  
**Objective:** Document findings from investigation and plan corrective actions  
**Status:** 🔴 **Pending Phase 1-2 Completion**  

---

## Context

You are implementing Phase 3 of the Comprehensive Chat Flow Investigation. The goal is to capture findings from the comprehensive investigation, analyze all identified issues, and create a detailed plan for improvements and fixes.

## Prerequisites

- **Phase 1 Complete:** `tests/fm_038/chat_flow_investigation.py` with comprehensive findings
- **Phase 2 Complete:** `tests/fm_038/FM_038_Debug_Notebook.ipynb` with detailed analysis
- **Complete Understanding:** Should have comprehensive understanding of entire chat flow
- **All Issues Identified:** Should know all issues affecting system performance

## Key Context

- **Scope**: Complete chat flow analysis, not just RAG issues
- **Focus**: Comprehensive analysis of all identified issues and bottlenecks
- **Goal**: Document findings and plan corrective actions for entire system
- **Priority**: Understanding all components and their interactions

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

## References

### Primary Documentation
- **Main Handoff:** `tests/fm_038/FM_038_AGENT_HANDOFF.md` - Task 3 details and analysis structure
- **Phased TODO:** `docs/initiatives/debug/fm_038_chat_rag_failures/TODO.md` - Phase 3 detailed tasks
- **RFC:** `docs/initiatives/debug/fm_038_chat_rag_failures/RFC.md` - Overall initiative context

### Phase 1-2 Results
- **Investigation Script:** `tests/fm_038/chat_flow_investigation.py` - Comprehensive findings and logs
- **Debug Notebook:** `tests/fm_038/FM_038_Debug_Notebook.ipynb` - Detailed analysis results
- **Timing Analysis:** Use timing data for performance analysis
- **Function Call Trace:** Use trace data for comprehensive analysis
- **Error Patterns:** Use error data for failure analysis

### Supporting Documents
- **Existing FRACAS:** `tests/fm_038/FM_038_FRACAS_REPORT.md` - Current investigation history
- **Investigation Summary:** `tests/fm_038/FM_038_INVESTIGATION_SUMMARY.md` - Quick reference

## Expected Deliverable

- `tests/fm_038/FM_038-1_COMPREHENSIVE_ANALYSIS.md` - Complete analysis report with:
  - Comprehensive findings documentation
  - Root cause analysis for all identified issues
  - Performance analysis and bottleneck identification
  - Error analysis and silent failure documentation
  - Corrective action plan with priorities
  - Implementation strategy and timeline
  - System monitoring and debugging framework

## Success Criteria

- All issues clearly identified and documented
- Root causes analyzed and prioritized
- Corrective actions detailed and actionable
- Implementation plan is comprehensive and realistic
- Success criteria defined for all improvements
- Monitoring framework established

---

**Next Phase:** Phase 4 - Implementation & Validation (after Phase 3 completion)
