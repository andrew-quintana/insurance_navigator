Core Components to PRESERVE:
  1. Upload Pipeline Infrastructure: backend/, api/upload_pipeline/, workers/
  2. Agent Workflows: agents/patient_navigator/, agents/tooling/rag/
  3. Integration Documentation: docs/initiatives/system/upload_refactor/003/integration/
  4. Database Schema: sql/, supabase/migrations/, backend/scripts/migrations/
  5. Testing Infrastructure: End-to-end tests for integration validation

  Potential Cleanup Targets organized by impact risk:

⏺ Methodical Project Cleanup Plan

  Based on my analysis of the integration documentation, here's a phased cleanup approach with end-to-end testing after each phase:

  End-to-End Test Baseline

  The integration tests validate: Document Upload → 003 Processing → Vector Storage → Agent RAG Queries → Conversations

  Test command: ./scripts/run-integration-tests.sh (per RFC001.md:142-151)

  ---
  PHASE 1: Low Risk Cleanup

  Archives, deprecated code, old documentation

  Target Directories:
  - agents/archive/ - Old agent implementations superseded by agents/patient_navigator/
  - archive/ - Deprecated supabase configurations
  - backups/ - Old backup files and rollback data
  - docs/archive/ - Historical documentation not related to current integration
  - graph/sandbox/ - Experimental code marked for cleanup
  - logs/ - Old log files
  - z_prompt_sops/ - Legacy prompt operations (not referenced in integration docs)

  Validation: Run integration tests to ensure no hidden dependencies

  ---
  PHASE 2: Medium Risk Cleanup

  Development artifacts, unused tools, redundant configs

  Target Directories:
  - notebooks/ - Jupyter notebooks (development artifacts)
  - datasets/ - Old prompt datasets
  - monitoring/ (standalone) - Replaced by integration monitoring
  - infrastructure/ - Deployment scripts not used in current integration
  - parsed_output/ - Temporary processing outputs
  - mock_storage/ - Development artifacts
  - node_modules/ (multiple copies) - Dependency cleanup
  - ui/build_logs/ - Build artifacts

  Validation: Run integration tests with both mock and real APIs

  ---
  PHASE 3: High Risk Cleanup

  Core components evaluation, unused services

  Target Directories:
  - config/ (partial) - Environment configs not used by integration
  - db/ (legacy service layer) - May be superseded by upload pipeline schema
  - graph/ (workflow orchestration) - May conflict with agent workflows
  - supabase/functions/ - Edge functions if replaced by workers
  - utils/ (partial) - Utility functions not used in integration

  Validation: Comprehensive integration testing including error scenarios and performance validation

  ---
  Test Strategy Per Phase

  After each phase:
  1. Integration Test Suite: Full upload → conversation flow
  2. Mock Environment: Validate development environment setup <15 minutes
  3. Real API Environment: Validate production API integration
  4. Performance Check: Ensure no degradation in response times
  5. Error Scenarios: Test failure handling across system boundaries

  Rollback Plan: Git commit after each successful phase allows rollback if issues discovered.