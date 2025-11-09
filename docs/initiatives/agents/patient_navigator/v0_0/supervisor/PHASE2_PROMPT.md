# Phase 2: Core Implementation - Implementation Prompt

**Context**: Implement Phase 2 of Patient Navigator Supervisor Workflow MVP - core workflow prescription and document availability functionality.

## Required Reading
- `@docs/initiatives/agents/patient_navigator/supervisor/TODO001_phase1_notes.md`
- `@docs/initiatives/agents/patient_navigator/supervisor/TODO001_phase1_decisions.md`
- `@docs/initiatives/agents/patient_navigator/supervisor/TODO001_phase1_handoff.md`
- `@docs/initiatives/agents/patient_navigator/supervisor/TODO001.md` (Phase 2 section)
- Created supervisor structure from Phase 1
- `@agents/zPrototyping/sandboxes/20250621_architecture_refactor/supervisor_workflow/workflow_prescription/`

## Objective
Implement core functionality for:
- WorkflowPrescriptionAgent with LLM-based few-shot learning
- DocumentAvailabilityChecker with Supabase integration for LangGraph nodes
- LangGraph workflow node implementations with orchestration logic
- Error handling and performance tracking in workflow state management

## Key Requirements
- Implement LLM-based workflow prescription with few-shot examples in WorkflowPrescriptionAgent
- Create deterministic document availability checking as LangGraph node (not agent-based)
- Build LangGraph node methods coordinating prescription and document checking
- Meet performance targets: <2 second execution, <500ms document checking
- Support agent → check → route execution flow in LangGraph workflow

## Expected Outputs
Save phase completion documentation:
- `@docs/initiatives/agents/patient_navigator/supervisor/TODO001_phase2_notes.md`
- `@docs/initiatives/agents/patient_navigator/supervisor/TODO001_phase2_decisions.md`
- `@docs/initiatives/agents/patient_navigator/supervisor/TODO001_phase2_handoff.md`

## Success Criteria
- All Phase 2 checklist items completed
- WorkflowPrescriptionAgent works with sample queries
- DocumentAvailabilityChecker integrates with Supabase
- LangGraph workflow nodes coordinate all components
- LangGraph workflow executes end-to-end successfully
- Error handling and graceful degradation implemented in workflow state