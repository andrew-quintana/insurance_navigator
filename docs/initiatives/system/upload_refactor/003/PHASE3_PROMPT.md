# Phase 3 Execution Prompt: Enhanced BaseWorker Implementation

## Context
You are implementing Phase 3 of the 003 Worker Refactor iteration. This phase implements the enhanced BaseWorker with comprehensive monitoring, logging, and local validation, building upon the local environment and infrastructure validation framework from previous phases.

## Documentation References
Please review these documents before starting implementation:
- `@docs/initiatives/system/upload_refactor/003/CONTEXT003.md` - Enhanced BaseWorker architecture and state machine implementation
- `@docs/initiatives/system/upload_refactor/003/TODO003.md` - Detailed implementation checklist (Phase 3 section)
- `@docs/initiatives/system/upload_refactor/003/RFC003.md` - Technical design for BaseWorker with comprehensive monitoring
- `@TODO003_phase2_notes.md` - Phase 2 infrastructure validation framework implementation
- `@TODO003_phase2_decisions.md` - Previous infrastructure validation decisions
- `@TODO003_phase2_handoff.md` - BaseWorker implementation requirements from Phase 2
- `@docs/initiatives/system/upload_refactor/002/CONTEXT002.md` - Original BaseWorker architecture foundation

## Primary Objective
Implement enhanced BaseWorker with comprehensive monitoring including:
1. BaseWorker core with enhanced monitoring and state machine processing
2. State machine implementation with comprehensive local validation
3. External service integration with resilience and error handling
4. Local testing and validation framework with complete coverage

## Key Implementation Requirements

### BaseWorker Core with Enhanced Monitoring
- Implement BaseWorker class with comprehensive logging and correlation ID tracking
- Create job polling mechanism with efficient database queries and health monitoring
- Add stage-specific processing methods with detailed progress tracking and metrics
- Implement comprehensive error handling with classification and recovery procedures

### State Machine Implementation with Local Validation
- Implement all state machine transitions with comprehensive local testing coverage
- Create buffer operations with idempotent writes and integrity validation
- Develop external service integration with both mock and real API testing
- Build progress tracking and monitoring with real-time updates and correlation

### External Service Integration with Resilience
- Implement LlamaParse integration with webhook handling and security validation
- Create OpenAI micro-batch processing with rate limiting and cost tracking
- Develop circuit breaker patterns and comprehensive retry logic with exponential backoff
- Build external service monitoring and failure detection systems

### Local Testing and Validation Framework
- Create comprehensive unit testing for all state machine transitions and edge cases
- Implement integration testing with mock services and real external APIs
- Develop performance testing and bottleneck identification procedures
- Build end-to-end validation testing with realistic document processing scenarios

## Expected Outputs
Document your work in these files:
- `@TODO003_phase3_notes.md` - BaseWorker implementation details and processing patterns
- `@TODO003_phase3_decisions.md` - Processing architecture decisions and trade-offs
- `@TODO003_phase3_handoff.md` - Local validation requirements for Phase 4
- `@TODO003_phase3_testing_summary.md` - Performance testing results and optimization findings

## Success Criteria
- BaseWorker processes all job stages from `parsed` through `complete` status successfully
- All state machine transitions validated in local environment with comprehensive test coverage
- External service integration handles success, failure, and rate limiting scenarios appropriately
- Micro-batch embedding processes large documents efficiently within memory limits
- Comprehensive monitoring provides real-time visibility into processing stages and health
- Local testing framework validates complete pipeline functionality before deployment

## Implementation Notes
- Follow the enhanced BaseWorker architecture specified in RFC003.md and CONTEXT003.md
- Build upon the local environment and infrastructure validation framework from previous phases
- Implement comprehensive monitoring and logging with correlation IDs for all processing stages
- Use both mock services and real external APIs for integration testing
- Focus on preventing the silent failures and processing issues experienced in 002
- Ensure all operations are idempotent and can resume from any failure point

## Critical Validation Points
- **State Machine Coverage**: 100% of state transitions tested and validated in local environment
- **Buffer Operations**: All buffer operations tested with real database constraints and idempotency
- **External Service Integration**: Both mock and real API integration tested with failure scenarios
- **Performance Validation**: Large document processing validated within memory and time constraints
- **Monitoring Integration**: Comprehensive monitoring operational with real-time status updates
- **Error Handling**: All error scenarios handled appropriately with proper classification and recovery

Start by reading all referenced documentation and previous phase outputs, then implement the enhanced BaseWorker following the detailed Phase 3 checklist and comprehensive validation requirements.