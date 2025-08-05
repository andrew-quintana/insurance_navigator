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
- DocumentAvailabilityChecker with Supabase integration
- SupervisorWorkflowAgent orchestration logic
- Error handling and performance tracking

## Key Requirements
- Implement LLM-based workflow prescription with few-shot examples
- Create deterministic document availability checking (not agent-based)
- Build orchestration logic coordinating prescription and document checking
- Meet performance targets: <2 second execution, <500ms document checking
- Support information_retrieval → strategy execution order

## Expected Outputs
Save phase completion documentation:
- `@docs/initiatives/agents/patient_navigator/supervisor/TODO001_phase2_notes.md`
- `@docs/initiatives/agents/patient_navigator/supervisor/TODO001_phase2_decisions.md`
- `@docs/initiatives/agents/patient_navigator/supervisor/TODO001_phase2_handoff.md`

## Success Criteria
- All Phase 2 checklist items completed
- Workflow prescription works with sample queries
- Document availability checking integrates with Supabase
- Orchestration logic coordinates all components
- Error handling and graceful degradation implemented