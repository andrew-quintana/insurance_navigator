# Phase 2 Prompt: Interactive Debugging Notebook

**Phase:** 2 - Interactive Debugging Notebook  
**Objective:** Convert the working script into a Jupyter notebook for step-by-step debugging  
**Status:** 🔴 **Pending Phase 1 Completion**  

---

## Context

You are implementing Phase 2 of the Comprehensive Chat Flow Investigation. The goal is to convert the working investigation script into a Jupyter notebook with individual cells for each step to enable detailed debugging, analysis, and exploration of the complete chat flow.

## Prerequisites

- **Phase 1 Complete:** `tests/fm_038/chat_flow_investigation.py` must be working
- **Script Findings:** Use findings from Phase 1 to guide notebook structure
- **Complete Analysis:** Should have comprehensive understanding of entire chat flow

## Key Context

- **Scope**: Complete chat flow analysis, not just RAG issues
- **Focus**: Function input/output analysis and comprehensive debugging
- **Goal**: Interactive exploration of entire system behavior
- **Priority**: Understanding all components through step-by-step analysis

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
- **Main Handoff:** `tests/fm_038/FM_038_AGENT_HANDOFF.md` - Task 2 details and notebook structure
- **Phased TODO:** `docs/initiatives/debug/fm_038_chat_rag_failures/TODO.md` - Phase 2 detailed tasks
- **RFC:** `docs/initiatives/debug/fm_038_chat_rag_failures/RFC.md` - Overall initiative context

### Phase 1 Results
- **Investigation Script:** `tests/fm_038/chat_flow_investigation.py` - Working script to convert
- **Script Logs:** Use logs from Phase 1 to identify key debugging points
- **Timing Analysis:** Use timing data to optimize notebook cells
- **Function Analysis:** Use input/output data to create analysis cells

### Supporting Documents
- **FRACAS Report:** `tests/fm_038/FM_038_FRACAS_REPORT.md` - Investigation history
- **Investigation Summary:** `tests/fm_038/FM_038_INVESTIGATION_SUMMARY.md` - Quick reference

## Expected Deliverable

- `tests/fm_038/FM_038_Debug_Notebook.ipynb` - Interactive notebook with:
  - Setup and environment cell
  - Authentication analysis cell
  - Request processing cell
  - Agent orchestration cells
  - Function analysis cells
  - RAG investigation cells
  - Response generation cells
  - Data analysis and visualization cells
  - Rich output and visualization
  - Clear documentation for each cell
  - Function input/output analysis tools
  - Performance profiling and bottleneck identification

## Success Criteria

- Notebook runs successfully from start to finish
- Each cell provides meaningful debugging information
- Developer can step through process interactively
- Clear identification of all issues and bottlenecks
- Rich visualization of system behavior
- Comprehensive analysis tools available

---

**Next Phase:** Phase 3 - Analysis & Documentation (after Phase 2 completion)
